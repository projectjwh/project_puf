"""Create 4 RBAC roles with schema-level grants.

Revision ID: 002
Revises: 001
Create Date: 2026-03-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_role_if_not_exists(role: str, password: str | None = None) -> None:
    """Create a role only if it doesn't already exist."""
    op.execute(
        f"DO $$ BEGIN "
        f"  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{role}') THEN "
        f"    CREATE ROLE {role} LOGIN PASSWORD '{password or role}_password'; "
        f"  END IF; "
        f"END $$"
    )


def upgrade() -> None:
    # puf_pipeline: CRUD on catalog, reference, staging
    _create_role_if_not_exists("puf_pipeline")
    for schema in ("catalog", "reference", "staging"):
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO puf_pipeline")
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} TO puf_pipeline")
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} "
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO puf_pipeline"
        )

    # puf_dbt: CRUD on staging/intermediate/mart, read on reference/catalog
    _create_role_if_not_exists("puf_dbt")
    for schema in ("staging", "intermediate", "mart"):
        op.execute(f"GRANT USAGE, CREATE ON SCHEMA {schema} TO puf_dbt")
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} TO puf_dbt")
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} "
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO puf_dbt"
        )
    for schema in ("reference", "catalog"):
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO puf_dbt")
        op.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO puf_dbt")
        op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO puf_dbt")

    # puf_api: READ ONLY on mart, reference, catalog
    _create_role_if_not_exists("puf_api")
    for schema in ("mart", "reference", "catalog"):
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO puf_api")
        op.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO puf_api")
        op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO puf_api")

    # puf_admin: already exists as the connection user (superuser)
    # Grant it ownership of all schemas for migration purposes
    for schema in ("catalog", "reference", "staging", "intermediate", "mart", "metadata", "raw"):
        op.execute(f"GRANT ALL ON SCHEMA {schema} TO puf_admin")


def downgrade() -> None:
    for role in ("puf_api", "puf_dbt", "puf_pipeline"):
        op.execute(f"REASSIGN OWNED BY {role} TO puf_admin")
        op.execute(f"DROP OWNED BY {role}")
        op.execute(
            f"DO $$ BEGIN "
            f"  IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{role}') THEN "
            f"    DROP ROLE {role}; "
            f"  END IF; "
            f"END $$"
        )
