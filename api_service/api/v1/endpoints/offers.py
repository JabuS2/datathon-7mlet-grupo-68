from typing import Annotated

from fastapi import APIRouter, Depends, Query

from core.auth_dependencies import get_current_user
from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from models.user import User
from schemas.cliente import ClienteResponse
from schemas.offer import OfferResponse
from schemas.profile import ProfileUpdate
from services.model_client import ModelServiceClient
from services.offer.offer import OfferService

router = APIRouter()
model_client = ModelServiceClient()

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get(
    "/offers",
    tags=["offers"],
    response_model=list[OfferResponse],
    response_model_exclude_none=True,
)
async def list_offers(
    user: CurrentUser,
    algorithm: str | None = Query(default=None),
    top: int | None = Query(default=None, ge=1),
    uow: UnitOfWork = Depends(get_uow),
):
    """Vitrine ranqueada pelo model_service a partir do contexto do cliente logado.

    `409 NO_CLIENT_PROFILE` se a conta não tem cliente vinculado (contas de operador).
    """
    service = OfferService(uow=uow, model_client=model_client)
    return await service.list_offers(user, algorithm, top)


@router.put("/profile", tags=["offers"], response_model=ClienteResponse)
async def put_profile(
    data: ProfileUpdate,
    user: CurrentUser,
    uow: UnitOfWork = Depends(get_uow),
):
    """Atualização parcial do contexto do próprio cliente. Leitura: `GET /me/profile`."""
    service = OfferService(uow=uow, model_client=model_client)
    return await service.update_profile(user, data)
