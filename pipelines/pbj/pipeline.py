"""Payroll-Based Journal (PBJ) Staffing Data pipeline.

Source: CMS PBJ Daily Nurse Staffing (~5.5M rows/quarter)
Outputs:
  - data/processed/pbj/{data_year}/pbj_staffing.parquet
  - staging.stg_cms__pbj_staffing (PostgreSQL, partitioned by data_year)

Daily staffing hours by facility — aggregated to quarterly in intermediate layer.
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import add_data_year
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="pbj")

COLUMN_MAPPING = {
    "CMS Certification Number (CCN)": "ccn",
    "PROVNUM": "ccn",
    "Federal Provider Number": "ccn",
    "Work Date": "work_date",
    "WorkDate": "work_date",
    "Hrs_CNA": "cna_hours",
    "CNA Hours": "cna_hours",
    "Hrs_LPN": "lpn_hours",
    "LPN Hours": "lpn_hours",
    "Hrs_RN": "rn_hours",
    "RN Hours": "rn_hours",
    "Hrs_TOTAL": "total_nurse_hours",
    "Total Nurse Hours": "total_nurse_hours",
    "Hrs_PT": "physical_therapist_hours",
}

STAGING_COLUMNS = [
    "ccn", "work_date", "cna_hours", "lpn_hours", "rn_hours",
    "total_nurse_hours", "physical_therapist_hours", "data_year",
]


def validate_pbj(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="pbj")
    check_required_columns(df, ["ccn", "work_date"], report)
    check_column_not_null(df, "ccn", report, severity="BLOCK")
    check_row_count(df, min_rows=1_000_000, max_rows=10_000_000, report=report, severity="WARN")
    return report


def transform_pbj(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    df["ccn"] = df["ccn"].astype(str).str.strip().str.zfill(6)

    if "work_date" in df.columns:
        df["work_date"] = pd.to_datetime(df["work_date"], errors="coerce").dt.date

    for col in ("cna_hours", "lpn_hours", "rn_hours",
                "total_nurse_hours", "physical_therapist_hours"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    # Compute total if not present
    if "total_nurse_hours" not in df.columns:
        hours_cols = [c for c in ("cna_hours", "lpn_hours", "rn_hours") if c in df.columns]
        if hours_cols:
            df["total_nurse_hours"] = df[hours_cols].sum(axis=1)

    df = add_data_year(df, data_year)
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

    log.info("pbj_start", run_date=str(run_date), data_year=data_year)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("pbj")
        landing = resolve_landing_path("pbj", run_date, data_year)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_pbj(df)
    report.raise_if_blocked()
    df = transform_pbj(df, data_year)

    parquet_path = (
        PROJECT_ROOT / settings.storage.processed_base / "pbj" / str(data_year) / "pbj_staffing.parquet"
    )
    write_parquet(df, parquet_path)
    results["pbj_parquet"] = len(df)

    out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "stg_cms__pbj_staffing", "staging", if_exists="append")
    results["stg_pbj"] = rows

    log.info("pbj_complete", **results)
    return results
