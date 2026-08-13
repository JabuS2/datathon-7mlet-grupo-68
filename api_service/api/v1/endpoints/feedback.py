from typing import Annotated

from fastapi import APIRouter, Depends

from core.auth_dependencies import get_current_user
from db.dependencies import get_uow
from db.unit_of_work import UnitOfWork
from models.user import User
from schemas.feedback import FeedbackCreate, FeedbackResponse
from services.bandit.client import BanditClient
from services.offer.offer import OfferService

router = APIRouter()
model_client = BanditClient()

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "/feedback",
    tags=["feedback"],
    response_model=FeedbackResponse,
    response_model_exclude_none=True,
)
async def post_feedback(
    data: FeedbackCreate,
    user: CurrentUser,
    uow: UnitOfWork = Depends(get_uow),
):
    service = OfferService(uow=uow, model_client=model_client)
    return await service.submit_feedback(user, data)
