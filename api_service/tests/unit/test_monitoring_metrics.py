"""Definições das métricas de monitoramento — lógica pura, sem banco.

O que estes testes protegem não é a query: é a *definição*. Regret contra o melhor braço
empírico e PSI sobre percentil de renda são os números que vão para a apresentação, então
o comportamento em amostra pequena e em caso degenerado precisa ser o declarado.
"""

import pytest

from services.monitoring.metrics import (
    PSI_ALERT_THRESHOLD,
    build_metrics,
    conversion_rate,
    empirical_regret,
    mean_reward,
    psi,
)


def test_conversao_e_media_de_zero_um():
    assert conversion_rate([1.0, 0.0, 1.0, 0.0]) == 0.5
    assert conversion_rate([]) == 0.0
    assert mean_reward([1.0, 0.0]) == 0.5


def test_regret_zero_quando_so_ha_um_braco():
    """Sem alternativa observada não há arrependimento a medir."""
    obs = [("A", 1.0)] * 10
    assert empirical_regret(obs) == 0.0


def test_regret_mede_distancia_para_o_melhor_braco():
    # A converte 100% (10 obs), B converte 0% (10 obs) → metade das decisões perde 1.0
    obs = [("A", 1.0)] * 10 + [("B", 0.0)] * 10
    assert empirical_regret(obs) == pytest.approx(0.5)


def test_regret_ignora_braco_com_poucas_observacoes():
    """Um braço com 1 impressão convertida não pode virar "o melhor" e inflar o regret."""
    obs = [("A", 0.0)] * 20 + [("SORTUDO", 1.0)]
    # SORTUDO tem p=1.0 mas só 1 observação: fica fora do cálculo do melhor
    assert empirical_regret(obs) == 0.0


def test_regret_nunca_negativo():
    obs = [("A", 1.0)] * 6 + [("B", 1.0)] * 6
    assert empirical_regret(obs) >= 0.0


def test_psi_zero_para_distribuicoes_iguais():
    dist = [10.0, 30.0, 50.0, 70.0, 90.0] * 4
    assert psi(dist, dist) == pytest.approx(0.0, abs=1e-9)


def test_psi_alto_quando_o_publico_muda_de_faixa():
    baixa = [5.0, 10.0, 15.0] * 10
    alta = [85.0, 90.0, 95.0] * 10
    assert psi(baixa, alta) > PSI_ALERT_THRESHOLD


def test_psi_finito_com_bin_vazio():
    """Bin sem amostra num dos períodos não pode virar infinito — é ruído, não drift."""
    ref = [10.0] * 10  # só o primeiro bin
    cur = [90.0] * 10  # só o último
    valor = psi(ref, cur)
    assert valor == valor and valor != float("inf")  # não é NaN nem inf


def test_psi_zero_sem_dados():
    assert psi([], [1.0]) == 0.0
    assert psi([1.0], []) == 0.0


def test_build_metrics_marca_alerta_so_no_drift():
    obs = [("A", 1.0)] * 6 + [("B", 0.0)] * 6
    metrics = {m.name: m for m in build_metrics(obs, [10.0] * 10, [90.0] * 10)}

    assert set(metrics) == {"conversion", "reward", "regret", "psi_drift"}
    assert metrics["conversion"].value == pytest.approx(0.5)
    assert metrics["psi_drift"].alert is True
    # as demais não são alerta por si só — quem decide limiar de negócio é o operador
    assert metrics["conversion"].alert is False
    assert metrics["regret"].alert is False


def test_build_metrics_com_periodo_vazio_nao_explode():
    metrics = {m.name: m.value for m in build_metrics([], [], [])}
    assert metrics == {"conversion": 0.0, "reward": 0.0, "regret": 0.0, "psi_drift": 0.0}
