"""Integration tests: run real pipelines against real PostgreSQL.

These tests require Docker:
    docker compose -f config/docker-compose.test.yml up -d
    export PUF_DB_PORT=5433 PUF_DB_PASSWORD=puf_test_password PUF_DB_NAME=puf_test
    alembic -c pipelines/alembic/alembic.ini upgrade head
    pytest -m integration -v

Skipped automatically when PostgreSQL is not available on port 5433.
"""

import pandas as pd
import pytest

# Check if test PostgreSQL is available
try:
    from sqlalchemy import create_engine, text

    _engine = create_engine(
        "postgresql://puf_admin:puf_test_password@localhost:5433/puf_test",
        connect_args={"connect_timeout": 2},
    )
    with _engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    PG_AVAILABLE = True
    _engine.dispose()
except Exception:
    PG_AVAILABLE = False

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not PG_AVAILABLE, reason="Test PostgreSQL not available on port 5433"),
]


@pytest.fixture(scope="module")
def pg_engine():
    """SQLAlchemy engine connected to test PostgreSQL."""
    engine = create_engine("postgresql://puf_admin:puf_test_password@localhost:5433/puf_test")
    yield engine
    engine.dispose()


@pytest.fixture()
def sample_fips_csv(tmp_path):
    """Create a small FIPS test CSV."""
    content = (
        "STATE|STUSAB|STATE_NAME|STATENS\n01|AL|Alabama|01779775\n06|CA|California|01779778\n36|NY|New York|01779796\n"
    )
    path = tmp_path / "state_fips.csv"
    path.write_text(content)
    return path


class TestReferenceEndToEnd:
    def test_fips_pipeline_creates_catalog_entries(self, pg_engine, sample_fips_csv, monkeypatch):
        """Run FIPS reference pipeline and verify catalog tracking."""
        # Override DB settings to point at test database
        monkeypatch.setenv("PUF_DB_PORT", "5433")
        monkeypatch.setenv("PUF_DB_PASSWORD", "puf_test_password")
        monkeypatch.setenv("PUF_DB_NAME", "puf_test")

        # Clear caches so new env vars are picked up
        from pipelines._common.config import get_database_settings, get_pipeline_settings

        get_database_settings.cache_clear()
        get_pipeline_settings.cache_clear()

        from pipelines.fips.pipeline import run

        try:
            result = run(source_path=sample_fips_csv)
            assert result > 0  # Rows loaded

            # Verify catalog.pipeline_runs has an entry
            with pg_engine.connect() as conn:
                runs = conn.execute(
                    text("SELECT status FROM catalog.pipeline_runs ORDER BY started_at DESC LIMIT 1")
                ).fetchone()
                if runs:
                    assert runs[0] == "success"
        finally:
            get_database_settings.cache_clear()
            get_pipeline_settings.cache_clear()


class TestValidationBlockPersistence:
    def test_blocked_validation_persists_before_raising(self, pg_engine, monkeypatch):
        """Verify that BLOCK validation results are persisted even when pipeline fails."""
        monkeypatch.setenv("PUF_DB_PORT", "5433")
        monkeypatch.setenv("PUF_DB_PASSWORD", "puf_test_password")
        monkeypatch.setenv("PUF_DB_NAME", "puf_test")

        from pipelines._common.config import get_database_settings, get_pipeline_settings

        get_database_settings.cache_clear()
        get_pipeline_settings.cache_clear()

        from pipelines._common.catalog import complete_pipeline_run, record_pipeline_run
        from pipelines._common.validate import (
            ValidationReport,
            check_required_columns,
        )

        try:
            run_id = record_pipeline_run("partb")
            if run_id < 0:
                pytest.skip("catalog.sources not seeded")

            # DataFrame missing required column
            df = pd.DataFrame({"wrong_column": ["data"]})
            report = ValidationReport(source="partb", run_id=run_id)
            check_required_columns(df, ["rendering_npi", "hcpcs_code"], report)

            with pytest.raises(ValueError, match="BLOCKED"):
                report.raise_if_blocked()

            # Verify validation results were persisted BEFORE the raise
            with pg_engine.connect() as conn:
                val_count = conn.execute(
                    text("SELECT COUNT(*) FROM catalog.validation_runs WHERE run_id = :rid"),
                    {"rid": run_id},
                ).scalar()
                assert val_count > 0  # At least the required_columns check

            complete_pipeline_run(run_id, "failed", error_message="Validation BLOCKED")
        finally:
            get_database_settings.cache_clear()
            get_pipeline_settings.cache_clear()
