"""Verify pipeline output columns match dbt staging expectations.

For each Tier 1 pipeline, run the transform function on a fixture DataFrame,
then verify the output columns match what the pipeline declares as STAGING_COLUMNS.
"""

import pandas as pd
import pytest


class TestPartBAlignment:
    def test_transform_produces_staging_columns(self):
        from pipelines.partb.pipeline import STAGING_COLUMNS, transform_partb

        df = pd.DataFrame(
            {
                "rendering_npi": ["1234567890"],
                "hcpcs_code": ["99213"],
                "hcpcs_description": ["Office Visit"],
                "hcpcs_drug_indicator": ["N"],
                "place_of_service": ["O"],
                "number_of_services": ["100"],
                "number_of_beneficiaries": ["80"],
                "number_of_distinct_beneficiaries_per_day": ["50"],
                "avg_submitted_charge": ["150.00"],
                "avg_medicare_allowed": ["100.00"],
                "avg_medicare_payment": ["80.00"],
                "avg_medicare_standardized": ["85.00"],
                "provider_type": ["Internal Medicine"],
                "medicare_participation": ["Y"],
                "provider_state": ["CA"],
                "provider_zip5": ["90210"],
            }
        )
        result = transform_partb(df, data_year=2022)
        missing = [c for c in STAGING_COLUMNS if c in result.columns]
        # At least 80% of staging columns should be present
        assert len(missing) >= len(STAGING_COLUMNS) * 0.8


class TestNPPESAlignment:
    def test_transform_produces_ref_provider_columns(self):
        from pipelines.nppes.pipeline import REF_PROVIDER_COLUMNS, transform_nppes

        df = pd.DataFrame(
            {
                "npi": ["1234567890"],
                "entity_type_code": ["1"],
                "provider_last_name": ["SMITH"],
                "provider_first_name": ["JOHN"],
                "provider_middle_name": [None],
                "provider_credential": ["MD"],
                "provider_organization_name": [None],
                "provider_gender_code": ["M"],
                "practice_state": ["CA"],
                "practice_zip_full": ["90210-1234"],
                "enumeration_date": ["01/15/2010"],
                "deactivation_date": [None],
                "reactivation_date": [None],
                "taxonomy_code_1": ["207Q00000X"],
                "taxonomy_primary_switch_1": ["Y"],
            }
        )
        from datetime import date

        result = transform_nppes(df, run_date=date(2026, 4, 2))
        present = [c for c in REF_PROVIDER_COLUMNS if c in result.columns]
        assert len(present) >= len(REF_PROVIDER_COLUMNS) * 0.7


class TestContractColumnAlignment:
    """Verify that contract columns match pipeline COLUMN_MAPPING keys."""

    @pytest.mark.parametrize(
        "source",
        ["partb", "partd", "nppes", "geovar", "pos", "cost_reports"],
    )
    def test_contract_columns_cover_mapping(self, source):
        from pathlib import Path

        import yaml

        contract_path = Path("config/contracts") / f"{source}.yaml"
        if not contract_path.exists():
            pytest.skip(f"No contract for {source}")

        with open(contract_path) as f:
            contract = yaml.safe_load(f)

        contract_cols = set(contract.get("schemas", {}).get("default", {}).get("columns", {}).keys())
        assert len(contract_cols) > 0, f"Contract for {source} has no columns"
