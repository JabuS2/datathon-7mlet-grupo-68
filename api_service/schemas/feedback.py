from schemas.base import BaseSchema


class FeedbackCreate(BaseSchema):
    arm_id: str
    clicked: bool
    algorithm: str | None = None


class FeedbackResponse(BaseSchema):
    arm_id: str
    clicked: bool
    reward: float
    algorithm: str
    status: str
