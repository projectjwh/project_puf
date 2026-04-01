"""PECOS Provider Enrollment pipeline.

Source: CMS Medicare Fee-for-Service Public Provider Enrollment (~2M rows)
Outputs:
  - data/processed/pecos/pecos_enrollment.parquet
  - reference.ref_pecos_enrollment (PostgreSQL)

Enriches provider identity with enrollment type, assignment status,
and organizational affiliations from PECOS.
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import (
    add_snapshot_metadata,
    clean_string_columns,
    normalize_npi,
)
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="pecos")

COLUMN_MAPPING = {
    "NPI": "npi",
    "PAC ID": "pac_id",
    "ENROLLMENT ID": "enrollment_id",
    "ENROLLMENT TYPE": "enrollment_type",
    "ENROLLMENT STATE": "enrollment_state",
    "PROVIDER TYPE": "provider_type",
    "SPECIALTY": "specialty",
    "ORGANIZATION NAME": "organization_name",
    "ACCEPTS MEDICARE APPROVED AMOUNT": "accepts_assignment",
    "PARTICIPATING": "participating",
    "ENROLLMENT DATE": "enrollment_date",
    # Alternative CMS field names
    "Enrlmt_ID": "enrollment_id",
    "Enrlmt_State_Cd": "enrollment_state",
    "Prvdr_Type": "provider_type",
    "Spclty": "specialty",
    "Org_Name": "organization_name",
    "Assgn_Ind": "accepts_assignment",
    "Prtcptg_Ind": "participating",
}

OUTPUT_COLUMNS = [
    "npi", "pac_id", "enrollment_id", "enrollment_type",
    "enrollment_state", "provider_type", "specialty",
    "organization_name", "accepts_assignment", "participating",
    "enrollment_date",
]


def validate_pecos(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="pecos")
    check_required_columns(df, ["npi"], report)
    check_column_not_null(df, "npi", report, severity="BLOCK")
    check_row_count(df, min_rows=1_000_000, max_rows=4_000_000, report=report, severity="WARN")
    return report


def transform_pecos(df: pd.DataFrame) -> pd.DataFrame:
    df["npi"] = normalize_npi(df["npi"])
    clean_string_columns(df, ["provider_type", "specialty", "organization_name"])

    # Assignment/participation flags
    for col in ("accepts_assignment", "participating"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper().isin(["Y", "TRUE", "1"])

    # Parse enrollment date
    if "enrollment_date" in df.columns:
        df["enrollment_date"] = pd.to_datetime(df["enrollment_date"], errors="coerce").dt.date

    df = add_snapshot_metadata(df, "pecos")
    return df


def run(source_path: Path | None = None, run_date: date | None = None) -> dict[str, int]:
    run_date = run_date or date.today()
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("pecos_start", run_date=str(run_date))

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("pecos")
        landing = resolve_landing_path("pecos", run_date)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_pecos(df)
    report.raise_if_blocked()

    df = transform_pecos(df)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "pecos" / "pecos_enrollment.parquet"
    write_parquet(df, parquet_path)
    results["pecos_parquet"] = len(df)

    out_cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "ref_pecos_enrollment", "reference", if_exists="replace")
    results["ref_pecos_enrollment"] = rows

    log.info("pecos_complete", **results)
    return results
