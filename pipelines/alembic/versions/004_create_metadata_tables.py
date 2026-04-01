"""Create metadata schema tables.

Tracks Alembic version and dbt run metadata.

Revision ID: 004
Revises: 003
Create Date: 2026-03-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. metadata.schema_version — tracks what Alembic has applied
    #    (Alembic's own alembic_version table lives in public; this is our
    #    application-level version tracking for the catalog/reference schemas)
    op.create_table(
        "schema_version",
        sa.Column("version_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("schema_name", sa.String(50), nullable=False),
        sa.Column("migration_id", sa.String(50), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("applied_at", sa.DateTime, server_default=sa.text("NOW()")),
        sa.Column("applied_by", sa.String(50)),
        schema="metadata",
    )

    # 2. metadata.dbt_run_log — captures dbt execution metadata
    op.create_table(
        "dbt_run_log",
        sa.Column("log_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("invocation_id", sa.String(36), nullable=False),  # dbt invocation UUID
        sa.Column("command", sa.String(50), nullable=False),  # run, test, snapshot, seed
        sa.Column("status", sa.String(20), nullable=False),  # success, error, skipped
        sa.Column("models_run", sa.Integer),
        sa.Column("models_errored", sa.Integer),
        sa.Column("tests_passed", sa.Integer),
        sa.Column("tests_failed", sa.Integer),
        sa.Column("tests_warned", sa.Integer),
        sa.Column("duration_seconds", sa.Numeric(10, 2)),
        sa.Column("started_at", sa.DateTime, nullable=False),
        sa.Column("completed_at", sa.DateTime),
        sa.Column("run_results_json", sa.Text),  # full run results for debugging
        schema="metadata",
    )
    op.create_index(
        "ix_dbt_run_log_invocation", "dbt_run_log", ["invocation_id"], schema="metadata"
    )


def downgrade() -> None:
    op.drop_table("dbt_run_log", schema="metadata")
    op.drop_table("schema_version", schema="metadata")
