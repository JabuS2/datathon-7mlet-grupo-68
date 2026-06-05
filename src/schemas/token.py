from src.schemas.base import BaseSchema


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str