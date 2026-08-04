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

    #: Necessário para o approval gate do model_service, que recebe quem aprovou.
    id: int | None = None
    email: str
    tipo: TipoUsuario | None = None
    is_admin: bool | None = None
    cod_cliente: int | None = None
    saldo_ficticio: float | None = None
