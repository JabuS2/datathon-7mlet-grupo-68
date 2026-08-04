"""oferta: valores comerciais (valor_total, desconto_pct, valor_final)

Revision ID: f0b6a874ee20
Revises: 77ee3fe5e1b0
Create Date: 2026-08-04 00:20:00.000000

Os três já existiam no `offer_catalog.json` e eram lidos só pelo model_service, que os
devolve no `/rank`. Trazê-los para a tabela é o que permite debitar o saldo do cliente com
um preço confiável do lado do servidor — aceitar o valor enviado pelo front seria deixar o
cliente escolher quanto pagar.

Nullable: o catálogo pode não precificar todo braço.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f0b6a874ee20"
down_revision: str | Sequence[str] | None = "77ee3fe5e1b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("ofertas", sa.Column("valor_total", sa.Float(), nullable=True))
    op.add_column("ofertas", sa.Column("desconto_pct", sa.Float(), nullable=True))
    op.add_column("ofertas", sa.Column("valor_final", sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ofertas", "valor_final")
    op.drop_column("ofertas", "desconto_pct")
    op.drop_column("ofertas", "valor_total")
