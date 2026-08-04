"""Roda a avaliação offline contra o golden set e escreve o relatório em `reports/`.

    python scripts/run_evaluation.py            # ou: make evaluate

Não precisa de Docker, banco nem model_service no ar: o harness usa o `BanditService` com
store em memória. Saída: `reports/evaluation-report.md` + código de saída 1 se alguma
propriedade bloqueante falhar (serve como gate de CI).

O relatório é de **propriedades** (elegibilidade, invariância de fairness), não de
performance. Regret e conversão vêm de tráfego real, pelo monitoramento do api_service.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "model_service"))

from catalog import Catalog  # noqa: E402
from evaluation import evaluate, load_cases  # noqa: E402
from service import BanditService  # noqa: E402
from store import StateStore  # noqa: E402

GOLDEN = os.path.join(BASE_DIR, "data", "golden_set")
CASES = os.path.join(GOLDEN, "evaluation_cases.jsonl")
OUTPUT = os.path.join(BASE_DIR, "reports", "evaluation-report.md")
ALGORITHMS = ("linucb", "thompson", "baseline")


class _MemoryStore(StateStore):
    """Store em memória: a avaliação parte sempre de estado limpo (cold-start)."""

    def __init__(self):
        self._states: dict[str, dict] = {}
        self._context: dict | None = None

    async def load_state(self, policy_id):
        return self._states.get(policy_id)

    async def save_state(self, policy_id, state):
        self._states[policy_id] = state

    async def delete_state(self, policy_id):
        self._states.pop(policy_id, None)

    async def load_context(self):
        return self._context

    async def save_context(self, state):
        self._context = state

    def lock(self, policy_id: str, timeout: int = 10, blocking_timeout: int = 10):
        return asyncio.Lock()


async def _run() -> int:
    cases = load_cases(CASES)
    if not cases:
        print(f"ERRO: golden set vazio ou ausente em {CASES}. Rode `make data-eval`.")
        return 1

    catalog = Catalog(
        os.path.join(GOLDEN, "offer_catalog.json"), os.path.join(GOLDEN, "golden_clients.csv")
    )

    lines = [
        "# Avaliação offline — golden set",
        "",
        "> Gerado por `scripts/run_evaluation.py`. **Relatório de propriedades, não de "
        "performance.** Regret, conversão e lift dependem de tráfego real e vêm do "
        "monitoramento (`GET /api/v1/monitoring/metrics`).",
        "",
        f"Casos: **{len(cases)}** — de `data/golden_set/evaluation_cases.jsonl`.",
        "",
        "| Propriedade | O que garante | Bloqueia? |",
        "|---|---|---|",
        "| `edge` | braço inelegível pelo catálogo não aparece no ranking | sim |",
        "| `adversarial` | variar atributo protegido não muda o que o cliente pode receber | sim |",
        "| `typical` | conformidade com a regra do baseline | não — divergir é aprender |",
        "",
    ]

    failed = False
    for algorithm in ALGORITHMS:
        service = BanditService(catalog, _MemoryStore(), default_algorithm=algorithm)
        report = await evaluate(service, cases, algorithm)
        summary = report.summary()
        failed = failed or not report.passed

        lines += [f"## `{algorithm}`", ""]
        lines.append(f"**Propriedades bloqueantes: {'OK' if report.passed else 'FALHA'}**")
        lines += ["", "| Tipo | Passou | Total |", "|---|---|---|"]
        for tipo, counts in sorted(summary["by_type"].items()):
            lines.append(f"| `{tipo}` | {counts['passed']} | {counts['total']} |")
        lines.append("")
        if summary["failures"]:
            lines += ["Falhas:", ""]
            lines += [
                f"- `{f['case_id']}` (`{f['type']}`) — {f['detail']}" for f in summary["failures"]
            ]
            lines.append("")
        print(f"{algorithm:<10} {'OK' if report.passed else 'FALHA'}  {json.dumps(summary['by_type'])}")

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nrelatório -> {OUTPUT}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run()))
