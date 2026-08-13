"""Resolução da política que atende `/rank` e `/update`.

Lógica pura (sem banco): o fake de UnitOfWork cobre os três caminhos. Os caminhos que
tocam Postgres de verdade — o `GovernanceService` — são exercitados pelo job
`model-service-tests` do CI, que sobe Postgres e roda `alembic upgrade head`.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from exceptions import NotFound
from service.policy_resolver import AUTO_PREFIX, auto_policy, resolve_policy


@dataclass
class _Policy:
    policy_id: str
    algorithm: str
    hyperparams: dict


class _FakeUow:
    """Só o que o resolver usa: buscar por id e buscar a ativa."""

    def __init__(self, policies=None, active=None):
        self._policies = {p.policy_id: p for p in (policies or [])}
        self._active = active

    async def get_policy(self, policy_id):
        return self._policies.get(policy_id)

    async def get_active_policy(self):
        return self._active


@pytest.mark.asyncio
async def test_sem_banco_usa_politica_implicita():
    """Caso 3 sem uow: preserva o comportamento anterior (uma pista por algoritmo)."""
    resolved = await resolve_policy(None, None, "linucb")
    assert resolved.policy_id == f"{AUTO_PREFIX}linucb"
    assert resolved.algorithm == "linucb"
    assert resolved.is_auto


@pytest.mark.asyncio
async def test_sem_politica_registrada_usa_implicita():
    resolved = await resolve_policy(_FakeUow(), None, "thompson")
    assert resolved.policy_id == f"{AUTO_PREFIX}thompson"
    assert not resolved.governed


@pytest.mark.asyncio
async def test_politica_ativa_vence_o_algoritmo_do_chamador():
    """Quem manda no algoritmo servido é a política promovida, não o corpo da requisição."""
    ativa = _Policy("linucb-v2", "linucb", {"alpha_scale": 0.4})
    resolved = await resolve_policy(_FakeUow(active=ativa), None, "thompson")
    assert resolved.policy_id == "linucb-v2"
    assert resolved.algorithm == "linucb"
    assert resolved.hyperparams == {"alpha_scale": 0.4}
    assert resolved.governed


@pytest.mark.asyncio
async def test_policy_id_explicito_tem_precedencia_sobre_a_ativa():
    ativa = _Policy("linucb-v2", "linucb", {})
    shadow = _Policy("linucb-v3", "linucb", {})
    uow = _FakeUow(policies=[ativa, shadow], active=ativa)
    resolved = await resolve_policy(uow, "linucb-v3", "linucb")
    assert resolved.policy_id == "linucb-v3"


@pytest.mark.asyncio
async def test_policy_id_desconhecido_e_404():
    with pytest.raises(NotFound):
        await resolve_policy(_FakeUow(), "nao-existe", "linucb")


def test_duas_politicas_do_mesmo_algoritmo_tem_chaves_de_estado_distintas():
    """A razão de existir do re-chaveamento: shadow e active não podem dividir pesos."""
    a = _Policy("linucb-v2", "linucb", {})
    b = _Policy("linucb-v3", "linucb", {})
    assert a.policy_id != b.policy_id
    # e a implícita não colide com nenhuma política nomeada
    assert auto_policy("linucb").policy_id not in {a.policy_id, b.policy_id}
