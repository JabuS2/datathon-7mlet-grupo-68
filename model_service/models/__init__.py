from models.base import BanditContext, BanditModel, RankedArm
from models.baseline import DeterministicBaseline
from models.context import SEG_KEYS, ContextBuilder
from models.linucb import LinUCB
from models.thompson import ThompsonSampling

ALGORITHMS = ("linucb", "thompson", "baseline")

__all__ = [
    "ALGORITHMS",
    "SEG_KEYS",
    "BanditContext",
    "BanditModel",
    "ContextBuilder",
    "DeterministicBaseline",
    "LinUCB",
    "RankedArm",
    "ThompsonSampling",
]


def model_from_state(state: dict) -> BanditModel:
    """Reconstrói o modelo correto a partir do campo ``name`` no estado."""
    name = state.get("name")
    if name == "linucb":
        return LinUCB.from_state(state)
    if name == "thompson":
        return ThompsonSampling.from_state(state)
    if name == "baseline":
        return DeterministicBaseline.from_state(state)
    raise ValueError(f"Modelo desconhecido no estado: {name!r}")
