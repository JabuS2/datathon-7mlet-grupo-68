from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Token(Base):
    __tablename__ = "token"

    access_token: Mapped[str] = mapped_column(String, nullable=False)
    token_type: Mapped[str] = mapped_column(String, nullable=False)
