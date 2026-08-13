from fastapi import APIRouter, Depends

from services.bandit import BanditService
from services.bandit.bandit_schemas import UpdateRequest, UpdateResponse
from services.bandit.dependencies import get_bandit_uow, get_service
from services.bandit.governance_uow import UnitOfWork
from services.bandit.policy_resolver import resolve_policy

router = APIRouter()


@router.post("/update", tags=["bandit"], response_model=UpdateResponse)
async def update(
    req: UpdateRequest,
    service: BanditService = Depends(get_service),
    uow: UnitOfWork = Depends(get_bandit_uow),
):
    async with uow:
        policy = await resolve_policy(uow, req.policy_id, service._resolve_algorithm(req.algorithm))
    result = await service.update(
        algorithm=req.algorithm,
        arm_id=req.arm_id,
        reward=req.reward,
        client=req.client,
        segments=req.segments,
        policy=policy,
    )
    return UpdateResponse(**result)
