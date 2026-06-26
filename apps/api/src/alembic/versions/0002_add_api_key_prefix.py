# SPDX-License-Identifier: AGPL-3.0-or-later
"""Add key_prefix to api_keys table

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "api_keys",
        sa.Column("key_prefix", sa.String(16), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("api_keys", "key_prefix")
