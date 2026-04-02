"""Create metric baselines table for statistical drift detection.

Revision ID: 012
Revises: 011
Create Date: 2026-04-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "012"
down_revision: str | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "metric_baselines",
        sa.Column("baseline_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("catalog.sources.source_id"), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("baseline_mean", sa.Numeric(18, 4)),
        sa.Column("baseline_stddev", sa.Numeric(18, 4)),
        sa.Column("baseline_min", sa.Numeric(18, 4)),
        sa.Column("baseline_max", sa.Numeric(18, 4)),
        sa.Column("sample_count", sa.Integer),
        sa.Column("computed_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="catalog",
    )
    op.create_index(
        "ix_metric_baselines_source_id",
        "metric_baselines",
        ["source_id"],
        schema="catalog",
    )


def downgrade() -> None:
    op.drop_table("metric_baselines", schema="catalog")
