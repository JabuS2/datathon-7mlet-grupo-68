from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str = Field(description="Nome do modelo registrado no MLflow")
    algorithm: str | None = Field(
        default=None, description="Algoritmo cujo estado atual será versionado"
    )


class LoadRequest(BaseModel):
    algorithm: str | None = Field(
        default=None, description="Algoritmo que receberá o estado carregado"
    )
    version: int | None = Field(default=None, description="Versão (default: mais recente)")
