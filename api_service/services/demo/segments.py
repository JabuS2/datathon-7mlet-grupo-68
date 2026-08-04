"""Classificação nos segmentos sintéticos do `offer_catalog.json`.

Porte das regras de `scripts/generate_golden_sample.py::compute_segments`, que produziu a
coluna `segmentos_sinteticos` do golden set. Aqui elas são aplicadas **em runtime**, ao
perfil montado no onboarding.

Por que recalcular em vez de copiar do template: as regras dependem de idade, renda,
`ind_ativo`, tempo de relacionamento e cinco flags de posse — justamente o que as respostas
do visitante sobrescrevem. Copiar a lista do template colava, por exemplo, `SEG-SENIOR` num
respondente de 25 anos, e os segmentos entram no vetor de contexto do LinUCB (one-hot) e na
escolha de categoria do baseline. Perfil internamente contraditório treina o modelo errado.

`SEG-VIAJANTE-EVENTO` não sai daqui: no golden set ele é sintético (~8% aleatório) e vem do
campo `evento_viagem_sintetico`, copiado do template.
"""

from __future__ import annotations

from typing import Any


def compute_segments(client: dict[str, Any], renda_percentil: float) -> list[str]:
    """Segmentos do cliente. `renda_percentil` é 0–100, relativo à base de clientes."""

    def flag(name: str) -> int:
        return 1 if client.get(name) else 0

    idade = int(client.get("idade") or 0)
    tempo = int(client.get("tempo_relacionamento_meses") or 0)
    ativo = flag("ind_ativo")
    segmento = client.get("segmento") or ""

    rules: dict[str, bool] = {
        "SEG-VIP": segmento == "01 - ALTA RENDA",
        "SEG-JOVEM": idade < 30,
        "SEG-SENIOR": idade >= 55,
        "SEG-ALTA-RENDA": renda_percentil >= 70 and 25 <= idade <= 55,
        "SEG-CREDITO-ATIVO": (
            ativo == 1
            and tempo >= 6
            and renda_percentil >= 50
            and flag("possui_emprestimo_pessoal") == 0
        ),
        "SEG-SEM-CARTAO": flag("possui_cartao_credito") == 0 and ativo == 1 and tempo >= 3,
        "SEG-INVESTIDOR-INICIANTE": flag("possui_fundo_investimento") == 0 and ativo == 1,
        "SEG-POUPADOR": flag("possui_cdb_curto_prazo") == 0 and renda_percentil >= 50,
        "SEG-CONTRIBUINTE-IR": (
            flag("possui_previdencia_privada") == 0
            and renda_percentil >= 60
            and 30 <= idade <= 60
        ),
        "SEG-INVESTIDOR-EXPERIENTE": (
            flag("possui_titulos_investimento") == 0 and flag("possui_fundo_investimento") == 1
        ),
        "SEG-PERFIL-FAMILIAR": 25 <= idade <= 60 and ativo == 1,
        "SEG-PROPRIETARIO": flag("possui_financiamento_imovel") == 1,
    }
    segments = [name for name, matches in rules.items() if matches]

    # sintético no golden set (~8%): não é derivável do perfil, vem do template
    if client.get("evento_viagem_sintetico"):
        segments.append("SEG-VIAJANTE-EVENTO")
    return segments
