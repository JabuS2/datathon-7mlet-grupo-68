from fastapi import APIRouter, Depends

from core.auth_dependencies import AuthDependencies
from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from schemas.feedback import FeedbackCreate, FeedbackResponse
from services.model_client import ModelServiceClient
from services.offer.offer import OfferService

router = APIRouter()
auth = AuthDependencies()
model_client = ModelServiceClient()


@router.post(
    "/feedback",
    tags=["feedback"],
    response_model=FeedbackResponse,
    response_model_exclude_none=True,
)
async def post_feedback(
    data: FeedbackCreate,
    current_user=Depends(auth.get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = OfferService(uow=uow, model_client=model_client)
    return await service.submit_feedback(current_user.id, data)
