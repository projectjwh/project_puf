"""Tests for Part D prescribers pipeline transforms."""

import pandas as pd
import pytest

from pipelines.partd.pipeline import transform_partd, validate_partd


@pytest.fixture
def raw_partd_df():
    """Minimal Part D-like DataFrame after column rename."""
    return pd.DataFrame({
        "prescriber_npi": ["1234567890", "1234567890", "0987654321"],
        "prescriber_last_name": ["  SMITH  ", "  SMITH  ", "  JONES  "],
        "prescriber_first_name": ["  JOHN  ", "  JOHN  ", "  MARY  "],
        "prescriber_state": ["CA", "CA", "NY"],
        "specialty_description": ["Internal Medicine", "Internal Medicine", "Family Medicine"],
        "drug_name": ["LISINOPRIL", "OXYCONTIN", "METFORMIN HCL"],
        "generic_name": ["LISINOPRIL", "OXYCODONE HCL", "METFORMIN HCL"],
        "total_claim_count": ["500", "50", "300"],
        "total_day_supply": ["15000", "1500", "9000"],
        "total_drug_cost": ["2500.00", "15000.00", "1200.00"],
        "total_beneficiary_count": ["200", "30", "150"],
        "is_opioid_flag": ["N", "Y", "N"],
        "opioid_claim_count": ["0", "50", "0"],
        "ge65_suppress_flag": [None, None, None],
    })


class TestTransformPartd:
    def test_opioid_flag(self, raw_partd_df):
        result = transform_partd(raw_partd_df, 2022)
        # Row 0: LISINOPRIL, is_opioid_flag=N → False
        assert result.iloc[0]["is_opioid"] == False  # noqa: E712
        # Row 1: OXYCONTIN, is_opioid_flag=Y → True
        assert result.iloc[1]["is_opioid"] == True  # noqa: E712

    def test_brand_generic_classification(self, raw_partd_df):
        result = transform_partd(raw_partd_df, 2022)
        # LISINOPRIL drug_name == generic_name → generic
        assert result.iloc[0]["is_generic"] == True  # noqa: E712
        assert result.iloc[0]["is_brand_name"] == False  # noqa: E712
        # OXYCONTIN != OXYCODONE HCL → brand
        assert result.iloc[1]["is_brand_name"] == True  # noqa: E712
        assert result.iloc[1]["is_generic"] == False  # noqa: E712

    def test_cost_per_claim(self, raw_partd_df):
        result = transform_partd(raw_partd_df, 2022)
        # Row 0: $2500 / 500 claims = $5.00
        assert result.iloc[0]["cost_per_claim"] == pytest.approx(5.00, abs=0.01)
        # Row 1: $15000 / 50 claims = $300.00
        assert result.iloc[1]["cost_per_claim"] == pytest.approx(300.00, abs=0.01)

    def test_cost_per_day(self, raw_partd_df):
        result = transform_partd(raw_partd_df, 2022)
        # Row 0: $2500 / 15000 days = $0.17
        assert result.iloc[0]["cost_per_day"] == pytest.approx(0.17, abs=0.01)

    def test_npi_normalization(self, raw_partd_df):
        result = transform_partd(raw_partd_df, 2022)
        assert all(result["prescriber_npi"].str.match(r"^\d{10}$"))

    def test_state_fips(self, raw_partd_df):
        result = transform_partd(raw_partd_df, 2022)
        assert result.iloc[0]["prescriber_state_fips"] == "06"  # CA
        assert result.iloc[2]["prescriber_state_fips"] == "36"  # NY

    def test_data_year(self, raw_partd_df):
        result = transform_partd(raw_partd_df, 2022)
        assert all(result["data_year"] == 2022)

    def test_integer_columns(self, raw_partd_df):
        result = transform_partd(raw_partd_df, 2022)
        assert result["total_claim_count"].dtype == "Int64"
        assert result["total_day_supply"].dtype == "Int64"
        assert result["total_beneficiary_count"].dtype == "Int64"

    def test_string_cleaning(self, raw_partd_df):
        result = transform_partd(raw_partd_df, 2022)
        assert result.iloc[0]["prescriber_last_name"] == "SMITH"


class TestValidatePartd:
    def test_valid_data(self, raw_partd_df):
        report = validate_partd(raw_partd_df)
        block_failures = [r for r in report.block_failures if "row_count" not in r.rule_name]
        assert len(block_failures) == 0

    def test_missing_npi_blocks(self):
        df = pd.DataFrame({
            "prescriber_npi": [None, "0987654321"],
            "drug_name": ["LISINOPRIL", "METFORMIN"],
        })
        report = validate_partd(df)
        not_null_failures = [r for r in report.block_failures if "not_null" in r.rule_name]
        assert len(not_null_failures) > 0
