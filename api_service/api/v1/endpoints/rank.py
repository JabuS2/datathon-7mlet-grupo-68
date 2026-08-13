from fastapi import APIRouter, Depends

from services.bandit import BanditService
from services.bandit.bandit_schemas import RankRequest, RankResponse
from services.bandit.dependencies import get_bandit_uow, get_service
from services.bandit.governance_uow import UnitOfWork
from services.bandit.policy_resolver import resolve_policy

router = APIRouter()


@router.post("/rank", tags=["bandit"], response_model=RankResponse)
async def rank(
    req: RankRequest,
    service: BanditService = Depends(get_service),
    uow: UnitOfWork = Depends(get_bandit_uow),
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
