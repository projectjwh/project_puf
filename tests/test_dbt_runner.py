"""Tests for pipelines._common.dbt_runner."""

from unittest.mock import patch

import pytest

from pipelines._common.dbt_runner import (
    DbtErrorType,
    DbtRunResult,
    ModelResult,
    _parse_json_logs,
    classify_error,
    run_dbt,
)

# ---------------------------------------------------------------------------
# classify_error
# ---------------------------------------------------------------------------


class TestClassifyError:
    def test_compile_error(self):
        assert classify_error("Compilation Error in model", "") == DbtErrorType.COMPILE

    def test_compile_error_yml(self):
        assert classify_error("", "YML Error in schema.yml") == DbtErrorType.COMPILE

    def test_runtime_error(self):
        assert classify_error("Runtime Error in model foo", "") == DbtErrorType.RUNTIME

    def test_database_error(self):
        assert classify_error("Database Error: relation does not exist", "") == DbtErrorType.RUNTIME

    def test_test_failure(self):
        assert classify_error("", "Failure in test unique_model_id") == DbtErrorType.TEST

    def test_unknown_error(self):
        assert classify_error("something went wrong", "oh no") == DbtErrorType.UNKNOWN

    def test_compile_takes_precedence_over_runtime(self):
        # When both markers appear, compile is checked first
        assert classify_error("Compilation Error and Runtime Error", "") == DbtErrorType.COMPILE


# ---------------------------------------------------------------------------
# _parse_json_logs
# ---------------------------------------------------------------------------


class TestParseJsonLogs:
    def test_parses_model_success(self):
        log_line = (
            '{"data": {"node_info": {"unique_id": "model.puf.stg_partb", '
            '"node_status": "success", "execution_time": 1.23}, '
            '"description": "OK created"}}'
        )
        results = _parse_json_logs(log_line)
        assert len(results) == 1
        assert results[0].unique_id == "model.puf.stg_partb"
        assert results[0].status == "success"
        assert results[0].execution_time == pytest.approx(1.23)

    def test_parses_model_error(self):
        log_line = (
            '{"data": {"node_info": {"unique_id": "model.puf.int_provider", '
            '"node_status": "error", "execution_time": 0.5}, '
            '"description": "relation missing"}}'
        )
        results = _parse_json_logs(log_line)
        assert len(results) == 1
        assert results[0].status == "error"
        assert results[0].message == "relation missing"

    def test_ignores_non_json_lines(self):
        raw = "Running dbt...\n{bad json\n"
        results = _parse_json_logs(raw)
        assert results == []

    def test_ignores_lines_without_node_status(self):
        raw = '{"data": {"description": "Found 10 models"}}\n'
        results = _parse_json_logs(raw)
        assert results == []

    def test_multiple_models(self):
        lines = "\n".join(
            [
                '{"data": {"node_info": {"unique_id": "model.a", "node_status": "success", "execution_time": 1.0}, "description": ""}}',
                '{"data": {"node_info": {"unique_id": "model.b", "node_status": "skipped", "execution_time": 0.0}, "description": ""}}',
                '{"data": {"node_info": {"unique_id": "model.c", "node_status": "error", "execution_time": 2.5}, "description": "fail"}}',
            ]
        )
        results = _parse_json_logs(lines)
        assert len(results) == 3
        statuses = [r.status for r in results]
        assert statuses == ["success", "skipped", "error"]


# ---------------------------------------------------------------------------
# DbtRunResult.to_dict
# ---------------------------------------------------------------------------


class TestDbtRunResult:
    def test_to_dict_success(self):
        result = DbtRunResult(
            success=True,
            models=[
                ModelResult(unique_id="model.a", status="success", execution_time=1.0),
                ModelResult(unique_id="model.b", status="success", execution_time=2.0),
            ],
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["models_passed"] == 2
        assert d["models_errored"] == 0
        assert d["error_type"] is None
        assert len(d["model_details"]) == 2

    def test_to_dict_failure(self):
        result = DbtRunResult(
            success=False,
            models=[
                ModelResult(unique_id="model.a", status="success"),
                ModelResult(unique_id="model.b", status="error", message="boom"),
            ],
            error_type=DbtErrorType.RUNTIME,
            error_message="Database Error",
        )
        d = result.to_dict()
        assert d["success"] is False
        assert d["models_passed"] == 1
        assert d["models_errored"] == 1
        assert d["error_type"] == "runtime"
        assert d["error_message"] == "Database Error"


# ---------------------------------------------------------------------------
# run_dbt (mocked subprocess)
# ---------------------------------------------------------------------------


class TestRunDbt:
    @patch("pipelines._common.dbt_runner.subprocess.run")
    def test_successful_run(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            '{"data": {"node_info": {"unique_id": "model.puf.stg_partb", '
            '"node_status": "success", "execution_time": 1.0}, "description": "OK"}}\n'
        )
        mock_run.return_value.stderr = ""

        result = run_dbt(select="tag:intermediate")
        assert result["success"] is True
        assert result["models_passed"] == 1
        assert result["error_type"] is None

    @patch("pipelines._common.dbt_runner.subprocess.run")
    def test_compile_error(self, mock_run):
        mock_run.return_value.returncode = 2
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Compilation Error in model foo"

        result = run_dbt()
        assert result["success"] is False
        assert result["error_type"] == "compile"

    @patch("pipelines._common.dbt_runner.subprocess.run")
    def test_runtime_error(self, mock_run):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Database Error: relation 'stg_partb' does not exist"

        result = run_dbt()
        assert result["success"] is False
        assert result["error_type"] == "runtime"

    @patch("pipelines._common.dbt_runner.subprocess.run")
    def test_test_failure(self, mock_run):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Failure in test unique_model_id"

        result = run_dbt()
        assert result["success"] is False
        assert result["error_type"] == "test"

    @patch("pipelines._common.dbt_runner.subprocess.run")
    def test_unknown_error(self, mock_run):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Something unexpected happened"

        result = run_dbt()
        assert result["success"] is False
        assert result["error_type"] == "unknown"

    @patch("pipelines._common.dbt_runner.subprocess.run")
    def test_command_includes_json_log_format(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""

        run_dbt(select="tag:mart")
        cmd = mock_run.call_args[0][0]
        assert "--log-format" in cmd
        assert "json" in cmd
        assert "--select" in cmd
        assert "tag:mart" in cmd

    @patch("pipelines._common.dbt_runner.subprocess.run")
    def test_returns_expected_keys(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""

        result = run_dbt()
        expected_keys = {
            "success",
            "models_passed",
            "models_errored",
            "models_skipped",
            "error_type",
            "error_message",
            "model_details",
        }
        assert set(result.keys()) == expected_keys

    @patch("pipelines._common.dbt_runner.subprocess.run")
    def test_truncates_long_error_messages(self, mock_run):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Database Error " + "x" * 3000

        result = run_dbt()
        assert result["success"] is False
        # Error message should be truncated
        assert len(result["error_message"]) < 3000
