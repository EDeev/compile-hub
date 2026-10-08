"""Привязки входа через внешние сервисы (Яндекс, VK ID)

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-08 06:14:15.850337
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "oauth_accounts",
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("provider_user_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("provider", "provider_user_id"),
        sa.UniqueConstraint("user_id", "provider", name="oauth_accounts_user_provider_key"),
    )


def downgrade() -> None:
    op.drop_table("oauth_accounts")
