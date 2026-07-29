from fastapi import APIRouter, Depends

from dependencies import get_service
from schemas.bandit import RankRequest, RankResponse
from service import BanditService

router = APIRouter()


@router.post("/rank", tags=["bandit"], response_model=RankResponse)
async def rank(req: RankRequest, service: BanditService = Depends(get_service)):
    result = await service.rank(
        algorithm=req.algorithm,
        client=req.client,
        segments=req.segments,
        top=req.top,
        exclude_arm_ids=req.exclude_arm_ids,
    )
    return RankResponse(**result)
