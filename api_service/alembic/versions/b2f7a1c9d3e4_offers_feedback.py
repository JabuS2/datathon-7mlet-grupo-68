"""client_profiles and feedback_events

Revision ID: b2f7a1c9d3e4
Revises: 0548fa41ad4c
Create Date: 2026-07-29 21:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2f7a1c9d3e4"
down_revision: str | Sequence[str] | None = "0548fa41ad4c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "client_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("segments", sa.JSON(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_client_profiles_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client_profiles")),
        sa.UniqueConstraint("user_id", name=op.f("uq_client_profiles_user_id")),
    )
    op.create_table(
        "feedback_events",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("arm_id", sa.String(), nullable=False),
        sa.Column("algorithm", sa.String(), nullable=False),
        sa.Column("clicked", sa.Boolean(), nullable=False),
        sa.Column("reward", sa.Float(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_feedback_events_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback_events")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("feedback_events")
    op.drop_table("client_profiles")
