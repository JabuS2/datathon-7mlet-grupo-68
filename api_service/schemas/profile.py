from typing import Any

from pydantic import Field

from schemas.base import BaseSchema


class ProfileUpsert(BaseSchema):
    features: dict[str, Any]
    segments: list[str] = Field(default_factory=list)


class ProfileResponse(BaseSchema):
    features: dict[str, Any]
    segments: list[str]
