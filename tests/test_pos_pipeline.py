"""Tests for POS Facilities pipeline transforms."""

import pandas as pd
import pytest

from pipelines.pos.pipeline import transform_pos, validate_pos


@pytest.fixture
def raw_pos_df():
    return pd.DataFrame(
        {
            "ccn": ["50001", "330001", "670001"],
            "facility_name": ["  Memorial Hospital  ", "NYC Medical", "  Austin Health  "],
            "facility_type": ["Short Term", "Short Term", "Long Term"],
            "facility_type_code": ["01", "01", "02"],
            "ownership_type": ["Voluntary", "Government", "Proprietary"],
            "ownership_code": ["02", "05", "04"],
            "state": ["CA", "NY", "TX"],
            "zip_full": ["90210-1234", "10001", "73301"],
            "bed_count": ["200", "500", "bad"],
            "bed_count_total": ["250", "600", "100"],
            "certification_date": ["2000-01-15", "1995-06-20", "2010-03-01"],
            "termination_date": [None, None, "2023-12-31"],
            "medicare_participation_code": ["1", "1", "1"],
            "medicaid_participation_code": ["1", "1", None],
        }
    )


class TestTransformPos:
    def test_ccn_zero_padding(self, raw_pos_df):
        result = transform_pos(raw_pos_df)
        assert result.iloc[0]["ccn"] == "050001"

    def test_zip5_extraction(self, raw_pos_df):
        result = transform_pos(raw_pos_df)
        assert result.iloc[0]["zip5"] == "90210"

    def test_state_fips(self, raw_pos_df):
        result = transform_pos(raw_pos_df)
        assert result.iloc[0]["state_fips"] == "06"

    def test_active_flag(self, raw_pos_df):
        result = transform_pos(raw_pos_df)
        assert result.iloc[0]["is_active"] == True  # noqa: E712
        assert result.iloc[2]["is_active"] == False  # noqa: E712

    def test_bed_count_numeric(self, raw_pos_df):
        result = transform_pos(raw_pos_df)
        assert result.iloc[0]["bed_count"] == 200
        assert pd.isna(result.iloc[2]["bed_count"])  # "bad" → NaN


class TestValidatePos:
    def test_valid_data(self, raw_pos_df):
        report = validate_pos(raw_pos_df)
        block_failures = [r for r in report.block_failures if "row_count" not in r.rule_name]
        assert len(block_failures) == 0
