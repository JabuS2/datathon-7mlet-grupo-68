from __future__ import annotations

import logging
from typing import Any

from catalog.loader import Catalog
from exceptions import BadRequest, NotFound
from models import (
    ALGORITHMS,
    BanditContext,
    BanditModel,
    ContextBuilder,
    DeterministicBaseline,
    LinUCB,
    ThompsonSampling,
    model_from_state,
)
from store.state_store import StateStore

logger = logging.getLogger(__name__)


class BanditService:
    """Orquestra catálogo + estado (Redis) + modelos de bandit.

    Loop de aprendizado (compute-on-read): ``update`` muta o estado no Redis; o próximo
    ``rank`` re-ranqueia com o estado atualizado. Não há materialização/pré-cálculo.
    """

    def __init__(self, catalog: Catalog, store: StateStore, default_algorithm: str = "linucb"):
        self.catalog = catalog
        self.store = store
        self.default_algorithm = default_algorithm
        self._context_builder: ContextBuilder | None = None

    # --------------------------------------------------------------- context
    async def _ctx_builder(self) -> ContextBuilder:
        if self._context_builder is not None:
            return self._context_builder
        state = await self.store.load_context()
        if state is None:
            mu, sd = self.catalog.context_stats()
            cb = ContextBuilder(self.catalog.ctx_cols, mu, sd)
            await self.store.save_context(cb.to_state())
        else:
            cb = ContextBuilder.from_state(state)
        self._context_builder = cb
        return cb

    def _context(
        self, cb: ContextBuilder, client: dict[str, Any], segments: list[str]
    ) -> BanditContext:
        return BanditContext(
            x=cb.build(client, segments),
            client=client,
            segments=segments,
            arm_categories=self.catalog.categories,
        )

    # ---------------------------------------------------------------- models
    def _resolve_algorithm(self, algorithm: str | None) -> str:
        algo = algorithm or self.default_algorithm
        if algo not in ALGORITHMS:
            raise BadRequest(
                f"Algoritmo inválido: {algo!r}. Opções: {ALGORITHMS}", code="INVALID_ALGORITHM"
            )
        return algo

    def _fresh_model(self, algorithm: str, dim: int) -> BanditModel:
        if algorithm == "linucb":
            return LinUCB(self.catalog.n_arms, dim, self.catalog.exploration)
        if algorithm == "thompson":
            return ThompsonSampling(self.catalog.n_arms)
        if algorithm == "baseline":
            return DeterministicBaseline(self.catalog.categories)
        raise BadRequest(f"Algoritmo inválido: {algorithm!r}", code="INVALID_ALGORITHM")

    async def _load_or_init(self, algorithm: str, dim: int) -> BanditModel:
        state = await self.store.load_state(algorithm)
        if state is not None:
            return model_from_state(state)
        model = self._fresh_model(algorithm, dim)
        await self.store.save_state(algorithm, model.get_state())
        return model

    # ------------------------------------------------------------------ API
    async def rank(
        self,
        algorithm: str | None,
        client: dict[str, Any],
        segments: list[str],
        top: int | None = None,
        exclude_arm_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        algo = self._resolve_algorithm(algorithm)
        cb = await self._ctx_builder()
        model = await self._load_or_init(algo, cb.dim)

        mask = self.catalog.eligibility_mask(client)
        exclude: list[int] = []
        for aid in exclude_arm_ids or []:
            idx = self.catalog.index_of(aid)
            if idx is not None:
                exclude.append(idx)

        ctx = self._context(cb, client, segments)
        ranked = model.rank(ctx, mask, tuple(exclude))

        results: list[dict[str, Any]] = []
        for rank_pos, ra in enumerate(ranked, start=1):
            o = self.catalog.offer(ra.arm_index)
            results.append(
                {
                    "arm_id": o["arm_id"],
                    "rank": rank_pos,
                    "score": round(ra.score, 6),
                    "pred": round(ra.pred, 6),
                    "bonus": round(ra.bonus, 6),
                    "category": o["category"],
                    "product_name": o["product_name"],
                    "description": o["description"],
                    "valor_total": o.get("valor_total"),
                    "desconto_pct": o.get("desconto_pct"),
                    "valor_final": o.get("valor_final"),
                }
            )
        if top is not None:
            results = results[:top]
        return {"algorithm": algo, "ranked": results}

    async def update(
        self,
        algorithm: str | None,
        arm_id: str,
        reward: float,
        client: dict[str, Any],
        segments: list[str],
    ) -> dict[str, Any]:
        algo = self._resolve_algorithm(algorithm)
        arm_index = self.catalog.index_of(arm_id)
        if arm_index is None:
            raise NotFound(f"arm_id desconhecido: {arm_id!r}", code="ARM_NOT_FOUND")

        cb = await self._ctx_builder()
        # lock por modelo: serializa o read-modify-write do estado
        async with self.store.lock(algo):
            model = await self._load_or_init(algo, cb.dim)
            ctx = self._context(cb, client, segments)
            model.update(arm_index, reward, ctx)
            await self.store.save_state(algo, model.get_state())

        logger.info(
            "bandit_update",
            extra={"algorithm": algo, "arm_id": arm_id, "reward": reward},
        )
        return {"algorithm": algo, "arm_id": arm_id, "status": "updated"}

    async def reset(self, algorithm: str | None) -> None:
        algo = self._resolve_algorithm(algorithm)
        await self.store.delete_state(algo)
