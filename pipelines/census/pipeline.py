"""Census Population Estimates pipeline.

Source: US Census Bureau county-level population estimates (~3.3K rows/year)
Outputs:
  - data/processed/census/census_population.parquet
  - reference.ref_census_population (PostgreSQL)

Provides population denominators for per-capita calculations across all geographic analyses.
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import (
    add_snapshot_metadata,
    normalize_fips_county,
    normalize_fips_state,
)
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="census")

# Census data comes in wide format (one column per year).
# Column names vary by vintage. Common patterns:
COLUMN_MAPPING = {
    "STATE": "state_fips",
    "COUNTY": "county_fips_suffix",
    "STNAME": "state_name",
    "CTYNAME": "county_name",
    "POPESTIMATE": "total_population",
    "POPEST65PLUS_CIV": "population_65_plus",
    "UNDER18_TOT": "population_under_18",
}

OUTPUT_COLUMNS = [
    "fips_code", "year", "state_fips", "county_fips",
    "state_name", "county_name",
    "total_population", "population_65_plus", "population_under_18",
]


def validate_census(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="census")
    check_required_columns(df, ["state_fips", "total_population"], report)
    check_column_not_null(df, "state_fips", report, severity="BLOCK")
    check_row_count(df, min_rows=50, max_rows=5_000, report=report, severity="WARN")
    return report


def transform_census(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    df["state_fips"] = normalize_fips_state(df["state_fips"])

    # Build county FIPS from state + county suffix
    if "county_fips_suffix" in df.columns:
        suffix = df["county_fips_suffix"].astype(str).str.strip().str.zfill(3)
        df["county_fips"] = df["state_fips"] + suffix
        # Full FIPS code = county_fips (5-digit) for counties, state_fips for states
        df["fips_code"] = df["county_fips"]
        # State-level rows have county suffix "000"
        state_mask = suffix == "000"
        df.loc[state_mask, "fips_code"] = df.loc[state_mask, "state_fips"]
    elif "county_fips" in df.columns:
        df["county_fips"] = normalize_fips_county(df["county_fips"])
        df["fips_code"] = df["county_fips"]
    else:
        df["fips_code"] = df["state_fips"]

    for col in ("total_population", "population_65_plus", "population_under_18"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    if "state_name" in df.columns:
        df["state_name"] = df["state_name"].astype(str).str.strip()
    if "county_name" in df.columns:
        df["county_name"] = df["county_name"].astype(str).str.strip()

    df["year"] = data_year
    df = add_snapshot_metadata(df, "census")
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

    log.info("census_start", run_date=str(run_date), data_year=data_year)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("census")
        landing = resolve_landing_path("census", run_date)
        data_file = download_file(source_def.url, landing)

    df = pd.read_csv(data_file, dtype=str, low_memory=False, encoding="latin-1")
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_census(df)
    report.raise_if_blocked()

    df = transform_census(df, data_year)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "census" / "census_population.parquet"
    write_parquet(df, parquet_path)
    results["census_parquet"] = len(df)

    out_cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "ref_census_population", "reference", if_exists="append")
    results["ref_census_population"] = rows

    log.info("census_complete", **results)
    return results
