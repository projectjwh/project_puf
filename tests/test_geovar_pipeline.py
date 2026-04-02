"""Tests for Geographic Variation pipeline transforms."""

import pandas as pd
import pytest

from pipelines.geovar.pipeline import transform_geovar, validate_geovar


@pytest.fixture
def raw_geovar_df():
    """Minimal GeoVar-like DataFrame after column rename."""
    return pd.DataFrame(
        {
            "bene_geo_lvl": ["National", "State", "State", "County"],
            "bene_geo_desc": ["National", "California", "New York", "Los Angeles, CA"],
            "bene_geo_cd": ["0", "06", "36", "06037"],
            "total_beneficiaries": ["60000000", "5000000", "3000000", "500000"],
            "total_beneficiaries_ffs": ["35000000", "2500000", "1500000", "250000"],
            "total_beneficiaries_ma": ["25000000", "2500000", "1500000", "250000"],
            "ma_participation_rate": ["0.4167", "0.5000", "0.5000", "0.5000"],
            "total_actual_costs": ["600000000000", "50000000000", "30000000000", "5000000000"],
            "actual_per_capita_costs": ["10000.00", "10000.00", "10000.00", "10000.00"],
            "standardized_per_capita_costs": ["9500.00", "10500.00", "11000.00", "10200.00"],
            "ip_per_capita_costs": ["3000.00", "3200.00", "3500.00", "3100.00"],
            "readmission_rate": ["0.1500", "0.1400", "0.1600", "0.1450"],
        }
    )


class TestTransformGeovar:
    def test_geo_level_standardization(self, raw_geovar_df):
        result = transform_geovar(raw_geovar_df, 2022)
        assert result.iloc[0]["bene_geo_lvl"] == "National"
        assert result.iloc[1]["bene_geo_lvl"] == "State"

    def test_state_fips_derivation(self, raw_geovar_df):
        result = transform_geovar(raw_geovar_df, 2022)
        # State-level: geo_cd "06" → state_fips "06"
        state_ca = result[result["bene_geo_desc"] == "California"].iloc[0]
        assert state_ca["state_fips"] == "06"

    def test_county_fips_derivation(self, raw_geovar_df):
        result = transform_geovar(raw_geovar_df, 2022)
        county_row = result[result["bene_geo_lvl"] == "County"].iloc[0]
        assert county_row["county_fips"] == "06037"
        assert county_row["state_fips"] == "06"

    def test_numeric_casting(self, raw_geovar_df):
        result = transform_geovar(raw_geovar_df, 2022)
        assert result["total_beneficiaries"].dtype == "Int64"
        assert result["actual_per_capita_costs"].dtype in ("float64", "Float64")

    def test_rate_rounding(self, raw_geovar_df):
        result = transform_geovar(raw_geovar_df, 2022)
        # Rates should be rounded to 4 decimal places
        assert result.iloc[0]["ma_participation_rate"] == pytest.approx(0.4167, abs=0.0001)
        assert result.iloc[0]["readmission_rate"] == pytest.approx(0.1500, abs=0.0001)

    def test_data_year(self, raw_geovar_df):
        result = transform_geovar(raw_geovar_df, 2022)
        assert all(result["data_year"] == 2022)

    def test_per_capita_rounding(self, raw_geovar_df):
        result = transform_geovar(raw_geovar_df, 2022)
        assert result.iloc[0]["actual_per_capita_costs"] == pytest.approx(10000.00, abs=0.01)


class TestValidateGeovar:
    def test_valid_data(self, raw_geovar_df):
        report = validate_geovar(raw_geovar_df)
        block_failures = [r for r in report.block_failures if "row_count" not in r.rule_name]
        assert len(block_failures) == 0

    def test_missing_geo_level_blocks(self):
        df = pd.DataFrame(
            {
                "bene_geo_lvl": [None, "State"],
                "bene_geo_cd": ["0", "06"],
            }
        )
        report = validate_geovar(df)
        not_null_failures = [r for r in report.block_failures if "not_null" in r.rule_name]
        assert len(not_null_failures) > 0
