from fastapi import APIRouter, Depends

from dependencies import get_service
from schemas.bandit import UpdateRequest, UpdateResponse
from service import BanditService

router = APIRouter()


@router.post("/update", tags=["bandit"], response_model=UpdateResponse)
async def update(req: UpdateRequest, service: BanditService = Depends(get_service)):
    result = await service.update(
        algorithm=req.algorithm,
        arm_id=req.arm_id,
        reward=req.reward,
        client=req.client,
        segments=req.segments,
    )
    return UpdateResponse(**result)
