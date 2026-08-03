import jwt

from agent_service.config import Settings


class InvalidToken(Exception):
    """Raised when an incoming JWT is missing or invalid."""


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise InvalidToken("Missing Authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise InvalidToken("Authorization header must be a Bearer token")

    return token


def validate_request_token(authorization: str | None, settings: Settings) -> dict:
    """Validate the incoming admin JWT (issued by api_service).

    Signature/expiry are verified with the shared secret. Fine-grained admin
    authorization is enforced downstream by api_service when the agent's tools
    reach the admin data endpoints.
    """
    token = _extract_bearer(authorization)

    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require_exp": True, "require_sub": True},
        )
    except jwt.PyJWTError as err:
        raise InvalidToken(str(err)) from err
