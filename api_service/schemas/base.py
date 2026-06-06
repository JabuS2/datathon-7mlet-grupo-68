from datetime import datetime
from typing import Any, Self, overload

from pydantic import BaseModel, ConfigDict

from utils.fake_factory import FakeFactory


class GenericSchema(BaseModel):
    class Config:
        validate_by_name = True
        str_strip_whitespace = True

    @overload
    @classmethod
    def fake(cls) -> Self: ...

    @overload
    @classmethod
    def fake(cls, **kwargs: Any) -> Self: ...

    @classmethod
    def fake(cls, **kwargs: Any) -> Self:
        return FakeFactory.model(cls, **kwargs)

    @classmethod
    def fakes(cls, count: int, **kwargs: Any) -> list[Self]:
        return [cls.fake(**kwargs) for _ in range(count)]


class BaseSchema(GenericSchema):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    created_at: datetime | None = None
    created_by: str | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None
