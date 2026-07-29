import numpy as np
import pytest

from models import BanditContext, ContextBuilder


@pytest.fixture
def ctx_cols():
    return [
        "idade",
        "renda_estimada_anual_brl",
        "tempo_relacionamento_meses",
        "ind_ativo",
        "possui_conta_corrente",
        "possui_cartao_credito",
        "possui_conta_investimento",
        "possui_fundo_investimento",
        "possui_financiamento_imovel",
    ]


@pytest.fixture
def context_builder(ctx_cols):
    mu = [40.0, 60000.0, 24.0, 1.0, 0.8, 0.5, 0.3, 0.2, 0.1]
    sd = [12.0, 30000.0, 18.0, 0.5, 0.4, 0.5, 0.45, 0.4, 0.3]
    return ContextBuilder(ctx_cols, mu, sd)


@pytest.fixture
def client():
    return {
        "idade": 30,
        "renda_estimada_anual_brl": 50000,
        "tempo_relacionamento_meses": 12,
        "ind_ativo": 1,
        "possui_conta_corrente": 1,
        "possui_cartao_credito": 0,
        "possui_conta_investimento": 0,
        "possui_fundo_investimento": 0,
        "possui_financiamento_imovel": 0,
        "segmento": "02 - VAREJO",
    }


@pytest.fixture
def bandit_ctx(context_builder, client):
    segments = ["SEG-JOVEM", "SEG-SEM-CARTAO"]
    x = context_builder.build(client, segments)
    return BanditContext(
        x=x,
        client=client,
        segments=segments,
        arm_categories=["credito", "credito", "seguro", "investimento"],
    )
