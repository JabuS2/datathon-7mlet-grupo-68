"""Seed idempotente do Postgres a partir dos dados de referência (catálogo + golden set).

Popula: ofertas (10 braços), segmentos sintéticos, políticas (baseline/thompson/linucb) com
os priors de `estado_braco` por braço, o subset de clientes (`origem='seed'`) e — se existir —
os casos do golden set. Reexecutar não duplica: cada bloco só insere o que ainda falta.
"""

from __future__ import annotations

from pathlib import Path

from db.unit_of_work import UnitOfWork
from enums.politica import AlgoritmoPolitica, StatusPolitica
from models.caso_avaliacao import CasoAvaliacao
from models.cliente import Cliente
from models.estado_braco import EstadoBraco
from models.oferta import Oferta
from models.politica import Politica
from models.segmento import Segmento
from services.catalog.loaders import (
    iter_seed_clients,
    load_evaluation_cases,
    load_offer_catalog,
    load_segments_from_clients,
)

# Políticas semeadas: LinUCB é a ativa (catálogo prod); as demais nascem em shadow para a
# comparação da Etapa 3 (baseline vs Thompson vs contextual).
SEED_POLICIES: list[tuple[str, AlgoritmoPolitica, StatusPolitica, dict]] = [
    (
        "baseline-v1",
        AlgoritmoPolitica.BASELINE,
        StatusPolitica.SHADOW,
        {"rule": "best_expected_revenue"},
    ),
    ("thompson-v1", AlgoritmoPolitica.THOMPSON, StatusPolitica.SHADOW, {}),
    ("linucb-v1", AlgoritmoPolitica.LINUCB, StatusPolitica.ACTIVE, {"alpha_scale": 0.2}),
]


def _golden_dir(data_dir: str | Path) -> Path:
    return Path(data_dir) / "golden_set"


async def seed_all(
    uow: UnitOfWork,
    data_dir: str | Path,
    *,
    client_limit: int | None = None,
) -> dict[str, int]:
    """Executa todos os blocos dentro da transação da `uow`. Devolve contagem de inserções."""
    golden = _golden_dir(data_dir)
    offers = load_offer_catalog(golden / "offer_catalog.json")

    counts = {
        "ofertas": await _seed_offers(uow, offers),
        "segmentos": await _seed_segments(
            uow, load_segments_from_clients(golden / "golden_clients.csv")
        ),
        "politicas": 0,
        "estados_braco": 0,
        "clientes": await _seed_clients(uow, golden / "golden_clients.csv", client_limit),
        "casos_avaliacao": await _seed_cases(
            uow, load_evaluation_cases(golden / "evaluation_cases.jsonl")
        ),
    }
    arm_ids = [o["arm_id"] for o in offers]
    counts["politicas"], counts["estados_braco"] = await _seed_policies(uow, arm_ids)
    return counts


async def _seed_offers(uow: UnitOfWork, offers: list[dict]) -> int:
    inserted = 0
    for kwargs in offers:
        if await uow.ofertas.get_by_arm_id(kwargs["arm_id"]) is None:
            uow.ofertas.add(Oferta(**kwargs))
            inserted += 1
    return inserted


async def _seed_segments(uow: UnitOfWork, segments: list[dict]) -> int:
    inserted = 0
    for kwargs in segments:
        if await uow.segmentos.get_by_segment_id(kwargs["segment_id"]) is None:
            uow.segmentos.add(Segmento(**kwargs))
            inserted += 1
    return inserted


async def _seed_policies(uow: UnitOfWork, arm_ids: list[str]) -> tuple[int, int]:
    pol_inserted = 0
    arm_inserted = 0
    for policy_id, algorithm, status, hyper in SEED_POLICIES:
        if await uow.politicas.get_by_policy_id(policy_id) is None:
            uow.politicas.add(
                Politica(
                    policy_id=policy_id,
                    version="1.0.0",
                    algorithm=algorithm,
                    hyperparams=dict(hyper),
                    status=status,
                )
            )
            pol_inserted += 1
        # Priors por braço (cold-start): Thompson α=β=1; LinUCB A/b nulos.
        for arm_id in arm_ids:
            if await uow.estados_braco.get(policy_id, arm_id) is None:
                uow.estados_braco.add(EstadoBraco(policy_id=policy_id, arm_id=arm_id))
                arm_inserted += 1
    return pol_inserted, arm_inserted


async def _seed_clients(uow: UnitOfWork, csv_path: Path, limit: int | None) -> int:
    existing = {c.cod_cliente for c in await uow.clientes.get_all()}
    inserted = 0
    for kwargs in iter_seed_clients(csv_path, limit):
        if kwargs["cod_cliente"] in existing:
            continue
        uow.clientes.add(Cliente(**kwargs))
        existing.add(kwargs["cod_cliente"])
        inserted += 1
    return inserted


async def _seed_cases(uow: UnitOfWork, cases: list[dict]) -> int:
    inserted = 0
    for kwargs in cases:
        if await uow.casos_avaliacao.get_by_field(CasoAvaliacao.case_id, kwargs["case_id"]) is None:
            uow.casos_avaliacao.add(CasoAvaliacao(**kwargs))
            inserted += 1
    return inserted
