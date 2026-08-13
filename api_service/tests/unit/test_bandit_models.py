from __future__ import annotations

from contextlib import asynccontextmanager

import numpy as np
import pytest

from exceptions import BadRequest, NotFound
from services.bandit.audit import build_audit, strip_protected
from services.bandit.catalog.loader import Catalog
from services.bandit.models.base import BanditContext, explore_or_exploit
from services.bandit.models.baseline import DeterministicBaseline
from services.bandit.models.context import ContextBuilder
from services.bandit.models.linucb import LinUCB
from services.bandit.models.thompson import ThompsonSampling
from services.bandit.policy_resolver import auto_policy, resolve_policy
from services.bandit.service import BanditService
from services.bandit.store.state_store import StateStore
from services.monitoring.service import MonitoringService


def test_context_builder_builds_and_roundtrips_state() -> None:
    builder = ContextBuilder(["idade", "renda"], [10, 100], [0, 10], ["SEG-A", "SEG-B"])
    vector = builder.build({"idade": 12, "renda": None}, ["SEG-B"])

    assert builder.dim == 5
    assert vector.tolist() == [1.0, 2.0, -10.0, 0.0, 1.0]
    restored = ContextBuilder.from_state(builder.to_state())
    assert restored.build({"idade": 12, "renda": 100}, ["SEG-A"]).tolist() == [1, 2, 0, 1, 0]


def test_baseline_covers_business_categories_and_filters() -> None:
    model = DeterministicBaseline(["credito", "seguro", "investimento"])
    ctx = BanditContext(np.ones(1), client={"segmento": "01 - ALTA RENDA"})
    ranked = model.rank(ctx, [True, True, True], exclude=(2,))
    assert [row.arm_index for row in ranked] == [0, 1]
    assert model.get_state() == {
        "name": "baseline",
        "arm_categories": ["credito", "seguro", "investimento"],
    }
    assert (
        DeterministicBaseline.from_state(model.get_state()).arm_categories == model.arm_categories
    )
    model.update(0, 1, ctx)

    cases = [
        (["SEG-VIP"], "investimento"),
        (["SEG-INVESTIDOR-EXPERIENTE"], "investimento"),
        (["SEG-SENIOR"], "seguro"),
        (["SEG-CREDITO-ATIVO"], "credito"),
        (["SEG-JOVEM"], "credito"),
        (["SEG-PERFIL-FAMILIAR"], "seguro"),
        ([], "investimento"),
        ([], "credito"),
    ]
    for segments, expected in cases:
        client = {
            "renda_estimada_anual_brl": 90_000 if expected == "investimento" and not segments else 0
        }
        assert model._target_category(client, segments) == expected


def test_linucb_update_rank_and_roundtrip() -> None:
    model = LinUCB(2, 2, [1, 2], scale=0.5)
    ctx = BanditContext(np.array([1.0, 2.0]))
    assert explore_or_exploit(2, -1) == "explore"
    assert explore_or_exploit(0.1, 1) == "exploit"
    cold = model.rank(ctx, [True, False])
    assert cold[0].reason_codes == ["policy:linucb", "cold_start"]
    model.update(0, 1, ctx)
    ranked = model.rank(ctx, [True, True], exclude=(1,))
    assert ranked[0].reason_codes[0] == "policy:linucb"
    restored = LinUCB.from_state(model.get_state())
    assert np.allclose(restored.b[0], model.b[0])


def test_thompson_update_rank_and_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    model = ThompsonSampling(2)
    monkeypatch.setattr(np.random, "beta", lambda alpha, beta: np.array([0.9, 0.1]))
    ctx = BanditContext(np.ones(1))
    assert model.rank(ctx, [True, False])[0].reason_codes == ["policy:thompson", "cold_start"]
    model.update(0, 1, ctx)
    model.update(1, 0, ctx)
    ranked = model.rank(ctx, [True, True], exclude=(1,))
    assert ranked[0].score == 0.9
    restored = ThompsonSampling.from_state(model.get_state())
    assert restored.alpha.tolist() == [2.0, 1.0]
    assert restored.beta.tolist() == [1.0, 2.0]


def test_audit_normalizes_values_and_strips_protected_data() -> None:
    audit = build_audit(
        {"idade": "42", "renda": None, "sexo": "x"},
        ["SEG-B", "SEG-A"],
        ["idade", "renda"],
        12.345,
        ["z", "a"],
    )
    assert audit["features_numericas"] == {"idade": 42.0, "renda": 0.0}
    assert audit["segmentos_sinteticos"] == ["SEG-A", "SEG-B"]
    assert audit["renda_percentil"] == 12.35
    assert "sexo" not in strip_protected({"sexo": "x", "idade": 42})
    assert build_audit({}, [], [], 0, [])["segmentos_sinteticos"] == []


class Reader:
    def __init__(self, policy=None, active=None):
        self.policy = policy
        self.active = active

    async def get_policy(self, policy_id):
        return self.policy

    async def get_active_policy(self):
        return self.active


@pytest.mark.asyncio
async def test_policy_resolution_explicit_active_auto_and_not_found() -> None:
    assert (await resolve_policy(None, None, "linucb")).is_auto
    explicit = type(
        "Policy", (), {"policy_id": "p1", "algorithm": "thompson", "hyperparams": None}
    )()
    resolved = await resolve_policy(Reader(policy=explicit), "p1", "baseline")
    assert resolved.policy_id == "p1" and resolved.algorithm == "thompson" and resolved.governed
    active = type(
        "Policy", (), {"policy_id": "p2", "algorithm": "baseline", "hyperparams": {"x": 1}}
    )()
    assert (await resolve_policy(Reader(active=active), None, "linucb")).policy_id == "p2"
    with pytest.raises(NotFound):
        await resolve_policy(Reader(), "missing", "linucb")
    assert auto_policy("x").policy_id == "auto-x"


class MemoryStore:
    def __init__(self):
        self.states = {}
        self.context = None

    async def load_context(self):
        return self.context

    async def save_context(self, state):
        self.context = state

    async def load_state(self, key):
        return self.states.get(key)

    async def save_state(self, key, state):
        self.states[key] = state

    async def delete_state(self, key):
        self.states.pop(key, None)

    @asynccontextmanager
    async def lock(self, key):
        yield


def _catalog(tmp_path):
    import json

    data = {
        "catalog_metadata": {},
        "offers": [
            {
                "arm_id": "A",
                "category": "credito",
                "product_name": "A",
                "description": "A",
                "context_features": ["idade"],
                "ucb_params": {"exploration_factor": 1.0},
                "eligible_segment": {"santander_filters": {}},
            },
            {
                "arm_id": "B",
                "category": "seguro",
                "product_name": "B",
                "description": "B",
                "context_features": ["idade"],
                "ucb_params": {"exploration_factor": 1.0},
                "eligible_segment": {"santander_filters": {"idade_min": 18}},
            },
        ],
    }
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(data))
    return Catalog(str(path))


@pytest.mark.asyncio
async def test_bandit_service_rank_update_and_state_projection(tmp_path) -> None:
    catalog = _catalog(tmp_path)
    store = MemoryStore()
    service = BanditService(catalog, store, "baseline")

    ranked = await service.rank(None, {"idade": 20, "sexo": "x"}, [], top=1)
    assert ranked["algorithm"] == "baseline"
    assert len(ranked["ranked"]) == 1
    assert "sexo" not in ranked["audit"]["features_numericas"]
    assert await service.snapshot_state("baseline")
    assert (await service.update("baseline", "A", 1, {"idade": 20}, []))["status"] == "updated"
    assert (await service.arm_states(auto_policy("baseline")))[0]["params"]["category"] == "credito"
    await service.restore_state("baseline", {"name": "baseline", "arm_categories": ["x", "y"]})
    await service.reset("baseline")
    with pytest.raises(NotFound):
        await service.update("baseline", "missing", 1, {}, [])
    with pytest.raises(BadRequest):
        service._resolve_algorithm("invalid")


def test_bandit_service_arm_params_and_catalog_filters(tmp_path) -> None:
    catalog = _catalog(tmp_path)
    service = BanditService(catalog, MemoryStore(), "linucb")
    assert service._arm_params("thompson", {"alpha": [2], "beta": [2]}, 0)["mean"] == 0.5
    assert service._arm_params("linucb", {"alpha": [1], "b": [[3, 4]]}, 0)["b_norm"] == 5
    assert service._arm_params("unknown", {}, 0) == {}
    assert catalog.index_of("missing") is None
    assert catalog.income_percentile(100) == 50
    assert catalog.eligibility_mask({"idade": 20}) == [True, True]


@pytest.mark.asyncio
async def test_state_store_serializes_json_and_lock() -> None:
    class Redis:
        def __init__(self):
            self.data = {}

        async def get(self, key):
            return self.data.get(key)

        async def set(self, key, value):
            self.data[key] = value

        async def delete(self, key):
            self.data.pop(key, None)

        def lock(self, key, **kwargs):
            return (key, kwargs)

    redis = Redis()
    store = StateStore(redis, "p")
    await store.save_state("x", {"v": 1})
    assert await store.load_state("x") == {"v": 1}
    assert await store.load_state("none") is None
    await store.delete_state("x")
    await store.save_context({"mu": [0]})
    assert await store.load_context() == {"mu": [0]}
    assert store._state_key("x") == "p:state:x"
    assert store._lock_key("x") == "p:lock:x"


def test_catalog_reads_client_stats_and_filters(tmp_path) -> None:
    import csv

    catalog = _catalog(tmp_path)
    csv_path = tmp_path / "clients.csv"
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["idade", "renda_estimada_anual_brl"])
        writer.writeheader()
        writer.writerows(
            [
                {"idade": 20, "renda_estimada_anual_brl": 100},
                {"idade": 30, "renda_estimada_anual_brl": 200},
            ]
        )
    catalog = Catalog(str(tmp_path / "catalog.json"), str(csv_path))
    assert catalog.context_stats()[0] == [25.0]
    assert catalog.income_percentile(200) == 100
    assert catalog.eligibility_mask({"idade": 10}) == [True, False]


@pytest.mark.asyncio
async def test_monitoring_compute_publish_and_active_versions() -> None:
    class Decisions:
        async def observations_since(self, start, policy):
            return [("A", 1.0, start)]

        async def renda_percentis_between(self, start, end, policy):
            return [10.0, 20.0]

        async def policy_versions_since(self, since):
            return ["p1"]

    class Uow:
        decisoes = Decisions()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class Client:
        def __init__(self):
            self.calls = []

        async def publish_metric(self, **kwargs):
            self.calls.append(kwargs)

    client = Client()
    service = MonitoringService(Uow(), client)
    result = await service.compute("p1", 2)
    assert result["decisions"] == 1
    await service.publish("p1", 2)
    assert client.calls
    assert await service.active_policy_versions() == ["p1"]


def test_model_registry_crud_and_artifact(monkeypatch) -> None:
    from mlflow.exceptions import MlflowException

    import services.bandit.registry.mlflow_registry as registry

    class Version:
        def __init__(self, name, version):
            self.name, self.version = name, version

    class Client:
        def search_model_versions(self, *args):
            return [Version("p", "2"), Version("p", "1")]

        def create_registered_model(self, name):
            return type("Model", (), {"name": name})()

        def delete_registered_model(self, name):
            self.deleted = name

        def delete_model_version(self, name, version):
            self.deleted_version = (name, version)

    fake_client = Client()
    monkeypatch.setattr(registry.mlflow, "set_tracking_uri", lambda uri: None)
    monkeypatch.setattr(registry, "MlflowClient", lambda tracking_uri: fake_client)
    model = registry.ModelRegistry("memory")
    assert model.list_models() == [{"name": "p", "versions": [1, 2], "latest_version": 2}]
    assert model.create_model("p")["created"]
    monkeypatch.setattr(
        fake_client,
        "create_registered_model",
        lambda name: (_ for _ in ()).throw(MlflowException("already exists")),
    )
    assert not model.create_model("p")["created"]
    assert model.delete_model("p")["deleted"]
    assert model.delete_version("p", 2)["deleted"]
    monkeypatch.setattr(
        registry.mlflow.pyfunc,
        "load_model",
        lambda path: type(
            "M", (), {"unwrap_python_model": lambda self: type("P", (), {"state": {"ok": 1}})()}
        )(),
    )
    assert model.load("p", 2) == {"ok": 1}
