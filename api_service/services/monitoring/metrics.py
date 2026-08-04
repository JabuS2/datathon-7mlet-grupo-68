"""Cálculo das métricas de monitoramento — funções puras sobre o log auditável.

Separado do serviço para ser testável sem banco: recebe listas de tuplas, devolve números.
As definições estão aqui porque são a parte que precisa ser defensável na apresentação, não
a query.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass

#: Faixas do PSI usadas na indústria: <0.1 estável, 0.1–0.25 mudança moderada, >0.25 relevante.
PSI_ALERT_THRESHOLD = 0.25
#: Bins fixos de percentil de renda — comparar distribuições exige bins iguais nos dois períodos.
PSI_BINS = (0.0, 20.0, 40.0, 60.0, 80.0, 100.0)
#: Suaviza bin vazio: sem isso o PSI vira infinito quando um período não tem nenhuma amostra
#: numa faixa, o que é ruído de amostra pequena e não drift.
_EPS = 1e-6
#: Braço com menos que isto no período não é candidato a "melhor" — taxa ruidosa demais.
_MIN_PULLS = 5


@dataclass(frozen=True)
class Metric:
    name: str
    value: float
    alert: bool = False


def conversion_rate(rewards: list[float]) -> float:
    """Fração de decisões premiadas. Reward é binário, então é média de 0/1."""
    if not rewards:
        return 0.0
    return sum(1.0 for r in rewards if r >= 1.0) / len(rewards)


def mean_reward(rewards: list[float]) -> float:
    if not rewards:
        return 0.0
    return sum(rewards) / len(rewards)


def empirical_regret(observations: list[tuple[str, float]]) -> float:
    """Regret médio por decisão contra o **melhor braço observado no período**.

    Não existe oráculo aqui: o reward contrafactual dos braços não servidos é desconhecido.
    O que dá para medir honestamente é o arrependimento contra a melhor taxa empírica
    observada — `regret = p(melhor braço) − p(braço servido)`, média sobre as decisões.

    Limitação que precisa ser dita junto do número: braços pouco servidos têm taxa ruidosa,
    e um braço com uma única impressão convertida vira "o melhor" com p=1.0. Por isso só
    entram no cálculo do melhor os braços com pelo menos `_MIN_PULLS` observações.
    """
    if not observations:
        return 0.0

    per_arm: dict[str, list[float]] = defaultdict(list)
    for arm_id, reward in observations:
        per_arm[arm_id].append(reward)

    rates = {
        arm: sum(1.0 for r in rs if r >= 1.0) / len(rs)
        for arm, rs in per_arm.items()
        if len(rs) >= _MIN_PULLS
    }
    if not rates:
        return 0.0

    best = max(rates.values())
    total = sum(best - rates.get(arm, 0.0) for arm, _ in observations)
    return max(total / len(observations), 0.0)


def _histogram(values: list[float]) -> list[float]:
    counts: Counter[int] = Counter()
    for v in values:
        for i in range(len(PSI_BINS) - 1):
            lo, hi = PSI_BINS[i], PSI_BINS[i + 1]
            # último bin fecha à direita para não perder o valor máximo
            if lo <= v < hi or (i == len(PSI_BINS) - 2 and v == hi):
                counts[i] += 1
                break
    total = sum(counts.values()) or 1
    return [counts[i] / total for i in range(len(PSI_BINS) - 1)]


def psi(reference: list[float], current: list[float]) -> float:
    """Population Stability Index entre duas distribuições de percentil de renda.

    `Σ (atual − ref) · ln(atual / ref)` sobre bins fixos. Mede se o público que está sendo
    servido mudou — é drift de *entrada*, não de performance, e por isso complementa o
    regret em vez de substituí-lo.
    """
    if not reference or not current:
        return 0.0
    ref_h, cur_h = _histogram(reference), _histogram(current)
    total = 0.0
    for r, c in zip(ref_h, cur_h, strict=True):
        r, c = max(r, _EPS), max(c, _EPS)
        total += (c - r) * math.log(c / r)
    return abs(total)


def build_metrics(
    observations: list[tuple[str, float]],
    reference_renda: list[float],
    current_renda: list[float],
) -> list[Metric]:
    """Conjunto completo de métricas de um período."""
    rewards = [r for _, r in observations]
    drift = psi(reference_renda, current_renda)
    return [
        Metric("conversion", round(conversion_rate(rewards), 6)),
        Metric("reward", round(mean_reward(rewards), 6)),
        Metric("regret", round(empirical_regret(observations), 6)),
        Metric("psi_drift", round(drift, 6), alert=drift > PSI_ALERT_THRESHOLD),
    ]
