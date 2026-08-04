"""Reprodução ponta a ponta do pipeline em ambiente local (Etapa 5 do PDF).

Comando único que executa:
  1. migrações Alembic (`upgrade head`)
  2. seed do catálogo, segmentos e um subset de clientes
  3. um ciclo de decisão auditável: decide -> clique -> reward (aprendizado)

Imprime o braço escolhido, a justificativa (reason codes), a versão da política e o registro
auditável — exatamente a evidência que a banca precisa ver.

**Pré-requisitos** (o bandit não roda mais em processo):
  docker-compose --profile api up -d postgres redis model
  python scripts/seed_policies.py          # registra as políticas no model_service

O ranking vem do model_service via HTTP; o que fica aqui é o log auditável
(`decisao`/`evento_impressao`/`recompensa`). Sem o model_service no ar, o passo 3 falha
com MODEL_SERVICE_UNAVAILABLE.

Uso (da raiz do repo):  python scripts/reproduce.py
Env: POSTGRES_* (conexão), MODEL_SERVICE_URL e DATA_DIR (default <repo>/data).
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

API_SERVICE = Path(__file__).resolve().parent.parent / "api_service"
sys.path.insert(0, str(API_SERVICE))

try:  # consoles Windows (cp1252) não encodam acentos por padrão
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import select  # noqa: E402

from db.session import db  # noqa: E402
from db.unit_of_work import UnitOfWork  # noqa: E402
from enums.decisao import TipoEvento  # noqa: E402
from models.cliente import Cliente  # noqa: E402
from services.decision.service import DecisionService  # noqa: E402
from services.seed.seeder import seed_all  # noqa: E402
from settings import settings  # noqa: E402


def _migrate() -> None:
    cfg = Config(str(API_SERVICE / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_SERVICE / "alembic"))
    command.upgrade(cfg, "head")


async def _fresh_service() -> tuple[DecisionService, object]:
    session = await db._session_factory().__aenter__()
    return DecisionService(UnitOfWork(session)), session


async def _run() -> None:
    print("-> 2/3 seed do banco")
    async for session in db.session():
        async with UnitOfWork(session) as uow:
            counts = await seed_all(uow, settings.DATA_DIR, client_limit=300)
        break
    print("   ", counts)

    async for session in db.session():
        cod = await session.scalar(select(Cliente.cod_cliente).where(Cliente.ind_ativo).limit(1))
        break

    print("\n-> 3/3 ciclo de decisão auditável")
    svc, s = await _fresh_service()
    decision = await svc.decide(cod, "app")
    await s.close()
    print(f"   /decide  cliente={cod}")
    print(f"     braço escolhido : {decision.arm_id} — {decision.product_name}")
    print(f"     versão política : {decision.policy_version}")
    print(f"     score           : {decision.score:.4f}")
    print(f"     reason codes    : {decision.reason_codes}")
    print(f"     decision_id     : {decision.decision_id}")

    svc, s = await _fresh_service()
    await svc.feedback(decision.decision_id, TipoEvento.CLICK)
    await s.close()
    print("   clique registrado  (DecisionService.feedback — via HTTP: POST /me/feedback)")

    svc, s = await _fresh_service()
    rw = await svc.reward(decision.decision_id, converted=True)
    await s.close()
    print(f"   /reward  value={rw.value:.4f} status={rw.status}  (bandit atualizado)")

    await db.dispose()
    print("\nOK: pipeline reproduzido com sucesso.")


def main() -> None:
    print("-> 1/3 migrações Alembic (upgrade head)")
    _migrate()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
