"""Medicare Part D Prescribers pipeline.

Source: CMS Medicare Part D Prescribers (~25M rows/year)
Outputs:
  - data/processed/partd/{data_year}/part_d_prescribers.parquet
  - staging.stg_cms__part_d_prescribers (PostgreSQL, partitioned by data_year)

Key transforms: opioid flagging, brand/generic classification, cost-per-claim derivation.
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, extract_zip, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import add_data_year, clean_string_columns, normalize_npi
from pipelines._common.validate import (
    ValidationReport,
    check_column_format,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="partd")

# CMS column names → canonical names
COLUMN_MAPPING = {
    # Prescriber identity
    "Prscrbr_NPI": "prescriber_npi",
    "Prscrbr_Last_Org_Name": "prescriber_last_name",
    "Prscrbr_First_Name": "prescriber_first_name",
    "Prscrbr_Type": "specialty_description",
    "Prscrbr_Type_Src": "specialty_source",
    "Prscrbr_St": "prescriber_state",
    "Prscrbr_State_Abrvtn": "prescriber_state",
    "Prscrbr_Gndr": "prescriber_gender",
    "Prscrbr_Ent_Cd": "entity_type",
    # Drug identity
    "Brnd_Name": "drug_name",
    "Gnrc_Name": "generic_name",
    # Claim counts
    "Tot_Clms": "total_claim_count",
    "Tot_Day_Suply": "total_day_supply",
    "Tot_Drug_Cst": "total_drug_cost",
    "Tot_Benes": "total_beneficiary_count",
    # GE65 fields
    "GE65_Sprsn_Flag": "ge65_suppress_flag",
    "GE65_Tot_Clms": "ge65_total_claims",
    "GE65_Tot_Drug_Cst": "ge65_total_drug_cost",
    # Opioid fields
    "Opioid_Drug_Flag": "is_opioid_flag",
    "Opioid_Tot_Clms": "opioid_claim_count",
    "Opioid_Prscrbr_Rate": "opioid_prescriber_rate",
    "Opioid_LA_Drug_Flag": "is_long_acting_opioid_flag",
    # Antibiotic fields
    "Antbtc_Drug_Flag": "is_antibiotic_flag",
    "Antpsychtc_Drug_Flag": "is_antipsychotic_flag",
}

STAGING_COLUMNS = [
    "prescriber_npi",
    "prescriber_last_name",
    "prescriber_first_name",
    "prescriber_state",
    "prescriber_state_fips",
    "specialty_description",
    "drug_name",
    "generic_name",
    "total_claim_count",
    "total_day_supply",
    "total_drug_cost",
    "total_beneficiary_count",
    "cost_per_claim",
    "cost_per_day",
    "is_brand_name",
    "is_generic",
    "is_opioid",
    "opioid_claim_count",
    "opioid_prescriber_rate",
    "ge65_suppress_flag",
    "data_year",
]


def validate_partd(df: pd.DataFrame) -> ValidationReport:
    """Part D-specific validation."""
    report = ValidationReport(source="partd")
    check_required_columns(df, ["prescriber_npi", "drug_name"], report)
    check_column_not_null(df, "prescriber_npi", report, severity="BLOCK")
    check_column_not_null(df, "drug_name", report, severity="BLOCK")
    check_column_format(df, "prescriber_npi", r"^\d{10}$", report, severity="WARN")
    check_row_count(df, min_rows=20_000_000, max_rows=30_000_000, report=report, severity="WARN")
    return report


def transform_partd(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    """Apply Part D-specific transforms."""
    # Normalize NPI
    df["prescriber_npi"] = normalize_npi(df["prescriber_npi"])

    # Clean string columns
    clean_string_columns(
        df, ["drug_name", "generic_name", "specialty_description", "prescriber_last_name", "prescriber_first_name"]
    )

    # State FIPS derivation
    from pipelines.nppes.pipeline import STATE_ABBREV_TO_FIPS

    if "prescriber_state" in df.columns:
        df["prescriber_state"] = df["prescriber_state"].astype(str).str.strip().str.upper()
        df["prescriber_state_fips"] = df["prescriber_state"].map(STATE_ABBREV_TO_FIPS)

    # Cast numeric columns
    numeric_cols = [
        "total_claim_count",
        "total_day_supply",
        "total_drug_cost",
        "total_beneficiary_count",
        "opioid_claim_count",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Integer columns
    for col in ("total_claim_count", "total_day_supply", "total_beneficiary_count", "opioid_claim_count"):
        if col in df.columns:
            df[col] = df[col].astype("Int64")

    # Opioid prescriber rate
    if "opioid_prescriber_rate" in df.columns:
        df["opioid_prescriber_rate"] = pd.to_numeric(df["opioid_prescriber_rate"], errors="coerce")

    # Opioid flag (from source flag or derived)
    if "is_opioid_flag" in df.columns:
        df["is_opioid"] = df["is_opioid_flag"].isin(["Y", "1", "True"])
    else:
        df["is_opioid"] = False

    # Brand/generic classification
    # CMS Part D data: if drug_name != generic_name → brand
    if "drug_name" in df.columns and "generic_name" in df.columns:
        df["is_brand_name"] = (df["drug_name"] != df["generic_name"]) & df["drug_name"].notna()
        df["is_generic"] = (df["drug_name"] == df["generic_name"]) & df["drug_name"].notna()
    else:
        df["is_brand_name"] = False
        df["is_generic"] = False

    # Derived cost metrics
    if "total_drug_cost" in df.columns and "total_claim_count" in df.columns:
        claims = pd.to_numeric(df["total_claim_count"], errors="coerce")
        cost = pd.to_numeric(df["total_drug_cost"], errors="coerce")
        df["cost_per_claim"] = (cost / claims.replace(0, pd.NA)).round(2)
    if "total_drug_cost" in df.columns and "total_day_supply" in df.columns:
        days = pd.to_numeric(df["total_day_supply"], errors="coerce")
        cost = pd.to_numeric(df["total_drug_cost"], errors="coerce")
        df["cost_per_day"] = (cost / days.replace(0, pd.NA)).round(2)

    # Round dollar amounts
    if "total_drug_cost" in df.columns:
        df["total_drug_cost"] = df["total_drug_cost"].round(2)

    df = add_data_year(df, data_year)
    return df


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    data_year: int | None = None,
) -> dict[str, int]:
    """Execute the Part D prescribers pipeline."""
    import time

    from pipelines._common.catalog import (
        complete_pipeline_run,
        record_pipeline_failure,
        record_pipeline_run,
        update_data_freshness,
    )
    from pipelines._common.validate import apply_quarantine

    run_date = run_date or date.today()
    data_year = data_year or run_date.year - 2
    settings = get_pipeline_settings()
    results: dict[str, int] = {}
    start_time = time.time()
    file_hash = ""

    run_id = record_pipeline_run("partd", run_date, data_year, stage="acquire")

    try:
        log.info("partd_start", run_date=str(run_date), data_year=data_year)

        # Acquire
        if source_path:
            csv_path = source_path
        else:
            source_def = get_source("partd")
            landing = resolve_landing_path("partd", run_date, data_year)
            downloaded = download_file(source_def.url, landing)
            from pipelines._common.acquire import compute_hash

            file_hash = compute_hash(downloaded)
            if downloaded.suffix == ".zip":
                extract_zip(downloaded, landing)
                csvs = list(landing.glob("*.csv"))
                csv_path = max(csvs, key=lambda p: p.stat().st_size)
            else:
                csv_path = downloaded

        log.info("reading_csv", path=str(csv_path))

        # Read
        df = pd.read_csv(csv_path, dtype=str, low_memory=False)
        df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})
        log.info("csv_read", rows=len(df), columns=len(df.columns))

        # Validate
        report = validate_partd(df)
        report.run_id = run_id
        report.raise_if_blocked()
        report.persist()
        log.info("validation_passed", warnings=len(report.warnings))

        # Apply quarantine
        df = apply_quarantine(df, report, run_id)

        # Transform
        df = transform_partd(df, data_year)
        results["partd_rows"] = len(df)

        # Write Parquet
        parquet_path = (
            PROJECT_ROOT / settings.storage.processed_base / "partd" / str(data_year) / "part_d_prescribers.parquet"
        )
        write_parquet(df, parquet_path)
        results["partd_parquet"] = len(df)

        # Load to staging (PostgreSQL)
        out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
        rows = copy_dataframe_to_pg(
            df[out_cols],
            "stg_cms__part_d_prescribers",
            "staging",
            if_exists="append",
        )
        results["stg_part_d"] = rows

        duration = time.time() - start_time
        complete_pipeline_run(
            run_id,
            "success",
            rows_processed=results.get("partd_rows", 0),
            rows_loaded=rows,
            file_hash=file_hash,
            duration_seconds=duration,
        )
        update_data_freshness("partd", data_year, file_hash)

        log.info("partd_complete", **results)
        return results

    except Exception as e:
        duration = time.time() - start_time
        complete_pipeline_run(run_id, "failed", error_message=str(e), duration_seconds=duration)
        record_pipeline_failure(run_id, e)
        raise
