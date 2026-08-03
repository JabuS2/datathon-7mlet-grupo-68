"""Núcleo do multi-armed bandit — serviço puro (sem FastAPI, sem SQLAlchemy).

Portado do notebook `notebooks/simulacao_portal_linucb.ipynb`. As camadas (elegibilidade,
contexto, reward composto, políticas e engine) operam sobre dicts/dataclasses simples, para que os
endpoints (E7) apenas carreguem estado do banco, chamem o engine e persistam de volta.
"""

from services.bandit.engine import BanditEngine, Decision
from services.bandit.state import ArmState, RankedArm

__all__ = ["ArmState", "BanditEngine", "Decision", "RankedArm"]
