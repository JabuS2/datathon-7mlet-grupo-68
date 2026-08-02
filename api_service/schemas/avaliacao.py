from enums.avaliacao import TipoCasoAvaliacao
from schemas.base import BaseSchema


class CasoAvaliacaoResponse(BaseSchema):
    """Caso do golden set (Etapa 4): contexto + ação/recompensa esperadas + critério pass/fail."""

    case_id: str
    context: dict
    expected_arm: str
    expected_reward: float | None = None
    rationale: str | None = None
    pass_fail_criteria: str | None = None
    type: TipoCasoAvaliacao
