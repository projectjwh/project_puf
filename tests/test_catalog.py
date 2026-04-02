"""Tests for pipelines._common.catalog module.

All tests mock the database layer — these are unit tests, not integration tests.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd

from pipelines._common.validate import ValidationReport, ValidationResult

# ---------------------------------------------------------------------------
# record_pipeline_run
# ---------------------------------------------------------------------------


class TestRecordPipelineRun:
    @patch("pipelines._common.catalog._resolve_source_id", return_value=1)
    @patch("pipelines._common.catalog.get_pg_engine")
    def test_returns_run_id_on_success(self, mock_engine, mock_resolve):
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 42
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.return_value.connect.return_value = mock_conn

        from pipelines._common.catalog import record_pipeline_run

        run_id = record_pipeline_run("partb", date(2026, 4, 1), 2024, "acquire")
        assert run_id == 42

    @patch("pipelines._common.catalog._resolve_source_id", return_value=None)
    def test_returns_negative_when_source_not_found(self, mock_resolve):
        from pipelines._common.catalog import record_pipeline_run

        run_id = record_pipeline_run("nonexistent", date(2026, 4, 1))
        assert run_id == -1


# ---------------------------------------------------------------------------
# complete_pipeline_run
# ---------------------------------------------------------------------------


class TestCompletePipelineRun:
    @patch("pipelines._common.catalog.get_pg_engine")
    def test_skips_when_run_id_negative(self, mock_engine):
        from pipelines._common.catalog import complete_pipeline_run

        complete_pipeline_run(-1, "success")
        mock_engine.assert_not_called()

    @patch("pipelines._common.catalog.get_pg_engine")
    def test_updates_run_on_success(self, mock_engine):
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.return_value.connect.return_value = mock_conn

        from pipelines._common.catalog import complete_pipeline_run

        complete_pipeline_run(42, "success", rows_loaded=1000, duration_seconds=5.5)
        mock_conn.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# persist_validation_report
# ---------------------------------------------------------------------------


class TestPersistValidationReport:
    @patch("pipelines._common.catalog.get_pg_engine")
    def test_persists_all_results(self, mock_engine):
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.return_value.connect.return_value = mock_conn

        report = ValidationReport(source="test")
        report.results = [
            ValidationResult("npi_not_null", "BLOCK", True, "0", "0"),
            ValidationResult("row_count_range", "WARN", False, "5000", "[7000, 10000]", "Row count too low", 5000),
        ]

        from pipelines._common.catalog import persist_validation_report

        persist_validation_report(report, run_id=42)

        # One INSERT per result
        assert mock_conn.execute.call_count == 2
        mock_conn.commit.assert_called_once()

    def test_skips_when_run_id_negative(self):
        report = ValidationReport(source="test")
        report.results = [ValidationResult("test_rule", "WARN", True)]

        from pipelines._common.catalog import persist_validation_report

        # Should not raise
        persist_validation_report(report, run_id=-1)

    def test_skips_when_no_results(self):
        report = ValidationReport(source="test")

        from pipelines._common.catalog import persist_validation_report

        persist_validation_report(report, run_id=42)


# ---------------------------------------------------------------------------
# write_quarantine_rows
# ---------------------------------------------------------------------------


class TestWriteQuarantineRows:
    def test_returns_clean_df_when_no_bad_rows(self):
        df = pd.DataFrame({"npi": ["1234567890", "0987654321"], "name": ["A", "B"]})
        mask = pd.Series([False, False])

        from pipelines._common.catalog import write_quarantine_rows

        clean = write_quarantine_rows(df, mask, "test_rule", -1, "test")
        assert len(clean) == 2

    def test_removes_bad_rows_from_result(self):
        df = pd.DataFrame({"npi": ["1234567890", "BAD", "0987654321"], "name": ["A", "B", "C"]})
        mask = pd.Series([False, True, False])

        from pipelines._common.catalog import write_quarantine_rows

        clean = write_quarantine_rows(df, mask, "test_rule", -1, "test")
        assert len(clean) == 2
        assert "BAD" not in clean["npi"].values

    def test_handles_all_rows_bad(self):
        df = pd.DataFrame({"npi": ["BAD1", "BAD2"], "name": ["A", "B"]})
        mask = pd.Series([True, True])

        from pipelines._common.catalog import write_quarantine_rows

        clean = write_quarantine_rows(df, mask, "test_rule", -1, "test")
        assert len(clean) == 0

    @patch("pipelines._common.catalog._resolve_source_id", return_value=1)
    @patch("pipelines._common.catalog.get_pg_engine")
    def test_writes_to_catalog_when_run_id_valid(self, mock_engine, mock_resolve):
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.return_value.connect.return_value = mock_conn

        df = pd.DataFrame({"npi": ["1234567890", "BAD"], "name": ["A", "B"]})
        mask = pd.Series([False, True])

        from pipelines._common.catalog import write_quarantine_rows

        clean = write_quarantine_rows(df, mask, "npi_format", run_id=42, source="test")
        assert len(clean) == 1
        # Should have written 1 quarantine row
        assert mock_conn.execute.call_count >= 1
        mock_conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# update_data_freshness
# ---------------------------------------------------------------------------


class TestUpdateDataFreshness:
    @patch("pipelines._common.catalog._resolve_source_id", return_value=None)
    def test_skips_when_source_not_found(self, mock_resolve):
        from pipelines._common.catalog import update_data_freshness

        # Should not raise
        update_data_freshness("nonexistent", file_hash="abc123")

    @patch("pipelines._common.catalog._resolve_source_id", return_value=1)
    @patch("pipelines._common.catalog.get_pg_engine")
    def test_inserts_when_no_existing_record(self, mock_engine, mock_resolve):
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        # First call (SELECT) returns no rows, second call (INSERT)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_conn.execute.return_value = mock_result
        mock_engine.return_value.connect.return_value = mock_conn

        from pipelines._common.catalog import update_data_freshness

        update_data_freshness("partb", data_year=2024, file_hash="abc123")

        # SELECT + INSERT = 2 execute calls
        assert mock_conn.execute.call_count == 2
        mock_conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# record_pipeline_failure
# ---------------------------------------------------------------------------


class TestRecordPipelineFailure:
    @patch("pipelines._common.catalog.get_pg_engine")
    def test_skips_when_run_id_negative(self, mock_engine):
        from pipelines._common.catalog import record_pipeline_failure

        record_pipeline_failure(-1, ValueError("test"))
        mock_engine.assert_not_called()

    @patch("pipelines._common.catalog.get_pg_engine")
    def test_classifies_validation_error(self, mock_engine):
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.return_value.connect.return_value = mock_conn

        from pipelines._common.catalog import record_pipeline_failure

        error = ValueError("Validation BLOCKED for partb: npi_not_null: 100 null values")
        record_pipeline_failure(42, error)

        mock_conn.execute.assert_called_once()
        # Verify the error_type parameter in the SQL call
        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        assert params["error_type"] == "validation"
        assert params["is_retryable"] is False
