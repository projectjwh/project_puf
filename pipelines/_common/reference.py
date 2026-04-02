"""Shared reference pipeline runner.

Provides a generic acquire → validate → transform → load pattern for
reference data sources. Individual source modules define their specific
column mappings, validation rules, and transforms.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from pipelines._common.acquire import compute_hash, download_file, extract_zip, resolve_landing_path
from pipelines._common.config import get_source
from pipelines._common.db import copy_dataframe_to_pg
from pipelines._common.logging import get_logger
from pipelines._common.validate import ValidationReport, check_required_columns, check_row_count

log = get_logger(stage="reference")


@dataclass
class ReferenceSourceConfig:
    """Configuration for a reference data source pipeline."""

    source_name: str  # short_name from sources.yaml
    target_table: str  # PostgreSQL table name (without schema)
    target_schema: str = "reference"

    # Column mapping: source_column → target_column
    column_mapping: dict[str, str] = field(default_factory=dict)

    # Required columns in source data (before renaming)
    required_source_columns: list[str] = field(default_factory=list)

    # Columns to keep after renaming (if empty, keep all)
    select_columns: list[str] = field(default_factory=list)

    # Type casting map: target_column → type
    type_map: dict[str, str] = field(default_factory=dict)

    # Row count validation
    min_rows: int = 0
    max_rows: int = 10_000_000

    # Custom transform function (receives DataFrame, returns DataFrame)
    transform_fn: Callable[[pd.DataFrame], pd.DataFrame] | None = None

    # File reading options
    read_options: dict[str, Any] = field(default_factory=dict)
    file_pattern: str = "*.csv"  # Glob pattern for finding the right file after extraction


def read_source_file(path: Path, config: ReferenceSourceConfig) -> pd.DataFrame:
    """Read a source file based on its format."""
    suffix = path.suffix.lower()
    opts = config.read_options

    if suffix == ".csv":
        return pd.read_csv(
            path,
            dtype=str,
            encoding=opts.get("encoding", "utf-8"),
            sep=opts.get("sep", ","),
            **{k: v for k, v in opts.items() if k not in ("encoding", "sep")},
        )
    elif suffix == ".tsv" or suffix == ".txt":
        return pd.read_csv(
            path,
            dtype=str,
            sep=opts.get("sep", "\t"),
            encoding=opts.get("encoding", "utf-8"),
            **{k: v for k, v in opts.items() if k not in ("encoding", "sep")},
        )
    elif suffix in (".xlsx", ".xls"):
        sheet = opts.get("sheet_name", 0)
        header = opts.get("header", 0)
        return pd.read_excel(path, dtype=str, sheet_name=sheet, header=header)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def find_data_file(landing_path: Path, config: ReferenceSourceConfig) -> Path:
    """Find the actual data file in the landing directory."""
    matches = list(landing_path.glob(config.file_pattern))
    if not matches:
        # Try recursively
        matches = list(landing_path.rglob(config.file_pattern))
    if not matches:
        raise FileNotFoundError(f"No files matching '{config.file_pattern}' in {landing_path}")
    # Return the largest file (likely the main data file)
    return max(matches, key=lambda p: p.stat().st_size)


def run_reference_pipeline(
    config: ReferenceSourceConfig,
    run_date: date | None = None,
    source_path: Path | None = None,
) -> int:
    """Execute a complete reference data pipeline.

    Steps:
        1. Acquire: Download and extract source file
        2. Read: Parse into DataFrame
        3. Validate: Check required columns, row count
        4. Transform: Rename, type cast, custom transforms
        5. Load: Copy to PostgreSQL reference schema

    Args:
        config: Source-specific pipeline configuration.
        run_date: Override run date (defaults to today).
        source_path: Override source file path (skip download).

    Returns:
        Number of rows loaded.
    """
    import time

    from pipelines._common.catalog import (
        complete_pipeline_run,
        record_pipeline_failure,
        record_pipeline_run,
        update_data_freshness,
    )

    run_date = run_date or date.today()
    source_def = get_source(config.source_name)
    start_time = time.time()
    file_hash = ""

    run_id = record_pipeline_run(config.source_name, run_date, stage="acquire")

    try:
        log.info("pipeline_start", source=config.source_name, table=config.target_table)

        # 1. Acquire
        if source_path:
            data_file = source_path
        else:
            landing = resolve_landing_path(config.source_name, run_date)

            # Download
            downloaded = download_file(source_def.url, landing)
            file_hash = compute_hash(downloaded)

            # Extract if archive
            if source_def.format in ("csv_zip", "zip_txt", "zip_csv", "zip_xlsx"):
                extract_zip(downloaded, landing)

            # Find the data file
            data_file = find_data_file(landing, config)

        log.info("reading_file", path=str(data_file))

        # 2. Read
        df = read_source_file(data_file, config)
        log.info("file_read", rows=len(df), columns=len(df.columns))

        # 3. Validate
        report = ValidationReport(source=config.source_name)
        report.run_id = run_id

        if config.required_source_columns:
            check_required_columns(df, config.required_source_columns, report)

        check_row_count(df, config.min_rows, config.max_rows, report, severity="WARN")

        report.raise_if_blocked()
        report.persist()

        # 4. Transform
        # Rename columns
        if config.column_mapping:
            existing_renames = {k: v for k, v in config.column_mapping.items() if k in df.columns}
            df = df.rename(columns=existing_renames)

        # Select columns
        if config.select_columns:
            available = [c for c in config.select_columns if c in df.columns]
            df = df[available]

        # Type casting
        if config.type_map:
            from pipelines._common.transform import cast_types

            df = cast_types(df, config.type_map)

        # Custom transform
        if config.transform_fn:
            df = config.transform_fn(df)

        # Add metadata
        df["_loaded_at"] = pd.Timestamp.now()

        log.info("transform_complete", rows=len(df), columns=list(df.columns))

        # 5. Load to PostgreSQL
        rows_loaded = copy_dataframe_to_pg(df, config.target_table, config.target_schema, if_exists="replace")

        duration = time.time() - start_time
        complete_pipeline_run(
            run_id,
            "success",
            rows_processed=len(df),
            rows_loaded=rows_loaded,
            file_hash=file_hash,
            duration_seconds=duration,
        )
        update_data_freshness(config.source_name, file_hash=file_hash)

        log.info(
            "pipeline_complete",
            source=config.source_name,
            table=f"{config.target_schema}.{config.target_table}",
            rows=rows_loaded,
        )
        return rows_loaded

    except Exception as e:
        duration = time.time() - start_time
        complete_pipeline_run(run_id, "failed", error_message=str(e), duration_seconds=duration)
        record_pipeline_failure(run_id, e)
        raise
