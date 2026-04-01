"""Medicare Inpatient Hospitals — by Provider and Service pipeline.

Source: CMS Inpatient Hospitals (~200K rows/year, DRG-level grain)
Outputs:
  - data/processed/inpatient/{data_year}/inpatient.parquet
  - staging.stg_cms__inpatient (PostgreSQL, partitioned by data_year)

Like Part B, CMS provides AVERAGES. Pipeline computes TOTALS:
  total_covered_charges = avg_covered_charges × total_discharges
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, extract_zip, resolve_landing_path
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

log = get_logger(source="inpatient")

COLUMN_MAPPING = {
    "Rndrng_Prvdr_CCN": "ccn",
    "Rndrng_Prvdr_Org_Name": "facility_name",
    "Rndrng_Prvdr_St": "provider_state",
    "Rndrng_Prvdr_State_Abrvtn": "provider_state",
    "DRG_Cd": "drg_code",
    "DRG_Desc": "drg_description",
    "Tot_Dschrgs": "total_discharges",
    "Avg_Submtd_Cvrd_Chrg": "avg_covered_charges",
    "Avg_Tot_Pymt_Amt": "avg_total_payments",
    "Avg_Mdcr_Pymt_Amt": "avg_medicare_payments",
    # Alternate column names
    "Provider Id": "ccn",
    "Provider Name": "facility_name",
    "Provider State": "provider_state",
    "DRG Definition": "drg_description",
    "Total Discharges": "total_discharges",
    "Average Covered Charges": "avg_covered_charges",
    "Average Total Payments": "avg_total_payments",
    "Average Medicare Payments": "avg_medicare_payments",
}

STAGING_COLUMNS = [
    "ccn", "facility_name", "provider_state", "provider_state_fips",
    "drg_code", "drg_description", "total_discharges",
    "avg_covered_charges", "avg_total_payments", "avg_medicare_payments",
    "total_covered_charges", "total_payments", "total_medicare_payments",
    "data_year",
]

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


def validate_inpatient(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="inpatient")
    check_required_columns(df, ["ccn", "drg_code"], report)
    check_column_not_null(df, "ccn", report, severity="BLOCK")
    check_row_count(df, min_rows=100_000, max_rows=500_000, report=report, severity="WARN")
    return report


def transform_inpatient(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    df["ccn"] = df["ccn"].astype(str).str.strip().str.zfill(6)

    # Extract DRG code from descriptions like "470 - MAJOR JOINT REPLACEMENT..."
    if "drg_code" not in df.columns and "drg_description" in df.columns:
        df["drg_code"] = df["drg_description"].str.extract(r"^(\d+)", expand=False)

    if "drg_code" in df.columns:
        df["drg_code"] = df["drg_code"].astype(str).str.strip().str.zfill(3)

    clean_string_columns(df, ["facility_name", "drg_description"])

    if "provider_state" in df.columns:
        df["provider_state"] = df["provider_state"].astype(str).str.strip().str.upper()
        df["provider_state_fips"] = df["provider_state"].map(STATE_ABBREV_TO_FIPS)

    # Numeric columns
    df["total_discharges"] = pd.to_numeric(df.get("total_discharges"), errors="coerce").astype("Int64")

    for col in ("avg_covered_charges", "avg_total_payments", "avg_medicare_payments"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"[$,]", "", regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # CRITICAL: Compute totals from averages
    total_pairs = [
        ("avg_covered_charges", "total_covered_charges"),
        ("avg_total_payments", "total_payments"),
        ("avg_medicare_payments", "total_medicare_payments"),
    ]
    for avg_col, total_col in total_pairs:
        if avg_col in df.columns and "total_discharges" in df.columns:
            df = compute_totals_from_averages(df, avg_col, "total_discharges", total_col)

    for col in df.columns:
        if col.startswith("total_") and col not in ("total_discharges",):
            if col in df.columns and hasattr(df[col], "round"):
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

    log.info("inpatient_start", run_date=str(run_date), data_year=data_year)

    if source_path:
        csv_path = source_path
    else:
        source_def = get_source("inpatient")
        landing = resolve_landing_path("inpatient", run_date, data_year)
        downloaded = download_file(source_def.url, landing)
        if downloaded.suffix == ".zip":
            extract_zip(downloaded, landing)
            csvs = list(landing.glob("*.csv"))
            csv_path = max(csvs, key=lambda p: p.stat().st_size)
        else:
            csv_path = downloaded

    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_inpatient(df)
    report.raise_if_blocked()

    df = transform_inpatient(df, data_year)
    results["inpatient_rows"] = len(df)

    parquet_path = (
        PROJECT_ROOT / settings.storage.processed_base
        / "inpatient" / str(data_year) / "inpatient.parquet"
    )
    write_parquet(df, parquet_path)
    results["inpatient_parquet"] = len(df)

    out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "stg_cms__inpatient", "staging", if_exists="append")
    results["stg_inpatient"] = rows

    log.info("inpatient_complete", **results)
    return results
