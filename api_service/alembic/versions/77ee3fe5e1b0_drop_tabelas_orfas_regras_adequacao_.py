"""drop tabelas orfas (regras_adequacao, experimentos, casos_avaliacao)

Revision ID: 77ee3fe5e1b0
Revises: 86865441ebd6
Create Date: 2026-08-03 23:20:00.000000

Três tabelas que nunca tiveram serviço nem endpoint. A Fase 4 (avaliação offline) era o
momento de dar uso a elas ou removê-las; nenhuma sobreviveu ao teste:

- `regras_adequacao` — a elegibilidade real é aplicada pelo model_service a partir dos
  `santander_filters` do `offer_catalog.json`. Manter uma segunda fonte de regras de
  suitability, inerte, era convite a divergência silenciosa.
- `casos_avaliacao` — o golden set de avaliação passou a viver em
  `data/golden_set/evaluation_cases.jsonl`, **versionado**, lido direto pelo harness. Uma
  cópia no banco não acrescenta nada e pode divergir do arquivo.
- `experimentos` — sem uso, sem seed, sem consumidor. O que a tabela prometia (comparar
  políticas) é feito hoje por `ciclos_retreino` no model_service.

O downgrade recria as três vazias.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "77ee3fe5e1b0"
down_revision: str | Sequence[str] | None = "86865441ebd6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table("regras_adequacao")
    op.drop_table("experimentos")
    op.drop_table("casos_avaliacao")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "casos_avaliacao",
        sa.Column("case_id", sa.String(length=60), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expected_arm", sa.String(length=20), nullable=False),
        sa.Column("expected_reward", sa.Float(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("pass_fail_criteria", sa.Text(), nullable=True),
        sa.Column(
            "type",
            sa.Enum("typical", "edge", "adversarial", name="tipocasoavaliacao", native_enum=False),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("case_id", name=op.f("pk_casos_avaliacao")),
    )
    op.create_table(
        "experimentos",
        sa.Column("experiment_id", sa.String(length=60), nullable=False),
        sa.Column("policy_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("running", "done", name="statusexperimento", native_enum=False),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("experiment_id", name=op.f("pk_experimentos")),
    )
    op.create_table(
        "regras_adequacao",
        sa.Column("rule_id", sa.String(length=60), nullable=False),
        sa.Column("arm_id", sa.String(length=20), nullable=False),
        sa.Column("condition", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "action",
            sa.Enum("block", "require_human", name="acaoadequacao", native_enum=False),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["arm_id"],
            ["ofertas.arm_id"],
            name=op.f("fk_regras_adequacao_arm_id_ofertas"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("rule_id", name=op.f("pk_regras_adequacao")),
    )
