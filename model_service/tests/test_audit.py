"""Contexto auditável e reason codes do `/rank` (Etapa 5 / LGPD).

Estes eram produzidos pelo bandit in-process do api_service. Com o ranking servido daqui,
é aqui que precisam ser provados — o api_service só persiste o que recebe em
`Decisao.context` e `Decisao.reason_codes`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from catalog import Catalog
from service import BanditService
from service.audit import MONITORED_ATTRIBUTES, PROTECTED_ATTRIBUTES, strip_protected

_REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG = str(_REPO_ROOT / "data" / "golden_set" / "offer_catalog.json")
CLIENTS = str(_REPO_ROOT / "data" / "golden_set" / "golden_clients.csv")

pytestmark = pytest.mark.skipif(
    not Path(CATALOG).exists(), reason="offer_catalog.json não encontrado"
)

CLIENT = {
    "idade": 24,
    "renda_estimada_anual_brl": 45000,
    "tempo_relacionamento_meses": 10,
    "ind_ativo": 1,
    "possui_conta_corrente": 1,
    "possui_cartao_credito": 0,
    "possui_conta_investimento": 0,
    "possui_fundo_investimento": 0,
    "possui_financiamento_imovel": 0,
}
SEGMENTS = ["SEG-JOVEM", "SEG-SEM-CARTAO"]


@pytest.fixture
def service():
    from tests.test_service import FakeStore

    catalog = Catalog(CATALOG, CLIENTS if Path(CLIENTS).exists() else None)
    return BanditService(catalog, FakeStore(), default_algorithm="linucb")


def test_strip_protected_remove_sexo():
    limpo = strip_protected({**CLIENT, "sexo": "F"})
    assert "sexo" not in limpo
    assert limpo["idade"] == 24


@pytest.mark.asyncio
async def test_audit_separa_excluido_de_monitorado(service):
    """Renda entra na decisão de forma legítima; sexo não entra de jeito nenhum.

    Declarar renda como "excluída" seria falso — ela compõe o contexto e governa a
    elegibilidade. O log a registra como monitorada, que é o que sustenta a análise de
    fairness por faixa de renda.
    """
    result = await service.rank("linucb", CLIENT, SEGMENTS)
    audit = result["audit"]

    assert audit["atributos_excluidos"] == PROTECTED_ATTRIBUTES
    assert audit["atributos_monitorados"] == MONITORED_ATTRIBUTES
    # coerência: o que é monitorado está em uso, logo não pode constar como excluído
    assert set(audit["atributos_excluidos"]).isdisjoint(audit["atributos_monitorados"])
    assert "renda_estimada_anual_brl" in audit["features_numericas"]
    assert "sexo" not in audit["features_numericas"]


@pytest.mark.asyncio
async def test_audit_nao_vaza_sexo_mesmo_se_enviado(service):
    """Defesa em profundidade: o api_service não envia, mas se enviasse não entraria."""
    result = await service.rank("linucb", {**CLIENT, "sexo": "F"}, SEGMENTS)
    assert "sexo" not in result["audit"]["features_numericas"]


@pytest.mark.asyncio
async def test_elegiveis_ignoram_o_recorte_do_top(service):
    """A auditoria precisa do conjunto que o cliente poderia receber, não do que coube."""
    completo = await service.rank("linucb", CLIENT, SEGMENTS)
    recortado = await service.rank("linucb", CLIENT, SEGMENTS, top=1)

    assert len(recortado["ranked"]) == 1
    assert recortado["audit"]["ofertas_elegiveis"] == completo["audit"]["ofertas_elegiveis"]
    assert len(recortado["audit"]["ofertas_elegiveis"]) >= 1


@pytest.mark.asyncio
async def test_reason_codes_linucb_marcam_cold_start(service):
    """Sem reward aplicado, todo braço do LinUCB está em cold-start (`b` zerado)."""
    result = await service.rank("linucb", CLIENT, SEGMENTS)
    for arm in result["ranked"]:
        assert "policy:linucb" in arm["reason_codes"]
        assert "cold_start" in arm["reason_codes"]


@pytest.mark.asyncio
async def test_reason_codes_saem_do_cold_start_apos_update(service):
    alvo = (await service.rank("linucb", CLIENT, SEGMENTS))["ranked"][0]["arm_id"]
    await service.update("linucb", alvo, 1.0, CLIENT, SEGMENTS)

    depois = await service.rank("linucb", CLIENT, SEGMENTS)
    codes = next(a["reason_codes"] for a in depois["ranked"] if a["arm_id"] == alvo)
    assert "cold_start" not in codes
    assert {"explore", "exploit"} & set(codes)


@pytest.mark.asyncio
async def test_reason_codes_baseline_declaram_a_categoria_alvo(service):
    """Baseline é determinístico — não há explore/exploit a declarar, e não declara."""
    result = await service.rank("baseline", CLIENT, SEGMENTS)
    codes = result["ranked"][0]["reason_codes"]
    assert "policy:baseline" in codes
    assert any(c.startswith("target_category:") for c in codes)
    assert not {"explore", "exploit", "cold_start"} & set(codes)


@pytest.mark.asyncio
async def test_reason_codes_thompson_marcam_prior_intocado(service):
    result = await service.rank("thompson", CLIENT, SEGMENTS)
    for arm in result["ranked"]:
        assert "policy:thompson" in arm["reason_codes"]
        assert "cold_start" in arm["reason_codes"]
