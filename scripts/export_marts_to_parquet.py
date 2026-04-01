"""Export dbt mart tables to Parquet for DuckDB analytical queries.

This script reads mart tables from PostgreSQL and writes them as Parquet files
to data/mart/{table_name}/ for consumption by the DuckDB query engine.

Usage:
    python scripts/export_marts_to_parquet.py
    python scripts/export_marts_to_parquet.py --tables mart_provider__practice_profile
"""

import argparse
from pathlib import Path

import pandas as pd

from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings
from pipelines._common.db import get_pg_engine, write_parquet
from pipelines._common.logging import get_logger

log = get_logger(source="export_parquet")

# Mart tables to export
MART_TABLES = [
    ("mart", "mart_provider__practice_profile"),
    ("mart", "mart_national__kpi_summary"),
    ("mart", "mart_geographic__spending_variation"),
    ("mart", "mart_geographic__by_state"),
    ("mart", "mart_opioid__by_state"),
    ("mart", "mart_opioid__top_prescribers"),
]


def export_table(schema: str, table: str, output_dir: Path) -> int:
    """Export a single table to Parquet. Returns row count."""
    engine = get_pg_engine()
    query = f"SELECT * FROM {schema}.{table}"  # noqa: S608

    log.info("exporting_table", schema=schema, table=table)

    df = pd.read_sql(query, engine)
    if df.empty:
        log.warning("empty_table", table=table)
        return 0

    parquet_path = output_dir / table / f"{table}.parquet"
    write_parquet(df, parquet_path)

    log.info("table_exported", table=table, rows=len(df), path=str(parquet_path))
    return len(df)


def export_all(tables: list[tuple[str, str]] | None = None) -> dict[str, int]:
    """Export all mart tables to Parquet."""
    settings = get_pipeline_settings()
    output_dir = PROJECT_ROOT / settings.storage.processed_base / "mart"
    tables = tables or MART_TABLES
    results: dict[str, int] = {}

    log.info("export_start", table_count=len(tables))

    for schema, table in tables:
        try:
            rows = export_table(schema, table, output_dir)
            results[table] = rows
        except Exception as e:
            log.error("export_failed", table=table, error=str(e))
            results[table] = -1

    log.info("export_complete", **results)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Export mart tables to Parquet")
    parser.add_argument("--tables", nargs="*", help="Specific tables to export")
    args = parser.parse_args()

    if args.tables:
        tables = [("mart", t) for t in args.tables]
    else:
        tables = MART_TABLES

    results = export_all(tables)
    for table, rows in results.items():
        status = "OK" if rows >= 0 else "FAILED"
        print(f"  {table}: {rows:,} rows [{status}]")


if __name__ == "__main__":
    main()
