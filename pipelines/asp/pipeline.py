"""Average Sales Price (ASP) Drug Pricing pipeline.

Source: CMS Medicare Part B Drug ASP (~800 rows/quarter)
Outputs:
  - data/processed/asp/asp_pricing.parquet
  - reference.ref_asp_pricing (PostgreSQL)
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

log = get_logger(source="asp")

COLUMN_MAPPING = {
    "HCPCS Code": "hcpcs_code",
    "HCPCS": "hcpcs_code",
    "Short Description": "short_description",
    "Payment Limit": "payment_limit",
    "Dosage Form": "dosage_form",
}

OUTPUT_COLUMNS = [
    "hcpcs_code",
    "short_description",
    "payment_limit",
    "dosage_form",
    "quarter",
    "year",
]


def validate_asp(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="asp")
    check_required_columns(df, ["hcpcs_code"], report)
    check_column_not_null(df, "hcpcs_code", report, severity="BLOCK")
    check_row_count(df, min_rows=100, max_rows=5_000, report=report, severity="WARN")
    return report


def transform_asp(df: pd.DataFrame, quarter: int, year: int) -> pd.DataFrame:
    df["hcpcs_code"] = df["hcpcs_code"].astype(str).str.strip().str.upper()
    clean_string_columns(df, ["short_description", "dosage_form"])

    if "payment_limit" in df.columns:
        df["payment_limit"] = df["payment_limit"].astype(str).str.replace(r"[$,]", "", regex=True)
        df["payment_limit"] = pd.to_numeric(df["payment_limit"], errors="coerce")

    df["quarter"] = quarter
    df["year"] = year
    df = add_snapshot_metadata(df, "asp")
    return df


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    quarter: int | None = None,
    year: int | None = None,
) -> dict[str, int]:
    run_date = run_date or date.today()
    quarter = quarter or ((run_date.month - 1) // 3 + 1)
    year = year or run_date.year
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("asp_start", run_date=str(run_date), quarter=quarter, year=year)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("asp")
        landing = resolve_landing_path("asp", run_date)
        data_file = download_file(source_def.url, landing)

    if str(data_file).endswith((".xlsx", ".xls")):
        df = pd.read_excel(data_file, dtype=str)
    else:
        df = pd.read_csv(data_file, dtype=str, low_memory=False)

    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_asp(df)
    report.raise_if_blocked()
    df = transform_asp(df, quarter, year)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "asp" / "asp_pricing.parquet"
    write_parquet(df, parquet_path)
    results["asp_parquet"] = len(df)

    out_cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "ref_asp_pricing", "reference", if_exists="append")
    results["ref_asp_pricing"] = rows

    log.info("asp_complete", **results)
    return results
