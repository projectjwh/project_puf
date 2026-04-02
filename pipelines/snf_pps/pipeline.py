"""SNF Prospective Payment System (PPS) pipeline.

Source: CMS SNF PPS rates (~1K rows/year)
Outputs:
  - data/processed/snf_pps/snf_pps.parquet
  - reference.ref_snf_pps (PostgreSQL)
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

log = get_logger(source="snf_pps")

COLUMN_MAPPING = {
    "PDPM Group": "pdpm_group",
    "PDPM Classification": "pdpm_group",
    "Component": "component",
    "Rate": "rate",
    "Case Mix Index": "case_mix_index",
    "CMI": "case_mix_index",
}

OUTPUT_COLUMNS = [
    "pdpm_group",
    "fiscal_year",
    "component",
    "rate",
    "case_mix_index",
]


def validate_snf_pps(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="snf_pps")
    check_required_columns(df, ["pdpm_group"], report)
    check_column_not_null(df, "pdpm_group", report, severity="BLOCK")
    check_row_count(df, min_rows=50, max_rows=5_000, report=report, severity="WARN")
    return report


def transform_snf_pps(df: pd.DataFrame, fiscal_year: int) -> pd.DataFrame:
    clean_string_columns(df, ["pdpm_group", "component"])

    for col in ("rate", "case_mix_index"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"[$,]", "", regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["fiscal_year"] = fiscal_year
    df = add_snapshot_metadata(df, "snf_pps")
    return df


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    fiscal_year: int | None = None,
) -> dict[str, int]:
    run_date = run_date or date.today()
    fiscal_year = fiscal_year or run_date.year
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("snf_pps_start", run_date=str(run_date), fiscal_year=fiscal_year)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("snf_pps")
        landing = resolve_landing_path("snf_pps", run_date)
        data_file = download_file(source_def.url, landing)

    if str(data_file).endswith((".xlsx", ".xls")):
        df = pd.read_excel(data_file, dtype=str)
    else:
        df = pd.read_csv(data_file, dtype=str, low_memory=False)

    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_snf_pps(df)
    report.raise_if_blocked()
    df = transform_snf_pps(df, fiscal_year)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "snf_pps" / "snf_pps.parquet"
    write_parquet(df, parquet_path)
    results["snf_pps_parquet"] = len(df)

    out_cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "ref_snf_pps", "reference", if_exists="replace")
    results["ref_snf_pps"] = rows

    log.info("snf_pps_complete", **results)
    return results
