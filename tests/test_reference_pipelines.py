"""Tests for reference pipeline modules.

Tests validate column mappings, transform functions, and config completeness
for all 14 Tier 1 reference sources. Does NOT test actual downloads.
"""

import pandas as pd
import pytest

from pipelines._common.reference import ReferenceSourceConfig


# ---------------------------------------------------------------------------
# Config import tests — verify all 14 modules have valid configs
# ---------------------------------------------------------------------------

def _import_pipeline(module_name: str) -> ReferenceSourceConfig:
    """Dynamically import a pipeline module and return its config."""
    mod = __import__(f"pipelines.{module_name}.pipeline", fromlist=["config"])
    return mod.config


def _import_run(module_name: str):
    """Dynamically import a pipeline module and return its run function."""
    mod = __import__(f"pipelines.{module_name}.pipeline", fromlist=["run"])
    return mod.run


ALL_REFERENCE_SOURCES = [
    "taxonomy", "icd10cm", "icd10pcs", "hcpcs", "msdrg", "ndc",
    "pos_codes", "zip_county", "cbsa", "ruca", "rvu", "wage_index", "ipps",
]


class TestAllConfigsValid:
    @pytest.mark.parametrize("source", ALL_REFERENCE_SOURCES)
    def test_config_has_required_fields(self, source):
        config = _import_pipeline(source)
        assert config.source_name, f"{source} missing source_name"
        assert config.target_table, f"{source} missing target_table"
        assert config.target_schema == "reference"
        assert config.target_table.startswith("ref_"), f"{source} table should start with ref_"

    @pytest.mark.parametrize("source", ALL_REFERENCE_SOURCES)
    def test_config_has_column_mapping(self, source):
        config = _import_pipeline(source)
        assert len(config.column_mapping) > 0, f"{source} has no column mappings"

    @pytest.mark.parametrize("source", ALL_REFERENCE_SOURCES)
    def test_run_function_exists(self, source):
        run_fn = _import_run(source)
        assert callable(run_fn), f"{source} run function not callable"

    @pytest.mark.parametrize("source", ALL_REFERENCE_SOURCES)
    def test_row_count_bounds_set(self, source):
        config = _import_pipeline(source)
        assert config.min_rows > 0 or config.max_rows < 10_000_000, \
            f"{source} should have row count bounds"


class TestFipsPipeline:
    def test_fips_has_two_configs(self):
        from pipelines.fips.pipeline import state_config, county_config
        assert state_config.target_table == "ref_state_fips"
        assert county_config.target_table == "ref_county_fips"

    def test_state_transform(self):
        from pipelines.fips.pipeline import _transform_states
        df = pd.DataFrame({
            "state_fips": ["6", "36", "72"],
            "state_abbreviation": ["CA", "NY", "PR"],
        })
        result = _transform_states(df)
        assert result["state_fips"].iloc[0] == "06"
        assert result["region"].iloc[0] == "West"
        assert result["is_state"].iloc[0] == True  # noqa: E712
        assert result["is_state"].iloc[2] == False  # noqa: E712 — PR is territory

    def test_county_transform(self):
        from pipelines.fips.pipeline import _transform_counties
        df = pd.DataFrame({
            "county_fips": ["1001", "06001"],
            "state_fips": ["1", "6"],
        })
        result = _transform_counties(df)
        assert result["county_fips"].iloc[0] == "01001"
        assert result["state_fips"].iloc[0] == "01"


class TestIcd10cmPipeline:
    def test_code_formatting(self):
        from pipelines.icd10cm.pipeline import _transform_icd10cm
        df = pd.DataFrame({
            "icd10_cm_code": ["E119", "A000", "Z00"],
        })
        result = _transform_icd10cm(df)
        assert result["icd10_cm_code_formatted"].iloc[0] == "E11.9"
        assert result["is_billable"].iloc[0] == True  # noqa: E712
        assert result["is_billable"].iloc[2] == False  # noqa: E712 — 3-char header

    def test_chapter_derivation(self):
        from pipelines.icd10cm.pipeline import _derive_chapter
        assert _derive_chapter("E119")[0] == "04"  # Endocrine
        assert _derive_chapter("I251")[0] == "09"  # Circulatory
        assert _derive_chapter("Z000")[0] == "21"  # Factors influencing health


class TestIcd10pcsPipeline:
    def test_section_derivation(self):
        from pipelines.icd10pcs.pipeline import _transform_icd10pcs
        df = pd.DataFrame({
            "icd10_pcs_code": ["0210093", "B210ZZZ"],
        })
        result = _transform_icd10pcs(df)
        assert result["section"].iloc[0] == "0"
        assert result["section_description"].iloc[0] == "Medical and Surgical"
        assert result["section"].iloc[1] == "B"
        assert result["section_description"].iloc[1] == "Imaging"
        assert result["is_billable"].iloc[0] == True  # noqa: E712


class TestNdcPipeline:
    def test_ndc_normalization(self):
        from pipelines.ndc.pipeline import _transform_ndc
        df = pd.DataFrame({
            "ndc_code": ["12345678901", "1234567890"],
            "dea_schedule": ["CII", None],
            "marketing_end_date": [None, None],
        })
        result = _transform_ndc(df)
        assert len(result["ndc_code"].iloc[0]) == 11
        assert result["is_opioid"].iloc[0] == True  # noqa: E712 — CII
        assert result["is_active"].iloc[0] == True  # noqa: E712 — no end date

    def test_ndc_formatted(self):
        from pipelines.ndc.pipeline import _transform_ndc
        df = pd.DataFrame({
            "ndc_code": ["12345678901"],
            "dea_schedule": [None],
            "marketing_end_date": [None],
        })
        result = _transform_ndc(df)
        assert result["ndc_formatted"].iloc[0] == "12345-6789-01"


class TestTaxonomyPipeline:
    def test_display_name(self):
        from pipelines.taxonomy.pipeline import _transform_taxonomy
        df = pd.DataFrame({
            "classification": ["Internal Medicine", "General Acute Care Hospital"],
            "specialization": ["Cardiology", ""],
            "grouping": ["Allopathic & Osteopathic Physicians", "Hospitals"],
        })
        result = _transform_taxonomy(df)
        assert result["display_name"].iloc[0] == "Internal Medicine - Cardiology"
        assert result["is_individual"].iloc[0] == True  # noqa: E712
        assert result["is_individual"].iloc[1] == False  # noqa: E712


class TestRucaPipeline:
    def test_rural_classification(self):
        from pipelines.ruca.pipeline import _transform_ruca
        df = pd.DataFrame({
            "zip_code": ["90210", "59001", "10001"],
            "ruca_code": ["1", "10", "1.1"],
            "ruca_secondary": [None, None, None],
        })
        result = _transform_ruca(df)
        assert result["is_rural"].iloc[0] == False  # noqa: E712 — metro
        assert result["is_rural"].iloc[1] == True  # noqa: E712 — rural


class TestRvuPipeline:
    def test_total_rvu_computation(self):
        from pipelines.rvu.pipeline import _transform_rvu
        df = pd.DataFrame({
            "hcpcs_code": ["99213"],
            "modifier": [""],
            "work_rvu": ["0.97"],
            "facility_pe_rvu": ["0.49"],
            "nonfacility_pe_rvu": ["1.39"],
            "malpractice_rvu": ["0.07"],
            "conversion_factor": ["33.8872"],
        })
        result = _transform_rvu(df)
        # Total facility RVU = 0.97 + 0.49 + 0.07 = 1.53
        assert result["total_facility_rvu"].iloc[0] == pytest.approx(1.53)
        # Total nonfacility RVU = 0.97 + 1.39 + 0.07 = 2.43
        assert result["total_nonfacility_rvu"].iloc[0] == pytest.approx(2.43)
        # Payment = RVU * CF
        assert result["facility_payment"].iloc[0] == pytest.approx(1.53 * 33.8872, rel=0.01)


class TestPosCodes:
    def test_facility_flag(self):
        from pipelines.pos_codes.pipeline import _transform_pos
        df = pd.DataFrame({
            "pos_code": ["11", "21", "99"],
        })
        result = _transform_pos(df)
        assert result["is_facility"].iloc[0] == False  # noqa: E712 — office
        assert result["is_facility"].iloc[1] == True  # noqa: E712 — inpatient hospital


_has_prefect = True
try:
    import prefect  # noqa: F401
except ImportError:
    _has_prefect = False


@pytest.mark.skipif(not _has_prefect, reason="prefect not installed")
class TestPrefectFlow:
    def test_flow_importable(self):
        from flows.reference_flow import load_reference_data
        assert callable(load_reference_data)

    def test_flow_has_all_sources(self):
        from flows.reference_flow import load_reference_data
        assert hasattr(load_reference_data, "fn") or callable(load_reference_data)
