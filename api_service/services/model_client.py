from __future__ import annotations

import logging
from typing import Any

import httpx

from http_exceptions import InternalServerError
from settings import settings

logger = logging.getLogger(__name__)


class ModelServiceClient:
    """Cliente HTTP para o model_service (bandits)."""

    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        self.base_url = (base_url or settings.MODEL_SERVICE_URL).rstrip("/")
        self.timeout = timeout

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            try:
                resp = await client.post(path, json=payload)
            except httpx.HTTPError as err:
                logger.exception("model_service_unreachable", extra={"path": path})
                raise InternalServerError(
                    f"Model service indisponível: {err}", code="MODEL_SERVICE_UNAVAILABLE"
                ) from err
        if resp.status_code >= 400:
            logger.error(
                "model_service_error",
                extra={"path": path, "status": resp.status_code, "body": resp.text[:500]},
            )
            raise InternalServerError(
                f"Model service retornou {resp.status_code}", code="MODEL_SERVICE_ERROR"
            )
        data: dict[str, Any] = resp.json()
        return data

    async def rank(
        self,
        algorithm: str | None,
        client: dict[str, Any],
        segments: list[str],
        top: int | None = None,
        exclude_arm_ids: list[str] | None = None,
        policy_id: str | None = None,
    ) -> dict[str, Any]:
        """Ranqueia as ofertas elegíveis.

        `policy_id` omitido: o model_service usa a política `active`. A resposta traz o
        `policy_id` efetivo, que é o que carimbamos em `Decisao.policy_version`.
        """
        return await self._post(
            "/api/v1/rank",
            {
                "algorithm": algorithm,
                "policy_id": policy_id,
                "client": client,
                "segments": segments,
                "top": top,
                "exclude_arm_ids": exclude_arm_ids or [],
            },
        )

    async def update(
        self,
        algorithm: str | None,
        arm_id: str,
        reward: float,
        client: dict[str, Any],
        segments: list[str],
        policy_id: str | None = None,
    ) -> dict[str, Any]:
        """Aplica a recompensa observada.

        Recompensa atrasada precisa passar `policy_id` **explícito**, o da decisão que a
        gerou: sem ele o model_service aplicaria na política ativa no momento, que pode não
        ser a mesma que decidiu — o aprendizado iria para o modelo errado depois de uma
        promoção.
        """
        return await self._post(
            "/api/v1/update",
            {
                "algorithm": algorithm,
                "policy_id": policy_id,
                "arm_id": arm_id,
                "reward": reward,
                "client": client,
                "segments": segments,
            },
        )
