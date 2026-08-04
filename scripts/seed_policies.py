"""Registra as políticas iniciais no model_service.

Antes isso era `_seed_policies` no seeder do api_service, escrevendo direto nas tabelas
`politicas`/`estados_braco`. Elas migraram para o model_service, que passou a ser dono do
ciclo de vida — então o registro agora é por HTTP, pela mesma porta que um operador usaria.

    python scripts/seed_policies.py [--url http://localhost:8002]

Idempotente: política que já existe devolve 409 POLICY_EXISTS e é reportada como "existe".
Não há priors por braço a semear — o estado nasce sob demanda no primeiro `/rank` de cada
política (chave Redis `bandit:state:{policy_id}`).
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

# LinUCB é a ativa (catálogo prod); as demais nascem em shadow para a comparação da Etapa 3.
SEED_POLICIES: list[dict] = [
    {
        "policy_id": "baseline-v1",
        "version": "1.0.0",
        "algorithm": "baseline",
        "hyperparams": {"rule": "best_expected_revenue"},
    },
    {"policy_id": "thompson-v1", "version": "1.0.0", "algorithm": "thompson", "hyperparams": {}},
    {
        "policy_id": "linucb-v1",
        "version": "1.0.0",
        "algorithm": "linucb",
        "hyperparams": {"alpha_scale": 0.2},
    },
]
ACTIVE_POLICY = "linucb-v1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default=os.getenv("MODEL_SERVICE_URL", "http://localhost:8002"),
        help="base do model_service (default: $MODEL_SERVICE_URL ou localhost:8002)",
    )
    args = parser.parse_args()
    base = args.url.rstrip("/")

    with httpx.Client(base_url=base, timeout=15.0) as client:
        for policy in SEED_POLICIES:
            resp = client.post("/api/v1/policies", json=policy)
            if resp.status_code == 200:
                print(f"  registrada  {policy['policy_id']} ({policy['algorithm']})")
            elif resp.status_code == 409:
                print(f"  já existe   {policy['policy_id']}")
            else:
                print(f"ERRO ao registrar {policy['policy_id']}: {resp.status_code} {resp.text}")
                return 1

        resp = client.post(f"/api/v1/policies/{ACTIVE_POLICY}/promote")
        if resp.status_code != 200:
            print(f"ERRO ao promover {ACTIVE_POLICY}: {resp.status_code} {resp.text}")
            return 1
        print(f"  ativa       {ACTIVE_POLICY}")

    print("OK: políticas registradas no model_service.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
