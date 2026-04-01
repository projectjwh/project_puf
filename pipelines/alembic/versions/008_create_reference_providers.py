"""Create provider and facility reference tables.

Tables: ref_providers, ref_provider_taxonomies, ref_pos_facilities

Revision ID: 008
Revises: 007
Create Date: 2026-03-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ref_providers — ~8M rows (master provider dimension from NPPES)
    op.create_table(
        "ref_providers",
        sa.Column("npi", sa.String(10), primary_key=True),
        sa.Column("entity_type_code", sa.String(1), nullable=False),  # 1=Individual, 2=Org
        sa.Column("entity_type", sa.String(15)),  # Individual, Organization
        sa.Column("display_name", sa.String(300), nullable=False),  # Derived
        sa.Column("provider_last_name", sa.String(150)),
        sa.Column("provider_first_name", sa.String(100)),
        sa.Column("provider_middle_name", sa.String(100)),
        sa.Column("provider_credential", sa.String(50)),
        sa.Column("provider_organization_name", sa.String(300)),
        sa.Column("provider_gender_code", sa.String(1)),
        # Practice address
        sa.Column("practice_address_line_1", sa.String(300)),
        sa.Column("practice_address_line_2", sa.String(300)),
        sa.Column("practice_city", sa.String(200)),
        sa.Column("practice_state", sa.String(2)),
        sa.Column("practice_zip5", sa.String(5)),
        sa.Column("practice_zip_full", sa.String(20)),
        sa.Column("practice_phone", sa.String(20)),
        sa.Column("practice_fax", sa.String(20)),
        # State FIPS (derived from state abbreviation)
        sa.Column("state_fips", sa.String(2)),
        # Taxonomy
        sa.Column("primary_taxonomy_code", sa.String(10)),
        sa.Column("primary_taxonomy_description", sa.String(300)),
        sa.Column("taxonomy_count", sa.SmallInteger),
        # Status
        sa.Column("enumeration_date", sa.Date),
        sa.Column("deactivation_date", sa.Date),
        sa.Column("reactivation_date", sa.Date),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_individual", sa.Boolean),
        sa.Column("is_organization", sa.Boolean),
        sa.Column("years_since_enumeration", sa.Numeric(5, 1)),
        # Metadata
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        sa.Column("_snapshot_date", sa.Date),
        schema="reference",
    )
    op.create_index("ix_ref_providers_state", "ref_providers", ["practice_state"], schema="reference")
    op.create_index("ix_ref_providers_zip5", "ref_providers", ["practice_zip5"], schema="reference")
    op.create_index("ix_ref_providers_taxonomy", "ref_providers", ["primary_taxonomy_code"], schema="reference")
    op.create_index("ix_ref_providers_active", "ref_providers", ["is_active"], schema="reference")
    op.create_index("ix_ref_providers_entity", "ref_providers", ["entity_type_code"], schema="reference")
    op.create_index("ix_ref_providers_state_fips", "ref_providers", ["state_fips"], schema="reference")
    op.create_index(
        "ix_ref_providers_name",
        "ref_providers",
        ["provider_last_name", "provider_first_name"],
        schema="reference",
    )

    # ref_provider_taxonomies — one row per NPI × taxonomy_code (unpivoted)
    op.create_table(
        "ref_provider_taxonomies",
        sa.Column("npi", sa.String(10), nullable=False),
        sa.Column("taxonomy_code", sa.String(10), nullable=False),
        sa.Column("taxonomy_slot", sa.SmallInteger, nullable=False),  # 1-15
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("license_number", sa.String(50)),
        sa.Column("license_state", sa.String(2)),
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_primary_key(
        "pk_ref_provider_taxonomies", "ref_provider_taxonomies",
        ["npi", "taxonomy_code", "taxonomy_slot"], schema="reference",
    )
    op.create_index(
        "ix_ref_provider_taxonomies_npi", "ref_provider_taxonomies",
        ["npi"], schema="reference",
    )
    op.create_index(
        "ix_ref_provider_taxonomies_code", "ref_provider_taxonomies",
        ["taxonomy_code"], schema="reference",
    )

    # ref_pos_facilities — ~300K rows (Provider of Services file)
    op.create_table(
        "ref_pos_facilities",
        sa.Column("ccn", sa.String(6), primary_key=True),  # CMS Certification Number
        sa.Column("facility_name", sa.String(300), nullable=False),
        sa.Column("facility_type", sa.String(100)),
        sa.Column("facility_type_code", sa.String(4)),
        sa.Column("ownership_type", sa.String(100)),
        sa.Column("ownership_code", sa.String(2)),
        # Address
        sa.Column("street_address", sa.String(300)),
        sa.Column("city", sa.String(200)),
        sa.Column("state", sa.String(2)),
        sa.Column("zip5", sa.String(5)),
        sa.Column("zip_full", sa.String(20)),
        sa.Column("county_code", sa.String(5)),
        sa.Column("phone", sa.String(20)),
        sa.Column("state_fips", sa.String(2)),
        # Capacity
        sa.Column("bed_count", sa.Integer),
        sa.Column("bed_count_total", sa.Integer),
        # Certification
        sa.Column("certification_date", sa.Date),
        sa.Column("termination_date", sa.Date),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        # Participation
        sa.Column("medicare_participating", sa.Boolean),
        sa.Column("medicaid_participating", sa.Boolean),
        # Metadata
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_index("ix_ref_pos_facilities_state", "ref_pos_facilities", ["state"], schema="reference")
    op.create_index("ix_ref_pos_facilities_type", "ref_pos_facilities", ["facility_type_code"], schema="reference")
    op.create_index("ix_ref_pos_facilities_active", "ref_pos_facilities", ["is_active"], schema="reference")


def downgrade() -> None:
    op.drop_table("ref_pos_facilities", schema="reference")
    op.drop_table("ref_provider_taxonomies", schema="reference")
    op.drop_table("ref_providers", schema="reference")
