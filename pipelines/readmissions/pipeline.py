"""Hospital Readmissions Reduction Program pipeline.

Source: CMS Hospital Compare (~3.5K hospitals, measure-level grain)
Outputs:
  - data/processed/readmissions/readmissions.parquet
  - staging.stg_cms__readmissions (PostgreSQL)
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import add_snapshot_metadata, clean_string_columns
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="readmissions")

COLUMN_MAPPING = {
    "Facility ID": "ccn",
    "Provider ID": "ccn",
    "Hospital Name": "facility_name",
    "Facility Name": "facility_name",
    "State": "provider_state",
    "Measure ID": "measure_id",
    "Measure Name": "measure_name",
    "Denominator": "denominator",
    "Score": "score",
    "Lower Estimate": "lower_estimate",
    "Upper Estimate": "upper_estimate",
    "Compared to National": "compared_to_national",
}

STAGING_COLUMNS = [
    "ccn",
    "facility_name",
    "provider_state",
    "measure_id",
    "measure_name",
    "denominator",
    "score",
    "lower_estimate",
    "upper_estimate",
    "compared_to_national",
    "data_year",
]


def validate_readmissions(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="readmissions")
    check_required_columns(df, ["ccn", "measure_id"], report)
    check_column_not_null(df, "ccn", report, severity="BLOCK")
    check_row_count(df, min_rows=1_000, max_rows=50_000, report=report, severity="WARN")
    return report


def transform_readmissions(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    df["ccn"] = df["ccn"].astype(str).str.strip().str.zfill(6)
    clean_string_columns(df, ["facility_name", "measure_id", "compared_to_national"])

    if "provider_state" in df.columns:
        df["provider_state"] = df["provider_state"].astype(str).str.strip().str.upper()

    if "denominator" in df.columns:
        df["denominator"] = pd.to_numeric(df["denominator"], errors="coerce").astype("Int64")

    for col in ("score", "lower_estimate", "upper_estimate"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace("Not Available", "", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["data_year"] = data_year
    df = add_snapshot_metadata(df, "readmissions")
    return df


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    data_year: int | None = None,
) -> dict[str, int]:
    run_date = run_date or date.today()
    data_year = data_year or run_date.year - 1
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("readmissions_start", run_date=str(run_date), data_year=data_year)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("readmissions")
        landing = resolve_landing_path("readmissions", run_date)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_readmissions(df)
    report.raise_if_blocked()
    df = transform_readmissions(df, data_year)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "readmissions" / "readmissions.parquet"
    write_parquet(df, parquet_path)
    results["readmissions_parquet"] = len(df)

    out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "stg_cms__readmissions", "staging", if_exists="replace")
    results["stg_readmissions"] = rows

    log.info("readmissions_complete", **results)
    return results
