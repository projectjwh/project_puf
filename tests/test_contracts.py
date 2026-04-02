"""Tests for data contract YAML files and contract validation."""

import pandas as pd
import pytest

from pipelines._common.config import CONFIG_DIR
from pipelines._common.validate import (
    ValidationReport,
    _load_contract,
    validate_against_contract,
)

TIER_1_SOURCES = ["partb", "partd", "nppes", "geovar", "pos", "cost_reports"]

CONTRACTS_DIR = CONFIG_DIR / "contracts"

# Map source → its pipeline's COLUMN_MAPPING keys
PIPELINE_COLUMN_MAPPINGS: dict[str, dict[str, str]] = {}


def _get_column_mapping(source: str) -> dict[str, str]:
    """Import and return COLUMN_MAPPING for a given source."""
    if source == "partb":
        from pipelines.partb.pipeline import COLUMN_MAPPING

        return COLUMN_MAPPING
    elif source == "partd":
        from pipelines.partd.pipeline import COLUMN_MAPPING

        return COLUMN_MAPPING
    elif source == "nppes":
        from pipelines.nppes.pipeline import COLUMN_MAPPING

        return COLUMN_MAPPING
    elif source == "geovar":
        from pipelines.geovar.pipeline import COLUMN_MAPPING

        return COLUMN_MAPPING
    elif source == "pos":
        from pipelines.pos.pipeline import COLUMN_MAPPING

        return COLUMN_MAPPING
    elif source == "cost_reports":
        from pipelines.cost_reports.pipeline import RPT_COLUMN_MAPPING

        return RPT_COLUMN_MAPPING
    else:
        raise ValueError(f"Unknown source: {source}")


# ---------------------------------------------------------------------------
# 5.4a: Every Tier 1 source has a contract YAML file
# ---------------------------------------------------------------------------


class TestContractFilesExist:
    @pytest.mark.parametrize("source", TIER_1_SOURCES)
    def test_contract_yaml_exists(self, source: str) -> None:
        """Every Tier 1 source must have a contract YAML file."""
        contract_path = CONTRACTS_DIR / f"{source}.yaml"
        assert contract_path.exists(), f"Missing contract file: {contract_path}"


# ---------------------------------------------------------------------------
# 5.4b: Contract YAML is valid (loads without error, has required keys)
# ---------------------------------------------------------------------------


class TestContractYamlValid:
    @pytest.mark.parametrize("source", TIER_1_SOURCES)
    def test_contract_loads_without_error(self, source: str) -> None:
        """Contract YAML should parse without error."""
        contract = _load_contract(source)
        assert contract, f"Contract for {source} is empty"

    @pytest.mark.parametrize("source", TIER_1_SOURCES)
    def test_contract_has_required_keys(self, source: str) -> None:
        """Contract must have source, version, grain, and schemas keys."""
        contract = _load_contract(source)
        assert "source" in contract, f"Missing 'source' key in {source} contract"
        assert "version" in contract, f"Missing 'version' key in {source} contract"
        assert "grain" in contract, f"Missing 'grain' key in {source} contract"
        assert "schemas" in contract, f"Missing 'schemas' key in {source} contract"

    @pytest.mark.parametrize("source", TIER_1_SOURCES)
    def test_contract_has_default_schema(self, source: str) -> None:
        """Contract must have a default schema with columns."""
        contract = _load_contract(source)
        schemas = contract.get("schemas", {})
        assert "default" in schemas, f"Missing 'default' schema in {source} contract"
        default = schemas["default"]
        assert "columns" in default, f"Missing 'columns' in default schema for {source}"
        assert len(default["columns"]) > 0, f"No columns defined in {source} contract"

    @pytest.mark.parametrize("source", TIER_1_SOURCES)
    def test_contract_source_matches_filename(self, source: str) -> None:
        """The source field in the contract must match the filename."""
        contract = _load_contract(source)
        assert contract["source"] == source

    @pytest.mark.parametrize("source", TIER_1_SOURCES)
    def test_contract_columns_have_type(self, source: str) -> None:
        """Every column in the contract must have a type field."""
        contract = _load_contract(source)
        columns = contract["schemas"]["default"]["columns"]
        for col_name, spec in columns.items():
            assert "type" in spec, f"Column {col_name} missing 'type' in {source} contract"

    @pytest.mark.parametrize("source", TIER_1_SOURCES)
    def test_contract_columns_have_maps_to(self, source: str) -> None:
        """Every column in the contract must have a maps_to field."""
        contract = _load_contract(source)
        columns = contract["schemas"]["default"]["columns"]
        for col_name, spec in columns.items():
            assert "maps_to" in spec, f"Column {col_name} missing 'maps_to' in {source} contract"


# ---------------------------------------------------------------------------
# 5.4c: Contract columns match pipeline COLUMN_MAPPING keys
# ---------------------------------------------------------------------------


class TestContractMatchesPipeline:
    @pytest.mark.parametrize("source", TIER_1_SOURCES)
    def test_contract_columns_match_column_mapping(self, source: str) -> None:
        """Contract column names must be a superset of pipeline COLUMN_MAPPING keys."""
        contract = _load_contract(source)
        contract_cols = set(contract["schemas"]["default"]["columns"].keys())
        mapping = _get_column_mapping(source)
        mapping_keys = set(mapping.keys())

        missing_from_contract = mapping_keys - contract_cols
        assert len(missing_from_contract) == 0, (
            f"Pipeline COLUMN_MAPPING keys missing from {source} contract: {sorted(missing_from_contract)}"
        )

    @pytest.mark.parametrize("source", TIER_1_SOURCES)
    def test_contract_maps_to_matches_column_mapping_values(self, source: str) -> None:
        """Contract maps_to values should match COLUMN_MAPPING values."""
        contract = _load_contract(source)
        contract_cols = contract["schemas"]["default"]["columns"]
        mapping = _get_column_mapping(source)

        for source_col, canonical_name in mapping.items():
            if source_col in contract_cols:
                contract_maps_to = contract_cols[source_col].get("maps_to", "")
                assert contract_maps_to == canonical_name, (
                    f"Contract maps_to mismatch for {source_col}: contract={contract_maps_to}, mapping={canonical_name}"
                )


# ---------------------------------------------------------------------------
# 5.4d: validate_against_contract with a matching DataFrame (passes)
# ---------------------------------------------------------------------------


class TestValidateAgainstContractPasses:
    def test_matching_dataframe_passes(self) -> None:
        """A DataFrame with all required columns should pass contract validation."""
        df = pd.DataFrame(
            {
                "Rndrng_NPI": ["1234567890", "0987654321"],
                "HCPCS_Cd": ["99213", "99214"],
                "Place_Of_Srvc": ["O", "F"],
                "Tot_Srvcs": ["100", "200"],
            }
        )
        report = ValidationReport(source="partb")
        validate_against_contract(df, "partb", 2022, report)
        # Should not have any BLOCK failures (row count WARN is expected for small test data)
        block_failures = [r for r in report.results if r.severity == "BLOCK" and not r.passed]
        assert len(block_failures) == 0


# ---------------------------------------------------------------------------
# 5.4e: validate_against_contract with a missing required column (BLOCK)
# ---------------------------------------------------------------------------


class TestValidateAgainstContractBlocks:
    def test_missing_required_column_blocks(self) -> None:
        """A DataFrame missing a required column should produce a BLOCK failure."""
        # partb contract requires Rndrng_NPI and HCPCS_Cd
        df = pd.DataFrame(
            {
                "HCPCS_Cd": ["99213", "99214"],
                "Place_Of_Srvc": ["O", "F"],
            }
        )
        report = ValidationReport(source="partb")
        validate_against_contract(df, "partb", 2022, report)
        block_failures = [r for r in report.results if r.severity == "BLOCK" and not r.passed]
        assert len(block_failures) > 0
        # Should mention the missing column
        assert any("Rndrng_NPI" in r.message for r in block_failures)

    def test_all_required_columns_missing_blocks(self) -> None:
        """A DataFrame missing all required columns should BLOCK."""
        df = pd.DataFrame({"some_random_column": ["a", "b"]})
        report = ValidationReport(source="partb")
        validate_against_contract(df, "partb", 2022, report)
        block_failures = [r for r in report.results if r.severity == "BLOCK" and not r.passed]
        assert len(block_failures) > 0


# ---------------------------------------------------------------------------
# 5.4f: validate_against_contract with an unexpected column (WARN)
# ---------------------------------------------------------------------------


class TestValidateAgainstContractWarns:
    def test_unexpected_column_warns(self) -> None:
        """A DataFrame with columns not in the contract should produce a WARN."""
        df = pd.DataFrame(
            {
                "Rndrng_NPI": ["1234567890"],
                "HCPCS_Cd": ["99213"],
                "EXTRA_COLUMN_NOT_IN_CONTRACT": ["surprise"],
            }
        )
        report = ValidationReport(source="partb")
        validate_against_contract(df, "partb", 2022, report)
        warnings = [r for r in report.results if r.severity == "WARN" and not r.passed]
        unexpected_warns = [r for r in warnings if "unexpected" in r.rule_name]
        assert len(unexpected_warns) > 0


# ---------------------------------------------------------------------------
# 5.4g: validate_against_contract with wrong row count (WARN)
# ---------------------------------------------------------------------------


class TestValidateAgainstContractRowCount:
    def test_row_count_below_minimum_warns(self) -> None:
        """A DataFrame with fewer rows than contract minimum should WARN."""
        # partb contract: min 8M, max 13M — our test df has 2 rows
        df = pd.DataFrame(
            {
                "Rndrng_NPI": ["1234567890", "0987654321"],
                "HCPCS_Cd": ["99213", "99214"],
            }
        )
        report = ValidationReport(source="partb")
        validate_against_contract(df, "partb", 2022, report)
        row_count_results = [r for r in report.results if r.rule_name == "row_count_range"]
        assert len(row_count_results) == 1
        assert not row_count_results[0].passed
        # partb row_count severity is WARN, so it should not be a BLOCK
        assert row_count_results[0].severity == "WARN"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestContractEdgeCases:
    def test_missing_contract_file_is_noop(self) -> None:
        """If contract file doesn't exist, validation should not add any results."""
        df = pd.DataFrame({"col1": [1, 2]})
        report = ValidationReport(source="nonexistent")
        validate_against_contract(df, "nonexistent_source", 2022, report)
        assert len(report.results) == 0

    def test_load_contract_returns_empty_for_missing(self) -> None:
        """_load_contract should return empty dict for missing source."""
        result = _load_contract("totally_nonexistent_source")
        assert result == {}

    def test_load_contract_returns_dict_for_existing(self) -> None:
        """_load_contract should return a non-empty dict for a real source."""
        result = _load_contract("partb")
        assert isinstance(result, dict)
        assert "source" in result

    def test_nppes_contract_row_count_is_block(self) -> None:
        """NPPES contract has BLOCK severity for row count — verify it blocks."""
        df = pd.DataFrame(
            {
                "NPI": ["1234567890"],
                "Entity Type Code": ["1"],
            }
        )
        report = ValidationReport(source="nppes")
        validate_against_contract(df, "nppes", 0, report)
        row_count_results = [r for r in report.results if r.rule_name == "row_count_range"]
        assert len(row_count_results) == 1
        assert row_count_results[0].severity == "BLOCK"
        assert not row_count_results[0].passed
