"""Add RLS to webhook_deliveries; add key_prefix column to api_keys.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-27
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add key_prefix to api_keys if missing (may have been added in model before migration)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='api_keys' AND column_name='key_prefix'
            ) THEN
                ALTER TABLE api_keys ADD COLUMN key_prefix VARCHAR(16) NOT NULL DEFAULT '';
            END IF;
        END
        $$;
    """)

    # Enable RLS on webhook_deliveries via policy on webhook_id → webhooks.tenant_id
    op.execute("ALTER TABLE webhook_deliveries ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY webhook_deliveries_tenant_isolation ON webhook_deliveries
        USING (
            webhook_id IN (
                SELECT id FROM webhooks
                WHERE tenant_id = current_setting('app.tenant_id', TRUE)::UUID
            )
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS webhook_deliveries_tenant_isolation ON webhook_deliveries")
    op.execute("ALTER TABLE webhook_deliveries DISABLE ROW LEVEL SECURITY")
