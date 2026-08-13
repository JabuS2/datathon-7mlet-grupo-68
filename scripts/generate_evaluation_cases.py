"""Gera o golden set de avaliação offline a partir dos dados reais.

    python scripts/generate_evaluation_cases.py     # ou: make data-eval

Saída: `data/golden_set/evaluation_cases.jsonl` — **versionado**, ao contrário das camadas
derivadas grandes. É ground truth de teste: pequeno, determinístico e precisa estar num
clone limpo para o harness rodar.

## O que é e o que não é ground truth

Cada caso declara uma **propriedade verificável nos dados**, não um "melhor braço" que
alguém arbitrou. Dois tipos carregam verdade de fato:

- `edge` — **elegibilidade**. Os `santander_filters` do catálogo definem quem é inelegível.
  "Este braço NÃO pode aparecer no ranking deste cliente" é checável contra o dado.
- `adversarial` — **invariância de fairness**. Dois clientes idênticos exceto por um
  atributo protegido têm de produzir o mesmo ranking. É regressão da exclusão de `sexo`.

O terceiro tipo é declaradamente mais fraco:

- `typical` — **conformidade com o baseline**, não correção. O braço esperado é o primeiro
  elegível, na ordem do catálogo, dentro da categoria-alvo — exatamente o que o
  `DeterministicBaseline` faz. Se o LinUCB diverge, isso é o bandit aprendendo, não um erro. O harness reporta esses casos em separado e eles **não** entram
  numa taxa de acerto que possa ser lida como qualidade do modelo.

Nenhum caso mede regret, conversão ou lift: esses vêm de tráfego real, via o monitoramento
da Fase 5. Um golden set não produz performance, produz garantias.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(BASE_DIR, "data", "golden_set")
CATALOG_PATH = os.path.join(GOLDEN, "sexo.json")
CLIENTS_PATH = os.path.join(GOLDEN, "golden_clients.csv")
OUTPUT_PATH = os.path.join(GOLDEN, "evaluation_cases.jsonl")

#: Colunas do cliente que compõem o contexto do caso. `sexo` fica de fora do contexto
#: normal de propósito — só os casos `adversarial` o injetam, para provar que não muda nada.
CONTEXT_COLUMNS = (
    "idade",
    "renda_estimada_anual_brl",
    "tempo_relacionamento_meses",
    "ind_ativo",
    "possui_conta_corrente",
    "possui_cartao_credito",
    "possui_conta_investimento",
    "possui_fundo_investimento",
    "possui_financiamento_imovel",
    "possui_emprestimo_pessoal",
    "possui_previdencia_privada",
    "segmento",
)

CASES_PER_TYPE = 8


def _num(value: str) -> Any:
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return float(value)
        except (TypeError, ValueError):
            return value


def _load_clients(limit: int = 400) -> list[dict]:
    with open(CLIENTS_PATH, encoding="utf-8") as fh:
        rows = []
        for i, row in enumerate(csv.DictReader(fh)):
            if i >= limit:
                break
            ctx = {c: _num(row[c]) for c in CONTEXT_COLUMNS if c in row}
            ctx["segmentos_sinteticos"] = json.loads(
                row.get("segmentos_sinteticos") or "[]"
            )
            ctx["cod_cliente"] = _num(row["cod_cliente"])
            ctx["_sexo"] = row.get("sexo")
            rows.append(ctx)
    return rows


def _load_offers() -> list[dict]:
    with open(CATALOG_PATH, encoding="utf-8") as fh:
        return json.load(fh)["offers"]


def _violates(client: dict, filters: dict) -> str | None:
    """Devolve a razão da inelegibilidade, ou None. Só regras checáveis pelo contexto."""
    for key, expected in filters.items():
        if key.endswith("_min"):
            field = key[: -len("_min")]
            if field in client and client[field] < expected:
                return f"{field} < {expected}"
        elif key.endswith("_max"):
            field = key[: -len("_max")]
            if field in client and client[field] > expected:
                return f"{field} > {expected}"
        elif key.endswith("_atual"):
            # sufixo "_atual" mapeia para a flag de posse sem o sufixo
            field = key[: -len("_atual")]
            if field in client and int(client[field]) != int(expected):
                return f"{field} != {expected}"
        elif key in client and int(client[key]) != int(expected):
            return f"{key} != {expected}"
    return None


def _edge_cases(clients: list[dict], offers: list[dict]) -> list[dict]:
    """Cliente × braço em que o catálogo diz, pelos filtros, que ele é inelegível."""
    cases = []
    for client in clients:
        for offer in offers:
            reason = _violates(client, offer["eligible_segment"]["santander_filters"])
            if reason is None:
                continue
            ctx = {k: v for k, v in client.items() if not k.startswith("_")}
            cases.append(
                {
                    "case_id": f"EDGE-{client['cod_cliente']}-{offer['arm_id']}",
                    "type": "edge",
                    "context": ctx,
                    "forbidden_arm": offer["arm_id"],
                    "expected_arm": None,
                    "rationale": (
                        f"Filtro do catálogo viola: {reason}. O braço {offer['arm_id']} não "
                        "pode aparecer no ranking deste cliente."
                    ),
                    "pass_fail_criteria": "forbidden_arm ausente de ranked[]",
                }
            )
            break  # um caso por cliente mantém o golden set legível
        if len(cases) >= CASES_PER_TYPE:
            break
    return cases


def _adversarial_cases(clients: list[dict]) -> list[dict]:
    """Mesmo cliente com `sexo` diferente: o ranking tem de ser idêntico."""
    cases = []
    for client in clients[:CASES_PER_TYPE]:
        ctx = {k: v for k, v in client.items() if not k.startswith("_")}
        cases.append(
            {
                "case_id": f"ADV-{client['cod_cliente']}-sexo",
                "type": "adversarial",
                "context": ctx,
                "perturbation": {"sexo": ["M", "F"]},
                "expected_arm": None,
                "rationale": (
                    "Atributo protegido não entra na decisão: variar `sexo` não pode alterar "
                    "a ordem do ranking."
                ),
                "pass_fail_criteria": "ranking idêntico para todos os valores da perturbação",
            }
        )
    return cases


def _typical_cases(clients: list[dict], offers: list[dict]) -> list[dict]:
    """Conformidade com a regra de negócio do baseline — NÃO é medida de qualidade."""
    # Ordem do CATÁLOGO, não por receita: o `DeterministicBaseline` pontua 1.0 para a
    # categoria-alvo e desempata por `arm_index`. Ordenar por receita aqui faria o caso
    # "conformidade com baseline" divergir do baseline — foi o que aconteceu na 1ª versão.
    by_category: dict[str, list[dict]] = {}
    for offer in offers:
        by_category.setdefault(offer["category"], []).append(offer)

    cases = []
    for client in clients:
        segments = client.get("segmentos_sinteticos") or []
        target = _target_category(client, segments)
        candidates = [
            o
            for o in by_category.get(target, [])
            if _violates(client, o["eligible_segment"]["santander_filters"]) is None
        ]
        if not candidates:
            continue
        ctx = {k: v for k, v in client.items() if not k.startswith("_")}
        cases.append(
            {
                "case_id": f"TYP-{client['cod_cliente']}",
                "type": "typical",
                "context": ctx,
                "expected_arm": candidates[0]["arm_id"],
                "rationale": (
                    f"Regra do baseline: categoria-alvo '{target}', primeiro elegível na ordem "
                    "do catálogo. Divergência do LinUCB é aprendizado, não erro."
                ),
                "pass_fail_criteria": "informativo — conformidade com baseline, não correção",
            }
        )
        if len(cases) >= CASES_PER_TYPE:
            break
    return cases


def _target_category(client: dict, segments: list[str]) -> str:
    """Mesma regra do `DeterministicBaseline` do model_service."""
    renda = float(client.get("renda_estimada_anual_brl") or 0.0)
    if client.get("segmento") == "01 - ALTA RENDA" or "SEG-VIP" in segments:
        return "investimento"
    if "SEG-INVESTIDOR-EXPERIENTE" in segments:
        return "investimento"
    if "SEG-SENIOR" in segments or "SEG-PROPRIETARIO" in segments:
        return "seguro"
    if "SEG-CREDITO-ATIVO" in segments or "SEG-SEM-CARTAO" in segments:
        return "credito"
    if "SEG-JOVEM" in segments:
        return "credito"
    if "SEG-PERFIL-FAMILIAR" in segments:
        return "seguro"
    if renda > 80_000:
        return "investimento"
    return "credito"


def main() -> int:
    clients, offers = _load_clients(), _load_offers()
    cases = _edge_cases(clients, offers) + _adversarial_cases(clients)
    cases += _typical_cases(clients, offers)

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="\n") as fh:
        for case in cases:
            fh.write(json.dumps(case, ensure_ascii=False, sort_keys=True) + "\n")

    counts: dict[str, int] = {}
    for case in cases:
        counts[case["type"]] = counts.get(case["type"], 0) + 1
    print(f"{len(cases)} casos -> {OUTPUT_PATH}")
    for tipo, n in sorted(counts.items()):
        print(f"   {tipo:<12} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
