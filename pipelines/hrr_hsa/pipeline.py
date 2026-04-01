"""Hospital Referral Region (HRR) and Health Service Area (HSA) pipeline.

Source: Dartmouth Atlas ZIP crosswalk (~6.5K rows, static)
Outputs:
  - data/processed/hrr_hsa/hrr_hsa.parquet
  - reference.ref_hrr_hsa (PostgreSQL)

Maps ZIP codes to HRRs and HSAs for geographic analysis of hospital markets.
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import add_snapshot_metadata, extract_zip5
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="hrr_hsa")

COLUMN_MAPPING = {
    "ZIPCODE": "zip_code",
    "zipcode": "zip_code",
    "Zip Code": "zip_code",
    "HRRNUMBER": "hrr_number",
    "hrr_num": "hrr_number",
    "HRR": "hrr_number",
    "HRRCITY": "hrr_city",
    "hrr_city": "hrr_city",
    "HRRSTATE": "hrr_state",
    "hrr_state": "hrr_state",
    "HSANUMBER": "hsa_number",
    "hsa_num": "hsa_number",
    "HSA": "hsa_number",
    "HSACITY": "hsa_city",
    "hsa_city": "hsa_city",
    "HSASTATE": "hsa_state",
    "hsa_state": "hsa_state",
}

OUTPUT_COLUMNS = [
    "zip_code", "hrr_number", "hrr_city", "hrr_state",
    "hsa_number", "hsa_city", "hsa_state",
]


def validate_hrr_hsa(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="hrr_hsa")
    check_required_columns(df, ["zip_code"], report)
    check_column_not_null(df, "zip_code", report, severity="BLOCK")
    check_row_count(df, min_rows=3_000, max_rows=50_000, report=report, severity="WARN")
    return report


def transform_hrr_hsa(df: pd.DataFrame) -> pd.DataFrame:
    df["zip_code"] = extract_zip5(df["zip_code"])

    for col in ("hrr_number", "hsa_number"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in ("hrr_city", "hsa_city"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    for col in ("hrr_state", "hsa_state"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    df = add_snapshot_metadata(df, "hrr_hsa")
    return df


def run(source_path: Path | None = None, run_date: date | None = None) -> dict[str, int]:
    run_date = run_date or date.today()
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("hrr_hsa_start", run_date=str(run_date))

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("hrr_hsa")
        landing = resolve_landing_path("hrr_hsa", run_date)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_hrr_hsa(df)
    report.raise_if_blocked()

    df = transform_hrr_hsa(df)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "hrr_hsa" / "hrr_hsa.parquet"
    write_parquet(df, parquet_path)
    results["hrr_hsa_parquet"] = len(df)

    out_cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "ref_hrr_hsa", "reference", if_exists="replace")
    results["ref_hrr_hsa"] = rows

    log.info("hrr_hsa_complete", **results)
    return results
