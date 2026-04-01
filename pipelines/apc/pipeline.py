"""Ambulatory Payment Classification (APC) pipeline.

Source: CMS OPPS Addendum A/B (~5K rows)
Outputs:
  - data/processed/apc/apc_codes.parquet
  - reference.ref_apc (PostgreSQL)

Maps outpatient procedures to APC payment groups with relative weights and rates.
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

log = get_logger(source="apc")

COLUMN_MAPPING = {
    "APC": "apc_code",
    "APC Code": "apc_code",
    "Group Title": "apc_description",
    "APC Description": "apc_description",
    "Payment Rate": "payment_rate",
    "Relative Weight": "relative_weight",
    "Minimum Unadjusted Copayment": "minimum_unadjusted_copayment",
    "Status Indicator": "status_indicator",
    "SI": "status_indicator",
}

OUTPUT_COLUMNS = [
    "apc_code", "apc_description", "payment_rate", "relative_weight",
    "minimum_unadjusted_copayment", "status_indicator", "effective_year",
]


def validate_apc(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="apc")
    check_required_columns(df, ["apc_code"], report)
    check_column_not_null(df, "apc_code", report, severity="BLOCK")
    check_row_count(df, min_rows=100, max_rows=10_000, report=report, severity="WARN")
    return report


def transform_apc(df: pd.DataFrame, effective_year: int) -> pd.DataFrame:
    df["apc_code"] = df["apc_code"].astype(str).str.strip()
    clean_string_columns(df, ["apc_description", "status_indicator"])

    for col in ("payment_rate", "relative_weight", "minimum_unadjusted_copayment"):
        if col in df.columns:
            # Remove $ and commas
            df[col] = df[col].astype(str).str.replace(r"[$,]", "", regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["effective_year"] = effective_year
    df = add_snapshot_metadata(df, "apc")
    return df


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    effective_year: int | None = None,
) -> dict[str, int]:
    run_date = run_date or date.today()
    effective_year = effective_year or run_date.year
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("apc_start", run_date=str(run_date), effective_year=effective_year)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("apc")
        landing = resolve_landing_path("apc", run_date)
        data_file = download_file(source_def.url, landing)

    # APC files are often Excel
    if str(data_file).endswith((".xlsx", ".xls")):
        df = pd.read_excel(data_file, dtype=str)
    else:
        df = pd.read_csv(data_file, dtype=str, low_memory=False)

    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_apc(df)
    report.raise_if_blocked()

    df = transform_apc(df, effective_year)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "apc" / "apc_codes.parquet"
    write_parquet(df, parquet_path)
    results["apc_parquet"] = len(df)

    out_cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "ref_apc", "reference", if_exists="replace")
    results["ref_apc"] = rows

    log.info("apc_complete", **results)
    return results
