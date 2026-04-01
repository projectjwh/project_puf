"""Ordering and Referring Physicians pipeline.

Source: CMS Order and Referring (~1.5M rows)
Outputs:
  - data/processed/ordering_referring/ordering_referring.parquet
  - reference.ref_ordering_referring (PostgreSQL)

Identifies physicians eligible to order/refer Medicare services.
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import add_snapshot_metadata, clean_string_columns, normalize_npi
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="ordering_referring")

COLUMN_MAPPING = {
    "NPI": "npi",
    "LAST NAME": "last_name",
    "FIRST NAME": "first_name",
    "STATE": "state",
    "SPECIALTY": "specialty",
    "ELIGIBLE": "eligible",
    "Lst_Nm": "last_name",
    "Frst_Nm": "first_name",
    "State_Cd": "state",
    "Spclty_Desc": "specialty",
}

OUTPUT_COLUMNS = ["npi", "last_name", "first_name", "state", "specialty", "eligible"]


def validate_ordering_referring(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="ordering_referring")
    check_required_columns(df, ["npi"], report)
    check_column_not_null(df, "npi", report, severity="BLOCK")
    check_row_count(df, min_rows=500_000, max_rows=3_000_000, report=report, severity="WARN")
    return report


def transform_ordering_referring(df: pd.DataFrame) -> pd.DataFrame:
    df["npi"] = normalize_npi(df["npi"])
    clean_string_columns(df, ["last_name", "first_name", "specialty"])

    if "state" in df.columns:
        df["state"] = df["state"].astype(str).str.strip().str.upper()

    # Eligible flag
    if "eligible" in df.columns:
        df["eligible"] = df["eligible"].astype(str).str.strip().str.upper().isin(["Y", "TRUE", "1"])
    else:
        df["eligible"] = True  # If present in file, they are eligible

    df = add_snapshot_metadata(df, "ordering_referring")
    return df


def run(source_path: Path | None = None, run_date: date | None = None) -> dict[str, int]:
    run_date = run_date or date.today()
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("ordering_referring_start", run_date=str(run_date))

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("ordering_referring")
        landing = resolve_landing_path("ordering_referring", run_date)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_ordering_referring(df)
    report.raise_if_blocked()

    df = transform_ordering_referring(df)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "ordering_referring" / "ordering_referring.parquet"
    write_parquet(df, parquet_path)
    results["ordering_referring_parquet"] = len(df)

    out_cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "ref_ordering_referring", "reference", if_exists="replace")
    results["ref_ordering_referring"] = rows

    log.info("ordering_referring_complete", **results)
    return results
