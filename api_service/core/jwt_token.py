from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from settings import settings


class JwtToken:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        self.settings = settings

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict) -> str:
        now = datetime.now(UTC)

        to_encode = data.copy()
        user_id = to_encode.pop("user_id")

        to_encode.update(
            {
                "sub": str(user_id),
                "iat": now,
                "exp": now + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            }
        )

        return jwt.encode(
            to_encode,
            self.settings.SECRET_KEY,
            algorithm=self.settings.ALGORITHM,
        )
