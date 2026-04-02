"""Hospital General Information pipeline.

Source: CMS Hospital Compare (~5K hospitals)
Outputs:
  - data/processed/hospital_general/hospital_general.parquet
  - reference.ref_hospital_general (PostgreSQL)
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, resolve_landing_path
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

log = get_logger(source="hospital_general")

COLUMN_MAPPING = {
    "Facility ID": "ccn",
    "Provider ID": "ccn",
    "Facility Name": "facility_name",
    "Hospital Name": "facility_name",
    "Address": "address",
    "City": "city",
    "State": "state",
    "ZIP Code": "zip_code",
    "County Name": "county_name",
    "Phone Number": "phone_number",
    "Hospital Type": "hospital_type",
    "Hospital Ownership": "hospital_ownership",
    "Emergency Services": "emergency_services",
    "Meets criteria for promoting interoperability of EHRs": "meets_ehr_criteria",
    "Hospital overall rating": "overall_rating",
    "Mortality national comparison": "mortality_national_comparison",
    "Safety of care national comparison": "safety_national_comparison",
    "Readmission national comparison": "readmission_national_comparison",
    "Patient experience national comparison": "patient_experience_national_comparison",
}

OUTPUT_COLUMNS = [
    "ccn",
    "facility_name",
    "address",
    "city",
    "state",
    "zip_code",
    "county_name",
    "phone_number",
    "hospital_type",
    "hospital_ownership",
    "emergency_services",
    "meets_ehr_criteria",
    "overall_rating",
    "mortality_national_comparison",
    "safety_national_comparison",
    "readmission_national_comparison",
    "patient_experience_national_comparison",
]


def validate_hospital_general(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="hospital_general")
    check_required_columns(df, ["ccn"], report)
    check_column_not_null(df, "ccn", report, severity="BLOCK")
    check_row_count(df, min_rows=2_000, max_rows=10_000, report=report, severity="WARN")
    return report


def transform_hospital_general(df: pd.DataFrame) -> pd.DataFrame:
    df["ccn"] = df["ccn"].astype(str).str.strip().str.zfill(6)
    clean_string_columns(df, ["facility_name", "hospital_type", "hospital_ownership", "city"])

    if "state" in df.columns:
        df["state"] = df["state"].astype(str).str.strip().str.upper()

    # Boolean columns
    for col in ("emergency_services", "meets_ehr_criteria"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper().isin(["YES", "Y", "TRUE", "1"])

    if "overall_rating" in df.columns:
        df["overall_rating"] = df["overall_rating"].astype(str).str.replace("Not Available", "", regex=False)
        df["overall_rating"] = pd.to_numeric(df["overall_rating"], errors="coerce").astype("Int64")

    df = add_snapshot_metadata(df, "hospital_general")
    return df


def run(source_path: Path | None = None, run_date: date | None = None) -> dict[str, int]:
    run_date = run_date or date.today()
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("hospital_general_start", run_date=str(run_date))

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("hospital_general")
        landing = resolve_landing_path("hospital_general", run_date)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False)
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_hospital_general(df)
    report.raise_if_blocked()
    df = transform_hospital_general(df)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "hospital_general" / "hospital_general.parquet"
    write_parquet(df, parquet_path)
    results["hospital_general_parquet"] = len(df)

    out_cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "ref_hospital_general", "reference", if_exists="replace")
    results["ref_hospital_general"] = rows

    log.info("hospital_general_complete", **results)
    return results
