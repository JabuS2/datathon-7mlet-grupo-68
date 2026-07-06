from sqlalchemy import BigInteger, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from enums.usuario import TipoUsuario
from models.base import BaseModel
from models.columns import enum_column


class User(BaseModel):
    """Autenticação unificada: operador (opera a plataforma) e cliente-demo (visitante da vitrine).

    O campo `tipo` discrimina o papel; `cod_cliente`/`saldo_ficticio` só valem p/ 'demo'.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    tipo: Mapped[TipoUsuario] = enum_column(
        TipoUsuario,
        nullable=False,
        default=TipoUsuario.OPERADOR,
        server_default=TipoUsuario.OPERADOR.value,
    )
    # Preenchido só quando tipo='demo' (perfil sintético anexado ao cadastro da vitrine).
    cod_cliente: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("clientes.cod_cliente", ondelete="SET NULL"), nullable=True
    )
    # Cosmético — só exibição na demo, nunca é feature de decisão.
    saldo_ficticio: Mapped[float | None] = mapped_column(Float, nullable=True)
