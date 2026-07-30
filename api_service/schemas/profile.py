from typing import Any

from schemas.base import BaseSchema


class ProfileUpsert(BaseSchema):
    features: dict[str, Any]
    segments: list[str] = []


class ProfileResponse(BaseSchema):
    features: dict[str, Any]
    segments: list[str]
