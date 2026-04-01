"""Medicare Part B Physician/Supplier Utilization pipeline.

Source: CMS Medicare Physician & Other Practitioners (~10M rows/year)
Outputs:
  - data/processed/partb/{data_year}/part_b_utilization.parquet
  - staging.stg_cms__part_b_utilization (PostgreSQL, partitioned by data_year)

Critical transform: CMS provides AVERAGES, not totals. This pipeline computes
total_submitted_charge = avg_submitted_charge * number_of_services (etc.)
Without these derived totals, aggregation across providers is impossible.
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
    extract_zip5,
    normalize_npi,
)
from pipelines._common.validate import (
    ValidationReport,
    check_column_format,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="partb")

# CMS column names → canonical names
COLUMN_MAPPING = {
    # NPI and provider info
    "Rndrng_NPI": "rendering_npi",
    "Rndrng_Prvdr_Last_Org_Name": "rendering_npi_name",
    "Rndrng_Prvdr_Type": "provider_type",
    "Rndrng_Prvdr_Gndr": "provider_gender",
    "Rndrng_Prvdr_Ent_Cd": "entity_type",
    "Rndrng_Prvdr_St": "provider_state",
    "Rndrng_Prvdr_State_Abrvtn": "provider_state",
    "Rndrng_Prvdr_Zip5": "provider_zip5",
    "Rndrng_Prvdr_RUCA": "provider_ruca",
    "Rndrng_Prvdr_Mdcr_Prtcptg_Ind": "medicare_participation",
    # HCPCS
    "HCPCS_Cd": "hcpcs_code",
    "HCPCS_Desc": "hcpcs_description",
    "HCPCS_Drug_Ind": "hcpcs_drug_indicator",
    # Place of service
    "Place_Of_Srvc": "place_of_service",
    # Service counts
    "Tot_Srvcs": "number_of_services",
    "Tot_Benes": "number_of_beneficiaries",
    "Tot_Bene_Day_Srvcs": "number_of_distinct_beneficiaries_per_day",
    # Averages (source format — must compute totals)
    "Avg_Sbmtd_Chrg": "avg_submitted_charge",
    "Avg_Mdcr_Alowd_Amt": "avg_medicare_allowed",
    "Avg_Mdcr_Pymt_Amt": "avg_medicare_payment",
    "Avg_Mdcr_Stdzd_Amt": "avg_medicare_standardized",
}

# Columns to load to staging (after transform)
STAGING_COLUMNS = [
    "rendering_npi", "rendering_npi_name", "entity_type",
    "hcpcs_code", "hcpcs_description", "hcpcs_drug_indicator",
    "place_of_service",
    "number_of_services", "number_of_beneficiaries",
    "number_of_distinct_beneficiaries_per_day",
    "avg_submitted_charge", "avg_medicare_allowed",
    "avg_medicare_payment", "avg_medicare_standardized",
    "total_submitted_charge", "total_medicare_allowed",
    "total_medicare_payment", "total_medicare_standardized",
    "provider_type", "medicare_participation",
    "provider_state", "provider_zip5", "provider_state_fips",
    "data_year",
]


def validate_partb(df: pd.DataFrame) -> ValidationReport:
    """Part B-specific validation."""
    report = ValidationReport(source="partb")
    check_required_columns(df, ["rendering_npi", "hcpcs_code"], report)
    check_column_not_null(df, "rendering_npi", report, severity="BLOCK")
    check_column_not_null(df, "hcpcs_code", report, severity="BLOCK")
    check_column_format(df, "rendering_npi", r"^\d{10}$", report, severity="WARN")
    check_row_count(df, min_rows=8_000_000, max_rows=13_000_000, report=report, severity="WARN")
    return report


def transform_partb(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    """Apply Part B-specific transforms.

    Critical: compute totals from averages for all dollar columns.
    """
    # Normalize NPI
    df["rendering_npi"] = normalize_npi(df["rendering_npi"])

    # Clean string columns
    clean_string_columns(df, ["hcpcs_description", "provider_type", "rendering_npi_name"])

    # Extract ZIP5 if full ZIP present
    if "provider_zip5" in df.columns:
        df["provider_zip5"] = extract_zip5(df["provider_zip5"])

    # State FIPS derivation
    from pipelines.nppes.pipeline import STATE_ABBREV_TO_FIPS
    if "provider_state" in df.columns:
        df["provider_state"] = df["provider_state"].astype(str).str.strip().str.upper()
        df["provider_state_fips"] = df["provider_state"].map(STATE_ABBREV_TO_FIPS)

    # Cast numeric columns
    numeric_cols = [
        "number_of_services", "number_of_beneficiaries",
        "number_of_distinct_beneficiaries_per_day",
        "avg_submitted_charge", "avg_medicare_allowed",
        "avg_medicare_payment", "avg_medicare_standardized",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # CRITICAL: Compute totals from averages
    # total = average × number_of_services
    total_pairs = [
        ("avg_submitted_charge", "total_submitted_charge"),
        ("avg_medicare_allowed", "total_medicare_allowed"),
        ("avg_medicare_payment", "total_medicare_payment"),
        ("avg_medicare_standardized", "total_medicare_standardized"),
    ]
    for avg_col, total_col in total_pairs:
        if avg_col in df.columns and "number_of_services" in df.columns:
            df = compute_totals_from_averages(df, avg_col, "number_of_services", total_col)

    # Round dollar amounts
    for col in df.columns:
        if col.startswith("total_") or col.startswith("avg_"):
            if col in df.columns and df[col].dtype in ("float64", "Float64"):
                df[col] = df[col].round(2)

    # Integer columns
    for col in ("number_of_beneficiaries", "number_of_distinct_beneficiaries_per_day"):
        if col in df.columns:
            df[col] = df[col].astype("Int64")

    df = add_data_year(df, data_year)
    return df


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    data_year: int | None = None,
) -> dict[str, int]:
    """Execute the Part B utilization pipeline."""
    import time

    from pipelines._common.catalog import (
        complete_pipeline_run,
        record_pipeline_failure,
        record_pipeline_run,
        update_data_freshness,
    )
    from pipelines._common.validate import apply_quarantine

    run_date = run_date or date.today()
    data_year = data_year or run_date.year - 2  # ~2 year lag
    settings = get_pipeline_settings()
    results: dict[str, int] = {}
    start_time = time.time()
    file_hash = ""

    run_id = record_pipeline_run("partb", run_date, data_year, stage="acquire")

    try:
        log.info("partb_start", run_date=str(run_date), data_year=data_year)

        # Acquire
        if source_path:
            csv_path = source_path
        else:
            source_def = get_source("partb")
            landing = resolve_landing_path("partb", run_date, data_year)
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
        report = validate_partb(df)
        report.run_id = run_id
        report.raise_if_blocked()
        report.persist()
        log.info("validation_passed", warnings=len(report.warnings))

        # Apply quarantine
        df = apply_quarantine(df, report, run_id)

        # Transform
        df = transform_partb(df, data_year)
        results["partb_rows"] = len(df)

        # Write Parquet
        parquet_path = (
            PROJECT_ROOT / settings.storage.processed_base
            / "partb" / str(data_year) / "part_b_utilization.parquet"
        )
        write_parquet(df, parquet_path)
        results["partb_parquet"] = len(df)

        # Load to staging (PostgreSQL)
        out_cols = [c for c in STAGING_COLUMNS if c in df.columns]
        rows = copy_dataframe_to_pg(
            df[out_cols], "stg_cms__part_b_utilization", "staging", if_exists="append",
        )
        results["stg_part_b"] = rows

        duration = time.time() - start_time
        complete_pipeline_run(
            run_id, "success", rows_processed=results.get("partb_rows", 0),
            rows_loaded=rows, file_hash=file_hash, duration_seconds=duration,
        )
        update_data_freshness("partb", data_year, file_hash)

        log.info("partb_complete", **results)
        return results

    except Exception as e:
        duration = time.time() - start_time
        complete_pipeline_run(run_id, "failed", error_message=str(e),
                              duration_seconds=duration)
        record_pipeline_failure(run_id, e)
        raise
