"""Seed do Postgres com o catálogo, segmentos, políticas, clientes e golden set.

Uso (a partir da raiz do repo, com o Postgres no ar e migrações aplicadas):

    python scripts/seed_db.py                 # seed completo (todos os clientes do golden set)
    python scripts/seed_db.py --client-limit 200   # subset menor p/ demo/testes

Variáveis de ambiente: POSTGRES_* (conexão) e DATA_DIR (default: <repo>/data).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# O pacote raiz do backend é `api_service/` — torna `db`, `services`, etc. importáveis.
API_SERVICE = Path(__file__).resolve().parent.parent / "api_service"
sys.path.insert(0, str(API_SERVICE))

try:  # consoles Windows (cp1252) não encodam acentos por padrão
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from db.session import db  # noqa: E402
from db.unit_of_work import UnitOfWork  # noqa: E402
from services.seed.seeder import seed_all  # noqa: E402
from settings import settings  # noqa: E402


async def _run(client_limit: int | None) -> dict[str, int]:
    counts: dict[str, int] = {}
    async for session in db.session():
        async with UnitOfWork(session) as uow:
            counts = await seed_all(uow, settings.DATA_DIR, client_limit=client_limit)
        break
    await db.dispose()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed do banco a partir dos dados de referência.")
    parser.add_argument(
        "--client-limit", type=int, default=None, help="máximo de clientes a semear (default: todos)"
    )
    args = parser.parse_args()

    counts = asyncio.run(_run(args.client_limit))
    print("Seed concluído. Inserções:")
    for entity, n in counts.items():
        print(f"  {entity:16} {n}")


if __name__ == "__main__":
    main()
