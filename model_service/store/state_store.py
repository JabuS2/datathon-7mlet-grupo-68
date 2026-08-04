from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis


class StateStore:
    """Persistência do estado dos bandits em Redis, **escopado por política**.

    - Estado de cada política: ``{prefix}:state:{policy_id}``.
    - Estado do ContextBuilder (mu/sd/seg_keys): ``{prefix}:context``.
    - Lock por política: ``{prefix}:lock:{policy_id}`` — serializa o read-modify-write do
      update (Sherman-Morrison) para não perder atualizações concorrentes.

    Antes a chave era o **algoritmo** (`state:linucb`). Isso impedia a governança: duas
    políticas LinUCB — uma `active`, outra `shadow` — compartilhariam o mesmo estado, e
    promover uma sobrescreveria os pesos da outra. Com a chave por política, cada versão
    mantém os próprios pesos e o rollback recupera intacto sem copiar nada: basta voltar a
    apontar `active` para a política anterior, cuja chave nunca foi tocada.
    """

    def __init__(self, redis: Redis, prefix: str = "bandit"):
        self.redis = redis
        self.prefix = prefix

    def _state_key(self, policy_id: str) -> str:
        return f"{self.prefix}:state:{policy_id}"

    def _lock_key(self, policy_id: str) -> str:
        return f"{self.prefix}:lock:{policy_id}"

    @property
    def _context_key(self) -> str:
        return f"{self.prefix}:context"

    async def load_state(self, policy_id: str) -> dict[str, Any] | None:
        raw = await self.redis.get(self._state_key(policy_id))
        return json.loads(raw) if raw else None

    async def save_state(self, policy_id: str, state: dict[str, Any]) -> None:
        await self.redis.set(self._state_key(policy_id), json.dumps(state))

    async def delete_state(self, policy_id: str) -> None:
        await self.redis.delete(self._state_key(policy_id))

    async def load_context(self) -> dict[str, Any] | None:
        raw = await self.redis.get(self._context_key)
        return json.loads(raw) if raw else None

    async def save_context(self, state: dict[str, Any]) -> None:
        await self.redis.set(self._context_key, json.dumps(state))

    def lock(self, policy_id: str, timeout: int = 10, blocking_timeout: int = 10):
        """Lock distribuído por política (async context manager)."""
        return self.redis.lock(
            self._lock_key(policy_id),
            timeout=timeout,
            blocking_timeout=blocking_timeout,
        )
