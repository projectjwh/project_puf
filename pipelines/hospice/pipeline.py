"""Hospice Utilization pipeline.

Source: CMS Medicare Hospice (~5K rows/year, CCN-level)
Outputs:
  - data/processed/hospice/{data_year}/hospice_utilization.parquet
  - staging.stg_cms__hospice_utilization (PostgreSQL)
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import add_data_year, clean_string_columns
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="hospice")

COLUMN_MAPPING = {
    "Rndrng_Prvdr_CCN": "ccn",
    "Rndrng_Prvdr_Org_Name": "facility_name",
    "Rndrng_Prvdr_St": "provider_state",
    "Rndrng_Prvdr_State_Abrvtn": "provider_state",
    "Tot_Benes": "total_beneficiaries",
    "Tot_Hospc_Chrg_Amt": "total_hospice_charge",
    "Tot_Hospc_Mdcr_Pymt_Amt": "total_hospice_medicare_payment",
    "Tot_Hospc_Days": "total_hospice_days",
    "Avg_Lngth_of_Stay": "avg_length_of_stay",
    "Provider Id": "ccn",
    "Provider Name": "facility_name",
    "Provider State": "provider_state",
}

STATE_ABBREV_TO_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "DC": "11", "FL": "12",
    "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18",
    "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23",
    "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33",
    "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38",
    "OH": "39", "OK": "40", "OR": "41", "PA": "42", "PR": "72",
    "RI": "44", "SC": "45", "SD": "46", "TN": "47", "TX": "48",
    "UT": "49", "VT": "50", "VA": "51", "VI": "78", "WA": "53",
    "WV": "54", "WI": "55", "WY": "56",
}

STAGING_COLUMNS = [
    "ccn", "facility_name", "provider_state", "provider_state_fips",
    "total_beneficiaries", "total_hospice_charge", "total_hospice_medicare_payment",
    "total_hospice_days", "avg_length_of_stay", "data_year",
]


def validate_hospice(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="hospice")
    check_required_columns(df, ["ccn"], report)
    check_column_not_null(df, "ccn", report, severity="BLOCK")
    check_row_count(df, min_rows=2_000, max_rows=10_000, report=report, severity="WARN")
    return report


def transform_hospice(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    df["ccn"] = df["ccn"].astype(str).str.strip().str.zfill(6)
    clean_string_columns(df, ["facility_name"])

    if "provider_state" in df.columns:
        df["provider_state"] = df["provider_state"].astype(str).str.strip().str.upper()
        df["provider_state_fips"] = df["provider_state"].map(STATE_ABBREV_TO_FIPS)

    for col in ("total_beneficiaries", "total_hospice_days"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in ("total_hospice_charge", "total_hospice_medicare_payment", "avg_length_of_stay"):
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

    log.info("hospice_start", run_date=str(run_date), data_year=data_year)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("hospice")
        landing = resolve_landing_path("hospice", run_date, data_year)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_hospice(df)
    report.raise_if_blocked()
    df = transform_hospice(df, data_year)

    parquet_path = (
        PROJECT_ROOT / settings.storage.processed_base / "hospice" / str(data_year) / "hospice_utilization.parquet"
    )
    write_parquet(df, parquet_path)
    results["hospice_parquet"] = len(df)

    out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "stg_cms__hospice_utilization", "staging", if_exists="append")
    results["stg_hospice"] = rows

    log.info("hospice_complete", **results)
    return results
