"""
Registro de execuções do MAB no MLflow (Etapa 7 — Ciclo de vida MLOps).

Fornece `registrar_execucao_mlflow`, usada pelo notebook
`mab_exploracao_algoritmos.ipynb` para registrar, por política avaliada
na Etapa 3 (Baseline, Thompson Sampling, LinUCB), os hiperparâmetros do
algoritmo e as métricas de reward, conversão, receita e exploração.

Tracking store local (SQLite): <raiz do repo>/mlflow.db
"""

import os

import mlflow

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TRACKING_URI = f"sqlite:///{os.path.join(BASE_DIR, 'mlflow.db')}"
DEFAULT_EXPERIMENT_NAME = "mab-santander-etapa3"


def registrar_execucao_mlflow(
    nome_politica: str,
    params: dict,
    metrics: dict,
    tags: dict | None = None,
    artifact_path: str | None = None,
    tracking_uri: str = DEFAULT_TRACKING_URI,
    experiment_name: str = DEFAULT_EXPERIMENT_NAME,
) -> str:
    """Registra uma execução (run) do MLflow com os parâmetros e métricas de uma política do MAB.

    Args:
        nome_politica: nome da política avaliada (ex.: "Baseline", "Thompson", "LinUCB").
        params: hiperparâmetros e configuração da simulação (ex.: alpha_ucb, n_rounds).
        metrics: métricas numéricas obtidas (reward, conversão, receita, exploração...).
        tags: tags adicionais do run (ex.: {"campeao": "True"}).
        artifact_path: caminho de um arquivo a anexar ao run como artefato (ex.: CSV de resumo).
        tracking_uri: URI do tracking store do MLflow.
        experiment_name: nome do experimento no MLflow.

    Returns:
        run_id da execução criada.
    """
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name=nome_politica) as run:
        mlflow.log_params({**params, "policy": nome_politica})
        mlflow.log_metrics(metrics)
        for chave, valor in (tags or {}).items():
            mlflow.set_tag(chave, valor)
        if artifact_path:
            mlflow.log_artifact(artifact_path)
        return run.info.run_id
