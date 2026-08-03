"""Contratos (E3): cada Response constrói a partir de um dict e re-serializa por alias (camelCase).

Garante que os schemas Pydantic batem com a forma de dados esperada pelos endpoints e pelo front.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from schemas.avaliacao import CasoAvaliacaoResponse
from schemas.cliente import ClienteResponse, OnboardingRequest
from schemas.decisao import (
    DecideRequest,
    DecideResponse,
    DecisaoResponse,
    FeedbackResponse,
    RewardResponse,
    ShowcaseResponse,
)
from schemas.experimento import ExperimentoResponse
from schemas.governanca import (
    AprovacaoHumanaResponse,
    CicloRetreinoResponse,
    MetricaResponse,
    RegraAdequacaoResponse,
)
from schemas.oferta import OfertaResponse
from schemas.politica import EstadoBracoResponse, PoliticaResponse
from schemas.segmento import SegmentoResponse

_NOW = datetime.now(UTC)
_DID = uuid4()

CLIENTE_FLAGS = {
    "possui_poupanca": False,
    "possui_conta_corrente": False,
    "possui_conta_corrente_plus": False,
    "possui_conta_premium": False,
    "possui_conta_salario": False,
    "possui_conta_junior": False,
    "possui_conta_universitaria": False,
    "possui_conta_digital": False,
    "possui_conta_investimento": False,
    "possui_cdb_curto_prazo": False,
    "possui_cdb_medio_prazo": False,
    "possui_cdb_longo_prazo": False,
    "possui_fundo_investimento": False,
    "possui_titulos_investimento": False,
    "possui_previdencia_privada": False,
    "possui_financiamento_imovel": False,
    "possui_financiamento_veiculo": False,
    "possui_emprestimo_pessoal": False,
    "possui_cartao_credito": False,
    "possui_aval_garantia": False,
    "possui_pagamento_tributos": False,
    "possui_folha_pagamento": False,
    "possui_beneficio_previdencia": False,
    "possui_debito_automatico": False,
}

CONTRACTS = [
    (DecideRequest, {"cod_cliente": 100870, "channel": "app"}),
    (
        DecideResponse,
        {
            "decision_id": _DID,
            "arm_id": "OFF-CR-001",
            "product_name": "Crédito Pessoal",
            "description": "...",
            "category": "credito",
            "channel": "app",
            "score": 1.23,
            "reason_codes": ["elegivel", "ucb_top"],
            "policy_version": "linucb-v1",
        },
    ),
    (
        ShowcaseResponse,
        {
            "cod_cliente": 100870,
            "policy_version": "linucb-v1",
            "items": [
                {
                    "arm_id": "OFF-CR-001",
                    "product_name": "Crédito",
                    "description": "x",
                    "category": "credito",
                    "score": 1.2,
                    "reason_codes": ["a"],
                    "rank": 1,
                }
            ],
        },
    ),
    (
        FeedbackResponse,
        {
            "event_id": uuid4(),
            "decision_id": _DID,
            "type": "click",
            "occurred_at": _NOW,
        },
    ),
    (
        RewardResponse,
        {"reward_id": uuid4(), "decision_id": _DID, "value": 0.6, "status": "observed"},
    ),
    (
        DecisaoResponse,
        {
            "decision_id": _DID,
            "cod_cliente": 100870,
            "policy_version": "linucb-v1",
            "chosen_arm_id": "OFF-CR-001",
            "channel": "app",
            "context": {"idade": 45},
            "reason_codes": ["a"],
            "score": 1.1,
            "created_at": _NOW,
        },
    ),
    (
        OnboardingRequest,
        {
            "email": "v@demo.com",
            "password": "segredo123",
            "idade": 30,
            "segmento": "02 - VAREJO",
            "renda_estimada_anual_brl": 50000,
        },
    ),
    (
        ClienteResponse,
        {
            "cod_cliente": 9000001,
            "idade": 30,
            "tempo_relacionamento_meses": 12,
            "ind_ativo": True,
            "segmento": "02 - VAREJO",
            "estado": "SP",
            "segmentos_sinteticos": ["SEG-JOVEM"],
            "origem": "demo",
            **CLIENTE_FLAGS,
        },
    ),
    (
        OfertaResponse,
        {
            "arm_id": "OFF-CR-001",
            "product_name": "Crédito",
            "description": "x",
            "category": "credito",
            "expected_revenue_brl": 1600,
            "context_features": ["idade"],
            "eligible_segment": {},
            "ucb_exploration_factor": 1.5,
        },
    ),
    (SegmentoResponse, {"segment_id": "SEG-VIP", "description": "vip", "filters": {}}),
    (
        PoliticaResponse,
        {
            "policy_id": "linucb-v1",
            "version": "1.0",
            "algorithm": "linucb",
            "hyperparams": {"alpha": 0.2},
            "status": "active",
            "created_at": _NOW,
        },
    ),
    (
        EstadoBracoResponse,
        {
            "policy_id": "linucb-v1",
            "arm_id": "OFF-CR-001",
            "alpha": 1.0,
            "beta": 1.0,
            "n_pulls": 5,
            "sum_reward": 2.0,
            "updated_at": _NOW,
        },
    ),
    (
        ExperimentoResponse,
        {
            "experiment_id": "exp-1",
            "policy_ids": ["linucb-v1"],
            "hypothesis": "h",
            "metrics": {"regret": 0.1},
            "status": "running",
        },
    ),
    (
        MetricaResponse,
        {
            "snapshot_id": uuid4(),
            "policy_id": "linucb-v1",
            "metric": "regret",
            "value": 0.1,
            "alert": False,
            "captured_at": _NOW,
        },
    ),
    (
        RegraAdequacaoResponse,
        {
            "rule_id": "R1",
            "arm_id": "OFF-CR-003",
            "condition": {"idade_max": 24},
            "action": "block",
        },
    ),
    (
        CicloRetreinoResponse,
        {
            "run_id": "run-1",
            "policy_id": "linucb-v2",
            "status": "candidate",
            "metrics": {},
        },
    ),
    (
        AprovacaoHumanaResponse,
        {
            "gate_id": uuid4(),
            "run_id": "run-1",
            "user_id": 1,
            "decision": "approve",
            "note": "ok",
            "decided_at": _NOW,
        },
    ),
    (
        CasoAvaliacaoResponse,
        {
            "case_id": "C1",
            "context": {"idade": 70},
            "expected_arm": "OFF-SEG-001",
            "expected_reward": 1.0,
            "rationale": "r",
            "pass_fail_criteria": "arm==expected",
            "type": "edge",
        },
    ),
]


@pytest.mark.parametrize(
    "model, payload", CONTRACTS, ids=[m.__name__ for m, _ in CONTRACTS]
)
def test_contract_roundtrip(model, payload):
    obj = model.model_validate(payload)  # entrada snake_case (populate_by_name)
    dumped = obj.model_dump(by_alias=True)  # saída camelCase (forma do contrato)
    reparsed = model.model_validate(dumped)  # re-parse pelos aliases
    assert reparsed == obj
