"""Tests for Tier 2 provider enrichment, code system, and geographic pipelines."""

import pandas as pd


class TestPecosPipeline:
    def test_column_mapping(self):
        from pipelines.pecos.pipeline import COLUMN_MAPPING

        assert "NPI" in COLUMN_MAPPING
        assert COLUMN_MAPPING["NPI"] == "npi"

    def test_transform_npi_normalization(self):
        from pipelines.pecos.pipeline import transform_pecos

        df = pd.DataFrame(
            {
                "npi": ["1234567890", "987654321"],
                "provider_type": ["  Internal Medicine  ", "Cardiology"],
                "accepts_assignment": ["Y", "N"],
            }
        )
        result = transform_pecos(df)
        assert result["npi"].iloc[0] == "1234567890"
        assert result["npi"].iloc[1] == "0987654321"

    def test_transform_assignment_flag(self):
        from pipelines.pecos.pipeline import transform_pecos

        df = pd.DataFrame(
            {
                "npi": ["1234567890"],
                "accepts_assignment": ["Y"],
                "participating": ["N"],
            }
        )
        result = transform_pecos(df)
        assert result["accepts_assignment"].iloc[0] == True  # noqa: E712
        assert result["participating"].iloc[0] == False  # noqa: E712

    def test_validate_blocks_missing_npi(self):
        from pipelines.pecos.pipeline import validate_pecos

        df = pd.DataFrame({"npi": [None, None], "provider_type": ["A", "B"]})
        report = validate_pecos(df)
        assert len(report.block_failures) > 0

    def test_output_columns(self):
        from pipelines.pecos.pipeline import OUTPUT_COLUMNS

        assert "npi" in OUTPUT_COLUMNS
        assert "enrollment_state" in OUTPUT_COLUMNS


class TestOrderingReferringPipeline:
    def test_column_mapping(self):
        from pipelines.ordering_referring.pipeline import COLUMN_MAPPING

        assert "NPI" in COLUMN_MAPPING

    def test_transform_eligible_flag(self):
        from pipelines.ordering_referring.pipeline import transform_ordering_referring

        df = pd.DataFrame(
            {
                "npi": ["1234567890"],
                "last_name": ["SMITH"],
                "first_name": ["JOHN"],
                "state": ["CA"],
                "eligible": ["Y"],
            }
        )
        result = transform_ordering_referring(df)
        assert result["eligible"].iloc[0] == True  # noqa: E712

    def test_transform_default_eligible(self):
        from pipelines.ordering_referring.pipeline import transform_ordering_referring

        df = pd.DataFrame(
            {
                "npi": ["1234567890"],
                "last_name": ["SMITH"],
                "first_name": ["JOHN"],
                "state": ["CA"],
            }
        )
        result = transform_ordering_referring(df)
        assert result["eligible"].iloc[0] == True  # noqa: E712


class TestAPCPipeline:
    def test_column_mapping(self):
        from pipelines.apc.pipeline import COLUMN_MAPPING

        assert "APC" in COLUMN_MAPPING
        assert COLUMN_MAPPING["APC"] == "apc_code"

    def test_transform_currency_stripping(self):
        from pipelines.apc.pipeline import transform_apc

        df = pd.DataFrame(
            {
                "apc_code": ["0012"],
                "apc_description": ["LOW LEVEL CLINIC VISIT"],
                "payment_rate": ["$150.50"],
                "relative_weight": ["1.2345"],
            }
        )
        result = transform_apc(df, 2024)
        assert result["payment_rate"].iloc[0] == 150.50
        assert result["effective_year"].iloc[0] == 2024

    def test_validate_blocks_missing_apc(self):
        from pipelines.apc.pipeline import validate_apc

        df = pd.DataFrame({"apc_code": [None]})
        report = validate_apc(df)
        assert len(report.block_failures) > 0


class TestHRRHSAPipeline:
    def test_column_mapping(self):
        from pipelines.hrr_hsa.pipeline import COLUMN_MAPPING

        assert "ZIPCODE" in COLUMN_MAPPING

    def test_transform_zip5(self):
        from pipelines.hrr_hsa.pipeline import transform_hrr_hsa

        df = pd.DataFrame(
            {
                "zip_code": ["90210-1234"],
                "hrr_number": ["123"],
                "hsa_number": ["456"],
                "hrr_city": ["los angeles"],
                "hsa_city": ["los angeles"],
                "hrr_state": ["ca"],
                "hsa_state": ["ca"],
            }
        )
        result = transform_hrr_hsa(df)
        assert result["zip_code"].iloc[0] == "90210"
        assert result["hrr_number"].iloc[0] == 123
        assert result["hrr_city"].iloc[0] == "Los Angeles"
        assert result["hrr_state"].iloc[0] == "CA"


class TestCensusPipeline:
    def test_column_mapping(self):
        from pipelines.census.pipeline import COLUMN_MAPPING

        assert "STATE" in COLUMN_MAPPING
        assert COLUMN_MAPPING["STATE"] == "state_fips"

    def test_transform_fips_derivation(self):
        from pipelines.census.pipeline import transform_census

        df = pd.DataFrame(
            {
                "state_fips": ["6"],
                "county_fips_suffix": ["037"],
                "state_name": ["California"],
                "county_name": ["Los Angeles"],
                "total_population": ["10000000"],
            }
        )
        result = transform_census(df, 2022)
        assert result["state_fips"].iloc[0] == "06"
        assert result["county_fips"].iloc[0] == "06037"
        assert result["fips_code"].iloc[0] == "06037"
        assert result["total_population"].iloc[0] == 10000000
        assert result["year"].iloc[0] == 2022

    def test_transform_state_level_fips(self):
        from pipelines.census.pipeline import transform_census

        df = pd.DataFrame(
            {
                "state_fips": ["6"],
                "county_fips_suffix": ["000"],
                "state_name": ["California"],
                "total_population": ["39000000"],
            }
        )
        result = transform_census(df, 2022)
        # State-level rows use state FIPS as fips_code
        assert result["fips_code"].iloc[0] == "06"
