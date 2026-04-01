"""Nursing Home Five-Star Quality Rating pipeline.

Source: CMS Provider Data (~15K facilities, monthly)
Outputs:
  - data/processed/five_star/five_star.parquet
  - staging.stg_cms__five_star (PostgreSQL)
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

log = get_logger(source="five_star")

COLUMN_MAPPING = {
    "Federal Provider Number": "ccn",
    "CMS Certification Number (CCN)": "ccn",
    "Provider Name": "facility_name",
    "Provider State": "provider_state",
    "Overall Rating": "overall_rating",
    "Health Inspection Rating": "health_inspection_rating",
    "Quality Measure Five-Star Rating": "quality_rating",
    "QM Rating": "quality_rating",
    "Staffing Rating": "staffing_rating",
    "RN Staffing Rating": "rn_staffing_rating",
    "Abuse Icon": "abuse_icon",
    "Total Weighted Health Survey Score": "total_weighted_health_survey_score",
    "Number of Facility Reported Incidents": "total_number_of_penalties",
    "Total Amount of Fines in Dollars": "total_fine_amount",
}

STAGING_COLUMNS = [
    "ccn", "facility_name", "provider_state",
    "overall_rating", "health_inspection_rating", "quality_rating",
    "staffing_rating", "rn_staffing_rating", "abuse_icon",
    "total_weighted_health_survey_score",
    "total_number_of_penalties", "total_fine_amount", "snapshot_date",
]


def validate_five_star(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="five_star")
    check_required_columns(df, ["ccn"], report)
    check_column_not_null(df, "ccn", report, severity="BLOCK")
    check_row_count(df, min_rows=10_000, max_rows=20_000, report=report, severity="WARN")
    return report


def transform_five_star(df: pd.DataFrame, snapshot_date: date) -> pd.DataFrame:
    df["ccn"] = df["ccn"].astype(str).str.strip().str.zfill(6)
    clean_string_columns(df, ["facility_name"])

    if "provider_state" in df.columns:
        df["provider_state"] = df["provider_state"].astype(str).str.strip().str.upper()

    for col in ("overall_rating", "health_inspection_rating", "quality_rating",
                "staffing_rating", "rn_staffing_rating", "total_number_of_penalties"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in ("total_weighted_health_survey_score", "total_fine_amount"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    df["snapshot_date"] = snapshot_date
    df = add_snapshot_metadata(df, "five_star")
    return df


def run(source_path: Path | None = None, run_date: date | None = None) -> dict[str, int]:
    run_date = run_date or date.today()
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("five_star_start", run_date=str(run_date))

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("five_star")
        landing = resolve_landing_path("five_star", run_date)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_five_star(df)
    report.raise_if_blocked()
    df = transform_five_star(df, run_date)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "five_star" / "five_star.parquet"
    write_parquet(df, parquet_path)
    results["five_star_parquet"] = len(df)

    out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "stg_cms__five_star", "staging", if_exists="replace")
    results["stg_five_star"] = rows

    log.info("five_star_complete", **results)
    return results
