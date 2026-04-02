"""DME Supplier Utilization pipeline.

Source: CMS DMEPOS Suppliers (~500K rows/year)
Outputs:
  - data/processed/dme/{data_year}/dme.parquet
  - staging.stg_cms__dme (PostgreSQL)
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import (
    add_data_year,
    clean_string_columns,
    normalize_npi,
)
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="dme")

COLUMN_MAPPING = {
    "Rfrg_NPI": "referring_npi",
    "Suplr_NPI": "supplier_npi",
    "Suplr_Prvdr_Last_Org_Name": "supplier_name",
    "Suplr_Prvdr_State_Abrvtn": "supplier_state",
    "HCPCS_Cd": "hcpcs_code",
    "HCPCS_Desc": "hcpcs_description",
    "Tot_Suplr_Srvcs": "number_of_services",
    "Tot_Suplr_Benes": "number_of_beneficiaries",
    "Avg_Suplr_Sbmtd_Chrg": "avg_submitted_charge",
    "Avg_Suplr_Mdcr_Alowd_Amt": "avg_medicare_allowed",
    "Avg_Suplr_Mdcr_Pymt_Amt": "avg_medicare_payment",
}

STAGING_COLUMNS = [
    "referring_npi",
    "supplier_npi",
    "supplier_name",
    "supplier_state",
    "hcpcs_code",
    "hcpcs_description",
    "number_of_services",
    "number_of_beneficiaries",
    "avg_submitted_charge",
    "avg_medicare_allowed",
    "avg_medicare_payment",
    "data_year",
]


def validate_dme(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="dme")
    check_required_columns(df, ["supplier_npi", "hcpcs_code"], report)
    check_column_not_null(df, "supplier_npi", report, severity="BLOCK")
    check_row_count(df, min_rows=100_000, max_rows=1_000_000, report=report, severity="WARN")
    return report


def transform_dme(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    df["supplier_npi"] = normalize_npi(df["supplier_npi"])
    if "referring_npi" in df.columns:
        df["referring_npi"] = normalize_npi(df["referring_npi"])

    clean_string_columns(df, ["supplier_name", "hcpcs_description"])

    if "supplier_state" in df.columns:
        df["supplier_state"] = df["supplier_state"].astype(str).str.strip().str.upper()

    if "hcpcs_code" in df.columns:
        df["hcpcs_code"] = df["hcpcs_code"].astype(str).str.strip().str.upper()

    for col in ("number_of_services",):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "number_of_beneficiaries" in df.columns:
        df["number_of_beneficiaries"] = pd.to_numeric(df["number_of_beneficiaries"], errors="coerce").astype("Int64")

    for col in ("avg_submitted_charge", "avg_medicare_allowed", "avg_medicare_payment"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    df = add_data_year(df, data_year)
    return df


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    data_year: int | None = None,
) -> dict[str, int]:
    run_date = run_date or date.today()
    data_year = data_year or run_date.year - 2
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("dme_start", run_date=str(run_date), data_year=data_year)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("dme")
        landing = resolve_landing_path("dme", run_date, data_year)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_dme(df)
    report.raise_if_blocked()
    df = transform_dme(df, data_year)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "dme" / str(data_year) / "dme.parquet"
    write_parquet(df, parquet_path)
    results["dme_parquet"] = len(df)

    out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "stg_cms__dme", "staging", if_exists="append")
    results["stg_dme"] = rows

    log.info("dme_complete", **results)
    return results
