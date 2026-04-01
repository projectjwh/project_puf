"""NPPES (National Plan & Provider Enumeration System) pipeline.

Source: CMS NPPES NPI Files (~8M rows, 8-10 GB uncompressed)
Outputs:
  - data/processed/nppes/nppes_all.parquet (all NPIs)
  - data/processed/nppes/nppes_active.parquet (active only)
  - reference.ref_providers (PostgreSQL, active providers)
  - reference.ref_provider_taxonomies (unpivoted taxonomy slots)
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import (
    acquire_source,
    compute_hash,
    download_file,
    extract_zip,
    resolve_landing_path,
    validate_file_size_gb,
)
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import (
    add_snapshot_metadata,
    clean_string_columns,
    extract_zip5,
    normalize_fips_state,
    normalize_npi,
)
from pipelines._common.validate import (
    ValidationReport,
    check_column_format,
    check_column_not_null,
    check_required_columns,
    check_row_count,
    check_uniqueness,
    check_value_set,
)

log = get_logger(source="nppes")

# State abbreviation → FIPS mapping (used for state_fips derivation)
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
    "WV": "54", "WI": "55", "WY": "56", "GU": "66", "AS": "60",
    "MP": "69",
}

# Core columns to keep from ~330 raw columns
CORE_COLUMNS = [
    "NPI",
    "Entity Type Code",
    "Replacement NPI",
    "Provider Organization Name (Legal Business Name)",
    "Provider Last Name (Legal Name)",
    "Provider First Name",
    "Provider Middle Name",
    "Provider Name Prefix Text",
    "Provider Name Suffix Text",
    "Provider Credential Text",
    "Provider Gender Code",
    # Practice address
    "Provider First Line Business Practice Location Address",
    "Provider Second Line Business Practice Location Address",
    "Provider Business Practice Location Address City Name",
    "Provider Business Practice Location Address State Name",
    "Provider Business Practice Location Address Postal Code",
    "Provider Business Practice Location Address Country Code (If outside U.S.)",
    "Provider Business Practice Location Address Telephone Number",
    "Provider Business Practice Location Address Fax Number",
    # Dates
    "Provider Enumeration Date",
    "NPI Deactivation Date",
    "NPI Reactivation Date",
    # Taxonomy slots 1-3 (keep first 3 out of 15)
    "Healthcare Provider Taxonomy Code_1",
    "Healthcare Provider Primary Taxonomy Switch_1",
    "Provider License Number_1",
    "Provider License Number State Code_1",
    "Healthcare Provider Taxonomy Code_2",
    "Healthcare Provider Primary Taxonomy Switch_2",
    "Healthcare Provider Taxonomy Code_3",
    "Healthcare Provider Primary Taxonomy Switch_3",
]

# Column rename mapping (raw → canonical)
COLUMN_MAPPING = {
    "NPI": "npi",
    "Entity Type Code": "entity_type_code",
    "Replacement NPI": "replacement_npi",
    "Provider Organization Name (Legal Business Name)": "provider_organization_name",
    "Provider Last Name (Legal Name)": "provider_last_name",
    "Provider First Name": "provider_first_name",
    "Provider Middle Name": "provider_middle_name",
    "Provider Name Prefix Text": "provider_name_prefix",
    "Provider Name Suffix Text": "provider_name_suffix",
    "Provider Credential Text": "provider_credential",
    "Provider Gender Code": "provider_gender_code",
    "Provider First Line Business Practice Location Address": "practice_address_line_1",
    "Provider Second Line Business Practice Location Address": "practice_address_line_2",
    "Provider Business Practice Location Address City Name": "practice_city",
    "Provider Business Practice Location Address State Name": "practice_state",
    "Provider Business Practice Location Address Postal Code": "practice_zip_full",
    "Provider Business Practice Location Address Country Code (If outside U.S.)": "practice_country_code",
    "Provider Business Practice Location Address Telephone Number": "practice_phone",
    "Provider Business Practice Location Address Fax Number": "practice_fax",
    "Provider Enumeration Date": "enumeration_date",
    "NPI Deactivation Date": "deactivation_date",
    "NPI Reactivation Date": "reactivation_date",
    "Healthcare Provider Taxonomy Code_1": "taxonomy_code_1",
    "Healthcare Provider Primary Taxonomy Switch_1": "taxonomy_primary_switch_1",
    "Provider License Number_1": "license_number_1",
    "Provider License Number State Code_1": "license_state_1",
    "Healthcare Provider Taxonomy Code_2": "taxonomy_code_2",
    "Healthcare Provider Primary Taxonomy Switch_2": "taxonomy_primary_switch_2",
    "Healthcare Provider Taxonomy Code_3": "taxonomy_code_3",
    "Healthcare Provider Primary Taxonomy Switch_3": "taxonomy_primary_switch_3",
}


def validate_nppes(df: pd.DataFrame) -> ValidationReport:
    """Run NPPES-specific validation rules."""
    report = ValidationReport(source="nppes")

    check_required_columns(df, ["npi", "entity_type_code"], report)
    check_column_not_null(df, "npi", report, severity="BLOCK")
    check_column_format(df, "npi", r"^\d{10}$", report, severity="BLOCK")
    check_uniqueness(df, ["npi"], report, severity="BLOCK")
    check_value_set(df, "entity_type_code", {"1", "2"}, report, severity="BLOCK")
    check_row_count(df, min_rows=7_000_000, max_rows=10_000_000, report=report, severity="BLOCK")

    # WARN-level checks
    if "provider_gender_code" in df.columns:
        check_value_set(df, "provider_gender_code", {"M", "F", ""}, report, severity="WARN")

    return report


def transform_nppes(df: pd.DataFrame, run_date: date) -> pd.DataFrame:
    """Apply NPPES-specific transforms."""
    # Normalize NPI
    df["npi"] = normalize_npi(df["npi"])

    # Clean string columns
    name_cols = ["provider_last_name", "provider_first_name", "provider_middle_name",
                 "provider_organization_name", "provider_credential"]
    clean_string_columns(df, [c for c in name_cols if c in df.columns])

    # Extract ZIP5
    if "practice_zip_full" in df.columns:
        df["practice_zip5"] = extract_zip5(df["practice_zip_full"])

    # State FIPS
    if "practice_state" in df.columns:
        df["state_fips"] = df["practice_state"].map(STATE_ABBREV_TO_FIPS)

    # Entity type label
    df["entity_type"] = df["entity_type_code"].map({"1": "Individual", "2": "Organization"})
    df["is_individual"] = df["entity_type_code"] == "1"
    df["is_organization"] = df["entity_type_code"] == "2"

    # Display name: "LAST, FIRST CREDENTIAL" for individuals, org name for orgs
    df["display_name"] = ""
    indiv = df["entity_type_code"] == "1"
    df.loc[indiv, "display_name"] = (
        df.loc[indiv, "provider_last_name"].fillna("") + ", " +
        df.loc[indiv, "provider_first_name"].fillna("")
    )
    cred_mask = indiv & df["provider_credential"].notna() & (df["provider_credential"] != "")
    df.loc[cred_mask, "display_name"] = (
        df.loc[cred_mask, "display_name"] + " " + df.loc[cred_mask, "provider_credential"]
    )
    org = df["entity_type_code"] == "2"
    df.loc[org, "display_name"] = df.loc[org, "provider_organization_name"].fillna("")

    # Primary taxonomy: find the slot where primary switch = 'Y'
    df["primary_taxonomy_code"] = None
    for i in range(1, 4):
        code_col = f"taxonomy_code_{i}"
        switch_col = f"taxonomy_primary_switch_{i}"
        if code_col in df.columns and switch_col in df.columns:
            mask = (df[switch_col] == "Y") & df["primary_taxonomy_code"].isna()
            df.loc[mask, "primary_taxonomy_code"] = df.loc[mask, code_col]

    # Fallback: use taxonomy_code_1 if no primary switch found
    no_primary = df["primary_taxonomy_code"].isna()
    if "taxonomy_code_1" in df.columns:
        df.loc[no_primary, "primary_taxonomy_code"] = df.loc[no_primary, "taxonomy_code_1"]

    # Count non-null taxonomy slots
    tax_cols = [f"taxonomy_code_{i}" for i in range(1, 4) if f"taxonomy_code_{i}" in df.columns]
    df["taxonomy_count"] = df[tax_cols].notna().sum(axis=1).astype("Int64")

    # Parse dates
    for date_col in ["enumeration_date", "deactivation_date", "reactivation_date"]:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], format="%m/%d/%Y", errors="coerce")

    # Active flag
    df["is_active"] = df["deactivation_date"].isna()

    # Years since enumeration
    today = pd.Timestamp(run_date)
    df["years_since_enumeration"] = (
        (today - df["enumeration_date"]).dt.days / 365.25
    ).round(1)

    # Snapshot date
    df["_snapshot_date"] = run_date

    return df


def build_taxonomy_table(df: pd.DataFrame) -> pd.DataFrame:
    """Unpivot taxonomy slots into ref_provider_taxonomies rows."""
    records = []
    for i in range(1, 4):
        code_col = f"taxonomy_code_{i}"
        switch_col = f"taxonomy_primary_switch_{i}"
        license_col = f"license_number_{i}"
        license_state_col = f"license_state_{i}"

        if code_col not in df.columns:
            continue

        mask = df[code_col].notna() & (df[code_col] != "")
        subset = df.loc[mask, ["npi"]].copy()
        subset["taxonomy_code"] = df.loc[mask, code_col]
        subset["taxonomy_slot"] = i
        subset["is_primary"] = df.loc[mask, switch_col] == "Y" if switch_col in df.columns else False

        if license_col in df.columns:
            subset["license_number"] = df.loc[mask, license_col]
        if license_state_col in df.columns:
            subset["license_state"] = df.loc[mask, license_state_col]

        records.append(subset)

    if records:
        return pd.concat(records, ignore_index=True)
    return pd.DataFrame()


# Provider columns for ref_providers table
REF_PROVIDER_COLUMNS = [
    "npi", "entity_type_code", "entity_type", "display_name",
    "provider_last_name", "provider_first_name", "provider_middle_name",
    "provider_credential", "provider_organization_name", "provider_gender_code",
    "practice_address_line_1", "practice_address_line_2", "practice_city",
    "practice_state", "practice_zip5", "practice_zip_full",
    "practice_phone", "practice_fax", "state_fips",
    "primary_taxonomy_code", "taxonomy_count",
    "enumeration_date", "deactivation_date", "reactivation_date",
    "is_active", "is_individual", "is_organization",
    "years_since_enumeration", "_snapshot_date",
]


def run(source_path: Path | None = None, run_date: date | None = None) -> dict[str, int]:
    """Execute the full NPPES pipeline.

    Returns dict with row counts for each output.
    """
    import time

    from pipelines._common.catalog import (
        complete_pipeline_run,
        record_pipeline_failure,
        record_pipeline_run,
        update_data_freshness,
    )
    from pipelines._common.validate import apply_quarantine

    run_date = run_date or date.today()
    settings = get_pipeline_settings()
    source_def = get_source("nppes")
    results: dict[str, int] = {}
    start_time = time.time()
    file_hash = ""

    run_id = record_pipeline_run("nppes", run_date, stage="acquire")

    try:
        log.info("nppes_pipeline_start", run_date=str(run_date))

        # 1. Acquire (or use provided source path)
        if source_path:
            csv_path = source_path
        else:
            landing = resolve_landing_path("nppes", run_date)
            downloaded = download_file(source_def.url, landing)
            validate_file_size_gb(downloaded, source_def.file_size.min_gb, source_def.file_size.max_gb)
            file_hash = compute_hash(downloaded)
            extract_zip(downloaded, landing)
            csvs = list(landing.glob("*.csv"))
            csv_path = max(csvs, key=lambda p: p.stat().st_size) if csvs else landing / "npidata.csv"

        log.info("reading_csv", path=str(csv_path))

        # 2. Read (only core columns to save memory)
        available_cols = pd.read_csv(csv_path, nrows=0, dtype=str).columns.tolist()
        cols_to_read = [c for c in CORE_COLUMNS if c in available_cols]

        df = pd.read_csv(csv_path, usecols=cols_to_read, dtype=str, low_memory=False)
        log.info("csv_read", rows=len(df), columns=len(df.columns))

        # Rename columns
        df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

        # 3. Validate
        report = validate_nppes(df)
        report.run_id = run_id
        report.raise_if_blocked()
        report.persist()
        log.info("validation_passed", warnings=len(report.warnings))

        # Apply quarantine
        df = apply_quarantine(df, report, run_id)

        # 4. Transform
        df = transform_nppes(df, run_date)

        # 5. Write Parquet — all NPIs
        all_path = PROJECT_ROOT / settings.storage.processed_base / "nppes" / "nppes_all.parquet"
        write_parquet(df, all_path)
        results["nppes_all_parquet"] = len(df)

        # 6. Write Parquet — active only
        active_df = df[df["is_active"] == True].copy()  # noqa: E712
        active_path = PROJECT_ROOT / settings.storage.processed_base / "nppes" / "nppes_active.parquet"
        write_parquet(active_df, active_path)
        results["nppes_active_parquet"] = len(active_df)

        # 7. Load ref_providers to PostgreSQL (active providers only)
        provider_cols = [c for c in REF_PROVIDER_COLUMNS if c in active_df.columns]
        provider_df = active_df[provider_cols].copy()
        rows = copy_dataframe_to_pg(provider_df, "ref_providers", "reference", if_exists="replace")
        results["ref_providers"] = rows

        # 8. Build and load ref_provider_taxonomies
        tax_df = build_taxonomy_table(active_df)
        if not tax_df.empty:
            rows = copy_dataframe_to_pg(tax_df, "ref_provider_taxonomies", "reference", if_exists="replace")
            results["ref_provider_taxonomies"] = rows

        # 9. Archive
        archive_path = PROJECT_ROOT / settings.storage.archive_base / "nppes" / run_date.isoformat()
        archive_path.mkdir(parents=True, exist_ok=True)
        write_parquet(df, archive_path / "nppes_all.parquet")

        duration = time.time() - start_time
        total_loaded = results.get("ref_providers", 0)
        complete_pipeline_run(
            run_id, "success", rows_processed=len(df),
            rows_loaded=total_loaded, file_hash=file_hash, duration_seconds=duration,
        )
        update_data_freshness("nppes", file_hash=file_hash)

        log.info("nppes_pipeline_complete", **results)
        return results

    except Exception as e:
        duration = time.time() - start_time
        complete_pipeline_run(run_id, "failed", error_message=str(e),
                              duration_seconds=duration)
        record_pipeline_failure(run_id, e)
        raise
