from enum import StrEnum


class TipoCasoAvaliacao(StrEnum):
    """Categoria de cobertura de um caso do golden set."""

    TYPICAL = "typical"
    EDGE = "edge"
    ADVERSARIAL = "adversarial"


class StatusExperimento(StrEnum):
    RUNNING = "running"
    DONE = "done"
