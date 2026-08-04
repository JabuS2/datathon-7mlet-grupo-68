"""drop governanca (migrada para o model_service)

Revision ID: 86865441ebd6
Revises: 83d11333b3fb
Create Date: 2026-08-03 22:31:42.449810

O ciclo de vida das políticas passou a ser do model_service, que tem banco próprio
(`model_service`, cadeia Alembic separada). Cinco tabelas saem daqui:

- `politicas`, `estados_braco` — o estado aprendido vive no Redis do model_service,
  chaveado por `policy_id`; `estados_braco` não foi recriada lá, porque materializar os
  mesmos pesos em Postgres criaria uma segunda cópia divergindo a cada `/update`.
- `ciclos_retreino`, `aprovacoes_humanas` — recriadas no model_service.
- `metricas_monitoramento` — o **cálculo** fica aqui (é `decisao`/`recompensa` que alimenta
  regret/conversão/PSI), mas ainda não existe; a tabela era só registro manual. Quando o
  cálculo for implementado (Fase 5), o resultado é publicado em `POST /metrics` do
  model_service. Sem consumidor hoje, sai.

Ficam no api_service: `decisao`, `evento_impressao`, `recompensa` — a trilha auditável,
chaveada por `cod_cliente`, junto de `clientes`.

O downgrade é **destrutivo por omissão**: recria as tabelas vazias. Os dados de governança,
depois desta migração, são do outro banco.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "86865441ebd6"
down_revision: str | Sequence[str] | None = "83d11333b3fb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # ordem: dependentes primeiro (FKs)
    op.drop_table("aprovacoes_humanas")
    op.drop_table("metricas_monitoramento")
    op.drop_table("ciclos_retreino")
    op.drop_table("estados_braco")
    op.drop_table("politicas")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "politicas",
        sa.Column("policy_id", sa.String(length=60), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column(
            "algorithm",
            sa.Enum("baseline", "thompson", "linucb", name="algoritmopolitica", native_enum=False),
            nullable=False,
        ),
        sa.Column("hyperparams", postgresql.JSONB(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("shadow", "active", "retired", name="statuspolitica", native_enum=False),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("policy_id", name=op.f("pk_politicas")),
    )
    op.create_table(
        "estados_braco",
        sa.Column("policy_id", sa.String(length=60), nullable=False),
        sa.Column("arm_id", sa.String(length=20), nullable=False),
        sa.Column("alpha", sa.Float(), nullable=False, server_default="1"),
        sa.Column("beta", sa.Float(), nullable=False, server_default="1"),
        sa.Column("n_pulls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sum_reward", sa.Float(), nullable=False, server_default="0"),
        sa.Column("A", postgresql.JSONB(), nullable=True),
        sa.Column("b", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["policy_id"],
            ["politicas.policy_id"],
            name=op.f("fk_estados_braco_policy_id_politicas"),
        ),
        sa.PrimaryKeyConstraint("policy_id", "arm_id", name=op.f("pk_estados_braco")),
    )
    op.create_table(
        "ciclos_retreino",
        sa.Column("run_id", sa.String(length=80), nullable=False),
        sa.Column("policy_id", sa.String(length=60), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "candidate",
                "approved",
                "rejected",
                "promoted",
                "rolled_back",
                name="statuscicloretreino",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("metrics", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["policy_id"],
            ["politicas.policy_id"],
            name=op.f("fk_ciclos_retreino_policy_id_politicas"),
        ),
        sa.PrimaryKeyConstraint("run_id", name=op.f("pk_ciclos_retreino")),
    )
    op.create_table(
        "metricas_monitoramento",
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("policy_id", sa.String(length=60), nullable=False),
        sa.Column(
            "metric",
            sa.Enum(
                "regret",
                "conversion",
                "reward",
                "psi_drift",
                name="tipometrica",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("alert", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("captured_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["policy_id"],
            ["politicas.policy_id"],
            name=op.f("fk_metricas_monitoramento_policy_id_politicas"),
        ),
        sa.PrimaryKeyConstraint("snapshot_id", name=op.f("pk_metricas_monitoramento")),
    )
    op.create_table(
        "aprovacoes_humanas",
        sa.Column("gate_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.String(length=80), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "decision",
            sa.Enum("approve", "reject", name="decisaoaprovacao", native_enum=False),
            nullable=False,
        ),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("decided_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["ciclos_retreino.run_id"],
            name=op.f("fk_aprovacoes_humanas_run_id_ciclos_retreino"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_aprovacoes_humanas_user_id_users")
        ),
        sa.PrimaryKeyConstraint("gate_id", name=op.f("pk_aprovacoes_humanas")),
    )
