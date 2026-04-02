"""Tests for catalog circuit breaker."""

from unittest.mock import MagicMock, patch


class TestCheckCircuitBreaker:
    @patch("pipelines._common.catalog._resolve_source_id", return_value=None)
    def test_returns_false_when_source_not_found(self, mock_resolve):
        from pipelines._common.catalog import check_circuit_breaker

        assert check_circuit_breaker("unknown") is False

    @patch("pipelines._common.catalog._resolve_source_id", return_value=1)
    @patch("pipelines._common.catalog.get_pg_engine")
    def test_returns_false_when_insufficient_history(self, mock_engine, mock_resolve):
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("success",), ("failed",)]  # Only 2 runs
        mock_conn.execute.return_value = mock_result
        mock_engine.return_value.connect.return_value = mock_conn

        from pipelines._common.catalog import check_circuit_breaker

        assert check_circuit_breaker("partb", max_consecutive_failures=5) is False

    @patch("pipelines._common.catalog._resolve_source_id", return_value=1)
    @patch("pipelines._common.catalog.get_pg_engine")
    def test_returns_true_when_all_failed(self, mock_engine, mock_resolve):
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("failed",)] * 5
        mock_conn.execute.return_value = mock_result
        mock_engine.return_value.connect.return_value = mock_conn

        from pipelines._common.catalog import check_circuit_breaker

        assert check_circuit_breaker("partb", max_consecutive_failures=5) is True

    @patch("pipelines._common.catalog._resolve_source_id", return_value=1)
    @patch("pipelines._common.catalog.get_pg_engine")
    def test_returns_false_when_one_success_in_window(self, mock_engine, mock_resolve):
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("failed",),
            ("failed",),
            ("success",),  # One success breaks the streak
            ("failed",),
            ("failed",),
        ]
        mock_conn.execute.return_value = mock_result
        mock_engine.return_value.connect.return_value = mock_conn

        from pipelines._common.catalog import check_circuit_breaker

        assert check_circuit_breaker("partb", max_consecutive_failures=5) is False

    @patch("pipelines._common.catalog._resolve_source_id", return_value=1)
    @patch("pipelines._common.catalog.get_pg_engine")
    def test_configurable_threshold(self, mock_engine, mock_resolve):
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("failed",)] * 3
        mock_conn.execute.return_value = mock_result
        mock_engine.return_value.connect.return_value = mock_conn

        from pipelines._common.catalog import check_circuit_breaker

        assert check_circuit_breaker("partb", max_consecutive_failures=3) is True

    @patch("pipelines._common.catalog._resolve_source_id", return_value=1)
    @patch("pipelines._common.catalog.get_pg_engine")
    def test_returns_false_on_db_error(self, mock_engine, mock_resolve):
        mock_engine.return_value.connect.side_effect = Exception("db down")

        from pipelines._common.catalog import check_circuit_breaker

        # Fail open — allow run even if check fails
        assert check_circuit_breaker("partb") is False
