"""Create geographic reference tables.

Tables: ref_state_fips, ref_county_fips, ref_zip_county_crosswalk, ref_cbsa, ref_ruca

Revision ID: 005
Revises: 004
Create Date: 2026-03-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ref_state_fips — 56 rows (50 states + DC + territories)
    op.create_table(
        "ref_state_fips",
        sa.Column("state_fips", sa.String(2), primary_key=True),
        sa.Column("state_abbreviation", sa.String(2), nullable=False),
        sa.Column("state_name", sa.String(50), nullable=False),
        sa.Column("region", sa.String(20)),
        sa.Column("division", sa.String(30)),
        sa.Column("is_state", sa.Boolean, server_default="true"),  # false for DC, territories
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_index(
        "ix_ref_state_fips_abbrev", "ref_state_fips", ["state_abbreviation"],
        unique=True, schema="reference",
    )

    # ref_county_fips — ~3,250 rows
    op.create_table(
        "ref_county_fips",
        sa.Column("county_fips", sa.String(5), primary_key=True),
        sa.Column("county_name", sa.String(100), nullable=False),
        sa.Column("state_fips", sa.String(2), sa.ForeignKey("reference.ref_state_fips.state_fips"), nullable=False),
        sa.Column("state_abbreviation", sa.String(2), nullable=False),
        sa.Column("class_code", sa.String(2)),  # H1=active, H4=consolidated, etc.
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_index(
        "ix_ref_county_fips_state", "ref_county_fips", ["state_fips"], schema="reference",
    )

    # ref_zip_county_crosswalk — ~50,000 rows
    op.create_table(
        "ref_zip_county_crosswalk",
        sa.Column("zip_code", sa.String(5), nullable=False),
        sa.Column("county_fips", sa.String(5), nullable=False),
        sa.Column("state_fips", sa.String(2)),
        sa.Column("state_abbreviation", sa.String(2)),
        sa.Column("residential_ratio", sa.Numeric(7, 4)),  # % of ZIP in this county
        sa.Column("business_ratio", sa.Numeric(7, 4)),
        sa.Column("other_ratio", sa.Numeric(7, 4)),
        sa.Column("total_ratio", sa.Numeric(7, 4)),
        sa.Column("quarter", sa.String(6)),  # e.g., "2024Q1"
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_primary_key(
        "pk_ref_zip_county", "ref_zip_county_crosswalk",
        ["zip_code", "county_fips"], schema="reference",
    )
    op.create_index(
        "ix_ref_zip_county_zip", "ref_zip_county_crosswalk", ["zip_code"], schema="reference",
    )
    op.create_index(
        "ix_ref_zip_county_county", "ref_zip_county_crosswalk", ["county_fips"], schema="reference",
    )

    # ref_cbsa — ~2,000 rows (Metropolitan/Micropolitan Statistical Areas)
    op.create_table(
        "ref_cbsa",
        sa.Column("cbsa_code", sa.String(5), primary_key=True),
        sa.Column("cbsa_title", sa.String(200), nullable=False),
        sa.Column("cbsa_type", sa.String(20)),  # Metropolitan, Micropolitan
        sa.Column("csa_code", sa.String(5)),  # Combined Statistical Area
        sa.Column("csa_title", sa.String(200)),
        sa.Column("county_fips", sa.String(5)),
        sa.Column("state_fips", sa.String(2)),
        sa.Column("central_outlying", sa.String(10)),  # Central, Outlying
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )

    # ref_ruca — ~75,000 rows (Rural-Urban Commuting Area codes by ZIP)
    op.create_table(
        "ref_ruca",
        sa.Column("zip_code", sa.String(5), primary_key=True),
        sa.Column("ruca_code", sa.String(5), nullable=False),  # Primary RUCA code
        sa.Column("ruca_secondary", sa.String(5)),  # Secondary code
        sa.Column("ruca_description", sa.String(200)),
        sa.Column("is_rural", sa.Boolean),  # Derived: codes 4-10 = rural
        sa.Column("state_fips", sa.String(2)),
        sa.Column("county_fips", sa.String(5)),
        sa.Column("tract_fips", sa.String(11)),
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_index(
        "ix_ref_ruca_code", "ref_ruca", ["ruca_code"], schema="reference",
    )


def downgrade() -> None:
    op.drop_table("ref_ruca", schema="reference")
    op.drop_table("ref_cbsa", schema="reference")
    op.drop_table("ref_zip_county_crosswalk", schema="reference")
    op.drop_table("ref_county_fips", schema="reference")
    op.drop_table("ref_state_fips", schema="reference")
