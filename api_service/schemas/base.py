from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict

from utils.fake_factory import FakeFactory


def to_camel(string: str) -> str:
    words = string.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        alias_generator=to_camel,
        from_attributes=True,
        extra="forbid",
        populate_by_name=True,
    )

    @classmethod
    def fake(cls, **kwargs: Any) -> Self:
        return FakeFactory.model(cls, **kwargs)

    @classmethod
    def fakes(cls, count: int, **kwargs: Any) -> list[Self]:
        return [cls.fake(**kwargs) for _ in range(count)]


class AuditSchema(BaseSchema):
    created_at: datetime | None = None
    created_by: str | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None
