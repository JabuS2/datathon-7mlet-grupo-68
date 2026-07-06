from enum import StrEnum


class Canal(StrEnum):
    """Ponto de contato digital onde a oferta é entregue."""

    APP = "app"
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"


class TipoEvento(StrEnum):
    """Evento observado após uma decisão."""

    IMPRESSION = "impression"
    CLICK = "click"


class StatusRecompensa(StrEnum):
    """Estado de observação da recompensa (delayed reward)."""

    PENDING = "pending"  # decisão registrada, resultado ainda não observado
    OBSERVED = "observed"  # transição/adoção observada
