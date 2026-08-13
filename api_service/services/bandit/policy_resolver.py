"""Resolução da política que atende uma requisição de `/rank` ou `/update`.

O estado do bandit passou a ser escopado por política. Mas nem toda instalação tem
governança configurada — e o api_service ainda chama `/rank` passando só `algorithm`.
A resolução cobre os três casos, nesta ordem:

1. `policy_id` explícito no corpo → usa essa política (404 se não existir).
2. Existe uma política `active` no banco → usa ela; o `algorithm` do corpo é ignorado,
   porque quem manda no algoritmo servido é a política promovida, não o chamador.
3. Não há política nenhuma → política **implícita** `auto-{algorithm}`, que preserva o
   comportamento anterior (uma pista de estado por algoritmo) sem exigir governança.

O caso 3 é o que mantém o contrato atual do api_service funcionando sem mudança.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from exceptions import NotFound

AUTO_PREFIX = "auto-"


class PolicyReader(Protocol):
    """Só o que a resolução precisa de um `UnitOfWork` — mantém o resolver testável sem banco."""

    async def get_policy(self, policy_id: str) -> Any: ...

    async def get_active_policy(self) -> Any: ...


@dataclass(frozen=True)
class ResolvedPolicy:
    """Política efetiva de uma requisição."""

    policy_id: str
    algorithm: str
    hyperparams: dict
    #: `False` quando é a política implícita (caso 3) — não existe linha em `politicas`.
    governed: bool

    @property
    def is_auto(self) -> bool:
        return not self.governed


def auto_policy(algorithm: str) -> ResolvedPolicy:
    return ResolvedPolicy(
        policy_id=f"{AUTO_PREFIX}{algorithm}",
        algorithm=algorithm,
        hyperparams={},
        governed=False,
    )


async def resolve_policy(
    uow: PolicyReader | None, policy_id: str | None, algorithm: str
) -> ResolvedPolicy:
    """Resolve a política efetiva. `uow=None` força o caso 3 (sem banco disponível)."""
    if uow is None:
        return auto_policy(algorithm)

    if policy_id is not None:
        policy = await uow.get_policy(policy_id)
        if policy is None:
            raise NotFound(f"Política desconhecida: {policy_id!r}", code="POLICY_NOT_FOUND")
        return ResolvedPolicy(
            policy_id=policy.policy_id,
            algorithm=str(policy.algorithm),
            hyperparams=dict(policy.hyperparams or {}),
            governed=True,
        )

    active = await uow.get_active_policy()
    if active is not None:
        return ResolvedPolicy(
            policy_id=active.policy_id,
            algorithm=str(active.algorithm),
            hyperparams=dict(active.hyperparams or {}),
            governed=True,
        )

    return auto_policy(algorithm)
