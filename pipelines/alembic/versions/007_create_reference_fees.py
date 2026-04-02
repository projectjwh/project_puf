"""Create fee schedule reference tables.

Tables: ref_rvu_fee_schedule, ref_wage_index, ref_ipps_rates

Revision ID: 007
Revises: 006
Create Date: 2026-03-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ref_rvu_fee_schedule — ~16,000 rows per year
    # Relative Value Units: work + practice expense + malpractice = total RVU
    op.create_table(
        "ref_rvu_fee_schedule",
        sa.Column("hcpcs_code", sa.String(5), nullable=False),
        sa.Column("modifier", sa.String(2), nullable=False, server_default=""),
        sa.Column("calendar_year", sa.SmallInteger, nullable=False),
        sa.Column("description", sa.String(500)),
        sa.Column("status_code", sa.String(1)),  # A=Active, R=Restricted, etc.
        sa.Column("work_rvu", sa.Numeric(10, 4)),
        sa.Column("facility_pe_rvu", sa.Numeric(10, 4)),  # Practice expense (facility)
        sa.Column("nonfacility_pe_rvu", sa.Numeric(10, 4)),  # Practice expense (non-facility)
        sa.Column("malpractice_rvu", sa.Numeric(10, 4)),
        sa.Column("total_facility_rvu", sa.Numeric(10, 4)),  # Derived: work + fac_pe + mp
        sa.Column("total_nonfacility_rvu", sa.Numeric(10, 4)),  # Derived: work + nonfac_pe + mp
        sa.Column("conversion_factor", sa.Numeric(10, 4)),  # Dollar multiplier
        sa.Column("facility_payment", sa.Numeric(18, 2)),  # Derived: total_fac_rvu * CF
        sa.Column("nonfacility_payment", sa.Numeric(18, 2)),  # Derived: total_nonfac_rvu * CF
        sa.Column("global_days", sa.String(5)),  # 000, 010, 090, XXX, ZZZ
        sa.Column("pctc_indicator", sa.String(1)),  # Professional/Technical component
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_primary_key(
        "pk_ref_rvu",
        "ref_rvu_fee_schedule",
        ["hcpcs_code", "modifier", "calendar_year"],
        schema="reference",
    )
    op.create_index(
        "ix_ref_rvu_hcpcs_year",
        "ref_rvu_fee_schedule",
        ["hcpcs_code", "calendar_year"],
        schema="reference",
    )

    # ref_wage_index — ~4,000 rows per year
    # Geographic Practice Cost Index adjustments by CBSA
    op.create_table(
        "ref_wage_index",
        sa.Column("cbsa_code", sa.String(5), nullable=False),
        sa.Column("fiscal_year", sa.SmallInteger, nullable=False),
        sa.Column("cbsa_name", sa.String(200)),
        sa.Column("state_fips", sa.String(2)),
        sa.Column("wage_index", sa.Numeric(10, 4), nullable=False),
        sa.Column("reclassified_wage_index", sa.Numeric(10, 4)),
        sa.Column("gpci_work", sa.Numeric(10, 4)),  # Geographic Practice Cost Index
        sa.Column("gpci_pe", sa.Numeric(10, 4)),
        sa.Column("gpci_mp", sa.Numeric(10, 4)),
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_primary_key(
        "pk_ref_wage_index",
        "ref_wage_index",
        ["cbsa_code", "fiscal_year"],
        schema="reference",
    )
    op.create_index(
        "ix_ref_wage_index_state",
        "ref_wage_index",
        ["state_fips"],
        schema="reference",
    )

    # ref_ipps_rates — ~800 rows per year
    # Inpatient PPS DRG relative weights and rates
    op.create_table(
        "ref_ipps_rates",
        sa.Column("drg_code", sa.String(3), nullable=False),
        sa.Column("fiscal_year", sa.SmallInteger, nullable=False),
        sa.Column("drg_description", sa.String(500)),
        sa.Column("relative_weight", sa.Numeric(10, 4), nullable=False),
        sa.Column("geometric_mean_los", sa.Numeric(8, 2)),
        sa.Column("arithmetic_mean_los", sa.Numeric(8, 2)),
        sa.Column("average_payment", sa.Numeric(18, 2)),  # National average
        sa.Column("discharge_count", sa.Integer),  # National total discharges
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="reference",
    )
    op.create_primary_key(
        "pk_ref_ipps_rates",
        "ref_ipps_rates",
        ["drg_code", "fiscal_year"],
        schema="reference",
    )


def downgrade() -> None:
    op.drop_table("ref_ipps_rates", schema="reference")
    op.drop_table("ref_wage_index", schema="reference")
    op.drop_table("ref_rvu_fee_schedule", schema="reference")
