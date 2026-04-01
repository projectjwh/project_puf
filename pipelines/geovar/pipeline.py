"""Medicare Geographic Variation pipeline.

Source: CMS Medicare Geographic Variation (~3.3K rows/year)
Outputs:
  - data/processed/geovar/{data_year}/geographic_variation.parquet
  - staging.stg_cms__geographic_variation (PostgreSQL)

Small reference-like dataset providing per-capita spending and utilization
metrics at state, county, and national levels. Key for geographic benchmarking.
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import (
    add_data_year,
    normalize_fips_county,
    normalize_fips_state,
)
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
    check_value_set,
)

log = get_logger(source="geovar")

# CMS column names → canonical names
COLUMN_MAPPING = {
    # Geography
    "Bene_Geo_Lvl": "bene_geo_lvl",
    "Bene_Geo_Desc": "bene_geo_desc",
    "Bene_Geo_Cd": "bene_geo_cd",
    # Beneficiary counts
    "Tot_Benes": "total_beneficiaries",
    "FFS_Benes": "total_beneficiaries_ffs",
    "MA_Benes": "total_beneficiaries_ma",
    "MA_Prtcptn_Rate": "ma_participation_rate",
    # Spending
    "Tot_Actual_Csts": "total_actual_costs",
    "Actual_Per_Cpta_Csts": "actual_per_capita_costs",
    "Stdzd_Per_Cpta_Csts": "standardized_per_capita_costs",
    # Service categories per capita
    "IP_Per_Cpta_Csts": "ip_per_capita_costs",
    "PAC_Per_Cpta_Csts": "op_per_capita_costs",
    "OP_Per_Cpta_Csts": "op_per_capita_costs",
    "SNF_Per_Cpta_Csts": "snf_per_capita_costs",
    "HHA_Per_Cpta_Csts": "hha_per_capita_costs",
    "Hospice_Per_Cpta_Csts": "hospice_per_capita_costs",
    "PrtB_Per_Cpta_Csts": "partb_per_capita_costs",
    "PrtD_Per_Cpta_Csts": "partd_per_capita_costs",
    "DME_Per_Cpta_Csts": "dme_per_capita_costs",
    # Utilization
    "IP_Cvrd_Stays_Per_1000": "ip_covered_stays_per_1000",
    "OP_Visits_Per_1000": "op_visits_per_1000",
    "ER_Visits_Per_1000": "er_visits_per_1000",
    "Readmsn_Rate": "readmission_rate",
    "ER_Visits_Rate": "ed_visit_rate",
}

STAGING_COLUMNS = [
    "bene_geo_lvl", "bene_geo_desc", "bene_geo_cd",
    "state_fips", "county_fips",
    "total_beneficiaries", "total_beneficiaries_ffs", "total_beneficiaries_ma",
    "ma_participation_rate",
    "total_actual_costs", "actual_per_capita_costs", "standardized_per_capita_costs",
    "ip_per_capita_costs", "op_per_capita_costs", "snf_per_capita_costs",
    "hha_per_capita_costs", "hospice_per_capita_costs",
    "partb_per_capita_costs", "partd_per_capita_costs", "dme_per_capita_costs",
    "ip_covered_stays_per_1000", "op_visits_per_1000", "er_visits_per_1000",
    "readmission_rate", "ed_visit_rate",
    "data_year",
]


def validate_geovar(df: pd.DataFrame) -> ValidationReport:
    """GeoVar-specific validation."""
    report = ValidationReport(source="geovar")
    check_required_columns(df, ["bene_geo_lvl"], report)
    check_column_not_null(df, "bene_geo_lvl", report, severity="BLOCK")
    if "bene_geo_lvl" in df.columns:
        check_value_set(
            df, "bene_geo_lvl",
            {"State", "County", "National", "STATE", "COUNTY", "NATIONAL"},
            report, severity="WARN",
        )
    check_row_count(df, min_rows=3_000, max_rows=5_000, report=report, severity="WARN")
    return report


def transform_geovar(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    """Apply GeoVar-specific transforms."""
    # Standardize geography level
    if "bene_geo_lvl" in df.columns:
        df["bene_geo_lvl"] = df["bene_geo_lvl"].str.strip().str.title()

    # Derive state_fips and county_fips from geo code
    if "bene_geo_cd" in df.columns:
        df["bene_geo_cd"] = df["bene_geo_cd"].astype(str).str.strip()

        # State-level rows: geo_cd is 2-digit state FIPS
        state_mask = df["bene_geo_lvl"] == "State"
        df.loc[state_mask, "state_fips"] = normalize_fips_state(df.loc[state_mask, "bene_geo_cd"])

        # County-level rows: geo_cd is 5-digit county FIPS
        county_mask = df["bene_geo_lvl"] == "County"
        df.loc[county_mask, "county_fips"] = normalize_fips_county(df.loc[county_mask, "bene_geo_cd"])
        df.loc[county_mask, "state_fips"] = df.loc[county_mask, "county_fips"].str[:2]

    # Cast numeric columns
    numeric_cols = [
        "total_beneficiaries", "total_beneficiaries_ffs", "total_beneficiaries_ma",
        "ma_participation_rate",
        "total_actual_costs", "actual_per_capita_costs", "standardized_per_capita_costs",
        "ip_per_capita_costs", "op_per_capita_costs", "snf_per_capita_costs",
        "hha_per_capita_costs", "hospice_per_capita_costs",
        "partb_per_capita_costs", "partd_per_capita_costs", "dme_per_capita_costs",
        "ip_covered_stays_per_1000", "op_visits_per_1000", "er_visits_per_1000",
        "readmission_rate", "ed_visit_rate",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Integer beneficiary counts
    for col in ("total_beneficiaries", "total_beneficiaries_ffs", "total_beneficiaries_ma"):
        if col in df.columns:
            df[col] = df[col].astype("Int64")

    # Round rate columns
    for col in ("ma_participation_rate", "readmission_rate", "ed_visit_rate"):
        if col in df.columns:
            df[col] = df[col].round(4)

    # Round per-capita costs
    for col in df.columns:
        if "per_capita" in col or "per_1000" in col:
            df[col] = df[col].round(2)

    df = add_data_year(df, data_year)
    return df


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    data_year: int | None = None,
) -> dict[str, int]:
    """Execute the Geographic Variation pipeline."""
    run_date = run_date or date.today()
    data_year = data_year or run_date.year - 2
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("geovar_start", run_date=str(run_date), data_year=data_year)

    # Acquire
    if source_path:
        csv_path = source_path
    else:
        source_def = get_source("geovar")
        landing = resolve_landing_path("geovar", run_date, data_year)
        csv_path = download_file(source_def.url, landing)

    log.info("reading_csv", path=str(csv_path))

    # Read
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})
    log.info("csv_read", rows=len(df))

    # Validate
    report = validate_geovar(df)
    report.raise_if_blocked()

    # Transform
    df = transform_geovar(df, data_year)
    results["geovar_rows"] = len(df)

    # Write Parquet
    parquet_path = (
        PROJECT_ROOT / settings.storage.processed_base
        / "geovar" / str(data_year) / "geographic_variation.parquet"
    )
    write_parquet(df, parquet_path)
    results["geovar_parquet"] = len(df)

    # Load to staging
    out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(
        df[out_cols], "stg_cms__geographic_variation", "staging", if_exists="append",
    )
    results["stg_geovar"] = rows

    log.info("geovar_complete", **results)
    return results
