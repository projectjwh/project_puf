"""Add ETag and Last-Modified columns to data_freshness.

Enables HTTP pre-check to skip unnecessary downloads for large files.

Revision ID: 011
Revises: 010
Create Date: 2026-04-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "data_freshness",
        sa.Column("latest_etag", sa.String(256), nullable=True),
        schema="catalog",
    )
    op.add_column(
        "data_freshness",
        sa.Column("latest_last_modified", sa.String(100), nullable=True),
        schema="catalog",
    )


def downgrade() -> None:
    op.drop_column("data_freshness", "latest_last_modified", schema="catalog")
    op.drop_column("data_freshness", "latest_etag", schema="catalog")
