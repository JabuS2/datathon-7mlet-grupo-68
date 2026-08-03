from enum import StrEnum


class AlgoritmoPolitica(StrEnum):
    """Algoritmo de decisão de uma versão de política."""

    BASELINE = "baseline"
    THOMPSON = "thompson"
    LINUCB = "linucb"


class StatusPolitica(StrEnum):
    """Ciclo de vida operacional de uma política."""

    SHADOW = "shadow"  # aprende em paralelo, não serve tráfego
    ACTIVE = "active"  # política que atende /decide
    RETIRED = "retired"  # aposentada / substituída
