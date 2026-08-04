from fastapi import APIRouter, Depends, Query

from core.auth_dependencies import AuthDependencies
from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from schemas.offer import OfferResponse
from schemas.profile import ProfileResponse, ProfileUpsert
from services.model_client import ModelServiceClient
from services.offer.offer import OfferService

router = APIRouter()
auth = AuthDependencies()
model_client = ModelServiceClient()


@router.get(
    "/offers",
    tags=["offers"],
    response_model=list[OfferResponse],
    response_model_exclude_none=True,
)
async def list_offers(
    algorithm: str | None = Query(default=None),
    top: int | None = Query(default=None, ge=1),
    current_user=Depends(auth.get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = OfferService(uow=uow, model_client=model_client)
    return await service.list_offers(current_user.id, algorithm, top)


@router.get("/profile", tags=["offers"], response_model=ProfileResponse)
async def get_profile(
    current_user=Depends(auth.get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = OfferService(uow=uow, model_client=model_client)
    return await service.get_profile(current_user.id)


@router.put("/profile", tags=["offers"], response_model=ProfileResponse)
async def put_profile(
    data: ProfileUpsert,
    current_user=Depends(auth.get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = OfferService(uow=uow, model_client=model_client)
    return await service.upsert_profile(current_user.id, data)
