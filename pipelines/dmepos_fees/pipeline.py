"""DMEPOS Fee Schedule pipeline.

Source: CMS DMEPOS Fee Schedule (~10K rows, quarterly)
Outputs:
  - data/processed/dmepos_fees/dmepos_fees.parquet
  - reference.ref_dmepos_fees (PostgreSQL)
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, extract_zip, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import add_snapshot_metadata
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="dmepos_fees")

COLUMN_MAPPING = {
    "HCPCS": "hcpcs_code",
    "HCPCS Code": "hcpcs_code",
    "Modifier": "modifier",
    "MODIFIER": "modifier",
    "State": "state",
    "STATE": "state",
    "Fee Amount": "fee_amount",
    "FEE_AMOUNT": "fee_amount",
}

OUTPUT_COLUMNS = [
    "hcpcs_code",
    "modifier",
    "state",
    "fee_amount",
    "effective_quarter",
]


def validate_dmepos(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="dmepos_fees")
    check_required_columns(df, ["hcpcs_code"], report)
    check_column_not_null(df, "hcpcs_code", report, severity="BLOCK")
    check_row_count(df, min_rows=1_000, max_rows=50_000, report=report, severity="WARN")
    return report


def transform_dmepos(df: pd.DataFrame, effective_quarter: str) -> pd.DataFrame:
    df["hcpcs_code"] = df["hcpcs_code"].astype(str).str.strip().str.upper()

    if "modifier" in df.columns:
        df["modifier"] = df["modifier"].astype(str).str.strip()

    if "state" in df.columns:
        df["state"] = df["state"].astype(str).str.strip().str.upper()

    if "fee_amount" in df.columns:
        df["fee_amount"] = df["fee_amount"].astype(str).str.replace(r"[$,]", "", regex=True)
        df["fee_amount"] = pd.to_numeric(df["fee_amount"], errors="coerce").round(2)

    df["effective_quarter"] = effective_quarter
    df = add_snapshot_metadata(df, "dmepos_fees")
    return df


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    effective_quarter: str | None = None,
) -> dict[str, int]:
    run_date = run_date or date.today()
    quarter = (run_date.month - 1) // 3 + 1
    effective_quarter = effective_quarter or f"{run_date.year}Q{quarter}"
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("dmepos_start", run_date=str(run_date), effective_quarter=effective_quarter)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("dmepos_fees")
        landing = resolve_landing_path("dmepos_fees", run_date)
        downloaded = download_file(source_def.url, landing)
        if downloaded.suffix == ".zip":
            extract_zip(downloaded, landing)
            csvs = list(landing.glob("*.csv"))
            data_file = csvs[0] if csvs else downloaded
        else:
            data_file = downloaded

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_dmepos(df)
    report.raise_if_blocked()
    df = transform_dmepos(df, effective_quarter)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "dmepos_fees" / "dmepos_fees.parquet"
    write_parquet(df, parquet_path)
    results["dmepos_parquet"] = len(df)

    out_cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "ref_dmepos_fees", "reference", if_exists="replace")
    results["ref_dmepos_fees"] = rows

    log.info("dmepos_complete", **results)
    return results
