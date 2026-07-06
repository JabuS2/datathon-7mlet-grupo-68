from enum import StrEnum


class TipoMetrica(StrEnum):
    """Métrica monitorada de uma política em operação."""

    REGRET = "regret"
    CONVERSION = "conversion"
    REWARD = "reward"
    PSI_DRIFT = "psi_drift"


class AcaoAdequacao(StrEnum):
    """O que fazer quando uma regra de suitability casa."""

    BLOCK = "block"
    REQUIRE_HUMAN = "require_human"


class StatusCicloRetreino(StrEnum):
    """Ciclo de vida de uma política candidata."""

    CANDIDATE = "candidate"
    APPROVED = "approved"
    PROMOTED = "promoted"
    ROLLED_BACK = "rolled_back"


class DecisaoAprovacao(StrEnum):
    """Veredito humano sobre promover uma política."""

    APPROVE = "approve"
    REJECT = "reject"
