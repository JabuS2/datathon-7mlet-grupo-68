"""Seed idempotente do Postgres a partir dos dados de referência (catálogo + golden set).

Popula: ofertas (10 braços), segmentos sintéticos, o subset de clientes (`origem='seed'`)
e — se existir — os casos do golden set. Reexecutar não duplica: cada bloco só insere o que
ainda falta.

Políticas **não** são semeadas aqui: `politicas`/`estados_braco` migraram para o
model_service. Use `scripts/seed_policies.py`, que as registra via HTTP.
"""

from __future__ import annotations

from pathlib import Path

from db.unit_of_work import UnitOfWork
from models.cliente import Cliente
from models.oferta import Oferta
from models.segmento import Segmento
from services.catalog.loaders import (
    iter_seed_clients,
    load_offer_catalog,
    load_segments_from_clients,
)


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

    return {
        "ofertas": await _seed_offers(uow, offers),
        "segmentos": await _seed_segments(
            uow, load_segments_from_clients(golden / "golden_clients.csv")
        ),
        "clientes": await _seed_clients(uow, golden / "golden_clients.csv", client_limit),
    }


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


