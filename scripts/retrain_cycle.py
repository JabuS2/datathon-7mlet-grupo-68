"""Abre um ciclo de retreino com as métricas apuradas do log auditável.

Junta as duas metades da Fase 5: o api_service calcula (é quem tem `decisao`/`recompensa`)
e o model_service registra o ciclo, versionando o estado da política no MLflow.

    python scripts/retrain_cycle.py --policy linucb-v1 [--window-days 14] [--publish]

Fluxo:
  1. `GET  {api}/api/v1/monitoring/metrics`  — apura conversão, reward, regret e PSI
  2. `POST {api}/.../publish`  (com --publish) — publica as métricas junto da política
  3. `POST {model}/api/v1/retrain-cycles`     — abre o ciclo `candidate`; o model_service
     registra o snapshot no MLflow e grava o `registry_version` no ciclo

O ciclo nasce `candidate`: promover exige o approval gate humano
(`POST {model}/api/v1/approvals`). Este script **não** promove nada.

Requer um token de operador (`--token` ou $OPERATOR_TOKEN) para as rotas do api_service.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", required=True, help="policy_id da candidata")
    parser.add_argument("--window-days", type=int, default=14)
    parser.add_argument("--run-id", default=None)
    parser.add_argument(
        "--publish",
        action="store_true",
        help="publica as métricas no model_service além de anexá-las ao ciclo",
    )
    parser.add_argument("--api", default=os.getenv("API_SERVICE_URL", "http://localhost:8001"))
    parser.add_argument("--model", default=os.getenv("MODEL_SERVICE_URL", "http://localhost:8002"))
    parser.add_argument("--token", default=os.getenv("OPERATOR_TOKEN", ""))
    args = parser.parse_args()

    if not args.token:
        print("ERRO: informe --token ou $OPERATOR_TOKEN (rotas de monitoramento são operador).")
        return 1

    headers = {"Authorization": f"Bearer {args.token}"}
    api, model = args.api.rstrip("/"), args.model.rstrip("/")

    with httpx.Client(timeout=60.0) as client:
        path = "/api/v1/monitoring/metrics"
        if args.publish:
            path = f"/api/v1/monitoring/metrics/{args.policy}/publish"
            resp = client.post(
                f"{api}{path}", headers=headers, params={"window_days": args.window_days}
            )
        else:
            resp = client.get(
                f"{api}{path}",
                headers=headers,
                params={"policy_version": args.policy, "window_days": args.window_days},
            )
        if resp.status_code != 200:
            print(f"ERRO ao apurar métricas: {resp.status_code} {resp.text}")
            return 1

        report = resp.json()
        metrics = {m["name"]: m["value"] for m in report["metrics"]}
        alerts = [m["name"] for m in report["metrics"] if m["alert"]]

        print(f"-> métricas ({report['decisions']} decisões em {args.window_days}d)")
        for name, value in metrics.items():
            print(f"     {name:<12} {value}")
        if alerts:
            print(f"   ALERTA em: {', '.join(alerts)}")
        if report["decisions"] == 0:
            print("   aviso: nenhuma decisão no período — os números são todos zero por"
                  " ausência de dado, não por performance.")

        resp = client.post(
            f"{model}/api/v1/retrain-cycles",
            json={"policy_id": args.policy, "run_id": args.run_id, "metrics": metrics},
        )
        if resp.status_code != 200:
            print(f"ERRO ao abrir o ciclo: {resp.status_code} {resp.text}")
            return 1

        cycle = resp.json()

    print("\n-> ciclo aberto")
    print(json.dumps(cycle, indent=2, ensure_ascii=False))
    # O model_service responde em snake_case: usa pydantic puro, não o BaseSchema com alias
    # camelCase do api_service. Os dois contratos convivem no mesmo fluxo — atenção ao ler.
    run_id = cycle["run_id"]
    if not cycle.get("registry_version"):
        print("   aviso: sem registry_version — o MLflow não respondeu; o ciclo foi aberto"
              " mesmo assim (o gate humano não depende do registry).")
    print(f"\nPróximo passo (gate humano):\n"
          f"  POST {model}/api/v1/approvals?user_id=<id>\n"
          f"       {{\"run_id\": \"{run_id}\", \"decision\": \"approve\"}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
