"""Create catalog schema tables (7 tables).

Tracks pipeline metadata, governance, lineage, and data quality.

Revision ID: 003
Revises: 002
Create Date: 2026-03-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. catalog.sources — registry of all data sources
    op.create_table(
        "sources",
        sa.Column("source_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_name", sa.String(100), nullable=False, unique=True),
        sa.Column("short_name", sa.String(50), nullable=False, unique=True),
        sa.Column("publisher", sa.String(50), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("download_url", sa.Text),
        sa.Column("format", sa.String(20)),
        sa.Column("update_frequency", sa.String(20)),
        sa.Column("tier", sa.SmallInteger, nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("primary_key_columns", sa.Text),  # JSON array as text
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="catalog",
    )

    # 2. catalog.source_columns — column-level metadata
    op.create_table(
        "source_columns",
        sa.Column("column_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("catalog.sources.source_id"), nullable=False),
        sa.Column("column_name", sa.String(200), nullable=False),
        sa.Column("source_column_name", sa.String(200)),
        sa.Column("data_type", sa.String(50), nullable=False),
        sa.Column("is_nullable", sa.Boolean, server_default="true"),
        sa.Column("is_primary_key", sa.Boolean, server_default="false"),
        sa.Column("description", sa.Text),
        sa.Column("validation_regex", sa.String(200)),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="catalog",
    )
    op.create_index(
        "ix_source_columns_source_id", "source_columns", ["source_id"], schema="catalog"
    )

    # 3. catalog.pipeline_runs — execution log
    op.create_table(
        "pipeline_runs",
        sa.Column("run_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("catalog.sources.source_id"), nullable=False),
        sa.Column("run_date", sa.Date, nullable=False),
        sa.Column("data_year", sa.SmallInteger),
        sa.Column("data_quarter", sa.SmallInteger),
        sa.Column("stage", sa.String(20), nullable=False),  # acquire, validate, transform, load
        sa.Column("status", sa.String(20), nullable=False),  # running, success, failed, skipped
        sa.Column("rows_processed", sa.BigInteger),
        sa.Column("rows_loaded", sa.BigInteger),
        sa.Column("file_hash", sa.String(64)),
        sa.Column("file_size_bytes", sa.BigInteger),
        sa.Column("duration_seconds", sa.Numeric(10, 2)),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.DateTime),
        schema="catalog",
    )
    op.create_index(
        "ix_pipeline_runs_source_date", "pipeline_runs", ["source_id", "run_date"], schema="catalog"
    )
    op.create_index(
        "ix_pipeline_runs_status", "pipeline_runs", ["status"], schema="catalog"
    )

    # 4. catalog.pipeline_failures — failure details with classification
    op.create_table(
        "pipeline_failures",
        sa.Column("failure_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Integer, sa.ForeignKey("catalog.pipeline_runs.run_id"), nullable=False),
        sa.Column("error_type", sa.String(50), nullable=False),  # download, validation, transform, load
        sa.Column("error_class", sa.String(100)),  # e.g. ConnectionError, SchemaViolation
        sa.Column("error_message", sa.Text, nullable=False),
        sa.Column("error_detail", sa.Text),  # full traceback or context
        sa.Column("is_retryable", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="catalog",
    )
    op.create_index(
        "ix_pipeline_failures_run_id", "pipeline_failures", ["run_id"], schema="catalog"
    )

    # 5. catalog.validation_runs — per-load quality scores
    op.create_table(
        "validation_runs",
        sa.Column("validation_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Integer, sa.ForeignKey("catalog.pipeline_runs.run_id"), nullable=False),
        sa.Column("rule_name", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),  # BLOCK, WARN, INFO
        sa.Column("passed", sa.Boolean, nullable=False),
        sa.Column("metric_value", sa.Text),
        sa.Column("threshold", sa.Text),
        sa.Column("message", sa.Text),
        sa.Column("rows_affected", sa.BigInteger),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="catalog",
    )
    op.create_index(
        "ix_validation_runs_run_id", "validation_runs", ["run_id"], schema="catalog"
    )
    op.create_index(
        "ix_validation_runs_severity", "validation_runs", ["severity", "passed"], schema="catalog"
    )

    # 6. catalog.quarantine_rows — rows failing validation
    op.create_table(
        "quarantine_rows",
        sa.Column("quarantine_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Integer, sa.ForeignKey("catalog.pipeline_runs.run_id"), nullable=False),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("catalog.sources.source_id"), nullable=False),
        sa.Column("rule_name", sa.String(100), nullable=False),
        sa.Column("row_data", sa.Text, nullable=False),  # JSON serialized row
        sa.Column("failure_reason", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="catalog",
    )
    op.create_index(
        "ix_quarantine_rows_run_id", "quarantine_rows", ["run_id"], schema="catalog"
    )
    op.create_index(
        "ix_quarantine_rows_source_id", "quarantine_rows", ["source_id"], schema="catalog"
    )

    # 7. catalog.data_freshness — staleness tracking
    op.create_table(
        "data_freshness",
        sa.Column("freshness_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("catalog.sources.source_id"), nullable=False),
        sa.Column("data_year", sa.SmallInteger),
        sa.Column("last_checked_at", sa.DateTime),
        sa.Column("last_changed_at", sa.DateTime),
        sa.Column("last_loaded_at", sa.DateTime),
        sa.Column("latest_file_hash", sa.String(64)),
        sa.Column("is_stale", sa.Boolean, server_default="false"),
        sa.Column("staleness_days", sa.Integer),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="catalog",
    )
    op.create_index(
        "ix_data_freshness_source_id", "data_freshness", ["source_id"], schema="catalog"
    )
    op.create_unique_constraint(
        "uq_data_freshness_source_year", "data_freshness", ["source_id", "data_year"], schema="catalog"
    )


def downgrade() -> None:
    op.drop_table("data_freshness", schema="catalog")
    op.drop_table("quarantine_rows", schema="catalog")
    op.drop_table("validation_runs", schema="catalog")
    op.drop_table("pipeline_failures", schema="catalog")
    op.drop_table("pipeline_runs", schema="catalog")
    op.drop_table("source_columns", schema="catalog")
    op.drop_table("sources", schema="catalog")
