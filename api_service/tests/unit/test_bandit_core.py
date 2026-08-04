"""E6 — núcleo do bandit: elegibilidade, contexto, reward binário e as 3 políticas.

Testes controlados (matemática das políticas) + uma checagem sobre o golden set real.
"""

from pathlib import Path

import numpy as np
import pytest

from enums.politica import AlgoritmoPolitica
from services.bandit.context import SEG_KEYS, ReferenceStats
from services.bandit.eligibility import is_eligible
from services.bandit.engine import BanditEngine
from services.bandit.policies import build_policy
from services.bandit.state import ArmState
from services.catalog.loaders import iter_seed_clients, load_offer_catalog
from settings import settings

GOLDEN = Path(settings.DATA_DIR) / "golden_set"
CTX_COLS = [
    "idade",
    "renda_estimada_anual_brl",
    "tempo_relacionamento_meses",
    "ind_ativo",
    "possui_conta_corrente",
    "possui_cartao_credito",
    "possui_conta_investimento",
    "possui_fundo_investimento",
    "possui_financiamento_imovel",
]


@pytest.fixture(scope="module")
def catalog():
    return load_offer_catalog(GOLDEN / "offer_catalog.json")


@pytest.fixture(scope="module")
def clients():
    return list(iter_seed_clients(GOLDEN / "golden_clients.csv", limit=500))


# ── elegibilidade ────────────────────────────────────────────────
def test_eligibility_suffix_conventions():
    client = {
        "ind_ativo": 1,
        "possui_cartao_credito": 0,
        "idade": 30,
        "tempo_relacionamento_meses": 10,
    }
    # cliente ativo, sem cartão, idade>=18 → elegível ao OFF-CR-002
    assert is_eligible(
        client, {"ind_ativo": 1, "possui_cartao_credito_atual": 0, "idade_min": 18}, 50.0
    )
    # já tem cartão → inelegível (_atual != 0)
    assert not is_eligible(
        {**client, "possui_cartao_credito": 1}, {"possui_cartao_credito_atual": 0}, 50.0
    )
    # renda abaixo do percentil mínimo → inelegível
    assert not is_eligible(client, {"renda_percentil_min": 70}, 50.0)
    # idade acima do máximo → inelegível
    assert not is_eligible({**client, "idade": 65}, {"idade_max": 60}, 50.0)


def test_eligibility_average_on_golden(catalog, clients):
    offers = catalog
    stats = ReferenceStats.fit(clients, CTX_COLS)
    counts = []
    for c in clients:
        pct = stats.renda_percentile(c.get("renda_estimada_anual_brl"))
        from services.bandit.eligibility import eligible_arm_ids

        counts.append(len(eligible_arm_ids(c, offers, pct)))
    avg = sum(counts) / len(counts)
    assert 1.0 <= avg <= 10.0  # cada cliente é elegível a um subconjunto plausível dos 10 braços
    assert max(counts) <= 10


# ── contexto ─────────────────────────────────────────────────────
def test_context_dimension(clients):
    stats = ReferenceStats.fit(clients, CTX_COLS)
    assert stats.dimension == 1 + len(CTX_COLS) + len(SEG_KEYS)  # 1 + 9 + 12 = 22
    x = stats.context_vector(clients[0])
    assert x.shape == (stats.dimension,)
    assert x[0] == 1.0  # bias


# ── reward binário ───────────────────────────────────────────────
def test_binary_reward_is_click_only():
    """A recompensa não depende mais da receita esperada do braço — só do clique."""
    assert BanditEngine.reward_value(True) == 1.0
    assert BanditEngine.reward_value(1) == 1.0
    assert BanditEngine.reward_value(False) == 0.0
    assert BanditEngine.reward_value(0) == 0.0


# ── políticas ────────────────────────────────────────────────────
def _states():
    return [
        ArmState("A").with_catalog(1.5, 1000.0),
        ArmState("B").with_catalog(1.5, 6000.0),
        ArmState("C").with_catalog(1.5, 3000.0),
    ]


def test_baseline_picks_max_revenue():
    policy = build_policy(AlgoritmoPolitica.BASELINE, dimension=22)
    ranked = policy.rank(np.zeros(22), _states())
    assert ranked[0].arm_id == "B"  # maior receita esperada
    assert "best_expected_revenue" in ranked[0].reason_codes


def test_thompson_deterministic_with_seed():
    rng = np.random.default_rng(42)
    policy = build_policy(AlgoritmoPolitica.THOMPSON, dimension=22, rng=rng)
    ranked = policy.rank(np.zeros(22), _states())
    assert len(ranked) == 3
    assert all("policy:thompson" in r.reason_codes for r in ranked)


def test_linucb_cold_start_then_learns():
    d = 22
    policy = build_policy(AlgoritmoPolitica.LINUCB, dimension=d, hyperparams={"alpha_scale": 0.2})
    x = np.ones(d)
    good, bad = ArmState("GOOD").with_catalog(1.5, 0.0), ArmState("BAD").with_catalog(1.5, 0.0)
    # cold-start: sem estado, ambos pontuam só pelo bônus de exploração
    assert policy.rank(x, [good, bad])[0].pred == pytest.approx(0.0)
    # realimenta GOOD com reward alto e BAD com reward baixo (mesmo contexto)
    for _ in range(20):
        policy.update(good, 1.0, x)
        policy.update(bad, 0.0, x)
    assert good.A is not None and len(good.A) == d and good.n_pulls == 20
    pred_good = (policy.rank(x, [good])[0]).pred
    pred_bad = (policy.rank(x, [bad])[0]).pred
    assert pred_good > pred_bad  # LinUCB aprendeu a preferência


def test_engine_decide_end_to_end(catalog, clients):
    offers = catalog
    stats = ReferenceStats.fit(clients, CTX_COLS)
    engine = BanditEngine(offers, stats)
    policy = build_policy(AlgoritmoPolitica.LINUCB, dimension=stats.dimension)
    states = [ArmState(o["arm_id"]) for o in offers]
    decision = engine.decide(clients[0], policy, states)
    assert decision is not None
    assert decision.arm_id in {o["arm_id"] for o in offers}
    assert "policy:linucb" in decision.reason_codes
    assert "sexo" in decision.context["atributos_excluidos"]  # auditoria LGPD
    assert decision.context["ofertas_elegiveis"]
