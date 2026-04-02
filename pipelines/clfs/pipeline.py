"""Clinical Laboratory Fee Schedule (CLFS) pipeline.

Source: CMS Clinical Lab Fee Schedule (~3K rows/year)
Outputs:
  - data/processed/clfs/clfs.parquet
  - reference.ref_clfs (PostgreSQL)
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, extract_zip, resolve_landing_path
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

log = get_logger(source="clfs")

COLUMN_MAPPING = {
    "HCPCS": "hcpcs_code",
    "HCPCS Code": "hcpcs_code",
    "Short Description": "short_description",
    "SHORT DESCRIPTION": "short_description",
    "National Limit Amount": "national_limit_amount",
    "NLA": "national_limit_amount",
    "Floor": "floor_amount",
    "Personal Use Crosswalk": "personal_use_crosswalk",
}

OUTPUT_COLUMNS = [
    "hcpcs_code",
    "effective_year",
    "short_description",
    "national_limit_amount",
    "floor_amount",
    "personal_use_crosswalk",
]


def validate_clfs(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="clfs")
    check_required_columns(df, ["hcpcs_code"], report)
    check_column_not_null(df, "hcpcs_code", report, severity="BLOCK")
    check_row_count(df, min_rows=1_000, max_rows=10_000, report=report, severity="WARN")
    return report


def transform_clfs(df: pd.DataFrame, effective_year: int) -> pd.DataFrame:
    df["hcpcs_code"] = df["hcpcs_code"].astype(str).str.strip().str.upper()
    clean_string_columns(df, ["short_description"])

    for col in ("national_limit_amount", "floor_amount"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"[$,]", "", regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    df["effective_year"] = effective_year
    df = add_snapshot_metadata(df, "clfs")
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

    log.info("clfs_start", run_date=str(run_date), effective_year=effective_year)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("clfs")
        landing = resolve_landing_path("clfs", run_date)
        downloaded = download_file(source_def.url, landing)
        if downloaded.suffix == ".zip":
            extract_zip(downloaded, landing)
            csvs = list(landing.glob("*.csv"))
            data_file = csvs[0] if csvs else downloaded
        else:
            data_file = downloaded

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_clfs(df)
    report.raise_if_blocked()
    df = transform_clfs(df, effective_year)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "clfs" / "clfs.parquet"
    write_parquet(df, parquet_path)
    results["clfs_parquet"] = len(df)

    out_cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "ref_clfs", "reference", if_exists="replace")
    results["ref_clfs"] = rows

    log.info("clfs_complete", **results)
    return results
