"""Tests for Tier 2 institutional utilization and fee schedule pipelines."""

import pandas as pd
import pytest

from pipelines._common.transform import compute_totals_from_averages


class TestInpatientPipeline:
    def test_column_mapping(self):
        from pipelines.inpatient.pipeline import COLUMN_MAPPING
        assert "Rndrng_Prvdr_CCN" in COLUMN_MAPPING
        assert COLUMN_MAPPING["DRG_Cd"] == "drg_code"

    def test_transform_totals_from_averages(self):
        from pipelines.inpatient.pipeline import transform_inpatient
        df = pd.DataFrame({
            "ccn": ["010001"],
            "drg_code": ["470"],
            "total_discharges": ["100"],
            "avg_covered_charges": ["$50,000.00"],
            "avg_total_payments": ["15000"],
            "avg_medicare_payments": ["12000"],
            "provider_state": ["AL"],
        })
        result = transform_inpatient(df, 2022)
        assert result["total_covered_charges"].iloc[0] == pytest.approx(5000000.0, rel=1e-2)
        assert result["total_payments"].iloc[0] == pytest.approx(1500000.0, rel=1e-2)
        assert result["data_year"].iloc[0] == 2022

    def test_transform_ccn_padding(self):
        from pipelines.inpatient.pipeline import transform_inpatient
        df = pd.DataFrame({
            "ccn": ["10001"],
            "drg_code": ["470"],
            "total_discharges": ["50"],
            "avg_covered_charges": ["1000"],
            "avg_total_payments": ["500"],
            "avg_medicare_payments": ["400"],
        })
        result = transform_inpatient(df, 2022)
        assert result["ccn"].iloc[0] == "010001"

    def test_transform_drg_extraction(self):
        from pipelines.inpatient.pipeline import transform_inpatient
        df = pd.DataFrame({
            "ccn": ["010001"],
            "drg_description": ["470 - MAJOR JOINT REPLACEMENT"],
            "total_discharges": ["10"],
            "avg_covered_charges": ["1000"],
            "avg_total_payments": ["500"],
            "avg_medicare_payments": ["400"],
        })
        result = transform_inpatient(df, 2022)
        assert result["drg_code"].iloc[0] == "470"

    def test_validate_blocks_missing_ccn(self):
        from pipelines.inpatient.pipeline import validate_inpatient
        df = pd.DataFrame({"ccn": [None], "drg_code": ["470"]})
        report = validate_inpatient(df)
        assert len(report.block_failures) > 0


class TestSNFPipeline:
    def test_column_mapping(self):
        from pipelines.snf.pipeline import COLUMN_MAPPING
        assert "Rndrng_Prvdr_CCN" in COLUMN_MAPPING

    def test_transform(self):
        from pipelines.snf.pipeline import transform_snf
        df = pd.DataFrame({
            "ccn": ["5001"],
            "facility_name": ["  SUNNY MEADOWS SNF  "],
            "provider_state": ["ca"],
            "total_stays": ["500"],
            "total_snf_charge": ["1000000"],
            "avg_length_of_stay": ["25.5"],
        })
        result = transform_snf(df, 2022)
        assert result["ccn"].iloc[0] == "005001"
        assert result["provider_state"].iloc[0] == "CA"
        assert result["total_stays"].iloc[0] == 500
        assert result["data_year"].iloc[0] == 2022


class TestHHAPipeline:
    def test_transform(self):
        from pipelines.hha.pipeline import transform_hha
        df = pd.DataFrame({
            "ccn": ["7001"],
            "facility_name": ["HOME HEALTH AGENCY"],
            "provider_state": ["NY"],
            "total_episodes": ["1000"],
            "total_hha_charge": ["500000"],
            "total_hha_visits": ["5000"],
            "avg_visits_per_episode": ["5.0"],
        })
        result = transform_hha(df, 2022)
        assert result["total_episodes"].iloc[0] == 1000
        assert result["total_hha_visits"].iloc[0] == 5000


class TestHospicePipeline:
    def test_transform(self):
        from pipelines.hospice.pipeline import transform_hospice
        df = pd.DataFrame({
            "ccn": ["8001"],
            "facility_name": ["COMFORT HOSPICE"],
            "provider_state": ["TX"],
            "total_beneficiaries": ["200"],
            "total_hospice_charge": ["800000"],
            "avg_length_of_stay": ["90.5"],
        })
        result = transform_hospice(df, 2022)
        assert result["total_beneficiaries"].iloc[0] == 200
        assert result["avg_length_of_stay"].iloc[0] == 90.5


class TestCLFSPipeline:
    def test_transform(self):
        from pipelines.clfs.pipeline import transform_clfs
        df = pd.DataFrame({
            "hcpcs_code": ["80047"],
            "short_description": ["METABOLIC PANEL"],
            "national_limit_amount": ["$14.50"],
        })
        result = transform_clfs(df, 2024)
        assert result["hcpcs_code"].iloc[0] == "80047"
        assert result["national_limit_amount"].iloc[0] == 14.50
        assert result["effective_year"].iloc[0] == 2024


class TestDMEPOSFeesPipeline:
    def test_transform(self):
        from pipelines.dmepos_fees.pipeline import transform_dmepos
        df = pd.DataFrame({
            "hcpcs_code": ["E0100"],
            "modifier": ["NU"],
            "state": ["CA"],
            "fee_amount": ["$250.00"],
        })
        result = transform_dmepos(df, "2024Q1")
        assert result["fee_amount"].iloc[0] == 250.00
        assert result["effective_quarter"].iloc[0] == "2024Q1"


class TestSNFPPSPipeline:
    def test_transform(self):
        from pipelines.snf_pps.pipeline import transform_snf_pps
        df = pd.DataFrame({
            "pdpm_group": ["PT - Ultra High"],
            "component": ["Physical Therapy"],
            "rate": ["$583.48"],
            "case_mix_index": ["1.4567"],
        })
        result = transform_snf_pps(df, 2024)
        assert result["rate"].iloc[0] == pytest.approx(583.48, rel=1e-2)
        assert result["fiscal_year"].iloc[0] == 2024
