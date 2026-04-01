"""Dialysis Facility Quality pipeline.

Source: CMS Dialysis Facility Compare (~7.5K facilities, measure-level grain)
Outputs:
  - data/processed/dialysis/dialysis.parquet
  - staging.stg_cms__dialysis (PostgreSQL)
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

log = get_logger(source="dialysis")

COLUMN_MAPPING = {
    "CMS Certification Number (CCN)": "ccn",
    "Provider Number": "ccn",
    "Facility Name": "facility_name",
    "State": "provider_state",
    "Measure ID": "measure_id",
    "Measure Name": "measure_name",
    "Score": "score",
    "National Average Score": "national_average",
    "Patient Count": "patient_count",
    "# of patients included in the measure": "patient_count",
    "Star Rating": "star_rating",
    "Five Star": "star_rating",
}

STAGING_COLUMNS = [
    "ccn", "facility_name", "provider_state", "measure_id",
    "measure_name", "score", "national_average", "patient_count", "star_rating",
]


def validate_dialysis(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="dialysis")
    check_required_columns(df, ["ccn"], report)
    check_column_not_null(df, "ccn", report, severity="BLOCK")
    check_row_count(df, min_rows=1_000, max_rows=50_000, report=report, severity="WARN")
    return report


def transform_dialysis(df: pd.DataFrame) -> pd.DataFrame:
    df["ccn"] = df["ccn"].astype(str).str.strip().str.zfill(6)
    clean_string_columns(df, ["facility_name", "measure_id"])

    if "provider_state" in df.columns:
        df["provider_state"] = df["provider_state"].astype(str).str.strip().str.upper()

    for col in ("score", "national_average"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace("Not Available", "", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ("patient_count", "star_rating"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    df = add_snapshot_metadata(df, "dialysis")
    return df


def run(source_path: Path | None = None, run_date: date | None = None) -> dict[str, int]:
    run_date = run_date or date.today()
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("dialysis_start", run_date=str(run_date))

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("dialysis")
        landing = resolve_landing_path("dialysis", run_date)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_dialysis(df)
    report.raise_if_blocked()
    df = transform_dialysis(df)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "dialysis" / "dialysis.parquet"
    write_parquet(df, parquet_path)
    results["dialysis_parquet"] = len(df)

    out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "stg_cms__dialysis", "staging", if_exists="replace")
    results["stg_dialysis"] = rows

    log.info("dialysis_complete", **results)
    return results
