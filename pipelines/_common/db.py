"""Database connection utilities for PostgreSQL and DuckDB.

Provides connection factories, bulk COPY operations, and DuckDB Parquet reading.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import duckdb
import pandas as pd
import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from pipelines._common.config import get_database_settings, get_pipeline_settings
from pipelines._common.logging import get_logger

log = get_logger(stage="db")


# ---------------------------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------------------------

def get_pg_engine(use_pgbouncer: bool = True) -> Engine:
    """Create a SQLAlchemy engine for PostgreSQL.

    Args:
        use_pgbouncer: If True, connect through PgBouncer (recommended for apps).
    """
    settings = get_database_settings()
    dsn = settings.pgbouncer_dsn if use_pgbouncer else settings.dsn
    return create_engine(dsn, pool_pre_ping=True)


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
) -> int:
    """Load a DataFrame into PostgreSQL using bulk insert.

    For tables < 1M rows, uses pandas to_sql with multi-row INSERT.
    For larger tables, uses psycopg2 COPY via StringIO for speed.

    Returns the number of rows loaded.
    """
    engine = get_pg_engine(use_pgbouncer=False)

    if len(df) < 1_000_000:
        df.to_sql(table_name, engine, schema=schema, if_exists=if_exists, index=False, method="multi", chunksize=10_000)
    else:
        # Use COPY for large datasets
        import io

        if if_exists == "replace":
            with engine.connect() as conn:
                conn.execute(text(f"TRUNCATE TABLE {schema}.{table_name}"))
                conn.commit()

        with get_pg_connection() as conn:
            buf = io.StringIO()
            df.to_csv(buf, index=False, header=False, sep="\t", na_rep="\\N")
            buf.seek(0)
            with conn.cursor() as cur:
                cur.copy_expert(
                    f"COPY {schema}.{table_name} FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\N')",
                    buf,
                )

    log.info("pg_load_complete", table=f"{schema}.{table_name}", rows=len(df))
    return len(df)


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


def write_parquet(df: pd.DataFrame, path: str | Path) -> Path:
    """Write a DataFrame to Parquet using DuckDB (ZSTD compression).

    Creates parent directories if needed. Returns the output path.
    """
    settings = get_pipeline_settings()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_duckdb_connection()
    conn.register("df", df)
    conn.execute(
        f"COPY df TO '{path}' (FORMAT PARQUET, COMPRESSION '{settings.parquet.compression}', "
        f"ROW_GROUP_SIZE {settings.parquet.row_group_size})"
    )

    log.info("parquet_written", path=str(path), rows=len(df), compression=settings.parquet.compression)
    return path
