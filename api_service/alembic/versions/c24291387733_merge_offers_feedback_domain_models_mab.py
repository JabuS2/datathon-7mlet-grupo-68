"""merge offers_feedback + domain_models_mab

Revision ID: c24291387733
Revises: b2f7a1c9d3e4, c77a8e237caf
Create Date: 2026-08-03 19:39:21.818302

Merge vazio: os dois branches criaram tabelas disjuntas (client_profiles/feedback_events
de um lado, o domínio MAB do outro), então só é preciso reunir os heads.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "c24291387733"
down_revision: str | Sequence[str] | None = ("b2f7a1c9d3e4", "c77a8e237caf")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
