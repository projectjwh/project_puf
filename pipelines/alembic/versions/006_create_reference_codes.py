"""Create code system reference tables.

Tables: ref_icd10_cm, ref_icd10_pcs, ref_hcpcs_codes, ref_msdrg,
        ref_ndc, ref_nucc_taxonomy, ref_place_of_service

Revision ID: 006
Revises: 005
Create Date: 2026-03-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ref_icd10_cm — ~72,000 diagnosis codes
    op.create_table(
        "ref_icd10_cm",
        sa.Column("icd10_cm_code", sa.String(10), primary_key=True),  # No dots: E119 not E11.9
        sa.Column("icd10_cm_code_formatted", sa.String(10)),  # With dots: E11.9
        sa.Column("description_short", sa.String(200)),
        sa.Column("description_long", sa.String(500)),
        sa.Column("chapter", sa.String(5)),
        sa.Column("chapter_description", sa.String(200)),
        sa.Column("block", sa.String(10)),  # Category range (e.g., E08-E13)
        sa.Column("block_description", sa.String(200)),
        sa.Column("is_billable", sa.Boolean, server_default="true"),
        sa.Column("fiscal_year", sa.SmallInteger),  # FY the code is effective
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_index(
        "ix_ref_icd10_cm_formatted", "ref_icd10_cm", ["icd10_cm_code_formatted"],
        schema="reference",
    )
    op.create_index(
        "ix_ref_icd10_cm_chapter", "ref_icd10_cm", ["chapter"], schema="reference",
    )

    # ref_icd10_pcs — ~78,000 procedure codes
    op.create_table(
        "ref_icd10_pcs",
        sa.Column("icd10_pcs_code", sa.String(7), primary_key=True),
        sa.Column("description_short", sa.String(200)),
        sa.Column("description_long", sa.String(500)),
        sa.Column("section", sa.String(1)),  # First character
        sa.Column("section_description", sa.String(200)),
        sa.Column("body_system", sa.String(1)),
        sa.Column("body_system_description", sa.String(200)),
        sa.Column("is_billable", sa.Boolean, server_default="true"),
        sa.Column("fiscal_year", sa.SmallInteger),
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_index(
        "ix_ref_icd10_pcs_section", "ref_icd10_pcs", ["section"], schema="reference",
    )

    # ref_hcpcs_codes — ~7,500 codes (CPT Level I + HCPCS Level II)
    op.create_table(
        "ref_hcpcs_codes",
        sa.Column("hcpcs_code", sa.String(5), primary_key=True),
        sa.Column("description_short", sa.String(200)),
        sa.Column("description_long", sa.String(500)),
        sa.Column("pricing_indicator", sa.String(2)),
        sa.Column("coverage_code", sa.String(2)),
        sa.Column("type_of_service", sa.String(3)),
        sa.Column("asc_payment_indicator", sa.String(2)),
        sa.Column("is_drug_code", sa.Boolean, server_default="false"),  # J-codes
        sa.Column("effective_date", sa.Date),
        sa.Column("termination_date", sa.Date),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("calendar_year", sa.SmallInteger),
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_index(
        "ix_ref_hcpcs_active", "ref_hcpcs_codes", ["is_active"], schema="reference",
    )

    # ref_msdrg — ~800 MS-DRG codes
    op.create_table(
        "ref_msdrg",
        sa.Column("drg_code", sa.String(3), nullable=False),
        sa.Column("fiscal_year", sa.SmallInteger, nullable=False),
        sa.Column("drg_description", sa.String(500), nullable=False),
        sa.Column("mdc_code", sa.String(2)),  # Major Diagnostic Category
        sa.Column("mdc_description", sa.String(200)),
        sa.Column("drg_type", sa.String(10)),  # Medical, Surgical
        sa.Column("weight", sa.Numeric(10, 4)),  # Relative weight
        sa.Column("geometric_mean_los", sa.Numeric(8, 2)),
        sa.Column("arithmetic_mean_los", sa.Numeric(8, 2)),
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_primary_key(
        "pk_ref_msdrg", "ref_msdrg", ["drg_code", "fiscal_year"], schema="reference",
    )
    op.create_index(
        "ix_ref_msdrg_mdc", "ref_msdrg", ["mdc_code"], schema="reference",
    )

    # ref_ndc — ~300,000 National Drug Codes
    op.create_table(
        "ref_ndc",
        sa.Column("ndc_code", sa.String(11), primary_key=True),  # 11-digit normalized
        sa.Column("ndc_formatted", sa.String(13)),  # 5-4-2 with dashes
        sa.Column("labeler_name", sa.String(200)),
        sa.Column("brand_name", sa.String(300)),
        sa.Column("generic_name", sa.String(500)),
        sa.Column("dosage_form", sa.String(100)),
        sa.Column("route", sa.String(200)),
        sa.Column("strength", sa.String(200)),
        sa.Column("package_description", sa.String(500)),
        sa.Column("product_type", sa.String(100)),  # HUMAN PRESCRIPTION, HUMAN OTC, etc.
        sa.Column("dea_schedule", sa.String(5)),  # CI, CII, CIII, CIV, CV
        sa.Column("is_opioid", sa.Boolean, server_default="false"),
        sa.Column("listing_date", sa.Date),
        sa.Column("marketing_start_date", sa.Date),
        sa.Column("marketing_end_date", sa.Date),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_index(
        "ix_ref_ndc_generic", "ref_ndc", ["generic_name"], schema="reference",
    )
    op.create_index(
        "ix_ref_ndc_brand", "ref_ndc", ["brand_name"], schema="reference",
    )
    op.create_index(
        "ix_ref_ndc_dea", "ref_ndc", ["dea_schedule"], schema="reference",
    )

    # ref_nucc_taxonomy — ~900 provider taxonomy codes
    op.create_table(
        "ref_nucc_taxonomy",
        sa.Column("taxonomy_code", sa.String(10), primary_key=True),
        sa.Column("grouping", sa.String(200)),
        sa.Column("classification", sa.String(200), nullable=False),
        sa.Column("specialization", sa.String(200)),
        sa.Column("definition", sa.Text),
        sa.Column("display_name", sa.String(300)),  # Derived: classification + specialization
        sa.Column("is_individual", sa.Boolean),  # vs. group/organization
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_index(
        "ix_ref_nucc_classification", "ref_nucc_taxonomy", ["classification"],
        schema="reference",
    )

    # ref_place_of_service — ~100 place of service codes
    op.create_table(
        "ref_place_of_service",
        sa.Column("pos_code", sa.String(2), primary_key=True),
        sa.Column("pos_name", sa.String(200), nullable=False),
        sa.Column("pos_description", sa.Text),
        sa.Column("effective_date", sa.Date),
        sa.Column("termination_date", sa.Date),
        sa.Column("is_facility", sa.Boolean),  # Facility vs. non-facility
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )


def downgrade() -> None:
    op.drop_table("ref_place_of_service", schema="reference")
    op.drop_table("ref_nucc_taxonomy", schema="reference")
    op.drop_table("ref_ndc", schema="reference")
    op.drop_table("ref_msdrg", schema="reference")
    op.drop_table("ref_hcpcs_codes", schema="reference")
    op.drop_table("ref_icd10_pcs", schema="reference")
    op.drop_table("ref_icd10_cm", schema="reference")
