from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RankRequest(BaseModel):
    algorithm: str | None = Field(
        default=None, description="linucb | thompson | baseline (default do serviço)"
    )
    policy_id: str | None = Field(
        default=None,
        description=(
            "Política a servir. Omitido: usa a `active`; sem nenhuma política registrada, "
            "cai na política implícita `auto-{algorithm}`."
        ),
    )
    client: dict[str, Any] = Field(
        description="Features do cliente (idade, renda_estimada_anual_brl, flags possui_*, etc.)"
    )
    segments: list[str] = Field(default_factory=list, description="Segmentos sintéticos do cliente")
    top: int | None = Field(default=None, ge=1, description="Limita ao top-N do ranking")
    exclude_arm_ids: list[str] = Field(default_factory=list)


class RankedOffer(BaseModel):
    arm_id: str
    rank: int
    score: float
    pred: float
    bonus: float
    category: str
    product_name: str
    description: str
    valor_total: float | None = None
    desconto_pct: float | None = None
    valor_final: float | None = None


class RankResponse(BaseModel):
    algorithm: str
    policy_id: str
    ranked: list[RankedOffer]


class UpdateRequest(BaseModel):
    algorithm: str | None = None
    policy_id: str | None = Field(
        default=None, description="Mesma resolução do /rank — omitido usa a política `active`."
    )
    arm_id: str
    reward: float = Field(description="Reward = click (0 ou 1)")
    client: dict[str, Any] = Field(default_factory=dict)
    segments: list[str] = Field(default_factory=list)


class UpdateResponse(BaseModel):
    algorithm: str
    policy_id: str
    arm_id: str
    status: str
