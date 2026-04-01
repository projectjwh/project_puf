"""State Drug Utilization Data (SDUD) — Medicaid pipeline.

Source: CMS/Medicaid.gov (~5M rows/quarter)
Outputs:
  - data/processed/sdud/{data_year}/sdud.parquet
  - staging.stg_cms__sdud (PostgreSQL, partitioned by data_year)

NDC normalization is critical: converts 10-digit variations to 11-digit (5-4-2).
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
    normalize_ndc_series,
)
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="sdud")

COLUMN_MAPPING = {
    "State": "state",
    "utilization_type": "utilization_type",
    "Utilization Type": "utilization_type",
    "NDC": "ndc",
    "ndc": "ndc",
    "Labeler Code": "labeler_code",
    "Product Code": "product_code",
    "Package Size": "package_size",
    "Year": "year",
    "Quarter": "quarter",
    "Suppression Used": "suppression_flag",
    "Number of Prescriptions": "number_of_prescriptions",
    "Total Amount Reimbursed": "total_amount_reimbursed",
    "Medicaid Amount Reimbursed": "medicaid_amount_reimbursed",
    "Non Medicaid Amount Reimbursed": "non_medicaid_amount_reimbursed",
    "Units Reimbursed": "units_reimbursed",
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
    "state", "state_fips", "ndc", "labeler_code", "product_code",
    "package_size", "year", "quarter", "suppression_flag", "utilization_type",
    "number_of_prescriptions", "total_amount_reimbursed",
    "medicaid_amount_reimbursed", "non_medicaid_amount_reimbursed",
    "units_reimbursed", "data_year",
]


def validate_sdud(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="sdud")
    check_required_columns(df, ["ndc", "state"], report)
    check_column_not_null(df, "ndc", report, severity="BLOCK")
    check_row_count(df, min_rows=100_000, max_rows=10_000_000, report=report, severity="WARN")
    return report


def transform_sdud(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    # Normalize NDC to 11 digits
    if "ndc" in df.columns:
        df["ndc"] = normalize_ndc_series(df["ndc"])

    if "state" in df.columns:
        df["state"] = df["state"].astype(str).str.strip().str.upper()
        df["state_fips"] = df["state"].map(STATE_ABBREV_TO_FIPS)

    for col in ("year", "quarter", "number_of_prescriptions"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in ("total_amount_reimbursed", "medicaid_amount_reimbursed",
                "non_medicaid_amount_reimbursed", "units_reimbursed"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    # Filter suppressed rows (keep only non-suppressed)
    if "suppression_flag" in df.columns:
        df["suppression_flag"] = df["suppression_flag"].astype(str).str.strip()

    df = add_data_year(df, data_year)
    return df


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    data_year: int | None = None,
) -> dict[str, int]:
    run_date = run_date or date.today()
    data_year = data_year or run_date.year - 1
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("sdud_start", run_date=str(run_date), data_year=data_year)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("sdud")
        landing = resolve_landing_path("sdud", run_date, data_year)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_sdud(df)
    report.raise_if_blocked()
    df = transform_sdud(df, data_year)

    parquet_path = (
        PROJECT_ROOT / settings.storage.processed_base / "sdud" / str(data_year) / "sdud.parquet"
    )
    write_parquet(df, parquet_path)
    results["sdud_parquet"] = len(df)

    out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "stg_cms__sdud", "staging", if_exists="append")
    results["stg_sdud"] = rows

    log.info("sdud_complete", **results)
    return results
