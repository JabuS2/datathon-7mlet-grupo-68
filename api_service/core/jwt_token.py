from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from settings import settings


class JwtToken:
    def __init__(self):
        self.pwd_context = PasswordHasher()
        self.settings = settings

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self.pwd_context.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False

    def create_access_token(self, data: dict) -> str:
        now = datetime.now(UTC)

        to_encode = data.copy()

        user_id = to_encode.pop("user_id", None)
        if user_id is None:
            raise ValueError("user_id é obrigatório para gerar o token")

        to_encode.update(
            {
                "sub": str(user_id),
                "iat": int(now.timestamp()),
                "exp": int(
                    (now + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
                ),
            }
        )

        return jwt.encode(
            to_encode,
            self.settings.SECRET_KEY,
            algorithm=self.settings.ALGORITHM,
        )
