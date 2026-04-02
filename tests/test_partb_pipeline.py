"""Tests for Part B utilization pipeline transforms."""

import pandas as pd
import pytest

from pipelines.partb.pipeline import transform_partb, validate_partb


@pytest.fixture
def raw_partb_df():
    """Minimal Part B-like DataFrame after column rename."""
    return pd.DataFrame(
        {
            "rendering_npi": ["1234567890", "0987654321", "1111111111"],
            "rendering_npi_name": ["  SMITH JOHN  ", "  ACME CLINIC  ", "  DOE JANE  "],
            "entity_type": ["I", "O", "I"],
            "hcpcs_code": ["99213", "99214", "J0170"],
            "hcpcs_description": ["Office Visit Level 3", "Office Visit Level 4", "Adrenalin Injection"],
            "hcpcs_drug_indicator": ["N", "N", "Y"],
            "place_of_service": ["F", "F", "O"],
            "number_of_services": ["150", "200", "50"],
            "number_of_beneficiaries": ["100", "120", "30"],
            "avg_submitted_charge": ["125.50", "180.00", "45.00"],
            "avg_medicare_allowed": ["85.00", "120.00", "30.00"],
            "avg_medicare_payment": ["68.00", "96.00", "24.00"],
            "avg_medicare_standardized": ["70.00", "100.00", "25.00"],
            "provider_type": ["Internal Medicine", "Multispecialty", "Family Medicine"],
            "provider_state": ["CA", "NY", "TX"],
            "provider_zip5": ["90210", "10001", "73301"],
            "medicare_participation": ["Y", "Y", "Y"],
        }
    )


class TestTransformPartb:
    def test_totals_from_averages(self, raw_partb_df):
        """CRITICAL: verify totals are computed from avg × service_count."""
        result = transform_partb(raw_partb_df, 2022)

        # Provider 1: 150 services × $125.50 avg = $18,825.00
        row = result[result["rendering_npi"] == "1234567890"].iloc[0]
        assert row["total_submitted_charge"] == pytest.approx(18825.00, abs=0.01)

        # Provider 1: 150 × $68.00 = $10,200.00
        assert row["total_medicare_payment"] == pytest.approx(10200.00, abs=0.01)

        # Provider 1: 150 × $85.00 = $12,750.00
        assert row["total_medicare_allowed"] == pytest.approx(12750.00, abs=0.01)

    def test_npi_normalization(self, raw_partb_df):
        result = transform_partb(raw_partb_df, 2022)
        assert all(result["rendering_npi"].str.match(r"^\d{10}$"))

    def test_state_fips_derivation(self, raw_partb_df):
        result = transform_partb(raw_partb_df, 2022)
        assert result.iloc[0]["provider_state_fips"] == "06"  # CA
        assert result.iloc[1]["provider_state_fips"] == "36"  # NY
        assert result.iloc[2]["provider_state_fips"] == "48"  # TX

    def test_data_year_added(self, raw_partb_df):
        result = transform_partb(raw_partb_df, 2022)
        assert all(result["data_year"] == 2022)

    def test_numeric_casting(self, raw_partb_df):
        result = transform_partb(raw_partb_df, 2022)
        # number_of_services may be int or float depending on whether values are whole
        assert pd.api.types.is_numeric_dtype(result["number_of_services"])
        assert pd.api.types.is_numeric_dtype(result["avg_submitted_charge"])

    def test_string_cleaning(self, raw_partb_df):
        result = transform_partb(raw_partb_df, 2022)
        # Names should be stripped and uppercased
        assert result.iloc[0]["rendering_npi_name"] == "SMITH JOHN"

    def test_integer_columns(self, raw_partb_df):
        result = transform_partb(raw_partb_df, 2022)
        assert result["number_of_beneficiaries"].dtype == "Int64"

    def test_drug_indicator_preserved(self, raw_partb_df):
        result = transform_partb(raw_partb_df, 2022)
        assert result.iloc[2]["hcpcs_drug_indicator"] == "Y"


class TestValidatePartb:
    def test_valid_data(self, raw_partb_df):
        report = validate_partb(raw_partb_df)
        block_failures = [r for r in report.block_failures if "row_count" not in r.rule_name]
        assert len(block_failures) == 0

    def test_missing_npi_blocks(self):
        df = pd.DataFrame(
            {
                "rendering_npi": [None, "0987654321"],
                "hcpcs_code": ["99213", "99214"],
            }
        )
        report = validate_partb(df)
        not_null_failures = [r for r in report.block_failures if "not_null" in r.rule_name]
        assert len(not_null_failures) > 0

    def test_missing_hcpcs_blocks(self):
        df = pd.DataFrame(
            {
                "rendering_npi": ["1234567890", "0987654321"],
                "hcpcs_code": [None, "99214"],
            }
        )
        report = validate_partb(df)
        not_null_failures = [r for r in report.block_failures if "not_null" in r.rule_name]
        assert len(not_null_failures) > 0
