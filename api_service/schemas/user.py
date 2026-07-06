from enums.usuario import TipoUsuario
from schemas.base import BaseSchema


class UserBase(BaseSchema):
    email: str
    password: str


class UserCreate(UserBase):
    pass


class UserLogin(UserBase):
    pass


class UserResponse(BaseSchema):
    """Conta do usuário logado. `cod_cliente`/`saldo_ficticio` existem só p/ `tipo='demo'`."""

    email: str
    tipo: TipoUsuario | None = None
    cod_cliente: int | None = None
    saldo_ficticio: float | None = None
