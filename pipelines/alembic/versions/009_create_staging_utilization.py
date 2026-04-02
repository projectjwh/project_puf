"""Create staging tables for utilization data (Part B, Part D, Geographic Variation).

Part B and Part D use PARTITION BY RANGE (data_year) for yearly data.
Geographic Variation is small (~3.3K rows/year) and uses a simple table.

Revision ID: 009
Revises: 008
Create Date: 2026-03-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # =========================================================================
    # stg_cms__part_b_utilization — ~10M rows/year
    # Grain: rendering_npi × hcpcs_code × place_of_service × data_year
    # =========================================================================
    op.execute("""
        CREATE TABLE staging.stg_cms__part_b_utilization (
            rendering_npi           VARCHAR(10) NOT NULL,
            rendering_npi_name      VARCHAR(300),
            entity_type             VARCHAR(1),
            hcpcs_code              VARCHAR(5) NOT NULL,
            hcpcs_description       VARCHAR(300),
            hcpcs_drug_indicator    VARCHAR(1),
            place_of_service        VARCHAR(1),
            -- Service counts
            number_of_services      NUMERIC(12, 1),
            number_of_beneficiaries INTEGER,
            number_of_distinct_beneficiaries_per_day INTEGER,
            -- Charge amounts (source provides AVERAGES)
            avg_submitted_charge    NUMERIC(12, 2),
            avg_medicare_allowed    NUMERIC(12, 2),
            avg_medicare_payment    NUMERIC(12, 2),
            avg_medicare_standardized NUMERIC(12, 2),
            -- Derived TOTALS (computed in pipeline, critical for aggregation)
            total_submitted_charge  NUMERIC(14, 2),
            total_medicare_allowed  NUMERIC(14, 2),
            total_medicare_payment  NUMERIC(14, 2),
            total_medicare_standardized NUMERIC(14, 2),
            -- Provider context (denormalized from source)
            provider_type           VARCHAR(100),
            medicare_participation  VARCHAR(1),
            provider_state          VARCHAR(2),
            provider_zip5           VARCHAR(5),
            provider_state_fips     VARCHAR(2),
            -- Partition key
            data_year               SMALLINT NOT NULL,
            -- Metadata
            _loaded_at              TIMESTAMP DEFAULT NOW()
        ) PARTITION BY RANGE (data_year);
    """)

    # Create partitions for 2019-2024 (expandable)
    for year in range(2019, 2025):
        op.execute(f"""
            CREATE TABLE staging.stg_cms__part_b_utilization_{year}
            PARTITION OF staging.stg_cms__part_b_utilization
            FOR VALUES FROM ({year}) TO ({year + 1});
        """)

    # Indexes on parent (propagate to partitions)
    op.execute("""
        CREATE INDEX ix_stg_partb_npi
        ON staging.stg_cms__part_b_utilization (rendering_npi);
    """)
    op.execute("""
        CREATE INDEX ix_stg_partb_hcpcs
        ON staging.stg_cms__part_b_utilization (hcpcs_code);
    """)
    op.execute("""
        CREATE INDEX ix_stg_partb_state_year
        ON staging.stg_cms__part_b_utilization (provider_state, data_year);
    """)
    op.execute("""
        CREATE INDEX ix_stg_partb_npi_year
        ON staging.stg_cms__part_b_utilization (rendering_npi, data_year);
    """)

    # =========================================================================
    # stg_cms__part_d_prescribers — ~25M rows/year
    # Grain: prescriber_npi × drug_name × generic_name × data_year
    # =========================================================================
    op.execute("""
        CREATE TABLE staging.stg_cms__part_d_prescribers (
            prescriber_npi          VARCHAR(10) NOT NULL,
            prescriber_last_name    VARCHAR(150),
            prescriber_first_name   VARCHAR(100),
            prescriber_state        VARCHAR(2),
            prescriber_state_fips   VARCHAR(2),
            specialty_description   VARCHAR(200),
            -- Drug identity
            drug_name               VARCHAR(300) NOT NULL,
            generic_name            VARCHAR(300),
            -- Claim counts
            total_claim_count       INTEGER,
            total_day_supply        INTEGER,
            total_drug_cost         NUMERIC(14, 2),
            total_beneficiary_count INTEGER,
            -- Derived cost metrics
            cost_per_claim          NUMERIC(10, 2),
            cost_per_day            NUMERIC(10, 2),
            -- Brand/generic
            is_brand_name           BOOLEAN,
            is_generic              BOOLEAN,
            -- Opioid flags
            is_opioid               BOOLEAN,
            opioid_claim_count      INTEGER,
            opioid_prescriber_rate  NUMERIC(5, 4),
            -- GE65 suppression
            ge65_suppress_flag      VARCHAR(1),
            -- Partition key
            data_year               SMALLINT NOT NULL,
            -- Metadata
            _loaded_at              TIMESTAMP DEFAULT NOW()
        ) PARTITION BY RANGE (data_year);
    """)

    for year in range(2019, 2025):
        op.execute(f"""
            CREATE TABLE staging.stg_cms__part_d_prescribers_{year}
            PARTITION OF staging.stg_cms__part_d_prescribers
            FOR VALUES FROM ({year}) TO ({year + 1});
        """)

    op.execute("""
        CREATE INDEX ix_stg_partd_npi
        ON staging.stg_cms__part_d_prescribers (prescriber_npi);
    """)
    op.execute("""
        CREATE INDEX ix_stg_partd_drug
        ON staging.stg_cms__part_d_prescribers (generic_name);
    """)
    op.execute("""
        CREATE INDEX ix_stg_partd_npi_year
        ON staging.stg_cms__part_d_prescribers (prescriber_npi, data_year);
    """)
    op.execute("""
        CREATE INDEX ix_stg_partd_state_year
        ON staging.stg_cms__part_d_prescribers (prescriber_state, data_year);
    """)
    op.execute("""
        CREATE INDEX ix_stg_partd_opioid
        ON staging.stg_cms__part_d_prescribers (is_opioid)
        WHERE is_opioid = TRUE;
    """)

    # =========================================================================
    # stg_cms__geographic_variation — ~3.3K rows/year (small, no partitioning)
    # Grain: bene_geo_lvl × state_fips × county_fips × data_year
    # =========================================================================
    op.create_table(
        "stg_cms__geographic_variation",
        # Geography
        sa.Column("bene_geo_lvl", sa.String(10), nullable=False),  # State, County, National
        sa.Column("bene_geo_desc", sa.String(100)),
        sa.Column("bene_geo_cd", sa.String(5)),
        sa.Column("state_fips", sa.String(2)),
        sa.Column("county_fips", sa.String(5)),
        # Beneficiary demographics
        sa.Column("total_beneficiaries", sa.Integer),
        sa.Column("total_beneficiaries_ffs", sa.Integer),
        sa.Column("total_beneficiaries_ma", sa.Integer),
        sa.Column("ma_participation_rate", sa.Numeric(5, 4)),
        # Spending per capita
        sa.Column("total_actual_costs", sa.Numeric(14, 2)),
        sa.Column("actual_per_capita_costs", sa.Numeric(10, 2)),
        sa.Column("standardized_per_capita_costs", sa.Numeric(10, 2)),
        # Service categories
        sa.Column("ip_per_capita_costs", sa.Numeric(10, 2)),
        sa.Column("op_per_capita_costs", sa.Numeric(10, 2)),
        sa.Column("snf_per_capita_costs", sa.Numeric(10, 2)),
        sa.Column("hha_per_capita_costs", sa.Numeric(10, 2)),
        sa.Column("hospice_per_capita_costs", sa.Numeric(10, 2)),
        sa.Column("partb_per_capita_costs", sa.Numeric(10, 2)),
        sa.Column("partd_per_capita_costs", sa.Numeric(10, 2)),
        sa.Column("dme_per_capita_costs", sa.Numeric(10, 2)),
        # Utilization
        sa.Column("ip_covered_stays_per_1000", sa.Numeric(8, 2)),
        sa.Column("op_visits_per_1000", sa.Numeric(8, 2)),
        sa.Column("er_visits_per_1000", sa.Numeric(8, 2)),
        sa.Column("readmission_rate", sa.Numeric(5, 4)),
        sa.Column("ed_visit_rate", sa.Numeric(5, 4)),
        # Partition key
        sa.Column("data_year", sa.SmallInteger, nullable=False),
        # Metadata
        sa.Column("_loaded_at", sa.DateTime, server_default=sa.text("NOW()")),
        schema="staging",
    )
    op.create_index(
        "ix_stg_geovar_state_year",
        "stg_cms__geographic_variation",
        ["state_fips", "data_year"],
        schema="staging",
    )
    op.create_index(
        "ix_stg_geovar_county_year",
        "stg_cms__geographic_variation",
        ["county_fips", "data_year"],
        schema="staging",
    )
    op.create_index(
        "ix_stg_geovar_level",
        "stg_cms__geographic_variation",
        ["bene_geo_lvl"],
        schema="staging",
    )


def downgrade() -> None:
    op.drop_table("stg_cms__geographic_variation", schema="staging")
    # Drop partitioned tables (parent drops children)
    op.execute("DROP TABLE IF EXISTS staging.stg_cms__part_d_prescribers CASCADE;")
    op.execute("DROP TABLE IF EXISTS staging.stg_cms__part_b_utilization CASCADE;")
