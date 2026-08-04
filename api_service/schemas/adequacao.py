"""Regras de adequação (suitability).

Morava em `schemas/governanca.py`, que foi para o model_service junto com o ciclo de vida
das políticas. Suitability não é governança de modelo: é regra de negócio sobre *a quem* uma
oferta pode ser servida, e o dado de referência (cliente, oferta) está aqui.

Nota: `RegraAdequacao` continua sem serviço e sem endpoint — a elegibilidade real roda no
model_service a partir do `offer_catalog.json`. A decisão de dar função à tabela ou removê-la
está na Fase 4 (avaliação offline), onde ela ou ganha uso ou não tem mais desculpa.
"""

from enums.governanca import AcaoAdequacao
from schemas.base import BaseSchema


class RegraAdequacaoResponse(BaseSchema):
    """Regra de suitability que bloqueia/exige revisão de uma oferta inadequada (Etapa 8)."""

    rule_id: str
    arm_id: str
    condition: dict
    action: AcaoAdequacao
