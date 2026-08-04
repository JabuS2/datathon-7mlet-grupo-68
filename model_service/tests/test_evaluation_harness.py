"""Avaliação offline contra o golden set (Etapa 4).

O harness roda sem Docker: `BanditService` + store em memória. Estes testes provam as duas
propriedades que bloqueiam — elegibilidade e invariância de fairness — sobre os casos reais
gerados de `golden_clients.csv` e `offer_catalog.json`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from catalog import Catalog
from evaluation import evaluate, load_cases
from service import BanditService

_REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG = str(_REPO_ROOT / "data" / "golden_set" / "offer_catalog.json")
CLIENTS = str(_REPO_ROOT / "data" / "golden_set" / "golden_clients.csv")
CASES = _REPO_ROOT / "data" / "golden_set" / "evaluation_cases.jsonl"

pytestmark = pytest.mark.skipif(
    not Path(CATALOG).exists() or not CASES.exists(),
    reason="golden set não encontrado (rode `make data-eval`)",
)


@pytest.fixture
def service():
    from tests.test_service import FakeStore

    return BanditService(Catalog(CATALOG, CLIENTS), FakeStore(), default_algorithm="linucb")


@pytest.fixture
def cases():
    return load_cases(CASES)


def test_golden_set_tem_os_tres_tipos(cases):
    tipos = {c["type"] for c in cases}
    assert tipos == {"edge", "adversarial", "typical"}
    assert len(cases) >= 20  # o model declara "golden set (>=20)"


@pytest.mark.asyncio
@pytest.mark.parametrize("algorithm", ["linucb", "thompson", "baseline"])
async def test_propriedades_valem_para_todos_os_algoritmos(service, cases, algorithm):
    """Elegibilidade e fairness são invariantes do serviço, não de um algoritmo."""
    report = await evaluate(service, cases, algorithm)
    assert report.passed, report.summary()["failures"]


@pytest.mark.asyncio
async def test_conformidade_com_baseline_nao_reprova(service, cases):
    """`typical` é informativo: o LinUCB pode divergir do baseline sem isso ser falha."""
    report = await evaluate(service, cases, "linucb")
    assert report.informational, "deveria haver casos informativos"
    # o veredito ignora os informativos
    assert report.passed == all(r.passed for r in report.blocking)


@pytest.mark.asyncio
async def test_caso_de_tipo_desconhecido_reprova(service):
    report = await evaluate(service, [{"case_id": "X", "type": "inventado"}], "linucb")
    assert not report.passed
    assert report.summary()["failures"][0]["detail"] == "tipo inválido"


@pytest.mark.asyncio
async def test_relatorio_separa_bloqueante_de_informativo(service, cases):
    report = await evaluate(service, cases, "linucb")
    by_type = report.summary()["by_type"]
    assert set(by_type) == {"edge", "adversarial", "typical"}
    assert {r.type for r in report.blocking} == {"edge", "adversarial"}
    assert {r.type for r in report.informational} == {"typical"}
