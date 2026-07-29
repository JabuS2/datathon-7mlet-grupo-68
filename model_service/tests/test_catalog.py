import json
from pathlib import Path

import pytest

from catalog import Catalog

_REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG = str(_REPO_ROOT / "data" / "golden_set" / "offer_catalog.json")
CLIENTS = str(_REPO_ROOT / "data" / "golden_set" / "golden_clients.csv")

pytestmark = pytest.mark.skipif(
    not Path(CATALOG).exists(),
    reason="offer_catalog.json não encontrado no repositório",
)


@pytest.fixture
def catalog():
    return Catalog(CATALOG, CLIENTS if Path(CLIENTS).exists() else None)


def test_catalog_loads_ten_arms(catalog):
    assert catalog.n_arms == 10
    assert len(catalog.arm_ids) == 10
    assert len(catalog.ctx_cols) == 9
    assert len(catalog.exploration) == 10


def test_index_of(catalog):
    assert catalog.index_of(catalog.arm_ids[0]) == 0
    assert catalog.index_of("NAO-EXISTE") is None


def test_price_fields_present_and_consistent():
    data = json.loads(Path(CATALOG).read_text(encoding="utf-8"))
    for o in data["offers"]:
        assert "valor_total" in o and "desconto_pct" in o and "valor_final" in o
        expected = round(o["valor_total"] * (1 - o["desconto_pct"] / 100), 2)
        assert o["valor_final"] == expected


def test_reward_is_click():
    data = json.loads(Path(CATALOG).read_text(encoding="utf-8"))
    assert data["catalog_metadata"]["reward_definition"]["type"] == "click"


def test_eligibility_filters_by_ownership(catalog):
    # OFF-CR-002 (Cartão de Crédito Mais) exige possui_cartao_credito_atual == 0
    idx = catalog.index_of("OFF-CR-002")
    has_card = {
        "ind_ativo": 1,
        "idade": 30,
        "possui_cartao_credito": 1,
        "renda_estimada_anual_brl": 50000,
    }
    no_card = {**has_card, "possui_cartao_credito": 0}
    assert catalog.eligibility_mask(has_card)[idx] is False
    assert catalog.eligibility_mask(no_card)[idx] is True


def test_income_percentile_monotonic(catalog):
    low = catalog.income_percentile(1000)
    high = catalog.income_percentile(10_000_000)
    assert 0 <= low <= high <= 100
