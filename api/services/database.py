"""Dual-engine database service: PostgreSQL + DuckDB.

Query routing strategy:
  - PostgreSQL: single-row lookups, filtered lists with pagination, small GROUP BYs
  - DuckDB:     large aggregations on Parquet, cross-year trends, full-table scans

Both engines are initialized at startup and shared via FastAPI dependency injection.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from pipelines._common.config import get_database_settings, get_pipeline_settings

_pg_engine: Engine | None = None
_duckdb_conn: duckdb.DuckDBPyConnection | None = None


def get_pg_engine() -> Engine:
    """Get or create the PostgreSQL engine (singleton)."""
    global _pg_engine
    if _pg_engine is None:
        db = get_database_settings()
        url = f"postgresql://{db.user}:{db.password}@{db.host}:{db.port}/{db.name}"
        _pg_engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _pg_engine


def get_duckdb_conn() -> duckdb.DuckDBPyConnection:
    """Get or create the DuckDB connection (singleton, read-only on Parquet)."""
    global _duckdb_conn
    if _duckdb_conn is None:
        _duckdb_conn = duckdb.connect(database=":memory:", read_only=False)
        # Register Parquet directories for mart tables
        settings = get_pipeline_settings()
        mart_dir = Path(settings.storage.processed_base) / "mart"
        if mart_dir.exists():
            for parquet_dir in mart_dir.iterdir():
                if parquet_dir.is_dir():
                    parquet_files = list(parquet_dir.glob("*.parquet"))
                    if parquet_files:
                        _duckdb_conn.execute(
                            f"CREATE VIEW IF NOT EXISTS {parquet_dir.name} AS "
                            f"SELECT * FROM read_parquet('{parquet_files[0]}')"
                        )
    return _duckdb_conn


def query_pg(sql: str, params: dict[str, Any] | None = None) -> list[dict]:
    """Execute a query against PostgreSQL, return list of dicts."""
    engine = get_pg_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in result.fetchall()]


def query_pg_df(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    """Execute a query against PostgreSQL, return DataFrame."""
    engine = get_pg_engine()
    return pd.read_sql(text(sql), engine, params=params or {})


def query_duckdb(sql: str) -> list[dict]:
    """Execute a query against DuckDB (Parquet), return list of dicts."""
    conn = get_duckdb_conn()
    result = conn.execute(sql)
    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


def query_duckdb_df(sql: str) -> pd.DataFrame:
    """Execute a query against DuckDB, return DataFrame."""
    conn = get_duckdb_conn()
    return conn.execute(sql).fetchdf()


def close_all() -> None:
    """Close all database connections."""
    global _pg_engine, _duckdb_conn
    if _pg_engine is not None:
        _pg_engine.dispose()
        _pg_engine = None
    if _duckdb_conn is not None:
        _duckdb_conn.close()
        _duckdb_conn = None
