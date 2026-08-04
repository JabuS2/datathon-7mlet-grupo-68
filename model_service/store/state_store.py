from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis


class StateStore:
    """Persistência do estado dos bandits em Redis.

    - Estado de cada modelo: ``{prefix}:state:{algorithm}``.
    - Estado do ContextBuilder (mu/sd/seg_keys): ``{prefix}:context``.
    - Lock por modelo: ``{prefix}:lock:{algorithm}`` — serializa o read-modify-write do
      update (Sherman-Morrison) para não perder atualizações concorrentes.
    """

    def __init__(self, redis: Redis, prefix: str = "bandit"):
        self.redis = redis
        self.prefix = prefix

    def _state_key(self, algorithm: str) -> str:
        return f"{self.prefix}:state:{algorithm}"

    def _lock_key(self, algorithm: str) -> str:
        return f"{self.prefix}:lock:{algorithm}"

    @property
    def _context_key(self) -> str:
        return f"{self.prefix}:context"

    async def load_state(self, algorithm: str) -> dict[str, Any] | None:
        raw = await self.redis.get(self._state_key(algorithm))
        return json.loads(raw) if raw else None

    async def save_state(self, algorithm: str, state: dict[str, Any]) -> None:
        await self.redis.set(self._state_key(algorithm), json.dumps(state))

    async def delete_state(self, algorithm: str) -> None:
        await self.redis.delete(self._state_key(algorithm))

    async def load_context(self) -> dict[str, Any] | None:
        raw = await self.redis.get(self._context_key)
        return json.loads(raw) if raw else None

    async def save_context(self, state: dict[str, Any]) -> None:
        await self.redis.set(self._context_key, json.dumps(state))

    def lock(self, algorithm: str, timeout: int = 10, blocking_timeout: int = 10):
        """Lock distribuído por modelo (async context manager)."""
        return self.redis.lock(
            self._lock_key(algorithm),
            timeout=timeout,
            blocking_timeout=blocking_timeout,
        )
