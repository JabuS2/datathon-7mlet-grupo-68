"""drop client_profiles (consolidado em clientes)

Revision ID: 83d11333b3fb
Revises: c24291387733
Create Date: 2026-08-03 21:21:14.157868

O contexto do bandit passou a vir de `clientes`, a mesma entidade que `decisao`,
`recompensa` e `evento_impressao` referenciam por `cod_cliente`. Enquanto o perfil vivia em
`client_profiles` (chaveado por `user_id`), a trilha auditável não conseguia ligar uma
decisão ao perfil que a gerou, e o `dict` livre de features não distinguia atributo
protegido (`sexo`) de sensível monitorado (`renda`) — distinção que `clientes` faz por
coluna.

O downgrade recria a tabela vazia: os perfis não são recuperáveis, porque as features JSON
não têm equivalente 1:1 nas colunas tipadas de `clientes`.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "83d11333b3fb"
down_revision: str | Sequence[str] | None = "c24291387733"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table("client_profiles")


def downgrade() -> None:
    """Downgrade schema."""
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
