"""MA County Rate Books / Benchmarks pipeline.

Source: CMS MA FFS County-Level Data (~3.3K counties/year)
Outputs:
  - data/processed/ma_benchmarks/ma_benchmarks.parquet
  - reference.ref_ma_benchmarks (PostgreSQL)
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import add_snapshot_metadata, normalize_fips_county
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="ma_benchmarks")

COLUMN_MAPPING = {
    "County FIPS Code": "county_fips",
    "FIPS": "county_fips",
    "State FIPS": "state_fips",
    "County Name": "county_name",
    "FFS Per Capita": "ffs_per_capita",
    "FFS_Spending": "ffs_per_capita",
    "MA Benchmark": "ma_benchmark",
    "Benchmark": "ma_benchmark",
    "Risk Score": "risk_score",
    "Quality Bonus %": "quality_bonus_pct",
}

OUTPUT_COLUMNS = [
    "county_fips",
    "year",
    "state_fips",
    "county_name",
    "ffs_per_capita",
    "ma_benchmark",
    "risk_score",
    "quality_bonus_pct",
]


def validate_ma_benchmarks(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="ma_benchmarks")
    check_required_columns(df, ["county_fips"], report)
    check_column_not_null(df, "county_fips", report, severity="BLOCK")
    check_row_count(df, min_rows=1_000, max_rows=5_000, report=report, severity="WARN")
    return report


def transform_ma_benchmarks(df: pd.DataFrame, year: int) -> pd.DataFrame:
    df["county_fips"] = normalize_fips_county(df["county_fips"])
    df["state_fips"] = df["county_fips"].str[:2]

    if "county_name" in df.columns:
        df["county_name"] = df["county_name"].astype(str).str.strip()

    for col in ("ffs_per_capita", "ma_benchmark"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"[$,]", "", regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    for col in ("risk_score", "quality_bonus_pct"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace("%", "", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["year"] = year
    df = add_snapshot_metadata(df, "ma_benchmarks")
    return df


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    year: int | None = None,
) -> dict[str, int]:
    run_date = run_date or date.today()
    year = year or run_date.year
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("ma_benchmarks_start", run_date=str(run_date), year=year)

    if source_path:
        data_file = source_path
    else:
        source_def = get_source("ma_benchmarks")
        landing = resolve_landing_path("ma_benchmarks", run_date)
        data_file = download_file(source_def.url, landing)

    if str(data_file).endswith((".xlsx", ".xls")):
        df = pd.read_excel(data_file, dtype=str)
    else:
        df = pd.read_csv(data_file, dtype=str, low_memory=False)

    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    report = validate_ma_benchmarks(df)
    report.raise_if_blocked()
    df = transform_ma_benchmarks(df, year)

    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "ma_benchmarks" / "ma_benchmarks.parquet"
    write_parquet(df, parquet_path)
    results["ma_benchmarks_parquet"] = len(df)

    out_cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    rows = copy_dataframe_to_pg(df[out_cols], "ref_ma_benchmarks", "reference", if_exists="append")
    results["ref_ma_benchmarks"] = rows

    log.info("ma_benchmarks_complete", **results)
    return results
