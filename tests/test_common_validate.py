"""Tests for pipelines._common.validate."""

from unittest.mock import patch

import pandas as pd
import pytest

from pipelines._common.validate import (
    ValidationReport,
    ValidationResult,
    check_column_format,
    check_column_not_null,
    check_null_rate,
    check_referential_integrity,
    check_required_columns,
    check_row_count,
    check_row_count_delta,
    check_uniqueness,
    check_value_range,
    check_value_set,
)


@pytest.fixture
def report():
    return ValidationReport(source="test")


class TestValidationReport:
    def test_empty_report_passes(self):
        report = ValidationReport(source="test")
        assert report.passed is True
        assert report.block_failures == []

    def test_warn_failure_still_passes(self, report):
        report.add(ValidationResult("r1", "WARN", False, message="just a warning"))
        assert report.passed is True
        assert len(report.warnings) == 1

    def test_block_failure_fails(self, report):
        report.add(ValidationResult("r1", "BLOCK", False, message="hard fail"))
        assert report.passed is False
        assert len(report.block_failures) == 1

    def test_raise_if_blocked(self, report):
        report.add(ValidationResult("r1", "BLOCK", False, message="bad"))
        with pytest.raises(ValueError, match="BLOCKED"):
            report.raise_if_blocked()


class TestCheckRequiredColumns:
    def test_all_present(self, sample_npi_df, report):
        check_required_columns(sample_npi_df, ["npi", "entity_type_code"], report)
        assert report.passed

    def test_missing_column(self, sample_npi_df, report):
        check_required_columns(sample_npi_df, ["npi", "nonexistent_column"], report)
        assert not report.passed


class TestCheckColumnNotNull:
    def test_no_nulls(self, sample_npi_df, report):
        check_column_not_null(sample_npi_df, "npi", report)
        assert report.passed

    def test_with_nulls(self, sample_npi_df, report):
        check_column_not_null(sample_npi_df, "provider_first_name", report)
        assert not report.passed  # Has None values


class TestCheckColumnFormat:
    def test_valid_npi_format(self, sample_npi_df, report):
        check_column_format(sample_npi_df, "npi", r"^\d{10}$", report)
        assert report.passed

    def test_invalid_format(self, report):
        df = pd.DataFrame({"code": ["ABC", "12345", "XY"]})
        check_column_format(df, "code", r"^\d{5}$", report)
        assert not report.passed


class TestCheckUniqueness:
    def test_unique_values(self, sample_npi_df, report):
        check_uniqueness(sample_npi_df, ["npi"], report)
        assert report.passed

    def test_duplicate_values(self, report):
        df = pd.DataFrame({"key": [1, 1, 2, 3]})
        check_uniqueness(df, ["key"], report)
        assert not report.passed


class TestCheckRowCount:
    def test_in_range(self, sample_npi_df, report):
        check_row_count(sample_npi_df, min_rows=1, max_rows=100, report=report)
        assert report.passed

    def test_below_range(self, sample_npi_df, report):
        check_row_count(sample_npi_df, min_rows=100, max_rows=1000, report=report)
        assert not report.results[-1].passed

    def test_above_range(self, sample_npi_df, report):
        check_row_count(sample_npi_df, min_rows=1, max_rows=2, report=report)
        assert not report.results[-1].passed


class TestCheckValueSet:
    def test_all_valid(self, sample_npi_df, report):
        check_value_set(sample_npi_df, "entity_type_code", {"1", "2"}, report)
        assert report.passed

    def test_invalid_values(self, report):
        df = pd.DataFrame({"code": ["A", "B", "C"]})
        check_value_set(df, "code", {"A", "B"}, report)
        assert not report.passed


class TestCheckNullRate:
    def test_low_null_rate(self, sample_npi_df, report):
        check_null_rate(sample_npi_df, "npi", max_rate=0.01, report=report)
        assert report.passed

    def test_high_null_rate(self, sample_npi_df, report):
        # provider_first_name has 2/5 = 40% nulls
        check_null_rate(sample_npi_df, "provider_first_name", max_rate=0.10, report=report)
        assert not report.results[-1].passed


class TestCheckValueRange:
    def test_in_range(self, sample_partb_df, report):
        check_value_range(sample_partb_df, "service_count", min_val=0, max_val=1000, report=report)
        assert report.passed

    def test_out_of_range(self, sample_partb_df, report):
        check_value_range(sample_partb_df, "service_count", min_val=0, max_val=100, report=report)
        assert not report.results[-1].passed


class TestCheckReferentialIntegrity:
    def test_high_match_rate(self, report):
        df = pd.DataFrame({"npi": ["1", "2", "3", "4", "5"]})
        ref = pd.DataFrame({"npi": ["1", "2", "3", "4", "5", "6"]})
        check_referential_integrity(df, "npi", ref, "npi", min_match_rate=0.95, report=report)
        assert report.passed

    def test_low_match_rate(self, report):
        df = pd.DataFrame({"npi": ["1", "2", "3", "4", "5"]})
        ref = pd.DataFrame({"npi": ["1", "2"]})
        check_referential_integrity(df, "npi", ref, "npi", min_match_rate=0.95, report=report)
        assert not report.results[-1].passed


class TestCheckRowCountDelta:
    def test_small_change(self, report):
        check_row_count_delta(100, 95, max_pct_change=0.10, report=report)
        assert report.passed

    def test_large_change(self, report):
        check_row_count_delta(100, 50, max_pct_change=0.10, report=report)
        assert not report.results[-1].passed


# ---------------------------------------------------------------------------
# Phase 2: Persistence and quarantine features
# ---------------------------------------------------------------------------

class TestValidationReportPersistence:
    def test_run_id_defaults_to_none(self):
        report = ValidationReport(source="test")
        assert report.run_id is None

    def test_run_id_can_be_set(self):
        report = ValidationReport(source="test", run_id=42)
        assert report.run_id == 42

    def test_persist_noop_when_no_run_id(self):
        """persist() should not raise when run_id is None."""
        report = ValidationReport(source="test")
        report.persist()  # should be a no-op

    def test_persist_noop_when_negative_run_id(self):
        """persist() should not raise when run_id is -1 (tracking disabled)."""
        report = ValidationReport(source="test", run_id=-1)
        report.persist()  # should be a no-op

    def test_raise_if_blocked_persists_first(self):
        """raise_if_blocked should call persist() before raising."""
        from unittest.mock import patch

        report = ValidationReport(source="test", run_id=42)
        report.add(ValidationResult("r1", "BLOCK", False, message="fail"))

        with patch.object(report, "persist") as mock_persist:
            with pytest.raises(ValueError, match="BLOCKED"):
                report.raise_if_blocked()
            mock_persist.assert_called_once()


class TestQuarantineMaskAccumulation:
    def test_masks_accumulated_via_check_column_not_null(self):
        df = pd.DataFrame({"npi": ["123", None, "456"]})
        report = ValidationReport(source="test")
        check_column_not_null(df, "npi", report)
        assert "npi_not_null" in report._quarantine_masks
        mask = report._quarantine_masks["npi_not_null"]
        assert mask[1] is True or mask[1] == True  # noqa: E712
        assert mask[0] is False or mask[0] == False  # noqa: E712

    def test_masks_accumulated_via_check_column_format(self):
        df = pd.DataFrame({"npi": ["1234567890", "BAD", "0987654321"]})
        report = ValidationReport(source="test")
        check_column_format(df, "npi", r"^\d{10}$", report)
        assert "npi_format" in report._quarantine_masks
        mask = report._quarantine_masks["npi_format"]
        assert mask[1] == True  # noqa: E712
        assert mask[0] == False  # noqa: E712

    def test_masks_accumulated_via_check_value_set(self):
        df = pd.DataFrame({"entity": ["1", "2", "X"]})
        report = ValidationReport(source="test")
        check_value_set(df, "entity", {"1", "2"}, report)
        assert "entity_value_set" in report._quarantine_masks

    def test_no_mask_when_check_passes(self):
        df = pd.DataFrame({"npi": ["1234567890", "0987654321"]})
        report = ValidationReport(source="test")
        check_column_not_null(df, "npi", report)
        assert len(report._quarantine_masks) == 0

    def test_apply_quarantine_removes_bad_rows(self):
        from pipelines._common.validate import apply_quarantine

        df = pd.DataFrame({"npi": ["1234567890", None, "0987654321"]})
        report = ValidationReport(source="test")
        check_column_not_null(df, "npi", report)

        with patch("pipelines._common.config.get_pipeline_settings") as mock_settings:
            mock_settings.return_value.quarantine_enabled = True
            clean = apply_quarantine(df, report, run_id=-1)

        assert len(clean) == 2
        assert None not in clean["npi"].values
