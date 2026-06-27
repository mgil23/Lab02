"""Initial schema with all tables, indexes, and RLS policies.

Revision ID: 0001
Revises:
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INT4RANGE, ARRAY, JSON, UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── tenants ───────────────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(63), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("subscription_status", sa.String(50), nullable=False, server_default="trialing"),
        sa.Column("stripe_customer_id", sa.String(255), unique=True),
        sa.Column("stripe_subscription_id", sa.String(255), unique=True),
        sa.Column("settings", JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── users ─────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255)),
        sa.Column("role", sa.String(50), nullable=False, server_default="reviewer"),
        sa.Column("sso_provider", sa.String(50)),
        sa.Column("sso_subject", sa.String(255)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "email"),
    )
    op.create_index("idx_users_tenant", "users", ["tenant_id"])

    # ── api_keys ──────────────────────────────────────────────────────
    op.create_table(
        "api_keys",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("key_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("scopes", ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_api_keys_tenant", "api_keys", ["tenant_id"])

    # ── document_types ────────────────────────────────────────────────
    op.create_table(
        "document_types",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("classification_hints", JSON, nullable=False, server_default="{}"),
        sa.Column("extraction_rules", JSON, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "slug"),
    )

    # ── document_type_fields ──────────────────────────────────────────
    op.create_table(
        "document_type_fields",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("document_type_id", UUID(as_uuid=True), sa.ForeignKey("document_types.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("field_type", sa.String(50), nullable=False),
        sa.Column("is_required", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("config", JSON, nullable=False, server_default="{}"),
    )

    # ── validation_rules ──────────────────────────────────────────────
    op.create_table(
        "validation_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("document_type_id", UUID(as_uuid=True), sa.ForeignKey("document_types.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_name", sa.String(255)),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("rule_config", JSON, nullable=False),
        sa.Column("error_message", sa.String(500), nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
    )

    # ── documents ─────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("storage_key", sa.String(1000), nullable=False),
        sa.Column("file_size", sa.BigInteger, nullable=False),
        sa.Column("page_count", sa.Integer),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("pipeline_run_id", UUID(as_uuid=True)),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_documents_tenant_status", "documents", ["tenant_id", "status"])
    op.create_index("idx_documents_tenant_created", "documents", ["tenant_id", "created_at"])

    # ── subdocuments ──────────────────────────────────────────────────
    op.create_table(
        "subdocuments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_type_id", UUID(as_uuid=True), sa.ForeignKey("document_types.id", ondelete="SET NULL")),
        sa.Column("page_range", INT4RANGE, nullable=False),
        sa.Column("page_count", sa.Integer, nullable=False),
        sa.Column("storage_key", sa.String(1000)),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("classification_confidence", sa.Numeric(5, 4)),
        sa.Column("classification_model", sa.String(100)),
        sa.Column("split_signals", JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_subdocuments_document", "subdocuments", ["document_id"])
    op.execute("CREATE INDEX idx_subdocuments_page_range ON subdocuments USING GIST(page_range)")

    # ── extracted_fields ──────────────────────────────────────────────
    op.create_table(
        "extracted_fields",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subdocument_id", UUID(as_uuid=True), sa.ForeignKey("subdocuments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("field_value", sa.Text),
        sa.Column("confidence", sa.Numeric(5, 4)),
        sa.Column("page_number", sa.Integer),
        sa.Column("bounding_box", JSON),
        sa.Column("source_text", sa.Text),
        sa.Column("reasoning", sa.Text),
        sa.Column("extraction_method", sa.String(50), nullable=False, server_default="llm"),
        sa.Column("validation_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("validation_errors", JSON),
        sa.Column("human_reviewed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("human_value", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_extracted_fields_subdoc", "extracted_fields", ["subdocument_id"])

    # ── pipeline_runs ─────────────────────────────────────────────────
    op.create_table(
        "pipeline_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="queued"),
        sa.Column("stages", JSON, nullable=False, server_default="{}"),
        sa.Column("total_duration_ms", sa.Integer),
        sa.Column("error_message", sa.Text),
        sa.Column("otel_trace_id", sa.String(32)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── usage_records ─────────────────────────────────────────────────
    op.create_table(
        "usage_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric", sa.String(100), nullable=False),
        sa.Column("quantity", sa.Numeric, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("stripe_usage_record_id", sa.String(255)),
        sa.Column("metadata", JSON),
    )
    op.create_index("idx_usage_tenant_metric_date", "usage_records", ["tenant_id", "metric", "recorded_at"])

    # ── webhooks ──────────────────────────────────────────────────────
    op.create_table(
        "webhooks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(2000), nullable=False),
        sa.Column("events", ARRAY(sa.String), nullable=False),
        sa.Column("secret_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── webhook_deliveries ────────────────────────────────────────────
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("webhook_id", UUID(as_uuid=True), sa.ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event", sa.String(100), nullable=False),
        sa.Column("payload", JSON, nullable=False),
        sa.Column("response_status", sa.Integer),
        sa.Column("response_body", sa.Text),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("attempt_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Enable RLS on all tenant-scoped tables ────────────────────────
    rls_tables = [
        "users", "api_keys", "document_types", "document_type_fields",
        "validation_rules", "documents", "subdocuments", "extracted_fields",
        "pipeline_runs", "usage_records", "webhooks",
    ]
    for table in rls_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
            USING (tenant_id = current_setting('app.tenant_id', TRUE)::UUID)
        """)

    # ── Helper function for setting tenant context ────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION set_tenant_context(p_tenant_id UUID)
        RETURNS VOID LANGUAGE plpgsql SECURITY DEFINER AS $$
        BEGIN
            PERFORM set_config('app.tenant_id', p_tenant_id::TEXT, TRUE);
        END;
        $$;
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS set_tenant_context")

    tables = [
        "webhook_deliveries", "webhooks", "usage_records", "pipeline_runs",
        "extracted_fields", "subdocuments", "documents", "validation_rules",
        "document_type_fields", "document_types", "api_keys", "users", "tenants",
    ]
    for table in tables:
        op.drop_table(table)
