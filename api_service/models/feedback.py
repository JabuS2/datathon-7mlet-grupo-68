from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class FeedbackEvent(BaseModel):
    """Evento de feedback (click) de um usuário sobre uma oferta.

    O ``reward`` é o próprio click (0/1); persistido para auditoria e replay.
    """

    __tablename__ = "feedback_events"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    arm_id: Mapped[str] = mapped_column(String, nullable=False)
    algorithm: Mapped[str] = mapped_column(String, nullable=False)
    clicked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reward: Mapped[float] = mapped_column(Float, nullable=False)
