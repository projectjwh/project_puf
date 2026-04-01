"""Tests for pipelines._common.validate."""

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
