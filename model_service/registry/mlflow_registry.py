from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Any

import mlflow
from mlflow.exceptions import MlflowException, RestException
from mlflow.tracking import MlflowClient

logger = logging.getLogger(__name__)


class _BanditArtifact(mlflow.pyfunc.PythonModel):  # type: ignore[name-defined]
    """Wrapper pyfunc que carrega o estado (JSON) do bandit de um artefato.

    O estado é totalmente serializável (A_inv/b, alpha/beta, mu/sd), então versioná-lo
    como artefato + pyfunc dá reprodutibilidade e recarga sem depender de pickles frágeis.
    """

    def load_context(self, context):
        with open(context.artifacts["state"], encoding="utf-8") as f:
            self.state = json.load(f)

    def predict(self, context, model_input=None):
        # o uso principal é versionar/recarregar o estado; predict retorna o estado
        return self.state


def _log_pyfunc(python_model, artifacts, registered_model_name):
    """log_model compatível com MLflow 2.x (artifact_path=) e 3.x (name=)."""
    try:
        return mlflow.pyfunc.log_model(
            name="model",
            python_model=python_model,
            artifacts=artifacts,
            registered_model_name=registered_model_name,
        )
    except TypeError:
        return mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=python_model,
            artifacts=artifacts,
            registered_model_name=registered_model_name,
        )


class ModelRegistry:
    """Gerencia o ciclo de vida dos modelos no MLflow Model Registry.

    Métodos: ``list_models``, ``create_model``, ``register_version``, ``delete_model``,
    ``load`` — CRUD de registros dos modelos de bandit.
    """

    def __init__(self, tracking_uri: str, experiment_name: str = "datathon-mab"):
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient(tracking_uri=tracking_uri)

    def _ensure_experiment(self) -> None:
        mlflow.set_experiment(self.experiment_name)

    # ------------------------------------------------------------------ list
    def list_models(self) -> list[dict[str, Any]]:
        """Lista os modelos registrados agregando por ``search_model_versions``.

        Nota: derivamos a lista das *versões* (em vez de ``search_registered_models``)
        porque o client MLflow mais novo não parseia corretamente a resposta de
        ``registered-models/search`` do servidor 2.12.1 (descasamento de versão),
        retornando vazio; ``search_model_versions`` funciona nesse par cliente/servidor.
        """
        by_name: dict[str, list[int]] = {}
        for v in self.client.search_model_versions():
            by_name.setdefault(v.name, []).append(int(v.version))
        return [
            {
                "name": name,
                "versions": sorted(versions),
                "latest_version": max(versions),
            }
            for name, versions in sorted(by_name.items())
        ]

    # ---------------------------------------------------------------- create
    def create_model(self, name: str) -> dict[str, Any]:
        """Cria um modelo registrado vazio (idempotente)."""
        try:
            rm = self.client.create_registered_model(name)
            return {"name": rm.name, "created": True}
        except (MlflowException, RestException) as err:
            if "RESOURCE_ALREADY_EXISTS" in str(err) or "already exist" in str(err).lower():
                return {"name": name, "created": False}
            raise

    # -------------------------------------------------------------- register
    def register_version(self, name: str, state: dict[str, Any]) -> dict[str, Any]:
        """Registra uma nova versão a partir de um snapshot de estado do bandit."""
        self._ensure_experiment()
        self.create_model(name)  # garante que o registered model existe
        tmp = tempfile.mkdtemp()
        state_path = os.path.join(tmp, "state.json")
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)
        with mlflow.start_run(run_name=f"register-{name}") as run:
            mlflow.log_params(
                {
                    "algorithm": state.get("name"),
                    "n_arms": state.get("n_arms"),
                    "d": state.get("d"),
                }
            )
            _log_pyfunc(_BanditArtifact(), {"state": state_path}, registered_model_name=name)
        versions = self.client.search_model_versions(f"name='{name}'")
        latest = max(int(v.version) for v in versions)
        logger.info(
            "model_registered",
            extra={"model_name": name, "version": latest, "run_id": run.info.run_id},
        )
        return {"name": name, "version": latest, "run_id": run.info.run_id}

    # ------------------------------------------------------------------ load
    def load(self, name: str, version: int | None = None) -> dict[str, Any]:
        """Carrega o estado (dict) da versão indicada (ou a mais recente)."""
        if version is None:
            versions = self.client.search_model_versions(f"name='{name}'")
            if not versions:
                raise MlflowException(f"Modelo sem versões: {name}")
            version = max(int(v.version) for v in versions)
        model = mlflow.pyfunc.load_model(f"models:/{name}/{version}")
        return model.unwrap_python_model().state

    # ---------------------------------------------------------------- delete
    def delete_model(self, name: str) -> dict[str, Any]:
        """Remove um modelo registrado e todas as suas versões."""
        self.client.delete_registered_model(name)
        return {"name": name, "deleted": True}

    def delete_version(self, name: str, version: int) -> dict[str, Any]:
        self.client.delete_model_version(name, str(version))
        return {"name": name, "version": version, "deleted": True}
