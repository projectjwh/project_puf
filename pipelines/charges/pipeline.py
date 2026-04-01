"""Inpatient Hospital Charge Data pipeline.

Source: CMS Inpatient Hospital Charges (~200K rows/year, DRG-level)
Outputs:
  - data/processed/charges/{data_year}/charges.parquet
  - staging.stg_cms__charges (PostgreSQL)

Like inpatient, CMS provides AVERAGES. Pipeline computes TOTALS.
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
    compute_totals_from_averages,
)
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)
from pipelines.inpatient.pipeline import STATE_ABBREV_TO_FIPS

log = get_logger(source="charges")

COLUMN_MAPPING = {
    "Rndrng_Prvdr_CCN": "ccn",
    "Provider Id": "ccn",
    "Rndrng_Prvdr_Org_Name": "facility_name",
    "Provider Name": "facility_name",
    "Rndrng_Prvdr_St": "provider_state",
    "Provider State": "provider_state",
    "DRG_Cd": "drg_code",
    "DRG Definition": "drg_description",
    "DRG_Desc": "drg_description",
    "Tot_Dschrgs": "total_discharges",
    "Total Discharges": "total_discharges",
    "Avg_Submtd_Cvrd_Chrg": "avg_covered_charges",
    "Average Covered Charges": "avg_covered_charges",
    "Avg_Tot_Pymt_Amt": "avg_total_payments",
    "Average Total Payments": "avg_total_payments",
    "Avg_Mdcr_Pymt_Amt": "avg_medicare_payments",
    "Average Medicare Payments": "avg_medicare_payments",
}

STAGING_COLUMNS = [
    "ccn", "facility_name", "provider_state", "provider_state_fips",
    "drg_code", "drg_description", "total_discharges",
    "avg_covered_charges", "avg_total_payments", "avg_medicare_payments",
    "total_covered_charges", "total_payments", "total_medicare_payments",
    "data_year",
]


def validate_charges(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="charges")
    check_required_columns(df, ["ccn", "drg_code"], report)
    check_column_not_null(df, "ccn", report, severity="BLOCK")
    check_row_count(df, min_rows=50_000, max_rows=500_000, report=report, severity="WARN")
    return report


def transform_charges(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    df["ccn"] = df["ccn"].astype(str).str.strip().str.zfill(6)

    if "drg_code" not in df.columns and "drg_description" in df.columns:
        df["drg_code"] = df["drg_description"].str.extract(r"^(\d+)", expand=False)

    if "drg_code" in df.columns:
        df["drg_code"] = df["drg_code"].astype(str).str.strip().str.zfill(3)

    clean_string_columns(df, ["facility_name", "drg_description"])

    if "provider_state" in df.columns:
        df["provider_state"] = df["provider_state"].astype(str).str.strip().str.upper()
        df["provider_state_fips"] = df["provider_state"].map(STATE_ABBREV_TO_FIPS)

    df["total_discharges"] = pd.to_numeric(df.get("total_discharges"), errors="coerce").astype("Int64")

    for col in ("avg_covered_charges", "avg_total_payments", "avg_medicare_payments"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"[$,]", "", regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    total_pairs = [
        ("avg_covered_charges", "total_covered_charges"),
        ("avg_total_payments", "total_payments"),
        ("avg_medicare_payments", "total_medicare_payments"),
    ]
    for avg_col, total_col in total_pairs:
        if avg_col in df.columns and "total_discharges" in df.columns:
            df = compute_totals_from_averages(df, avg_col, "total_discharges", total_col)

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

    log.info("charges_start", run_date=str(run_date), data_year=data_year)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("charges")
        landing = resolve_landing_path("charges", run_date, data_year)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_charges(df)
    report.raise_if_blocked()
    df = transform_charges(df, data_year)

    parquet_path = (
        PROJECT_ROOT / settings.storage.processed_base / "charges" / str(data_year) / "charges.parquet"
    )
    write_parquet(df, parquet_path)
    results["charges_parquet"] = len(df)

    out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "stg_cms__charges", "staging", if_exists="append")
    results["stg_charges"] = rows

    log.info("charges_complete", **results)
    return results
