"""Create Tier 2 staging and reference tables.

Revision ID: 010
Create Date: 2026-03-04

Adds staging/reference tables for all 26 Tier 2 data sources:
- Provider: pecos enrollment, ordering/referring
- Code Systems: APC
- Geographic: HRR/HSA, census population
- Utilization: inpatient, SNF, HHA, hospice
- Fee Schedules: CLFS, DMEPOS, SNF PPS
- Drug: SDUD, RxNorm, ASP
- Quality: Five-Star, PBJ, CAHPS, dialysis, readmissions
- Hospital: cost reports (SNF/HHA/hospice), hospital general
- Charges: hospital charges
- DME: supplier utilization
- MA: enrollment, benchmarks
"""

import sqlalchemy as sa
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # REFERENCE TABLES (small lookups — standard create_table)
    # =========================================================================

    # APC codes
    op.create_table(
        "ref_apc",
        sa.Column("apc_code", sa.String(10), primary_key=True),
        sa.Column("apc_description", sa.Text),
        sa.Column("payment_rate", sa.Numeric(12, 2)),
        sa.Column("relative_weight", sa.Numeric(8, 4)),
        sa.Column("minimum_unadjusted_copayment", sa.Numeric(12, 2)),
        sa.Column("status_indicator", sa.String(5)),
        sa.Column("effective_year", sa.Integer),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="reference",
    )

    # HRR/HSA geographic crosswalk
    op.create_table(
        "ref_hrr_hsa",
        sa.Column("zip_code", sa.String(5), primary_key=True),
        sa.Column("hrr_number", sa.Integer),
        sa.Column("hrr_city", sa.String(100)),
        sa.Column("hrr_state", sa.String(2)),
        sa.Column("hsa_number", sa.Integer),
        sa.Column("hsa_city", sa.String(100)),
        sa.Column("hsa_state", sa.String(2)),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="reference",
    )

    # Census population
    op.create_table(
        "ref_census_population",
        sa.Column("fips_code", sa.String(5), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("state_fips", sa.String(2)),
        sa.Column("county_fips", sa.String(5)),
        sa.Column("state_name", sa.String(100)),
        sa.Column("county_name", sa.String(100)),
        sa.Column("total_population", sa.BigInteger),
        sa.Column("population_65_plus", sa.BigInteger),
        sa.Column("population_under_18", sa.BigInteger),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        sa.PrimaryKeyConstraint("fips_code", "year"),
        schema="reference",
    )

    # PECOS enrollment
    op.create_table(
        "ref_pecos_enrollment",
        sa.Column("npi", sa.String(10), nullable=False),
        sa.Column("pac_id", sa.String(20)),
        sa.Column("enrollment_id", sa.String(20)),
        sa.Column("enrollment_type", sa.String(50)),
        sa.Column("enrollment_state", sa.String(2)),
        sa.Column("provider_type", sa.String(100)),
        sa.Column("specialty", sa.String(200)),
        sa.Column("organization_name", sa.String(300)),
        sa.Column("accepts_assignment", sa.Boolean),
        sa.Column("participating", sa.Boolean),
        sa.Column("enrollment_date", sa.Date),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="reference",
    )
    op.create_index("idx_ref_pecos_npi", "ref_pecos_enrollment", ["npi"], schema="reference")

    # Ordering/Referring
    op.create_table(
        "ref_ordering_referring",
        sa.Column("npi", sa.String(10), nullable=False),
        sa.Column("last_name", sa.String(200)),
        sa.Column("first_name", sa.String(200)),
        sa.Column("state", sa.String(2)),
        sa.Column("specialty", sa.String(200)),
        sa.Column("eligible", sa.Boolean),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="reference",
    )
    op.create_index("idx_ref_ordering_npi", "ref_ordering_referring", ["npi"], schema="reference")

    # RxNorm drug crosswalk
    op.create_table(
        "ref_rxnorm",
        sa.Column("rxcui", sa.String(20), primary_key=True),
        sa.Column("rxaui", sa.String(20)),
        sa.Column("name", sa.Text),
        sa.Column("tty", sa.String(20)),
        sa.Column("suppress", sa.String(5)),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="reference",
    )

    # NDC-RXCUI crosswalk (from RxNorm SAT table)
    op.create_table(
        "ref_ndc_rxcui",
        sa.Column("ndc", sa.String(11), nullable=False),
        sa.Column("rxcui", sa.String(20), nullable=False),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        sa.PrimaryKeyConstraint("ndc", "rxcui"),
        schema="reference",
    )
    op.create_index("idx_ref_ndc_rxcui_ndc", "ref_ndc_rxcui", ["ndc"], schema="reference")

    # Fee schedule: CLFS
    op.create_table(
        "ref_clfs",
        sa.Column("hcpcs_code", sa.String(10), nullable=False),
        sa.Column("effective_year", sa.Integer, nullable=False),
        sa.Column("short_description", sa.Text),
        sa.Column("national_limit_amount", sa.Numeric(12, 2)),
        sa.Column("floor_amount", sa.Numeric(12, 2)),
        sa.Column("personal_use_crosswalk", sa.String(10)),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        sa.PrimaryKeyConstraint("hcpcs_code", "effective_year"),
        schema="reference",
    )

    # Fee schedule: DMEPOS
    op.create_table(
        "ref_dmepos_fees",
        sa.Column("hcpcs_code", sa.String(10), nullable=False),
        sa.Column("modifier", sa.String(5)),
        sa.Column("state", sa.String(2)),
        sa.Column("fee_amount", sa.Numeric(12, 2)),
        sa.Column("effective_quarter", sa.String(6)),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="reference",
    )
    op.create_index("idx_ref_dmepos_hcpcs", "ref_dmepos_fees", ["hcpcs_code"], schema="reference")

    # Fee schedule: SNF PPS
    op.create_table(
        "ref_snf_pps",
        sa.Column("pdpm_group", sa.String(50), nullable=False),
        sa.Column("fiscal_year", sa.Integer, nullable=False),
        sa.Column("component", sa.String(50)),
        sa.Column("rate", sa.Numeric(12, 2)),
        sa.Column("case_mix_index", sa.Numeric(8, 4)),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        sa.PrimaryKeyConstraint("pdpm_group", "fiscal_year"),
        schema="reference",
    )

    # ASP drug pricing
    op.create_table(
        "ref_asp_pricing",
        sa.Column("hcpcs_code", sa.String(10), nullable=False),
        sa.Column("short_description", sa.Text),
        sa.Column("payment_limit", sa.Numeric(12, 4)),
        sa.Column("dosage_form", sa.String(100)),
        sa.Column("quarter", sa.Integer, nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        sa.PrimaryKeyConstraint("hcpcs_code", "quarter", "year"),
        schema="reference",
    )

    # MA benchmarks
    op.create_table(
        "ref_ma_benchmarks",
        sa.Column("county_fips", sa.String(5), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("state_fips", sa.String(2)),
        sa.Column("county_name", sa.String(100)),
        sa.Column("ffs_per_capita", sa.Numeric(12, 2)),
        sa.Column("ma_benchmark", sa.Numeric(12, 2)),
        sa.Column("risk_score", sa.Numeric(8, 4)),
        sa.Column("quality_bonus_pct", sa.Numeric(5, 2)),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        sa.PrimaryKeyConstraint("county_fips", "year"),
        schema="reference",
    )
    op.create_index("idx_ref_ma_bench_county", "ref_ma_benchmarks", ["county_fips"], schema="reference")

    # Hospital general information
    op.create_table(
        "ref_hospital_general",
        sa.Column("ccn", sa.String(6), primary_key=True),
        sa.Column("facility_name", sa.String(300)),
        sa.Column("address", sa.Text),
        sa.Column("city", sa.String(100)),
        sa.Column("state", sa.String(2)),
        sa.Column("zip_code", sa.String(10)),
        sa.Column("county_name", sa.String(100)),
        sa.Column("phone_number", sa.String(20)),
        sa.Column("hospital_type", sa.String(100)),
        sa.Column("hospital_ownership", sa.String(100)),
        sa.Column("emergency_services", sa.Boolean),
        sa.Column("meets_ehr_criteria", sa.Boolean),
        sa.Column("overall_rating", sa.Integer),
        sa.Column("mortality_national_comparison", sa.String(50)),
        sa.Column("safety_national_comparison", sa.String(50)),
        sa.Column("readmission_national_comparison", sa.String(50)),
        sa.Column("patient_experience_national_comparison", sa.String(50)),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="reference",
    )

    # =========================================================================
    # STAGING TABLES (analytical data — some partitioned)
    # =========================================================================

    # Inpatient utilization — partitioned by data_year
    op.execute("""
        CREATE TABLE staging.stg_cms__inpatient (
            ccn VARCHAR(6) NOT NULL,
            facility_name VARCHAR(300),
            provider_state VARCHAR(2),
            provider_state_fips VARCHAR(2),
            drg_code VARCHAR(5) NOT NULL,
            drg_description TEXT,
            total_discharges INTEGER,
            avg_covered_charges NUMERIC(14, 2),
            avg_total_payments NUMERIC(14, 2),
            avg_medicare_payments NUMERIC(14, 2),
            total_covered_charges NUMERIC(14, 2),
            total_payments NUMERIC(14, 2),
            total_medicare_payments NUMERIC(14, 2),
            data_year INTEGER NOT NULL,
            _loaded_at TIMESTAMP,
            _source VARCHAR(50)
        ) PARTITION BY RANGE (data_year)
    """)
    for year in range(2019, 2025):
        op.execute(f"""
            CREATE TABLE staging.stg_cms__inpatient_y{year}
            PARTITION OF staging.stg_cms__inpatient
            FOR VALUES FROM ({year}) TO ({year + 1})
        """)
    op.create_index("idx_stg_inpatient_ccn", "stg_cms__inpatient", ["ccn"], schema="staging")
    op.create_index("idx_stg_inpatient_drg", "stg_cms__inpatient", ["drg_code", "data_year"], schema="staging")

    # SNF utilization
    op.create_table(
        "stg_cms__snf_utilization",
        sa.Column("ccn", sa.String(6), nullable=False),
        sa.Column("facility_name", sa.String(300)),
        sa.Column("provider_state", sa.String(2)),
        sa.Column("provider_state_fips", sa.String(2)),
        sa.Column("total_stays", sa.Integer),
        sa.Column("total_snf_charge", sa.Numeric(14, 2)),
        sa.Column("total_snf_medicare_payment", sa.Numeric(14, 2)),
        sa.Column("total_snf_covered_days", sa.Integer),
        sa.Column("avg_length_of_stay", sa.Numeric(8, 2)),
        sa.Column("data_year", sa.Integer, nullable=False),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="staging",
    )
    op.create_index("idx_stg_snf_ccn_year", "stg_cms__snf_utilization", ["ccn", "data_year"], schema="staging")

    # HHA utilization
    op.create_table(
        "stg_cms__hha_utilization",
        sa.Column("ccn", sa.String(6), nullable=False),
        sa.Column("facility_name", sa.String(300)),
        sa.Column("provider_state", sa.String(2)),
        sa.Column("provider_state_fips", sa.String(2)),
        sa.Column("total_episodes", sa.Integer),
        sa.Column("total_hha_charge", sa.Numeric(14, 2)),
        sa.Column("total_hha_medicare_payment", sa.Numeric(14, 2)),
        sa.Column("total_hha_visits", sa.Integer),
        sa.Column("avg_visits_per_episode", sa.Numeric(8, 2)),
        sa.Column("data_year", sa.Integer, nullable=False),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="staging",
    )
    op.create_index("idx_stg_hha_ccn_year", "stg_cms__hha_utilization", ["ccn", "data_year"], schema="staging")

    # Hospice utilization
    op.create_table(
        "stg_cms__hospice_utilization",
        sa.Column("ccn", sa.String(6), nullable=False),
        sa.Column("facility_name", sa.String(300)),
        sa.Column("provider_state", sa.String(2)),
        sa.Column("provider_state_fips", sa.String(2)),
        sa.Column("total_beneficiaries", sa.Integer),
        sa.Column("total_hospice_charge", sa.Numeric(14, 2)),
        sa.Column("total_hospice_medicare_payment", sa.Numeric(14, 2)),
        sa.Column("total_hospice_days", sa.Integer),
        sa.Column("avg_length_of_stay", sa.Numeric(8, 2)),
        sa.Column("data_year", sa.Integer, nullable=False),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="staging",
    )
    op.create_index("idx_stg_hospice_ccn_year", "stg_cms__hospice_utilization", ["ccn", "data_year"], schema="staging")

    # SDUD — partitioned by data_year (quarterly, 5M rows/quarter)
    op.execute("""
        CREATE TABLE staging.stg_cms__sdud (
            state VARCHAR(2) NOT NULL,
            state_fips VARCHAR(2),
            ndc VARCHAR(11) NOT NULL,
            labeler_code VARCHAR(10),
            product_code VARCHAR(10),
            package_size VARCHAR(10),
            year INTEGER NOT NULL,
            quarter INTEGER NOT NULL,
            suppression_flag VARCHAR(5),
            utilization_type VARCHAR(5),
            number_of_prescriptions INTEGER,
            total_amount_reimbursed NUMERIC(14, 2),
            medicaid_amount_reimbursed NUMERIC(14, 2),
            non_medicaid_amount_reimbursed NUMERIC(14, 2),
            units_reimbursed NUMERIC(14, 2),
            data_year INTEGER NOT NULL,
            _loaded_at TIMESTAMP,
            _source VARCHAR(50)
        ) PARTITION BY RANGE (data_year)
    """)
    for year in range(2019, 2025):
        op.execute(f"""
            CREATE TABLE staging.stg_cms__sdud_y{year}
            PARTITION OF staging.stg_cms__sdud
            FOR VALUES FROM ({year}) TO ({year + 1})
        """)
    op.create_index("idx_stg_sdud_ndc", "stg_cms__sdud", ["ndc"], schema="staging")
    op.create_index("idx_stg_sdud_state_year", "stg_cms__sdud", ["state", "data_year"], schema="staging")

    # Five-Star quality ratings
    op.create_table(
        "stg_cms__five_star",
        sa.Column("ccn", sa.String(6), nullable=False),
        sa.Column("facility_name", sa.String(300)),
        sa.Column("provider_state", sa.String(2)),
        sa.Column("overall_rating", sa.Integer),
        sa.Column("health_inspection_rating", sa.Integer),
        sa.Column("quality_rating", sa.Integer),
        sa.Column("staffing_rating", sa.Integer),
        sa.Column("rn_staffing_rating", sa.Integer),
        sa.Column("abuse_icon", sa.String(20)),
        sa.Column("total_weighted_health_survey_score", sa.Numeric(10, 2)),
        sa.Column("total_number_of_penalties", sa.Integer),
        sa.Column("total_fine_amount", sa.Numeric(12, 2)),
        sa.Column("snapshot_date", sa.Date),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="staging",
    )
    op.create_index("idx_stg_five_star_ccn", "stg_cms__five_star", ["ccn"], schema="staging")

    # PBJ staffing
    op.execute("""
        CREATE TABLE staging.stg_cms__pbj_staffing (
            ccn VARCHAR(6) NOT NULL,
            work_date DATE NOT NULL,
            cna_hours NUMERIC(10, 2),
            lpn_hours NUMERIC(10, 2),
            rn_hours NUMERIC(10, 2),
            total_nurse_hours NUMERIC(10, 2),
            physical_therapist_hours NUMERIC(10, 2),
            data_year INTEGER NOT NULL,
            _loaded_at TIMESTAMP,
            _source VARCHAR(50)
        ) PARTITION BY RANGE (data_year)
    """)
    for year in range(2019, 2025):
        op.execute(f"""
            CREATE TABLE staging.stg_cms__pbj_staffing_y{year}
            PARTITION OF staging.stg_cms__pbj_staffing
            FOR VALUES FROM ({year}) TO ({year + 1})
        """)
    op.create_index("idx_stg_pbj_ccn_date", "stg_cms__pbj_staffing", ["ccn", "work_date"], schema="staging")

    # CAHPS patient experience
    op.create_table(
        "stg_cms__cahps",
        sa.Column("ccn", sa.String(6), nullable=False),
        sa.Column("facility_name", sa.String(300)),
        sa.Column("measure_id", sa.String(30), nullable=False),
        sa.Column("measure_name", sa.Text),
        sa.Column("score", sa.Numeric(8, 2)),
        sa.Column("sample_size", sa.Integer),
        sa.Column("footnote", sa.Text),
        sa.Column("start_date", sa.Date),
        sa.Column("end_date", sa.Date),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="staging",
    )
    op.create_index("idx_stg_cahps_ccn", "stg_cms__cahps", ["ccn", "measure_id"], schema="staging")

    # Dialysis quality
    op.create_table(
        "stg_cms__dialysis",
        sa.Column("ccn", sa.String(6), nullable=False),
        sa.Column("facility_name", sa.String(300)),
        sa.Column("provider_state", sa.String(2)),
        sa.Column("measure_id", sa.String(30), nullable=False),
        sa.Column("measure_name", sa.Text),
        sa.Column("score", sa.Numeric(8, 2)),
        sa.Column("national_average", sa.Numeric(8, 2)),
        sa.Column("patient_count", sa.Integer),
        sa.Column("star_rating", sa.Integer),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="staging",
    )
    op.create_index("idx_stg_dialysis_ccn", "stg_cms__dialysis", ["ccn", "measure_id"], schema="staging")

    # Hospital readmissions
    op.create_table(
        "stg_cms__readmissions",
        sa.Column("ccn", sa.String(6), nullable=False),
        sa.Column("facility_name", sa.String(300)),
        sa.Column("provider_state", sa.String(2)),
        sa.Column("measure_id", sa.String(30), nullable=False),
        sa.Column("measure_name", sa.Text),
        sa.Column("denominator", sa.Integer),
        sa.Column("score", sa.Numeric(8, 4)),
        sa.Column("lower_estimate", sa.Numeric(8, 4)),
        sa.Column("upper_estimate", sa.Numeric(8, 4)),
        sa.Column("compared_to_national", sa.String(50)),
        sa.Column("data_year", sa.Integer),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="staging",
    )
    op.create_index("idx_stg_readmit_ccn", "stg_cms__readmissions", ["ccn", "measure_id"], schema="staging")

    # Hospital charges
    op.create_table(
        "stg_cms__charges",
        sa.Column("ccn", sa.String(6), nullable=False),
        sa.Column("facility_name", sa.String(300)),
        sa.Column("provider_state", sa.String(2)),
        sa.Column("provider_state_fips", sa.String(2)),
        sa.Column("drg_code", sa.String(5), nullable=False),
        sa.Column("drg_description", sa.Text),
        sa.Column("total_discharges", sa.Integer),
        sa.Column("avg_covered_charges", sa.Numeric(14, 2)),
        sa.Column("avg_total_payments", sa.Numeric(14, 2)),
        sa.Column("avg_medicare_payments", sa.Numeric(14, 2)),
        sa.Column("total_covered_charges", sa.Numeric(14, 2)),
        sa.Column("total_payments", sa.Numeric(14, 2)),
        sa.Column("total_medicare_payments", sa.Numeric(14, 2)),
        sa.Column("data_year", sa.Integer, nullable=False),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="staging",
    )
    op.create_index("idx_stg_charges_ccn_drg", "stg_cms__charges", ["ccn", "drg_code", "data_year"], schema="staging")

    # DME supplier utilization
    op.create_table(
        "stg_cms__dme",
        sa.Column("referring_npi", sa.String(10)),
        sa.Column("supplier_npi", sa.String(10), nullable=False),
        sa.Column("supplier_name", sa.String(300)),
        sa.Column("supplier_state", sa.String(2)),
        sa.Column("hcpcs_code", sa.String(10), nullable=False),
        sa.Column("hcpcs_description", sa.Text),
        sa.Column("number_of_services", sa.Numeric(14, 2)),
        sa.Column("number_of_beneficiaries", sa.Integer),
        sa.Column("avg_submitted_charge", sa.Numeric(14, 2)),
        sa.Column("avg_medicare_allowed", sa.Numeric(14, 2)),
        sa.Column("avg_medicare_payment", sa.Numeric(14, 2)),
        sa.Column("data_year", sa.Integer, nullable=False),
        sa.Column("_loaded_at", sa.DateTime),
        sa.Column("_source", sa.String(50)),
        schema="staging",
    )
    op.create_index("idx_stg_dme_supplier", "stg_cms__dme", ["supplier_npi", "data_year"], schema="staging")

    # MA enrollment
    op.execute("""
        CREATE TABLE staging.stg_cms__ma_enrollment (
            contract_id VARCHAR(10) NOT NULL,
            plan_id VARCHAR(10),
            county_fips VARCHAR(5) NOT NULL,
            state_fips VARCHAR(2),
            state VARCHAR(2),
            year_month VARCHAR(7) NOT NULL,
            enrollment_count INTEGER,
            eligible_count INTEGER,
            penetration_rate NUMERIC(8, 4),
            data_year INTEGER NOT NULL,
            _loaded_at TIMESTAMP,
            _source VARCHAR(50)
        ) PARTITION BY RANGE (data_year)
    """)
    for year in range(2019, 2025):
        op.execute(f"""
            CREATE TABLE staging.stg_cms__ma_enrollment_y{year}
            PARTITION OF staging.stg_cms__ma_enrollment
            FOR VALUES FROM ({year}) TO ({year + 1})
        """)
    op.create_index(
        "idx_stg_ma_enroll_county", "stg_cms__ma_enrollment", ["county_fips", "data_year"], schema="staging"
    )

    # Cost reports — SNF, HHA, Hospice (same HCRIS structure as hospital)
    for facility_type in ("snf", "hha", "hospice"):
        table_name = f"stg_cms__cost_reports_{facility_type}"
        op.create_table(
            table_name,
            sa.Column("rpt_rec_num", sa.BigInteger, nullable=False),
            sa.Column("ccn", sa.String(6), nullable=False),
            sa.Column("report_status_code", sa.String(5)),
            sa.Column("fiscal_year_begin", sa.Date),
            sa.Column("fiscal_year_end", sa.Date),
            sa.Column("total_patient_revenue", sa.Numeric(16, 2)),
            sa.Column("total_operating_expenses", sa.Numeric(16, 2)),
            sa.Column("net_income", sa.Numeric(16, 2)),
            sa.Column("total_beds_available", sa.Integer),
            sa.Column("total_patient_days", sa.Integer),
            sa.Column("total_discharges", sa.Integer),
            sa.Column("operating_margin", sa.Numeric(8, 4)),
            sa.Column("cost_to_charge_ratio", sa.Numeric(8, 4)),
            sa.Column("data_year", sa.Integer, nullable=False),
            sa.Column("_loaded_at", sa.DateTime),
            sa.Column("_source", sa.String(50)),
            schema="staging",
        )
        op.create_index(
            f"idx_stg_cr_{facility_type}_ccn",
            table_name,
            ["ccn", "data_year"],
            schema="staging",
        )


def downgrade() -> None:
    # Staging tables
    for table in (
        "stg_cms__ma_enrollment",
        "stg_cms__dme",
        "stg_cms__charges",
        "stg_cms__readmissions",
        "stg_cms__dialysis",
        "stg_cms__cahps",
        "stg_cms__pbj_staffing",
        "stg_cms__five_star",
        "stg_cms__sdud",
        "stg_cms__hospice_utilization",
        "stg_cms__hha_utilization",
        "stg_cms__snf_utilization",
        "stg_cms__inpatient",
        "stg_cms__cost_reports_snf",
        "stg_cms__cost_reports_hha",
        "stg_cms__cost_reports_hospice",
    ):
        op.execute(f"DROP TABLE IF EXISTS staging.{table} CASCADE")

    # Reference tables
    for table in (
        "ref_ma_benchmarks",
        "ref_asp_pricing",
        "ref_snf_pps",
        "ref_dmepos_fees",
        "ref_clfs",
        "ref_ndc_rxcui",
        "ref_rxnorm",
        "ref_hospital_general",
        "ref_ordering_referring",
        "ref_pecos_enrollment",
        "ref_census_population",
        "ref_hrr_hsa",
        "ref_apc",
    ):
        op.execute(f"DROP TABLE IF EXISTS reference.{table} CASCADE")
