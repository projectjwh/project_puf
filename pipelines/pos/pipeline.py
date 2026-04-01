"""Provider of Services (POS) Facilities pipeline.

Source: CMS Provider of Services Current Files (~300K rows)
Outputs:
  - data/processed/pos/pos_facilities.parquet
  - reference.ref_pos_facilities (PostgreSQL)
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import clean_string_columns, extract_zip5, normalize_fips_county
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="pos")

COLUMN_MAPPING = {
    "PRVDR_NUM": "ccn",
    "FAC_NAME": "facility_name",
    "GNRL_FAC_TYPE_DESC": "facility_type",
    "GNRL_CNTL_TYPE_DESC": "ownership_type",
    "GNRL_CNTL_TYPE_CD": "ownership_code",
    "ST_ADR": "street_address",
    "CITY_NAME": "city",
    "STATE_CD": "state",
    "ZIP_CD": "zip_full",
    "COUNTY_CD": "county_code",
    "PHNE_NUM": "phone",
    "BED_CNT": "bed_count",
    "TOT_BED_CNT": "bed_count_total",
    "CRTFCTN_DT": "certification_date",
    "TRMNTN_DT": "termination_date",
    "MDCR_PRTCPTN_CD": "medicare_participation_code",
    "MDCD_PRTCPTN_CD": "medicaid_participation_code",
    "PRVDR_CTGRY_CD": "facility_type_code",
    "PRVDR_CTGRY_SBTYP_CD": "facility_subtype_code",
}

# State abbreviation → FIPS (same as NPPES)
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

REF_POS_COLUMNS = [
    "ccn", "facility_name", "facility_type", "facility_type_code",
    "ownership_type", "ownership_code",
    "street_address", "city", "state", "zip5", "zip_full", "county_code",
    "phone", "state_fips",
    "bed_count", "bed_count_total",
    "certification_date", "termination_date", "is_active",
    "medicare_participating", "medicaid_participating",
]


def validate_pos(df: pd.DataFrame) -> ValidationReport:
    """POS-specific validation."""
    report = ValidationReport(source="pos")
    check_required_columns(df, ["ccn", "facility_name"], report)
    check_column_not_null(df, "ccn", report, severity="BLOCK")
    check_row_count(df, min_rows=100_000, max_rows=500_000, report=report, severity="WARN")
    return report


def transform_pos(df: pd.DataFrame) -> pd.DataFrame:
    """POS-specific transforms."""
    df["ccn"] = df["ccn"].str.strip().str.zfill(6)

    clean_string_columns(df, ["facility_name", "facility_type", "ownership_type", "city"])

    if "zip_full" in df.columns:
        df["zip5"] = extract_zip5(df["zip_full"])

    if "state" in df.columns:
        df["state"] = df["state"].str.strip().str.upper()
        df["state_fips"] = df["state"].map(STATE_ABBREV_TO_FIPS)

    # Numeric columns
    for col in ("bed_count", "bed_count_total"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Date columns
    for col in ("certification_date", "termination_date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Active flag
    df["is_active"] = df.get("termination_date", pd.Series(dtype="datetime64[ns]")).isna()

    # Participation flags
    df["medicare_participating"] = df.get("medicare_participation_code", "").isin(["1", "Y", "M"])
    df["medicaid_participating"] = df.get("medicaid_participation_code", "").isin(["1", "Y", "D"])

    return df


def run(source_path: Path | None = None, run_date: date | None = None) -> dict[str, int]:
    """Execute the POS facilities pipeline."""
    run_date = run_date or date.today()
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("pos_pipeline_start", run_date=str(run_date))

    # Acquire
    if source_path:
        data_file = source_path
    else:
        source_def = get_source("pos")
        landing = resolve_landing_path("pos", run_date)
        data_file = download_file(source_def.url, landing)

    # Read
    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})
    log.info("csv_read", rows=len(df))

    # Validate
    report = validate_pos(df)
    report.raise_if_blocked()

    # Transform
    df = transform_pos(df)

    # Write Parquet
    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "pos" / "pos_facilities.parquet"
    write_parquet(df, parquet_path)
    results["pos_parquet"] = len(df)

    # Load to PostgreSQL
    out_cols = [c for c in REF_POS_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "ref_pos_facilities", "reference", if_exists="replace")
    results["ref_pos_facilities"] = rows

    log.info("pos_pipeline_complete", **results)
    return results
