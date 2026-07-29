import numpy as np

from models import (
    DeterministicBaseline,
    LinUCB,
    ThompsonSampling,
    model_from_state,
)


# ------------------------------------------------------------------- LinUCB
def test_linucb_cold_start_ranks_by_exploration(bandit_ctx):
    model = LinUCB(n_arms=4, d=bandit_ctx.x.size, exploration=[1.5, 1.5, 1.4, 2.2])
    mask = [True, True, True, True]
    ranked = model.rank(bandit_ctx, mask)
    assert len(ranked) == 4
    # cold start: pred == 0 para todos, ordena pelo bônus de exploração
    assert all(abs(r.pred) < 1e-9 for r in ranked)
    assert ranked == sorted(ranked, key=lambda r: -r.score)


def test_linucb_learns_from_reward(bandit_ctx):
    model = LinUCB(n_arms=4, d=bandit_ctx.x.size, exploration=[1.5, 1.5, 1.5, 1.5])
    mask = [True, True, True, True]
    before = {r.arm_index: r.pred for r in model.rank(bandit_ctx, mask)}
    for _ in range(30):
        model.update(0, 1.0, bandit_ctx)
    after = {r.arm_index: r.pred for r in model.rank(bandit_ctx, mask)}
    # o braço reforçado com clicks deve ter pred (exploitation) maior
    assert after[0] > before[0]


def test_linucb_respects_eligibility_and_exclude(bandit_ctx):
    model = LinUCB(n_arms=4, d=bandit_ctx.x.size, exploration=[1.5, 1.5, 1.5, 1.5])
    ranked = model.rank(bandit_ctx, [True, False, True, True], exclude=(2,))
    idxs = {r.arm_index for r in ranked}
    assert idxs == {0, 3}  # 1 inelegível, 2 excluído


def test_linucb_state_roundtrip(bandit_ctx):
    model = LinUCB(n_arms=4, d=bandit_ctx.x.size, exploration=[1.5, 1.5, 1.4, 2.2])
    for _ in range(15):
        model.update(1, 1.0, bandit_ctx)
    restored = model_from_state(model.get_state())
    assert isinstance(restored, LinUCB)
    r1 = model.rank(bandit_ctx, [True] * 4)
    r2 = restored.rank(bandit_ctx, [True] * 4)
    assert [x.arm_index for x in r1] == [x.arm_index for x in r2]
    for a, b in zip(r1, r2, strict=True):
        assert abs(a.score - b.score) < 1e-9


# --------------------------------------------------------------- Thompson
def test_thompson_update_moves_beta_params(bandit_ctx):
    model = ThompsonSampling(n_arms=4)
    model.update(0, 1.0, bandit_ctx)  # sucesso
    model.update(1, 0.0, bandit_ctx)  # falha
    assert model.alpha[0] == 2.0 and model.beta[0] == 1.0
    assert model.alpha[1] == 1.0 and model.beta[1] == 2.0


def test_thompson_rank_only_eligible(bandit_ctx):
    np.random.seed(1)
    model = ThompsonSampling(n_arms=4)
    ranked = model.rank(bandit_ctx, [True, False, False, True])
    assert {r.arm_index for r in ranked} == {0, 3}


def test_thompson_state_roundtrip(bandit_ctx):
    model = ThompsonSampling(n_arms=4)
    for _ in range(5):
        model.update(2, 1.0, bandit_ctx)
    restored = model_from_state(model.get_state())
    assert isinstance(restored, ThompsonSampling)
    assert np.allclose(restored.alpha, model.alpha)
    assert np.allclose(restored.beta, model.beta)


# --------------------------------------------------------------- Baseline
def test_baseline_targets_credito_for_young(bandit_ctx):
    model = DeterministicBaseline(bandit_ctx.arm_categories)
    ranked = model.rank(bandit_ctx, [True] * 4)
    # cliente SEG-JOVEM => categoria credito primeiro
    assert bandit_ctx.arm_categories[ranked[0].arm_index] == "credito"


def test_baseline_vip_prefers_investimento():
    from models import BanditContext

    cats = ["credito", "investimento", "seguro"]
    ctx = BanditContext(
        x=np.zeros(3),
        client={"renda_estimada_anual_brl": 200000, "segmento": "01 - ALTA RENDA"},
        segments=["SEG-VIP"],
        arm_categories=cats,
    )
    model = DeterministicBaseline(cats)
    ranked = model.rank(ctx, [True, True, True])
    assert cats[ranked[0].arm_index] == "investimento"


def test_baseline_update_is_noop(bandit_ctx):
    model = DeterministicBaseline(bandit_ctx.arm_categories)
    state_before = model.get_state()
    model.update(0, 1.0, bandit_ctx)
    assert model.get_state() == state_before
