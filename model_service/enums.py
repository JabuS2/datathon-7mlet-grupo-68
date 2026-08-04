"""Enums de governança.

Espelham os do api_service (`enums/politica.py`, `enums/governanca.py`) porque os contratos
HTTP precisam bater — mas são independentes: os dois serviços podem evoluir separado, e
duplicar quatro StrEnums é mais barato que criar um pacote compartilhado entre dois serviços
que já têm ciclos de deploy distintos.
"""

from enum import StrEnum


class AlgoritmoPolitica(StrEnum):
    """Algoritmo de decisão de uma versão de política. Tem de casar com `models.ALGORITHMS`."""

    BASELINE = "baseline"
    THOMPSON = "thompson"
    LINUCB = "linucb"


class StatusPolitica(StrEnum):
    """Ciclo de vida operacional de uma política."""

    SHADOW = "shadow"  # aprende em paralelo, não serve tráfego
    ACTIVE = "active"  # política que atende /rank e /update
    RETIRED = "retired"  # aposentada / substituída


class StatusCicloRetreino(StrEnum):
    """Ciclo de vida de uma política candidata."""

    CANDIDATE = "candidate"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROMOTED = "promoted"
    ROLLED_BACK = "rolled_back"


class DecisaoAprovacao(StrEnum):
    """Veredito humano sobre promover uma política."""

    APPROVE = "approve"
    REJECT = "reject"
