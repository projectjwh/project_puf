"""Tests for NPPES pipeline transforms and validation."""

from datetime import date

import pandas as pd
import pytest

from pipelines.nppes.pipeline import (
    REF_PROVIDER_COLUMNS,
    build_taxonomy_table,
    transform_nppes,
    validate_nppes,
)


@pytest.fixture
def raw_nppes_df():
    """Minimal NPPES-like DataFrame after column rename."""
    return pd.DataFrame(
        {
            "npi": ["1234567890", "0987654321", "1111111111"],
            "entity_type_code": ["1", "2", "1"],
            "provider_last_name": ["  smith  ", "ACME CORP", "  doe  "],
            "provider_first_name": ["  john  ", None, "  jane  "],
            "provider_credential": ["  MD  ", None, "  NP  "],
            "provider_organization_name": [None, "ACME HEALTH SYSTEM", None],
            "provider_gender_code": ["M", None, "F"],
            "practice_state": ["CA", "NY", "TX"],
            "practice_zip_full": ["90210-1234", "10001", "73301-0000"],
            "taxonomy_code_1": ["207Q00000X", "282N00000X", "363L00000X"],
            "taxonomy_primary_switch_1": ["Y", "Y", "N"],
            "taxonomy_code_2": [None, None, "363LP0200X"],
            "taxonomy_primary_switch_2": [None, None, "Y"],
            "enumeration_date": ["05/23/2005", "01/15/2010", "11/30/2018"],
            "deactivation_date": [None, None, None],
            "reactivation_date": [None, None, None],
        }
    )


class TestTransformNppes:
    def test_display_name_individual(self, raw_nppes_df):
        result = transform_nppes(raw_nppes_df, date(2026, 3, 4))
        # Individual: "LAST, FIRST CREDENTIAL"
        assert "SMITH" in result.iloc[0]["display_name"]
        assert "JOHN" in result.iloc[0]["display_name"]
        assert "MD" in result.iloc[0]["display_name"]

    def test_display_name_organization(self, raw_nppes_df):
        result = transform_nppes(raw_nppes_df, date(2026, 3, 4))
        assert "ACME HEALTH SYSTEM" in result.iloc[1]["display_name"]

    def test_zip5_extraction(self, raw_nppes_df):
        result = transform_nppes(raw_nppes_df, date(2026, 3, 4))
        assert result.iloc[0]["practice_zip5"] == "90210"
        assert result.iloc[1]["practice_zip5"] == "10001"

    def test_state_fips_derivation(self, raw_nppes_df):
        result = transform_nppes(raw_nppes_df, date(2026, 3, 4))
        assert result.iloc[0]["state_fips"] == "06"  # CA
        assert result.iloc[1]["state_fips"] == "36"  # NY

    def test_primary_taxonomy_extraction(self, raw_nppes_df):
        result = transform_nppes(raw_nppes_df, date(2026, 3, 4))
        # NPI 1: taxonomy_1 switch=Y → 207Q00000X
        assert result.iloc[0]["primary_taxonomy_code"] == "207Q00000X"
        # NPI 3: taxonomy_1 switch=N, taxonomy_2 switch=Y → 363LP0200X
        assert result.iloc[2]["primary_taxonomy_code"] == "363LP0200X"

    def test_entity_type_flags(self, raw_nppes_df):
        result = transform_nppes(raw_nppes_df, date(2026, 3, 4))
        assert result.iloc[0]["is_individual"] == True  # noqa: E712
        assert result.iloc[1]["is_organization"] == True  # noqa: E712

    def test_active_flag(self, raw_nppes_df):
        result = transform_nppes(raw_nppes_df, date(2026, 3, 4))
        assert all(result["is_active"])

    def test_years_since_enumeration(self, raw_nppes_df):
        result = transform_nppes(raw_nppes_df, date(2026, 3, 4))
        # Enumerated 2005-05-23, now 2026-03-04 → ~20.8 years
        assert result.iloc[0]["years_since_enumeration"] > 20

    def test_snapshot_date(self, raw_nppes_df):
        result = transform_nppes(raw_nppes_df, date(2026, 3, 4))
        assert result.iloc[0]["_snapshot_date"] == date(2026, 3, 4)


class TestBuildTaxonomyTable:
    def test_unpivots_taxonomies(self, raw_nppes_df):
        transformed = transform_nppes(raw_nppes_df, date(2026, 3, 4))
        tax_df = build_taxonomy_table(transformed)

        # NPI 1: 1 taxonomy slot
        npi1_rows = tax_df[tax_df["npi"] == "1234567890"]
        assert len(npi1_rows) == 1
        assert npi1_rows.iloc[0]["taxonomy_code"] == "207Q00000X"
        assert npi1_rows.iloc[0]["is_primary"] == True  # noqa: E712

    def test_multiple_taxonomies(self, raw_nppes_df):
        transformed = transform_nppes(raw_nppes_df, date(2026, 3, 4))
        tax_df = build_taxonomy_table(transformed)

        # NPI 3 (1111111111): 2 taxonomy slots
        npi3_rows = tax_df[tax_df["npi"] == "1111111111"]
        assert len(npi3_rows) == 2


class TestValidateNppes:
    def test_valid_data_passes(self, raw_nppes_df):
        # Need to rename and have enough rows for validation
        # Skip row count check by testing individual rules
        report = validate_nppes(raw_nppes_df)
        # Should pass column and format checks, but fail row count (only 3 rows)
        block_failures = [r for r in report.block_failures if "row_count" not in r.rule_name]
        assert len(block_failures) == 0

    def test_invalid_npi_blocks(self):
        df = pd.DataFrame(
            {
                "npi": ["BADNPI1234", "0987654321"],
                "entity_type_code": ["1", "2"],
            }
        )
        report = validate_nppes(df)
        format_failures = [r for r in report.block_failures if "format" in r.rule_name]
        assert len(format_failures) > 0


class TestRefProviderColumns:
    def test_all_columns_defined(self):
        """Verify REF_PROVIDER_COLUMNS matches expected output schema."""
        assert "npi" in REF_PROVIDER_COLUMNS
        assert "display_name" in REF_PROVIDER_COLUMNS
        assert "primary_taxonomy_code" in REF_PROVIDER_COLUMNS
        assert "is_active" in REF_PROVIDER_COLUMNS
        assert "state_fips" in REF_PROVIDER_COLUMNS
