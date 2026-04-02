"""Medicare Advantage Enrollment by County pipeline.

Source: CMS MA State/County Penetration (~50K rows/month)
Outputs:
  - data/processed/ma_enrollment/{data_year}/ma_enrollment.parquet
  - staging.stg_cms__ma_enrollment (PostgreSQL, partitioned by data_year)
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import add_data_year, normalize_fips_county
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="ma_enrollment")

COLUMN_MAPPING = {
    "Contract Number": "contract_id",
    "Plan ID": "plan_id",
    "SSA State County Code": "county_ssa",
    "FIPS State County Code": "county_fips",
    "State": "state",
    "County": "county_name",
    "Enrollment": "enrollment_count",
    "Eligibles": "eligible_count",
    "Penetration": "penetration_rate",
    "Year-Month": "year_month",
}

STAGING_COLUMNS = [
    "contract_id",
    "plan_id",
    "county_fips",
    "state_fips",
    "state",
    "year_month",
    "enrollment_count",
    "eligible_count",
    "penetration_rate",
    "data_year",
]


def validate_ma_enrollment(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="ma_enrollment")
    check_required_columns(df, ["county_fips"], report)
    check_column_not_null(df, "county_fips", report, severity="BLOCK")
    check_row_count(df, min_rows=10_000, max_rows=200_000, report=report, severity="WARN")
    return report


def transform_ma_enrollment(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    if "county_fips" in df.columns:
        df["county_fips"] = normalize_fips_county(df["county_fips"])
        df["state_fips"] = df["county_fips"].str[:2]

    if "state" in df.columns:
        df["state"] = df["state"].astype(str).str.strip().str.upper()

    for col in ("enrollment_count", "eligible_count"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    if "penetration_rate" in df.columns:
        # May come as "45.2%" — strip % and convert
        df["penetration_rate"] = df["penetration_rate"].astype(str).str.replace("%", "", regex=False).str.strip()
        df["penetration_rate"] = pd.to_numeric(df["penetration_rate"], errors="coerce")
        # Convert to decimal if > 1 (i.e., 45.2 → 0.452)
        mask = df["penetration_rate"] > 1
        df.loc[mask, "penetration_rate"] = df.loc[mask, "penetration_rate"] / 100
        df["penetration_rate"] = df["penetration_rate"].round(4)

    df = add_data_year(df, data_year)
    return df


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    data_year: int | None = None,
) -> dict[str, int]:
    run_date = run_date or date.today()
    data_year = data_year or run_date.year
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("ma_enrollment_start", run_date=str(run_date), data_year=data_year)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("ma_enrollment")
        landing = resolve_landing_path("ma_enrollment", run_date, data_year)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_ma_enrollment(df)
    report.raise_if_blocked()
    df = transform_ma_enrollment(df, data_year)

    parquet_path = (
        PROJECT_ROOT / settings.storage.processed_base / "ma_enrollment" / str(data_year) / "ma_enrollment.parquet"
    )
    write_parquet(df, parquet_path)
    results["ma_enrollment_parquet"] = len(df)

    out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "stg_cms__ma_enrollment", "staging", if_exists="append")
    results["stg_ma_enrollment"] = rows

    log.info("ma_enrollment_complete", **results)
    return results
