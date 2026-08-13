from __future__ import annotations

import logging
from typing import Any

from exceptions import BadRequest, NotFound
from services.bandit.audit import build_audit, strip_protected
from services.bandit.catalog.loader import Catalog
from services.bandit.models import (
    ALGORITHMS,
    BanditContext,
    BanditModel,
    ContextBuilder,
    DeterministicBaseline,
    LinUCB,
    ThompsonSampling,
    model_from_state,
)
from services.bandit.policy_resolver import ResolvedPolicy, auto_policy
from services.bandit.store.state_store import StateStore

logger = logging.getLogger(__name__)


class BanditService:
    """Orquestra catálogo + estado (Redis) + modelos de bandit.

    Loop de aprendizado (compute-on-read): ``update`` muta o estado no Redis; o próximo
    ``rank`` re-ranqueia com o estado atualizado. Não há materialização/pré-cálculo.

    O estado é **escopado por política** (`ResolvedPolicy`), não por algoritmo: é o que
    permite duas versões do mesmo algoritmo coexistirem como `active` e `shadow` com pesos
    independentes. Quem resolve a política é `service.policy_resolver`; aqui ela chega
    pronta. Sem governança configurada, o resolver devolve a política implícita
    `auto-{algorithm}` e o comportamento é idêntico ao anterior.
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

    async def _load_or_init(self, policy: ResolvedPolicy, dim: int) -> BanditModel:
        state = await self.store.load_state(policy.policy_id)
        if state is not None:
            return model_from_state(state)
        model = self._fresh_model(policy.algorithm, dim)
        await self.store.save_state(policy.policy_id, model.get_state())
        return model

    def _policy_or_auto(self, policy: ResolvedPolicy | None, algorithm: str | None):
        """Compat: chamada sem política resolvida cai na política implícita do algoritmo."""
        if policy is not None:
            self._resolve_algorithm(policy.algorithm)
            return policy
        return auto_policy(self._resolve_algorithm(algorithm))

    # ------------------------------------------------------------------ API
    async def rank(
        self,
        algorithm: str | None,
        client: dict[str, Any],
        segments: list[str],
        top: int | None = None,
        exclude_arm_ids: list[str] | None = None,
        policy: ResolvedPolicy | None = None,
    ) -> dict[str, Any]:
        pol = self._policy_or_auto(policy, algorithm)
        cb = await self._ctx_builder()
        model = await self._load_or_init(pol, cb.dim)

        # defesa em profundidade: o api_service já não envia atributos protegidos
        client = strip_protected(client)

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
                    "reason_codes": list(ra.reason_codes),
                    "category": o["category"],
                    "product_name": o["product_name"],
                    "description": o["description"],
                    "valor_total": o.get("valor_total"),
                    "desconto_pct": o.get("desconto_pct"),
                    "valor_final": o.get("valor_final"),
                }
            )
        # elegíveis = a máscara, não o recorte do `top`: a auditoria precisa do conjunto
        # que o cliente poderia ter recebido, não do que coube na vitrine.
        eligible_ids = [self.catalog.offer(j)["arm_id"] for j, ok in enumerate(mask) if ok]
        audit = build_audit(
            client=client,
            segments=segments,
            ctx_cols=list(self.catalog.ctx_cols),
            renda_percentil=self.catalog.income_percentile(
                float(client.get("renda_estimada_anual_brl") or 0.0)
            ),
            eligible_arm_ids=eligible_ids,
        )

        if top is not None:
            results = results[:top]
        return {
            "algorithm": pol.algorithm,
            "policy_id": pol.policy_id,
            "ranked": results,
            "audit": audit,
        }

    async def update(
        self,
        algorithm: str | None,
        arm_id: str,
        reward: float,
        client: dict[str, Any],
        segments: list[str],
        policy: ResolvedPolicy | None = None,
    ) -> dict[str, Any]:
        pol = self._policy_or_auto(policy, algorithm)
        arm_index = self.catalog.index_of(arm_id)
        if arm_index is None:
            raise NotFound(f"arm_id desconhecido: {arm_id!r}", code="ARM_NOT_FOUND")

        cb = await self._ctx_builder()
        # lock por política: serializa o read-modify-write do estado
        async with self.store.lock(pol.policy_id):
            model = await self._load_or_init(pol, cb.dim)
            ctx = self._context(cb, client, segments)
            model.update(arm_index, reward, ctx)
            await self.store.save_state(pol.policy_id, model.get_state())

        logger.info(
            "bandit_update",
            extra={
                "algorithm": pol.algorithm,
                "policy_id": pol.policy_id,
                "arm_id": arm_id,
                "reward": reward,
            },
        )
        return {
            "algorithm": pol.algorithm,
            "policy_id": pol.policy_id,
            "arm_id": arm_id,
            "status": "updated",
        }

    async def reset(self, algorithm: str | None, policy: ResolvedPolicy | None = None) -> None:
        pol = self._policy_or_auto(policy, algorithm)
        await self.store.delete_state(pol.policy_id)

    async def snapshot_state(
        self, algorithm: str | None, policy: ResolvedPolicy | None = None
    ) -> dict[str, Any]:
        """Estado atual do modelo da política (inicializando se necessário) — para o registry."""
        pol = self._policy_or_auto(policy, algorithm)
        cb = await self._ctx_builder()
        model = await self._load_or_init(pol, cb.dim)
        return model.get_state()

    async def restore_state(
        self, algorithm: str | None, state: dict[str, Any], policy: ResolvedPolicy | None = None
    ) -> None:
        """Sobrescreve o estado da política no Redis (ex.: carregado do MLflow)."""
        pol = self._policy_or_auto(policy, algorithm)
        async with self.store.lock(pol.policy_id):
            await self.store.save_state(pol.policy_id, state)

    async def arm_states(
        self, policy: ResolvedPolicy, dim: int | None = None
    ) -> list[dict[str, Any]]:
        """Projeta o estado da política como uma linha por braço.

        Substitui a tabela `estados_braco` do api_service: os pesos já estão no estado
        serializado do modelo, então materializá-los em Postgres criaria uma segunda cópia
        divergindo a cada `/update`.
        """
        cb = await self._ctx_builder()
        model = await self._load_or_init(policy, dim or cb.dim)
        state = model.get_state()
        return self._project_arms(state)

    def _project_arms(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        """Extrai os parâmetros por braço do estado serializado.

        `params` é **específico do algoritmo** de propósito: o `alpha` do LinUCB é fator de
        exploração e o do Thompson é parâmetro da Beta. Achatar os dois num campo comum
        (como fazia `estados_braco`, com colunas polimórficas) faz o número de um algoritmo
        ser lido com o significado do outro.
        """
        name = state.get("name")
        rows: list[dict[str, Any]] = []
        for idx in range(self.catalog.n_arms):
            offer = self.catalog.offer(idx)
            rows.append(
                {
                    "arm_id": offer["arm_id"],
                    "algorithm": name,
                    "params": self._arm_params(name, state, idx),
                }
            )
        return rows

    @staticmethod
    def _arm_params(name: Any, state: dict[str, Any], idx: int) -> dict[str, Any]:
        def at(key: str) -> float | None:
            seq = state.get(key) or []
            return float(seq[idx]) if idx < len(seq) else None

        if name == "thompson":
            alpha, beta = at("alpha"), at("beta")
            mean = alpha / (alpha + beta) if alpha is not None and beta else None
            return {"alpha": alpha, "beta": beta, "mean": mean}

        if name == "linucb":
            b = (state.get("b") or [None])[idx] if idx < len(state.get("b") or []) else None
            b_norm = float(sum(v * v for v in b) ** 0.5) if b else 0.0
            return {"exploration_alpha": at("alpha"), "b_norm": round(b_norm, 6)}

        if name == "baseline":
            cats = state.get("arm_categories") or []
            return {"category": cats[idx] if idx < len(cats) else None}

        return {}
