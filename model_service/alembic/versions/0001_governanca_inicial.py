"""governança inicial: politicas, ciclos_retreino, aprovacoes_humanas, metricas_snapshot

Revision ID: 0001_governanca
Revises:
Create Date: 2026-08-03 21:40:00.000000

Primeira migração do banco PRÓPRIO do model_service. Não há `estados_braco`: o estado
aprendido vive no Redis chaveado por `policy_id`, de modo que cada política mantém os
próprios pesos e o rollback recupera intacto sem cópia.

`aprovacoes_humanas.user_id` não tem FK — `users` está no banco do api_service.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_governanca"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def _timestamps() -> tuple[sa.Column, sa.Column]:
    """Colunas de auditoria de linha. Recriadas a cada tabela: em SQLAlchemy 2.0 um
    objeto `Column` não pode ser reaproveitado entre tabelas (e `Column.copy()` saiu)."""
    return (
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )


def upgrade() -> None:
    """Upgrade schema."""
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
        *_timestamps(),
        sa.PrimaryKeyConstraint("policy_id", name=op.f("pk_politicas")),
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
        sa.Column("registry_version", sa.String(length=40), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["policy_id"],
            ["politicas.policy_id"],
            name=op.f("fk_ciclos_retreino_policy_id_politicas"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("run_id", name=op.f("pk_ciclos_retreino")),
    )
    op.create_table(
        "aprovacoes_humanas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=80), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "decision",
            sa.Enum("approve", "reject", name="decisaoaprovacao", native_enum=False),
            nullable=False,
        ),
        sa.Column("note", sa.String(length=500), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["ciclos_retreino.run_id"],
            name=op.f("fk_aprovacoes_humanas_run_id_ciclos_retreino"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_aprovacoes_humanas")),
    )
    op.create_table(
        "metricas_snapshot",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("policy_id", sa.String(length=60), nullable=False),
        sa.Column("metric", sa.String(length=40), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("alert", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["policy_id"],
            ["politicas.policy_id"],
            name=op.f("fk_metricas_snapshot_policy_id_politicas"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_metricas_snapshot")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("metricas_snapshot")
    op.drop_table("aprovacoes_humanas")
    op.drop_table("ciclos_retreino")
    op.drop_table("politicas")
