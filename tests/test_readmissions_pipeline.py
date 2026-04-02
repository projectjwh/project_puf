"""Tests for Hospital Readmissions Reduction Program pipeline."""

import pandas as pd
import pytest

from pipelines.readmissions.pipeline import (
    COLUMN_MAPPING,
    STAGING_COLUMNS,
    transform_readmissions,
    validate_readmissions,
)


@pytest.fixture
def raw_readmissions_df():
    return pd.DataFrame(
        {
            "ccn": ["010001", "330001", "450001"],
            "facility_name": ["  MEMORIAL HOSPITAL  ", "NYC MEDICAL CENTER", "  HOUSTON GENERAL  "],
            "provider_state": ["al", "NY", "tx"],
            "measure_id": ["READM-30-HF-HRRP", "READM-30-AMI-HRRP", "READM-30-PN-HRRP"],
            "measure_name": ["Heart Failure", "AMI", "Pneumonia"],
            "denominator": ["1000", "500", "Not Available"],
            "score": ["0.9876", "1.0234", "Not Available"],
            "lower_estimate": ["0.95", "0.98", "Not Available"],
            "upper_estimate": ["1.02", "1.07", "Not Available"],
            "compared_to_national": [
                "WORSE THAN NATIONAL RATE",
                "NO DIFFERENT THAN NATIONAL RATE",
                "BETTER THAN NATIONAL RATE",
            ],
        }
    )


class TestColumnMapping:
    def test_has_ccn_keys(self):
        """COLUMN_MAPPING should map at least one CMS CCN column."""
        ccn_mapped = [k for k, v in COLUMN_MAPPING.items() if v == "ccn"]
        assert len(ccn_mapped) >= 1

    def test_has_expected_output_keys(self):
        """COLUMN_MAPPING should produce key output columns."""
        output_cols = set(COLUMN_MAPPING.values())
        assert "ccn" in output_cols
        assert "measure_id" in output_cols
        assert "score" in output_cols
        assert "denominator" in output_cols
        assert "compared_to_national" in output_cols

    def test_staging_columns_has_required(self):
        assert "ccn" in STAGING_COLUMNS
        assert "measure_id" in STAGING_COLUMNS
        assert "data_year" in STAGING_COLUMNS


class TestValidateReadmissions:
    def test_valid_data(self, raw_readmissions_df):
        report = validate_readmissions(raw_readmissions_df)
        block_failures = [r for r in report.block_failures if "row_count" not in r.rule_name]
        assert len(block_failures) == 0

    def test_blocks_on_missing_ccn_column(self):
        """Validation should raise when CCN column is entirely absent."""
        df = pd.DataFrame({"measure_id": ["READM-30-HF-HRRP"]})
        with pytest.raises(KeyError):
            validate_readmissions(df)

    def test_blocks_on_all_null_ccn(self):
        """Validation should BLOCK when all CCN values are null."""
        df = pd.DataFrame({"ccn": [None], "measure_id": ["READM-30-HF-HRRP"]})
        report = validate_readmissions(df)
        assert len(report.block_failures) > 0

    def test_blocks_on_missing_measure_id_column(self):
        """Validation should BLOCK when measure_id column is missing."""
        df = pd.DataFrame({"ccn": ["010001"]})
        report = validate_readmissions(df)
        assert len(report.block_failures) > 0

    def test_blocks_on_null_ccn(self):
        """Validation should BLOCK when CCN has null values."""
        df = pd.DataFrame({"ccn": [None], "measure_id": ["READM-30-HF-HRRP"]})
        report = validate_readmissions(df)
        assert len(report.block_failures) > 0

    def test_warns_on_row_count(self):
        """Row count outside expected range should generate a warning."""
        df = pd.DataFrame({"ccn": ["010001"], "measure_id": ["READM-30-HF"]})
        report = validate_readmissions(df)
        row_count_results = [r for r in report.results if r.rule_name == "row_count_range"]
        assert len(row_count_results) == 1
        assert not row_count_results[0].passed


class TestTransformReadmissions:
    def test_ccn_zero_padding(self, raw_readmissions_df):
        """CCN should be zero-padded to 6 digits."""
        result = transform_readmissions(raw_readmissions_df, 2022)
        assert result["ccn"].iloc[0] == "010001"
        assert result["ccn"].iloc[1] == "330001"

    def test_not_available_to_none(self, raw_readmissions_df):
        """'Not Available' values should become None/NaN."""
        result = transform_readmissions(raw_readmissions_df, 2022)
        assert pd.isna(result["score"].iloc[2])
        assert pd.isna(result["lower_estimate"].iloc[2])
        assert pd.isna(result["upper_estimate"].iloc[2])

    def test_score_numeric(self, raw_readmissions_df):
        """Score should be cast to numeric."""
        result = transform_readmissions(raw_readmissions_df, 2022)
        assert result["score"].iloc[0] == pytest.approx(0.9876, rel=1e-4)
        assert result["score"].iloc[1] == pytest.approx(1.0234, rel=1e-4)

    def test_denominator_numeric(self, raw_readmissions_df):
        """Denominator should be cast to Int64."""
        result = transform_readmissions(raw_readmissions_df, 2022)
        assert result["denominator"].iloc[0] == 1000
        assert result["denominator"].iloc[1] == 500

    def test_data_year(self, raw_readmissions_df):
        """Transform should set data_year."""
        result = transform_readmissions(raw_readmissions_df, 2022)
        assert result["data_year"].iloc[0] == 2022

    def test_provider_state_upper(self, raw_readmissions_df):
        """Provider state should be uppercased."""
        result = transform_readmissions(raw_readmissions_df, 2022)
        assert result["provider_state"].iloc[0] == "AL"
        assert result["provider_state"].iloc[2] == "TX"
