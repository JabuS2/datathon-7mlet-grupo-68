from schemas.base import BaseSchema


class UserBase(BaseSchema):
    email: str
    password: str


class UserCreate(UserBase):
    pass


class UserLogin(UserBase):
    pass


class UserResponse(BaseSchema):
    email: str
    is_admin: bool | None = None
