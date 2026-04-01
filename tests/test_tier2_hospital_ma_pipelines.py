"""Tests for Tier 2 hospital financial, charges, DME, and MA pipelines."""

import pandas as pd
import pytest

from pipelines._common.transform import normalize_npi, normalize_fips_county


class TestCostReportsSNFPipeline:
    def test_staging_columns(self):
        from pipelines.cost_reports_snf.pipeline import STAGING_COLUMNS
        assert "ccn" in STAGING_COLUMNS
        assert "operating_margin" in STAGING_COLUMNS

    def test_validate(self):
        from pipelines.cost_reports_snf.pipeline import validate_snf_cr
        df = pd.DataFrame({"rpt_rec_num": ["1"], "ccn": ["005001"]})
        report = validate_snf_cr(df)
        assert report.passed


class TestCostReportsHHAPipeline:
    def test_staging_columns(self):
        from pipelines.cost_reports_hha.pipeline import STAGING_COLUMNS
        assert "ccn" in STAGING_COLUMNS

    def test_validate(self):
        from pipelines.cost_reports_hha.pipeline import validate_hha_cr
        df = pd.DataFrame({"rpt_rec_num": ["1"], "ccn": ["007001"]})
        report = validate_hha_cr(df)
        assert report.passed


class TestCostReportsHospicePipeline:
    def test_staging_columns(self):
        from pipelines.cost_reports_hospice.pipeline import STAGING_COLUMNS
        assert "ccn" in STAGING_COLUMNS

    def test_validate(self):
        from pipelines.cost_reports_hospice.pipeline import validate_hospice_cr
        df = pd.DataFrame({"rpt_rec_num": ["1"], "ccn": ["008001"]})
        report = validate_hospice_cr(df)
        assert report.passed


class TestHospitalGeneralPipeline:
    def test_column_mapping(self):
        from pipelines.hospital_general.pipeline import COLUMN_MAPPING
        assert "Facility ID" in COLUMN_MAPPING

    def test_transform(self):
        from pipelines.hospital_general.pipeline import transform_hospital_general
        df = pd.DataFrame({
            "ccn": ["10001"],
            "facility_name": ["  TEST HOSPITAL  "],
            "state": ["ca"],
            "hospital_type": ["Acute Care Hospitals"],
            "emergency_services": ["Yes"],
            "overall_rating": ["4"],
        })
        result = transform_hospital_general(df)
        assert result["ccn"].iloc[0] == "010001"
        assert result["state"].iloc[0] == "CA"
        assert result["emergency_services"].iloc[0] == True  # noqa: E712
        assert result["overall_rating"].iloc[0] == 4

    def test_transform_not_available(self):
        from pipelines.hospital_general.pipeline import transform_hospital_general
        df = pd.DataFrame({
            "ccn": ["010001"],
            "facility_name": ["TEST"],
            "overall_rating": ["Not Available"],
        })
        result = transform_hospital_general(df)
        assert pd.isna(result["overall_rating"].iloc[0])


class TestChargesPipeline:
    def test_transform_totals(self):
        from pipelines.charges.pipeline import transform_charges
        df = pd.DataFrame({
            "ccn": ["010001"],
            "drg_code": ["470"],
            "total_discharges": ["100"],
            "avg_covered_charges": ["$50,000"],
            "avg_total_payments": ["15000"],
            "avg_medicare_payments": ["12000"],
            "provider_state": ["AL"],
        })
        result = transform_charges(df, 2022)
        assert result["total_covered_charges"].iloc[0] == pytest.approx(5000000.0, rel=1e-2)
        assert result["provider_state_fips"].iloc[0] == "01"

    def test_validate(self):
        from pipelines.charges.pipeline import validate_charges
        df = pd.DataFrame({
            "ccn": ["010001"], "drg_code": ["470"],
        })
        report = validate_charges(df)
        assert report.passed


class TestDMEPipeline:
    def test_transform_npi(self):
        from pipelines.dme.pipeline import transform_dme
        df = pd.DataFrame({
            "supplier_npi": ["1234567890"],
            "referring_npi": ["987654321"],
            "supplier_name": ["  DME SUPPLY CO  "],
            "hcpcs_code": ["e0100"],
            "number_of_services": ["150"],
            "number_of_beneficiaries": ["50"],
            "avg_submitted_charge": ["250.00"],
        })
        result = transform_dme(df, 2022)
        assert result["supplier_npi"].iloc[0] == "1234567890"
        assert result["referring_npi"].iloc[0] == "0987654321"
        assert result["hcpcs_code"].iloc[0] == "E0100"
        assert result["data_year"].iloc[0] == 2022

    def test_validate_blocks_missing_supplier(self):
        from pipelines.dme.pipeline import validate_dme
        df = pd.DataFrame({"supplier_npi": [None], "hcpcs_code": ["E0100"]})
        report = validate_dme(df)
        assert len(report.block_failures) > 0


class TestMAEnrollmentPipeline:
    def test_transform_penetration_rate(self):
        from pipelines.ma_enrollment.pipeline import transform_ma_enrollment
        df = pd.DataFrame({
            "county_fips": ["6037"],
            "state": ["CA"],
            "enrollment_count": ["100000"],
            "eligible_count": ["300000"],
            "penetration_rate": ["33.3%"],
        })
        result = transform_ma_enrollment(df, 2022)
        assert result["county_fips"].iloc[0] == "06037"
        assert result["state_fips"].iloc[0] == "06"
        assert result["penetration_rate"].iloc[0] == pytest.approx(0.333, rel=1e-2)

    def test_transform_penetration_decimal_format(self):
        from pipelines.ma_enrollment.pipeline import transform_ma_enrollment
        df = pd.DataFrame({
            "county_fips": ["06037"],
            "enrollment_count": ["100000"],
            "penetration_rate": ["0.333"],
        })
        result = transform_ma_enrollment(df, 2022)
        assert result["penetration_rate"].iloc[0] == pytest.approx(0.333, rel=1e-2)


class TestMABenchmarksPipeline:
    def test_transform(self):
        from pipelines.ma_benchmarks.pipeline import transform_ma_benchmarks
        df = pd.DataFrame({
            "county_fips": ["6037"],
            "county_name": ["Los Angeles"],
            "ffs_per_capita": ["$10,500.00"],
            "ma_benchmark": ["$11,000.00"],
            "risk_score": ["1.05"],
        })
        result = transform_ma_benchmarks(df, 2024)
        assert result["county_fips"].iloc[0] == "06037"
        assert result["ffs_per_capita"].iloc[0] == 10500.00
        assert result["ma_benchmark"].iloc[0] == 11000.00
        assert result["year"].iloc[0] == 2024

    def test_validate(self):
        from pipelines.ma_benchmarks.pipeline import validate_ma_benchmarks
        df = pd.DataFrame({"county_fips": ["06037"]})
        report = validate_ma_benchmarks(df)
        assert report.passed
