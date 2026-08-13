"""Reincorpora a governança no banco único da API após a consolidação do model service."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "f0b6a874ee20"
branch_labels = None
depends_on = None


def _timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "politicas",
        sa.Column("policy_id", sa.String(60), primary_key=True),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("algorithm", sa.String(20), nullable=False),
        sa.Column("hyperparams", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "ciclos_retreino",
        sa.Column("run_id", sa.String(80), primary_key=True),
        sa.Column("policy_id", sa.String(60), sa.ForeignKey("politicas.policy_id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("metrics", postgresql.JSONB(), nullable=False),
        sa.Column("registry_version", sa.String(40)),
        *_timestamps(),
    )
    op.create_table(
        "aprovacoes_humanas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(80), sa.ForeignKey("ciclos_retreino.run_id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(10), nullable=False),
        sa.Column("note", sa.String(500)),
        *_timestamps(),
    )
    op.create_table(
        "metricas_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("policy_id", sa.String(60), sa.ForeignKey("politicas.policy_id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric", sa.String(40), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("alert", sa.Boolean(), nullable=False),
        *_timestamps(),
    )


def downgrade() -> None:
    op.drop_table("metricas_snapshot")
    op.drop_table("aprovacoes_humanas")
    op.drop_table("ciclos_retreino")
    op.drop_table("politicas")
