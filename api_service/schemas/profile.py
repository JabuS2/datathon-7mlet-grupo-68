"""Contrato de atualização do contexto do próprio cliente (`PUT /profile`).

Antes o perfil era um `dict` livre em `client_profiles`. Consolidamos em `Cliente`: as
features viraram colunas tipadas, então a atualização é parcial e explícita — não dá mais
para escrever uma chave que o modelo vai ignorar em silêncio.

A leitura do perfil é `GET /me/profile` (`ClienteResponse`), que já devolve tudo.
"""

from pydantic import Field

from schemas.base import BaseSchema


class ProfileUpdate(BaseSchema):
    """Campos de contexto que o próprio cliente pode alterar. Tudo opcional (PATCH-like).

    Fora daqui de propósito: `cod_cliente` e `origem` (identidade), `sexo` (atributo
    protegido — LGPD, nunca é feature de decisão) e as flags de posse de produto, que são
    consequência do que o cliente contratou, não algo que ele declara.
    """

    idade: int | None = Field(default=None, ge=18, le=100)
    renda_estimada_anual_brl: float | None = Field(default=None, ge=0)
    tempo_relacionamento_meses: int | None = Field(default=None, ge=0)
    segmento: str | None = Field(default=None, max_length=40)
    estado: str | None = Field(default=None, min_length=2, max_length=2)
