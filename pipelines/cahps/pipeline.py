"""CAHPS Hospital Patient Experience pipeline.

Source: CMS Hospital Compare (~4.5K hospitals, measure-level grain)
Outputs:
  - data/processed/cahps/cahps.parquet
  - staging.stg_cms__cahps (PostgreSQL)
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

log = get_logger(source="cahps")

COLUMN_MAPPING = {
    "Facility ID": "ccn",
    "Provider ID": "ccn",
    "Facility Name": "facility_name",
    "Hospital Name": "facility_name",
    "HCAHPS Measure ID": "measure_id",
    "Measure ID": "measure_id",
    "HCAHPS Question": "measure_name",
    "Measure Name": "measure_name",
    "Patient Survey Star Rating": "score",
    "HCAHPS Answer Percent": "score",
    "Number of Completed Surveys": "sample_size",
    "Footnote": "footnote",
    "Start Date": "start_date",
    "End Date": "end_date",
}

STAGING_COLUMNS = [
    "ccn", "facility_name", "measure_id", "measure_name",
    "score", "sample_size", "footnote", "start_date", "end_date",
]


def validate_cahps(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="cahps")
    check_required_columns(df, ["ccn", "measure_id"], report)
    check_column_not_null(df, "ccn", report, severity="BLOCK")
    check_row_count(df, min_rows=1_000, max_rows=100_000, report=report, severity="WARN")
    return report


def transform_cahps(df: pd.DataFrame) -> pd.DataFrame:
    df["ccn"] = df["ccn"].astype(str).str.strip().str.zfill(6)
    clean_string_columns(df, ["facility_name", "measure_id"])

    if "score" in df.columns:
        df["score"] = df["score"].astype(str).str.replace("Not Available", "", regex=False)
        df["score"] = pd.to_numeric(df["score"], errors="coerce")

    if "sample_size" in df.columns:
        df["sample_size"] = pd.to_numeric(df["sample_size"], errors="coerce").astype("Int64")

    for col in ("start_date", "end_date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    df = add_snapshot_metadata(df, "cahps")
    return df


def run(source_path: Path | None = None, run_date: date | None = None) -> dict[str, int]:
    run_date = run_date or date.today()
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("cahps_start", run_date=str(run_date))

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("cahps")
        landing = resolve_landing_path("cahps", run_date)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_cahps(df)
    report.raise_if_blocked()
    df = transform_cahps(df)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "cahps" / "cahps.parquet"
    write_parquet(df, parquet_path)
    results["cahps_parquet"] = len(df)

    out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "stg_cms__cahps", "staging", if_exists="replace")
    results["stg_cahps"] = rows

    log.info("cahps_complete", **results)
    return results
