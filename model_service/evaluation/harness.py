"""Avaliação offline do bandit contra o golden set (Etapa 4).

Roda direto sobre o `BanditService` — sem HTTP, sem Postgres, sem Redis (usa um store em
memória). É deliberado: um harness que só roda no CI não serve para demonstrar nada.

## O que ele mede

Um **relatório de propriedades**, não de performance:

- `edge` — elegibilidade: o braço proibido pelo catálogo não aparece no ranking. Falha aqui
  é bug de conformidade, e o critério é ground truth (vem dos `santander_filters`).
- `adversarial` — invariância de fairness: variar um atributo protegido não altera a ordem
  do ranking. Falha aqui é vazamento de atributo protegido para a decisão.
- `typical` — conformidade com a regra do baseline. **Informativo**: divergência do LinUCB
  é aprendizado, não erro. Reportado em separado e fora da taxa de aprovação.

Regret, conversão e lift **não** saem daqui: dependem de tráfego real e vêm do monitoramento
(`api_service/services/monitoring`). Golden set produz garantia, não performance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from service import BanditService

#: Tipos cujo resultado entra na taxa de aprovação. `typical` fica fora de propósito;
#: `invalid` entra porque caso mal formado é falha do golden set, não resultado neutro.
BLOCKING_TYPES = ("edge", "adversarial", "invalid")

#: Políticas que amostram a cada chamada — a ORDEM do ranking varia entre execuções
#: idênticas por desenho. Para elas a invariância verificável é o *conjunto* elegível, não
#: a ordem; exigir ordem estável confundiria aleatoriedade com vazamento de atributo.
STOCHASTIC = ("thompson",)


@dataclass
class CaseResult:
    case_id: str
    type: str
    passed: bool
    detail: str = ""


@dataclass
class EvaluationReport:
    algorithm: str
    results: list[CaseResult] = field(default_factory=list)

    @property
    def blocking(self) -> list[CaseResult]:
        return [r for r in self.results if r.type in BLOCKING_TYPES]

    @property
    def informational(self) -> list[CaseResult]:
        return [r for r in self.results if r.type not in BLOCKING_TYPES]

    @property
    def passed(self) -> bool:
        """Só as propriedades bloqueiam. Conformidade com baseline nunca reprova.

        Relatório sem nenhum caso bloqueante é reprovado: `all([])` é `True`, e um golden
        set vazio passando silenciosamente é pior que uma falha.
        """
        blocking = self.blocking
        return bool(blocking) and all(r.passed for r in blocking)

    def summary(self) -> dict[str, Any]:
        by_type: dict[str, dict[str, int]] = {}
        for r in self.results:
            slot = by_type.setdefault(r.type, {"total": 0, "passed": 0})
            slot["total"] += 1
            slot["passed"] += int(r.passed)
        return {
            "algorithm": self.algorithm,
            "passed": self.passed,
            "by_type": by_type,
            "failures": [
                {"case_id": r.case_id, "type": r.type, "detail": r.detail}
                for r in self.results
                if not r.passed
            ],
        }


def load_cases(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


async def _ranked_ids(service: BanditService, algorithm: str, context: dict) -> list[str]:
    segments = list(context.get("segmentos_sinteticos") or [])
    result = await service.rank(algorithm, dict(context), segments)
    return [r["arm_id"] for r in result["ranked"]]


async def _check_edge(service: BanditService, algorithm: str, case: dict) -> CaseResult:
    forbidden = case["forbidden_arm"]
    ranked = await _ranked_ids(service, algorithm, case["context"])
    ok = forbidden not in ranked
    return CaseResult(
        case["case_id"],
        case["type"],
        ok,
        "" if ok else f"braço inelegível {forbidden} apareceu no ranking",
    )


async def _check_adversarial(service: BanditService, algorithm: str, case: dict) -> CaseResult:
    """Variar o atributo protegido não pode mudar o que o cliente pode receber.

    Para política determinística exigimos a ordem idêntica. Para estocástica, o conjunto:
    Thompson amostra a cada chamada, então duas execuções com o MESMO contexto já divergem
    na ordem — reprovar por isso seria medir o gerador de números aleatórios.
    """
    (attr, values), *_ = case["perturbation"].items()
    rankings = []
    for value in values:
        ranked = await _ranked_ids(service, algorithm, {**case["context"], attr: value})
        rankings.append(ranked)

    if algorithm in STOCHASTIC:
        ok = all(set(r) == set(rankings[0]) for r in rankings)
        what = "conjunto elegível mudou"
    else:
        ok = all(r == rankings[0] for r in rankings)
        what = "ranking mudou"
    return CaseResult(
        case["case_id"],
        case["type"],
        ok,
        "" if ok else f"{what} ao variar `{attr}` — atributo protegido influenciou",
    )


async def _check_typical(service: BanditService, algorithm: str, case: dict) -> CaseResult:
    ranked = await _ranked_ids(service, algorithm, case["context"])
    expected = case["expected_arm"]
    ok = bool(ranked) and ranked[0] == expected
    return CaseResult(
        case["case_id"],
        case["type"],
        ok,
        "" if ok else f"topo={ranked[0] if ranked else None}, baseline diria {expected}",
    )


_CHECKS = {"edge": _check_edge, "adversarial": _check_adversarial, "typical": _check_typical}


async def evaluate(
    service: BanditService, cases: list[dict], algorithm: str = "linucb"
) -> EvaluationReport:
    """Roda todos os casos contra um algoritmo. Caso de tipo desconhecido é reprovado."""
    report = EvaluationReport(algorithm=algorithm)
    for case in cases:
        check = _CHECKS.get(case.get("type", ""))
        if check is None:
            # tipo "invalid" (bloqueante) e não o tipo original: um caso que o harness não
            # sabe checar não pode ser contabilizado como neutro.
            report.results.append(
                CaseResult(case.get("case_id", "?"), "invalid", False, "tipo inválido")
            )
            continue
        report.results.append(await check(service, algorithm, case))
    return report
