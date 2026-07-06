"""Catálogo público (autenticado): ofertas e segmentos para a vitrine."""

from typing import Annotated

from fastapi import APIRouter, Depends

from core.auth_dependencies import get_current_user
from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from models.user import User
from schemas.oferta import OfertaResponse
from schemas.segmento import SegmentoResponse

router = APIRouter(tags=["catalog"])

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/offers", response_model=list[OfertaResponse])
async def list_offers(_: CurrentUser, uow: UnitOfWork = Depends(get_uow)):
    return [OfertaResponse.model_validate(o) for o in await uow.ofertas.get_all()]


@router.get("/segments", response_model=list[SegmentoResponse])
async def list_segments(_: CurrentUser, uow: UnitOfWork = Depends(get_uow)):
    return [SegmentoResponse.model_validate(s) for s in await uow.segmentos.get_all()]
