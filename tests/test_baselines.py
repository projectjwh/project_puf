"""Tests for pipelines._common.baselines."""

from unittest.mock import patch

import pandas as pd

from pipelines._common.baselines import check_against_baseline, compute_baselines
from pipelines._common.validate import ValidationReport


class TestComputeBaselines:
    @patch("pipelines._common.db.query_pg")
    def test_returns_empty_when_no_history(self, mock_query):
        mock_query.return_value = pd.DataFrame()
        result = compute_baselines("partb")
        assert result == {}

    @patch("pipelines._common.db.query_pg")
    def test_returns_stats_when_history_exists(self, mock_query):
        mock_query.return_value = pd.DataFrame(
            {
                "rule_name": ["row_count_range"],
                "baseline_mean": [9500000.0],
                "baseline_stddev": [200000.0],
                "baseline_min": [9100000.0],
                "baseline_max": [9900000.0],
                "sample_count": [8],
            }
        )
        result = compute_baselines("partb")
        assert "row_count_range" in result
        assert result["row_count_range"]["mean"] == 9500000.0
        assert result["row_count_range"]["stddev"] == 200000.0
        assert result["row_count_range"]["sample_count"] == 8

    @patch("pipelines._common.db.query_pg")
    def test_returns_empty_on_db_error(self, mock_query):
        mock_query.side_effect = Exception("connection refused")
        result = compute_baselines("partb")
        assert result == {}

    @patch("pipelines._common.db.query_pg")
    def test_multiple_metrics(self, mock_query):
        mock_query.return_value = pd.DataFrame(
            {
                "rule_name": ["row_count_range", "npi_null_rate"],
                "baseline_mean": [9500000.0, 0.001],
                "baseline_stddev": [200000.0, 0.0005],
                "baseline_min": [9100000.0, 0.0005],
                "baseline_max": [9900000.0, 0.002],
                "sample_count": [8, 5],
            }
        )
        result = compute_baselines("partb")
        assert len(result) == 2


class TestCheckAgainstBaseline:
    def test_passes_when_within_threshold(self):
        report = ValidationReport(source="test")
        baselines = {
            "row_count_range": {"mean": 9500000, "stddev": 200000, "min": 9100000, "max": 9900000, "sample_count": 8}
        }
        check_against_baseline({"row_count_range": 9600000}, baselines, report, z_threshold=2.0)
        assert report.passed
        assert report.results[0].passed

    def test_warns_when_exceeds_threshold(self):
        report = ValidationReport(source="test")
        baselines = {
            "row_count_range": {"mean": 9500000, "stddev": 200000, "min": 9100000, "max": 9900000, "sample_count": 8}
        }
        # 5M is (9.5M - 5M) / 200K = 22.5 stddevs away
        check_against_baseline({"row_count_range": 5000000}, baselines, report, z_threshold=2.0)
        assert not report.results[0].passed
        assert report.results[0].severity == "WARN"
        assert "deviates" in report.results[0].message

    def test_handles_zero_stddev(self):
        report = ValidationReport(source="test")
        baselines = {
            "row_count_range": {"mean": 9500000, "stddev": 0, "min": 9500000, "max": 9500000, "sample_count": 5}
        }
        # Different value with zero stddev should flag
        check_against_baseline({"row_count_range": 9500001}, baselines, report)
        assert not report.results[0].passed

    def test_passes_when_exact_match_with_zero_stddev(self):
        report = ValidationReport(source="test")
        baselines = {
            "row_count_range": {"mean": 9500000, "stddev": 0, "min": 9500000, "max": 9500000, "sample_count": 5}
        }
        check_against_baseline({"row_count_range": 9500000}, baselines, report)
        assert report.results[0].passed

    def test_skips_metrics_without_baselines(self):
        report = ValidationReport(source="test")
        baselines = {}
        check_against_baseline({"row_count_range": 5000000}, baselines, report)
        assert len(report.results) == 0

    def test_always_warn_severity(self):
        report = ValidationReport(source="test")
        baselines = {"row_count_range": {"mean": 100, "stddev": 10, "min": 80, "max": 120, "sample_count": 5}}
        check_against_baseline({"row_count_range": 1000}, baselines, report)
        assert report.results[0].severity == "WARN"
        # WARN doesn't block the pipeline
        assert report.passed
