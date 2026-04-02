"""Catalog writer for pipeline metadata, validation, quarantine, and freshness.

Bridges pipeline execution to the 7 catalog tables (Alembic migration 003):
- catalog.sources, catalog.source_columns
- catalog.pipeline_runs, catalog.pipeline_failures
- catalog.validation_runs, catalog.quarantine_rows
- catalog.data_freshness
"""

from __future__ import annotations

import json
import traceback
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import text

from pipelines._common.db import get_pg_engine
from pipelines._common.logging import get_logger

if TYPE_CHECKING:
    import pandas as pd

    from pipelines._common.validate import ValidationReport

log = get_logger(stage="catalog")


# ---------------------------------------------------------------------------
# Pipeline run lifecycle
# ---------------------------------------------------------------------------


def _resolve_source_id(source: str) -> int | None:
    """Look up source_id from catalog.sources by short_name.

    Returns None if the source is not seeded yet (graceful degradation).
    """
    engine = get_pg_engine(use_pgbouncer=False)
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT source_id FROM catalog.sources WHERE short_name = :name"),
                {"name": source},
            )
            row = result.fetchone()
            return row[0] if row else None
    except Exception:
        return None


def record_pipeline_run(
    source: str,
    run_date: date | None = None,
    data_year: int | None = None,
    stage: str = "acquire",
) -> int:
    """Insert a new pipeline_runs row and return its run_id.

    If catalog.sources is not seeded or the table doesn't exist,
    logs a warning and returns -1 (caller should handle gracefully).
    """
    run_date = run_date or date.today()
    source_id = _resolve_source_id(source)

    if source_id is None:
        log.warning(
            "catalog_source_not_found", source=source, message="catalog.sources not seeded; run tracking disabled"
        )
        return -1

    engine = get_pg_engine(use_pgbouncer=False)
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO catalog.pipeline_runs
                        (source_id, run_date, data_year, stage, status, started_at)
                    VALUES
                        (:source_id, :run_date, :data_year, :stage, 'running', NOW())
                    RETURNING run_id
                """),
                {
                    "source_id": source_id,
                    "run_date": run_date,
                    "data_year": data_year,
                    "stage": stage,
                },
            )
            conn.commit()
            run_id = int(result.scalar())  # type: ignore[arg-type]
            log.info("pipeline_run_started", run_id=run_id, source=source, stage=stage)
            return run_id
    except Exception as e:
        log.warning("record_pipeline_run_failed", source=source, error=str(e))
        return -1


def complete_pipeline_run(
    run_id: int,
    status: str,
    rows_processed: int = 0,
    rows_loaded: int = 0,
    file_hash: str = "",
    file_size_bytes: int = 0,
    duration_seconds: float = 0,
    error_message: str = "",
) -> None:
    """Update a pipeline_runs row with completion status and metrics."""
    if run_id < 0:
        return  # Tracking disabled

    engine = get_pg_engine(use_pgbouncer=False)
    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    UPDATE catalog.pipeline_runs
                    SET status = :status,
                        rows_processed = :rows_processed,
                        rows_loaded = :rows_loaded,
                        file_hash = :file_hash,
                        file_size_bytes = :file_size_bytes,
                        duration_seconds = :duration_seconds,
                        error_message = :error_message,
                        completed_at = NOW()
                    WHERE run_id = :run_id
                """),
                {
                    "run_id": run_id,
                    "status": status,
                    "rows_processed": rows_processed,
                    "rows_loaded": rows_loaded,
                    "file_hash": file_hash,
                    "file_size_bytes": file_size_bytes,
                    "duration_seconds": round(duration_seconds, 2),
                    "error_message": error_message[:4000] if error_message else "",
                },
            )
            conn.commit()
            log.info("pipeline_run_completed", run_id=run_id, status=status, rows_loaded=rows_loaded)
    except Exception as e:
        log.warning("complete_pipeline_run_failed", run_id=run_id, error=str(e))


# ---------------------------------------------------------------------------
# Pipeline failure classification
# ---------------------------------------------------------------------------


def record_pipeline_failure(run_id: int, error: Exception) -> None:
    """Classify and record a pipeline failure to catalog.pipeline_failures."""
    if run_id < 0:
        return

    import subprocess

    import httpx
    import psycopg2

    error_class = type(error).__name__

    if isinstance(error, (httpx.ConnectError, httpx.TimeoutException)):
        error_type = "download"
        is_retryable = True
    elif isinstance(error, httpx.HTTPStatusError):
        error_type = "download"
        is_retryable = error.response.status_code >= 500
    elif isinstance(error, ValueError) and "Validation BLOCKED" in str(error):
        error_type = "validation"
        is_retryable = False
    elif isinstance(error, psycopg2.OperationalError):
        error_type = "load"
        is_retryable = True
    elif isinstance(error, subprocess.CalledProcessError):
        error_type = "transform"
        is_retryable = False
    else:
        error_type = "unknown"
        is_retryable = False

    error_detail = traceback.format_exception(type(error), error, error.__traceback__)
    detail_str = "".join(error_detail)[-4000:]

    engine = get_pg_engine(use_pgbouncer=False)
    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO catalog.pipeline_failures
                        (run_id, error_type, error_class, error_message, error_detail, is_retryable)
                    VALUES
                        (:run_id, :error_type, :error_class, :error_message, :error_detail, :is_retryable)
                """),
                {
                    "run_id": run_id,
                    "error_type": error_type,
                    "error_class": error_class,
                    "error_message": str(error)[:4000],
                    "error_detail": detail_str,
                    "is_retryable": is_retryable,
                },
            )
            conn.commit()
            log.info("pipeline_failure_recorded", run_id=run_id, error_type=error_type, is_retryable=is_retryable)
    except Exception as e:
        log.warning("record_pipeline_failure_failed", run_id=run_id, error=str(e))


# ---------------------------------------------------------------------------
# Validation persistence
# ---------------------------------------------------------------------------


def persist_validation_report(report: ValidationReport, run_id: int) -> None:
    """Write all ValidationResult entries to catalog.validation_runs.

    Maps 1:1 to the table schema from migration 003.
    """
    if run_id < 0 or not report.results:
        return

    engine = get_pg_engine(use_pgbouncer=False)
    try:
        with engine.connect() as conn:
            for r in report.results:
                conn.execute(
                    text("""
                        INSERT INTO catalog.validation_runs
                            (run_id, rule_name, severity, passed, metric_value,
                             threshold, message, rows_affected)
                        VALUES
                            (:run_id, :rule_name, :severity, :passed, :metric_value,
                             :threshold, :message, :rows_affected)
                    """),
                    {
                        "run_id": run_id,
                        "rule_name": r.rule_name,
                        "severity": r.severity,
                        "passed": r.passed,
                        "metric_value": r.metric_value,
                        "threshold": r.threshold,
                        "message": r.message[:4000] if r.message else "",
                        "rows_affected": r.rows_affected,
                    },
                )
            conn.commit()
            log.info("validation_report_persisted", run_id=run_id, source=report.source, checks=len(report.results))
    except Exception as e:
        log.warning("persist_validation_report_failed", run_id=run_id, error=str(e))


# ---------------------------------------------------------------------------
# Quarantine
# ---------------------------------------------------------------------------


def write_quarantine_rows(
    df: pd.DataFrame,
    mask: pd.Series,
    rule_name: str,
    run_id: int,
    source: str,
) -> pd.DataFrame:
    """Move rows matching mask to catalog.quarantine_rows.

    Returns the clean DataFrame (rows NOT matching mask).
    If run tracking is disabled (run_id < 0), returns df with bad rows removed
    but does not write to catalog.
    """
    bad_rows = df.loc[mask]
    clean_df = df.loc[~mask].copy()

    if len(bad_rows) == 0:
        return clean_df

    log.info("quarantine_rows", source=source, rule=rule_name, quarantined=len(bad_rows), kept=len(clean_df))

    if run_id < 0:
        return clean_df

    source_id = _resolve_source_id(source)
    if source_id is None:
        return clean_df

    engine = get_pg_engine(use_pgbouncer=False)
    try:
        # Batch quarantine rows in chunks to avoid huge single inserts
        chunk_size = 1000
        with engine.connect() as conn:
            for start in range(0, len(bad_rows), chunk_size):
                chunk = bad_rows.iloc[start : start + chunk_size]
                rows_json = chunk.to_json(orient="records", date_format="iso")
                parsed = json.loads(rows_json)

                for row_data in parsed:
                    conn.execute(
                        text("""
                            INSERT INTO catalog.quarantine_rows
                                (run_id, source_id, rule_name, row_data, failure_reason)
                            VALUES
                                (:run_id, :source_id, :rule_name, :row_data, :failure_reason)
                        """),
                        {
                            "run_id": run_id,
                            "source_id": source_id,
                            "rule_name": rule_name,
                            "row_data": json.dumps(row_data),
                            "failure_reason": f"Failed validation rule: {rule_name}",
                        },
                    )
            conn.commit()
    except Exception as e:
        log.warning("write_quarantine_rows_failed", source=source, error=str(e))

    return clean_df


# ---------------------------------------------------------------------------
# Data freshness
# ---------------------------------------------------------------------------


def update_data_freshness(
    source: str,
    data_year: int | None = None,
    file_hash: str = "",
) -> None:
    """Upsert catalog.data_freshness with latest hash and timestamps."""
    source_id = _resolve_source_id(source)
    if source_id is None:
        return

    engine = get_pg_engine(use_pgbouncer=False)
    try:
        with engine.connect() as conn:
            # Check if row exists
            result = conn.execute(
                text("""
                    SELECT freshness_id FROM catalog.data_freshness
                    WHERE source_id = :source_id
                      AND (data_year = :data_year OR (data_year IS NULL AND :data_year IS NULL))
                """),
                {"source_id": source_id, "data_year": data_year},
            )
            existing = result.fetchone()

            if existing:
                conn.execute(
                    text("""
                        UPDATE catalog.data_freshness
                        SET latest_file_hash = :file_hash,
                            last_loaded_at = NOW(),
                            last_changed_at = NOW(),
                            last_checked_at = NOW(),
                            is_stale = false,
                            staleness_days = 0,
                            updated_at = NOW()
                        WHERE freshness_id = :freshness_id
                    """),
                    {"file_hash": file_hash, "freshness_id": existing[0]},
                )
            else:
                conn.execute(
                    text("""
                        INSERT INTO catalog.data_freshness
                            (source_id, data_year, latest_file_hash,
                             last_loaded_at, last_changed_at, last_checked_at,
                             is_stale, staleness_days)
                        VALUES
                            (:source_id, :data_year, :file_hash,
                             NOW(), NOW(), NOW(), false, 0)
                    """),
                    {
                        "source_id": source_id,
                        "data_year": data_year,
                        "file_hash": file_hash,
                    },
                )
            conn.commit()
            log.info(
                "data_freshness_updated", source=source, data_year=data_year, hash=file_hash[:16] if file_hash else ""
            )
    except Exception as e:
        log.warning("update_data_freshness_failed", source=source, error=str(e))
