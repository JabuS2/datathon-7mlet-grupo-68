"""Catálogo (autenticado): ofertas e segmentos para a vitrine.

`/offers` é a **vitrine** — devolve só o que o cliente pode ver. Receita esperada, fator de
exploração, features de contexto e as regras de elegibilidade são parâmetros internos do bandit
e ficam em `/offers/catalog`, restrita a operador: expor a receita esperada por oferta ao próprio
cliente entrega a régua comercial, e expor `eligible_segment` entrega como burlar o filtro.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from core.auth_dependencies import get_current_user, require_operador
from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from models.user import User
from schemas.oferta import OfertaPublica, OfertaResponse
from schemas.segmento import SegmentoResponse

router = APIRouter(tags=["catalog"])

CurrentUser = Annotated[User, Depends(get_current_user)]
Operador = Annotated[User, Depends(require_operador)]


@router.get("/offers", response_model=list[OfertaPublica])
async def list_offers(_: CurrentUser, uow: UnitOfWork = Depends(get_uow)):
    """Vitrine: recorte visível ao cliente (sem parâmetros internos do bandit)."""
    return [OfertaPublica.model_validate(o) for o in await uow.ofertas.get_all()]


@router.get("/offers/catalog", response_model=list[OfertaResponse])
async def list_offers_catalog(_: Operador, uow: UnitOfWork = Depends(get_uow)):
    """Catálogo completo com os parâmetros do bandit — só operador."""
    return [OfertaResponse.model_validate(o) for o in await uow.ofertas.get_all()]


@router.get("/segments", response_model=list[SegmentoResponse])
async def list_segments(_: CurrentUser, uow: UnitOfWork = Depends(get_uow)):
    return [SegmentoResponse.model_validate(s) for s in await uow.segmentos.get_all()]
