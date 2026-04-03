"""Database connection utilities for PostgreSQL and DuckDB.

Provides connection factories, bulk COPY operations, and DuckDB Parquet reading.
"""

import re
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from pipelines._common.config import get_database_settings, get_pipeline_settings
from pipelines._common.logging import get_logger

log = get_logger(stage="db")

_SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


# ---------------------------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------------------------


_engines: dict[bool, Engine] = {}


def get_pg_engine(use_pgbouncer: bool = True) -> Engine:
    """Get or create a SQLAlchemy engine for PostgreSQL (singleton per mode).

    Args:
        use_pgbouncer: If True, connect through PgBouncer (recommended for apps).
    """
    if use_pgbouncer not in _engines:
        settings = get_database_settings()
        dsn = settings.pgbouncer_dsn if use_pgbouncer else settings.dsn
        _engines[use_pgbouncer] = create_engine(dsn, pool_pre_ping=True)
    return _engines[use_pgbouncer]


@contextmanager
def get_pg_connection(use_pgbouncer: bool = False) -> Generator[Any, None, None]:
    """Get a raw psycopg2 connection for COPY and bulk operations.

    Use direct connection (not PgBouncer) for COPY commands, since
    COPY requires a persistent connection that PgBouncer transaction
    mode may interrupt.
    """
    settings = get_database_settings()
    conn = psycopg2.connect(
        host=settings.host,
        port=settings.pgbouncer_port if use_pgbouncer else settings.port,
        dbname=settings.database,
        user=settings.user,
        password=settings.password,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_sql(sql: str, params: dict[str, Any] | None = None, schema: str | None = None) -> None:
    """Execute a SQL statement against PostgreSQL."""
    engine = get_pg_engine(use_pgbouncer=False)
    with engine.connect() as conn:
        if schema:
            conn.execute(text(f"SET search_path TO {schema}"))
        conn.execute(text(sql), params or {})
        conn.commit()


def copy_dataframe_to_pg(
    df: pd.DataFrame,
    table_name: str,
    schema: str,
    if_exists: str = "replace",
    copy_chunk_size: int = 500_000,
) -> int:
    """Load a DataFrame into PostgreSQL using bulk insert.

    For tables < 1M rows, uses pandas to_sql with multi-row INSERT.
    For larger tables, uses chunked psycopg2 COPY with savepoints so that
    a single failing chunk doesn't roll back the entire load.

    Returns the number of rows actually loaded (may be < len(df) if chunks failed).
    """
    engine = get_pg_engine(use_pgbouncer=False)

    # Validate identifiers to prevent SQL injection
    if not _SAFE_IDENTIFIER.match(table_name):
        raise ValueError(f"Unsafe table name: {table_name!r}")
    if not _SAFE_IDENTIFIER.match(schema):
        raise ValueError(f"Unsafe schema name: {schema!r}")

    if len(df) < 1_000_000:
        df.to_sql(
            table_name,
            engine,
            schema=schema,
            if_exists=if_exists,
            index=False,
            method="multi",
            chunksize=10_000,
        )
        rows_loaded = len(df)
    else:
        import io

        if if_exists == "replace":
            with engine.connect() as conn:
                conn.execute(text(f"TRUNCATE TABLE {schema}.{table_name}"))
                conn.commit()

        rows_loaded = 0
        failed_chunks = 0
        total_chunks = (len(df) + copy_chunk_size - 1) // copy_chunk_size

        with get_pg_connection() as conn, conn.cursor() as cur:
            for i in range(0, len(df), copy_chunk_size):
                chunk = df.iloc[i : i + copy_chunk_size]
                chunk_num = i // copy_chunk_size + 1
                savepoint = f"chunk_{chunk_num}"

                try:
                    cur.execute(f"SAVEPOINT {savepoint}")
                    buf = io.StringIO()
                    chunk.to_csv(buf, index=False, header=False, sep="\t", na_rep="\\N")
                    buf.seek(0)
                    cur.copy_expert(
                        f"COPY {schema}.{table_name} FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\N')",
                        buf,
                    )
                    cur.execute(f"RELEASE SAVEPOINT {savepoint}")
                    rows_loaded += len(chunk)
                except Exception as e:
                    cur.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                    failed_chunks += 1
                    log.warning(
                        "copy_chunk_failed",
                        table=f"{schema}.{table_name}",
                        chunk=chunk_num,
                        total_chunks=total_chunks,
                        rows_in_chunk=len(chunk),
                        error=str(e)[:500],
                    )

        if failed_chunks > 0:
            log.warning(
                "copy_partial_load",
                table=f"{schema}.{table_name}",
                rows_loaded=rows_loaded,
                rows_attempted=len(df),
                failed_chunks=failed_chunks,
                total_chunks=total_chunks,
            )

    log.info("pg_load_complete", table=f"{schema}.{table_name}", rows=rows_loaded)
    return rows_loaded


def query_pg(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    """Execute a SELECT query and return results as a DataFrame."""
    engine = get_pg_engine()
    return pd.read_sql(text(sql), engine, params=params or {})


# ---------------------------------------------------------------------------
# DuckDB
# ---------------------------------------------------------------------------


def get_duckdb_connection() -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB connection."""
    conn = duckdb.connect()
    return conn


def read_parquet(path: str | Path, sql: str | None = None) -> pd.DataFrame:
    """Read a Parquet file using DuckDB, optionally applying a SQL filter.

    Args:
        path: Path to Parquet file or glob pattern (e.g., "data/processed/partb/*/partb_utilization.parquet").
        sql: Optional SQL query. Use 'df' as the table reference.
             E.g., "SELECT * FROM df WHERE data_year = 2022"

    Returns:
        DataFrame with query results.
    """
    conn = get_duckdb_connection()
    path_str = str(path)

    if sql:
        # Register the parquet as a view, then query it
        conn.execute(f"CREATE OR REPLACE VIEW df AS SELECT * FROM read_parquet('{path_str}')")
        return conn.execute(sql).fetchdf()
    else:
        return conn.execute(f"SELECT * FROM read_parquet('{path_str}')").fetchdf()


def write_parquet(
    df: pd.DataFrame,
    path: str | Path,
    metadata: dict[str, str] | None = None,
) -> Path:
    """Write a DataFrame to Parquet with ZSTD compression and optional lineage metadata.

    Creates parent directories if needed. Returns the output path.

    Args:
        df: DataFrame to write.
        path: Output path.
        metadata: Optional key-value pairs to embed in Parquet file metadata
                  (e.g., puf.source_name, puf.pipeline_run_id).
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    settings = get_pipeline_settings()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    table = pa.Table.from_pandas(df)

    # Embed lineage metadata if provided
    if metadata:
        existing_meta = table.schema.metadata or {}
        merged = {**existing_meta, **{k.encode(): v.encode() for k, v in metadata.items()}}
        table = table.replace_schema_metadata(merged)

    pq.write_table(
        table,
        str(path),
        compression=settings.parquet.compression,
        row_group_size=settings.parquet.row_group_size,
    )

    log.info(
        "parquet_written",
        path=str(path),
        rows=len(df),
        compression=settings.parquet.compression,
        has_metadata=bool(metadata),
    )
    return path
