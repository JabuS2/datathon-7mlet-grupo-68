from fastapi import APIRouter, Depends

from db.unit_of_work import UnitOfWork
from dependencies import get_service, get_uow
from schemas.bandit import RankRequest, RankResponse
from service import BanditService
from service.policy_resolver import resolve_policy

router = APIRouter()


@router.post("/rank", tags=["bandit"], response_model=RankResponse)
async def rank(
    req: RankRequest,
    service: BanditService = Depends(get_service),
    uow: UnitOfWork = Depends(get_uow),
):
    async with uow:
        policy = await resolve_policy(uow, req.policy_id, service._resolve_algorithm(req.algorithm))
    result = await service.rank(
        algorithm=req.algorithm,
        client=req.client,
        segments=req.segments,
        top=req.top,
        exclude_arm_ids=req.exclude_arm_ids,
        policy=policy,
    )
    return RankResponse(**result)
