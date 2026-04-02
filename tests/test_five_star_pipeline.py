"""Tests for Five-Star Quality Rating pipeline."""

from datetime import date

import pandas as pd
import pytest

from pipelines.five_star.pipeline import (
    COLUMN_MAPPING,
    STAGING_COLUMNS,
    transform_five_star,
    validate_five_star,
)


@pytest.fixture
def raw_five_star_df():
    return pd.DataFrame(
        {
            "ccn": ["5001", "330001", "67001"],
            "facility_name": ["  SUNNY NURSING HOME  ", "NYC CARE CENTER", "  AUSTIN REHAB  "],
            "provider_state": ["ca", "NY", "tx"],
            "overall_rating": ["4", "2", "5"],
            "health_inspection_rating": ["3", "1", "4"],
            "quality_rating": ["5", "3", "5"],
            "staffing_rating": ["4", "2", "4"],
            "rn_staffing_rating": ["3", "1", "5"],
            "total_number_of_penalties": ["2", "5", "0"],
            "total_fine_amount": ["15000.00", "75000.50", "0"],
            "total_weighted_health_survey_score": ["45.5", "120.3", "10.0"],
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
        assert "facility_name" in output_cols
        assert "overall_rating" in output_cols
        assert "health_inspection_rating" in output_cols
        assert "staffing_rating" in output_cols
        assert "quality_rating" in output_cols

    def test_staging_columns_has_ccn(self):
        assert "ccn" in STAGING_COLUMNS
        assert "overall_rating" in STAGING_COLUMNS
        assert "snapshot_date" in STAGING_COLUMNS


class TestValidateFiveStar:
    def test_valid_data(self, raw_five_star_df):
        report = validate_five_star(raw_five_star_df)
        # Only row_count might warn (we have 3 rows, not 10K+)
        block_failures = [r for r in report.block_failures if "row_count" not in r.rule_name]
        assert len(block_failures) == 0

    def test_blocks_on_missing_ccn_column(self):
        """Validation should raise when CCN column is entirely absent."""
        df = pd.DataFrame({"facility_name": ["TEST"]})
        with pytest.raises(KeyError):
            validate_five_star(df)

    def test_blocks_on_all_null_ccn(self):
        """Validation should BLOCK when all CCN values are null."""
        df = pd.DataFrame({"ccn": [None, None]})
        report = validate_five_star(df)
        assert len(report.block_failures) > 0

    def test_blocks_on_null_ccn(self):
        """Validation should BLOCK when CCN has null values."""
        df = pd.DataFrame({"ccn": [None, "010001"]})
        report = validate_five_star(df)
        assert len(report.block_failures) > 0

    def test_warns_on_row_count(self):
        """Row count outside expected range should generate a warning."""
        df = pd.DataFrame({"ccn": ["010001"]})
        report = validate_five_star(df)
        row_count_results = [r for r in report.results if r.rule_name == "row_count_range"]
        assert len(row_count_results) == 1
        assert not row_count_results[0].passed


class TestTransformFiveStar:
    def test_ccn_zero_padding(self, raw_five_star_df):
        """CCN should be zero-padded to 6 digits."""
        result = transform_five_star(raw_five_star_df, date(2024, 1, 1))
        assert result["ccn"].iloc[0] == "005001"
        assert result["ccn"].iloc[1] == "330001"
        assert result["ccn"].iloc[2] == "067001"

    def test_ratings_cast_to_int(self, raw_five_star_df):
        """Rating columns should be cast to Int64."""
        result = transform_five_star(raw_five_star_df, date(2024, 1, 1))
        assert result["overall_rating"].iloc[0] == 4
        assert result["health_inspection_rating"].iloc[0] == 3
        assert result["quality_rating"].iloc[0] == 5
        assert result["staffing_rating"].iloc[0] == 4
        assert result["rn_staffing_rating"].iloc[0] == 3
        assert result["total_number_of_penalties"].iloc[0] == 2

    def test_fine_amount_numeric(self, raw_five_star_df):
        """Fine amount should be cast to float."""
        result = transform_five_star(raw_five_star_df, date(2024, 1, 1))
        assert result["total_fine_amount"].iloc[0] == 15000.00
        assert result["total_fine_amount"].iloc[1] == 75000.50

    def test_snapshot_date(self, raw_five_star_df):
        """Transform should set snapshot_date."""
        result = transform_five_star(raw_five_star_df, date(2024, 3, 15))
        assert result["snapshot_date"].iloc[0] == date(2024, 3, 15)

    def test_provider_state_upper(self, raw_five_star_df):
        """Provider state should be uppercased."""
        result = transform_five_star(raw_five_star_df, date(2024, 1, 1))
        assert result["provider_state"].iloc[0] == "CA"
        assert result["provider_state"].iloc[2] == "TX"

    def test_facility_name_stripped(self, raw_five_star_df):
        """Facility name should be stripped of whitespace."""
        result = transform_five_star(raw_five_star_df, date(2024, 1, 1))
        assert result["facility_name"].iloc[0] == "SUNNY NURSING HOME"
