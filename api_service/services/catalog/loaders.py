"""Parsers puros dos dados de referência (catálogo, golden set) → kwargs prontos p/ os models.

Sem dependência de DB nem de pandas: só `csv`/`json` da stdlib. Cada função devolve dicts cujas
chaves batem com os campos dos models SQLAlchemy, para o seeder apenas instanciar e persistir.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from pathlib import Path

from models.cliente import PRODUCT_FLAGS

# ─────────────────────────── catálogo de ofertas ───────────────────────────


def load_offer_catalog(path: str | Path) -> tuple[dict, list[dict]]:
    """Lê `offer_catalog.json` → (reward_definition, lista de kwargs de `Oferta`)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    meta = data.get("catalog_metadata", {})
    reward_definition = meta.get("reward_definition", {})

    offers: list[dict] = []
    for off in data.get("offers", []):
        offers.append(
            {
                "arm_id": off["arm_id"],
                "product_name": off["product_name"],
                "description": off["description"],
                "category": off["category"],
                "expected_revenue_brl": float(off["expected_revenue_brl"]),
                "context_features": off.get("context_features", []),
                "eligible_segment": off.get("eligible_segment", {}),
                "ucb_exploration_factor": float(
                    off.get("ucb_params", {}).get("exploration_factor", 1.5)
                ),
            }
        )
    return reward_definition, offers


# ─────────────────────────── segmentos sintéticos ───────────────────────────


def load_segments_from_clients(path: str | Path) -> list[dict]:
    """Deriva os `segment_id` distintos da coluna `segmentos_sinteticos` do golden set."""
    seen: set[str] = set()
    with Path(path).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            for seg in _parse_json_list(row.get("segmentos_sinteticos")):
                seen.add(seg)
    return [{"segment_id": s, "description": None, "filters": {}} for s in sorted(seen)]


# ─────────────────────────── clientes (seed) ───────────────────────────


def iter_seed_clients(path: str | Path, limit: int | None = None) -> Iterator[dict]:
    """Itera o golden set → kwargs de `Cliente(origem='seed')`."""
    with Path(path).open(encoding="utf-8", newline="") as fh:
        for i, row in enumerate(csv.DictReader(fh)):
            if limit is not None and i >= limit:
                break
            kwargs = {
                "cod_cliente": int(row["cod_cliente"]),
                "idade": int(float(row["idade"])),
                "tempo_relacionamento_meses": int(float(row["tempo_relacionamento_meses"] or 0)),
                "ind_ativo": _to_bool(row.get("ind_ativo")),
                "segmento": (row.get("segmento") or None),
                "estado": (row.get("estado") or None),
                "sexo": (row.get("sexo") or None),
                "renda_estimada_anual_brl": _to_float(row.get("renda_estimada_anual_brl")),
                "segmentos_sinteticos": _parse_json_list(row.get("segmentos_sinteticos")),
                "evento_viagem_sintetico": _to_bool(row.get("evento_viagem_sintetico")),
                "origem": "seed",
            }
            for flag in PRODUCT_FLAGS:
                kwargs[flag] = _to_bool(row.get(flag))
            yield kwargs


# ─────────────────────────── golden set (avaliação) ───────────────────────────


def load_evaluation_cases(path: str | Path) -> list[dict]:
    """Lê `evaluation_cases.jsonl` (tolerante: [] se o arquivo ainda não existir)."""
    p = Path(path)
    if not p.exists():
        return []
    cases: list[dict] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        raw = json.loads(line)
        cases.append(
            {
                "case_id": raw["case_id"],
                "context": raw.get("context", {}),
                "expected_arm": raw["expected_arm"],
                "expected_reward": raw.get("expected_reward"),
                "rationale": raw.get("rationale"),
                "pass_fail_criteria": raw.get("pass_fail_criteria"),
                "type": raw.get("type", "typical"),
            }
        )
    return cases


# ─────────────────────────── helpers ───────────────────────────


def _to_bool(value: str | None) -> bool:
    if value is None or value == "":
        return False
    try:
        return float(value) >= 0.5
    except ValueError:
        return str(value).strip().lower() in {"true", "s", "sim", "yes"}


def _to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return [str(x) for x in parsed] if isinstance(parsed, list) else []
    except (ValueError, TypeError):
        return []
