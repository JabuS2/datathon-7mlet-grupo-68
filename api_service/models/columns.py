"""Helpers de coluna reutilizáveis pelos models."""

from enum import Enum
from typing import Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import mapped_column


def enum_column(enum_cls: type[Enum], **kwargs: Any):
    """Coluna de enum armazenada como VARCHAR pelo **valor** do StrEnum (não pelo nome).

    Sem `values_callable`, o SQLAlchemy persiste o *nome* do membro (`SEED`); aqui persistimos o
    *valor* (`seed`), casando com os contratos Pydantic e deixando as linhas legíveis no banco.
    `native_enum=False` evita criar tipos ENUM nativos no Postgres (migrações mais simples).
    """
    length = max(len(str(member.value)) for member in enum_cls)
    return mapped_column(
        SAEnum(
            enum_cls,
            native_enum=False,
            values_callable=lambda e: [str(member.value) for member in e],
            length=length,
        ),
        **kwargs,
    )
