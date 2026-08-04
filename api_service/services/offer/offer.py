from __future__ import annotations

import logging

from db.unit_of_work import UnitOfWork
from models.client_profile import ClientProfile
from models.feedback import FeedbackEvent
from schemas.feedback import FeedbackCreate, FeedbackResponse
from schemas.offer import OfferResponse
from schemas.profile import ProfileResponse, ProfileUpsert
from services.model_client import ModelServiceClient
from settings import settings

logger = logging.getLogger(__name__)

# Perfil default (usado quando o usuário ainda não tem perfil) — mantém o fluxo
# funcional out-of-the-box para demonstração.
DEFAULT_PROFILE_FEATURES: dict = {
    "idade": 30,
    "renda_estimada_anual_brl": 60000,
    "tempo_relacionamento_meses": 18,
    "ind_ativo": 1,
    "possui_conta_corrente": 1,
    "possui_cartao_credito": 0,
    "possui_conta_investimento": 0,
    "possui_fundo_investimento": 0,
    "possui_financiamento_imovel": 0,
    "segmento": "02 - VAREJO",
}
DEFAULT_SEGMENTS: list[str] = ["SEG-JOVEM", "SEG-SEM-CARTAO"]


class OfferService:
    """Regras de ofertas: ranquear ofertas do usuário e aplicar feedback.

    O contexto do bandit vem do perfil do usuário (ClientProfile) ou de um perfil
    default. O estado do modelo vive no model_service; aqui só orquestramos.
    """

    def __init__(self, uow: UnitOfWork, model_client: ModelServiceClient):
        self.uow = uow
        self.model_client = model_client

    async def _resolve_context(self, user_id: int) -> tuple[dict, list[str]]:
        """Lê o perfil do usuário via uow (deve ser chamado dentro de ``async with self.uow``)."""
        profile = await self.uow.profiles.get_by_user_id(user_id)
        if profile is not None:
            return dict(profile.features), list(profile.segments)
        return dict(DEFAULT_PROFILE_FEATURES), list(DEFAULT_SEGMENTS)

    async def list_offers(
        self, user_id: int, algorithm: str | None = None, top: int | None = None
    ) -> list[OfferResponse]:
        async with self.uow:
            features, segments = await self._resolve_context(user_id)
        algo = algorithm or settings.DEFAULT_ALGORITHM

        result = await self.model_client.rank(algo, features, segments, top)
        offers = [
            OfferResponse(
                arm_id=r["arm_id"],
                rank=r["rank"],
                score=r["score"],
                category=r["category"],
                product_name=r["product_name"],
                description=r["description"],
                valor_total=r.get("valor_total"),
                desconto_pct=r.get("desconto_pct"),
                valor_final=r.get("valor_final"),
            )
            for r in result["ranked"]
        ]
        logger.info(
            "offers_listed",
            extra={
                "user_id": user_id,
                "algorithm": result.get("algorithm", algo),
                "count": len(offers),
                "top_arm": offers[0].arm_id if offers else None,
            },
        )
        return offers

    async def submit_feedback(self, user_id: int, data: FeedbackCreate) -> FeedbackResponse:
        reward = 1.0 if data.clicked else 0.0
        algo = data.algorithm or settings.DEFAULT_ALGORITHM

        async with self.uow:
            features, segments = await self._resolve_context(user_id)
            self.uow.feedback.add(
                FeedbackEvent(
                    user_id=user_id,
                    arm_id=data.arm_id,
                    algorithm=algo,
                    clicked=data.clicked,
                    reward=reward,
                )
            )

        # propaga o feedback ao modelo (recalcula as próximas ofertas do usuário)
        await self.model_client.update(algo, data.arm_id, reward, features, segments)

        logger.info(
            "feedback_submitted",
            extra={
                "user_id": user_id,
                "arm_id": data.arm_id,
                "clicked": data.clicked,
                "reward": reward,
                "algorithm": algo,
            },
        )
        return FeedbackResponse(
            arm_id=data.arm_id,
            clicked=data.clicked,
            reward=reward,
            algorithm=algo,
            status="applied",
        )

    async def upsert_profile(self, user_id: int, data: ProfileUpsert) -> ProfileResponse:
        async with self.uow:
            profile = await self.uow.profiles.get_by_user_id(user_id)
            if profile is not None:
                profile.features = data.features
                profile.segments = data.segments
            else:
                self.uow.profiles.add(
                    ClientProfile(
                        user_id=user_id, features=data.features, segments=data.segments
                    )
                )
            return ProfileResponse(features=data.features, segments=data.segments)

    async def get_profile(self, user_id: int) -> ProfileResponse:
        async with self.uow:
            profile = await self.uow.profiles.get_by_user_id(user_id)
            if profile is not None:
                return ProfileResponse(
                    features=dict(profile.features), segments=list(profile.segments)
                )
        return ProfileResponse(
            features=dict(DEFAULT_PROFILE_FEATURES), segments=list(DEFAULT_SEGMENTS)
        )
