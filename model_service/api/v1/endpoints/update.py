from fastapi import APIRouter, Depends

from db.unit_of_work import UnitOfWork
from dependencies import get_service, get_uow
from schemas.bandit import UpdateRequest, UpdateResponse
from service import BanditService
from service.policy_resolver import resolve_policy

router = APIRouter()


@router.post("/update", tags=["bandit"], response_model=UpdateResponse)
async def update(
    req: UpdateRequest,
    service: BanditService = Depends(get_service),
    uow: UnitOfWork = Depends(get_uow),
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
