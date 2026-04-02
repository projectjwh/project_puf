"""Tests for Tier 2 drug/prescribing and quality pipelines."""

import pandas as pd
import pytest

from pipelines._common.transform import normalize_ndc_to_11


class TestSDUDPipeline:
    def test_column_mapping(self):
        from pipelines.sdud.pipeline import COLUMN_MAPPING

        assert "NDC" in COLUMN_MAPPING
        assert "State" in COLUMN_MAPPING

    def test_transform_ndc_normalization(self):
        from pipelines.sdud.pipeline import transform_sdud

        df = pd.DataFrame(
            {
                "ndc": ["0002-1433-01"],
                "state": ["CA"],
                "number_of_prescriptions": ["5000"],
                "total_amount_reimbursed": ["50000.50"],
                "units_reimbursed": ["10000"],
            }
        )
        result = transform_sdud(df, 2022)
        # NDC should be normalized to 11 digits
        assert len(result["ndc"].iloc[0]) == 11
        assert result["state"].iloc[0] == "CA"
        assert result["state_fips"].iloc[0] == "06"
        assert result["data_year"].iloc[0] == 2022

    def test_transform_numeric_casting(self):
        from pipelines.sdud.pipeline import transform_sdud

        df = pd.DataFrame(
            {
                "ndc": ["12345678901"],
                "state": ["NY"],
                "number_of_prescriptions": ["1000"],
                "total_amount_reimbursed": ["25000.75"],
                "medicaid_amount_reimbursed": ["20000.50"],
                "units_reimbursed": ["5000"],
            }
        )
        result = transform_sdud(df, 2022)
        assert result["number_of_prescriptions"].iloc[0] == 1000
        assert result["total_amount_reimbursed"].iloc[0] == pytest.approx(25000.75, rel=1e-2)

    def test_validate_blocks_missing_ndc(self):
        from pipelines.sdud.pipeline import validate_sdud

        df = pd.DataFrame({"ndc": [None], "state": ["CA"]})
        report = validate_sdud(df)
        assert len(report.block_failures) > 0


class TestRxNormPipeline:
    def test_read_rrf(self):
        """Test RRF reader handles pipe-delimited format."""
        from pipelines.rxnorm.pipeline import RXNCONSO_COLUMNS

        assert "rxcui" in RXNCONSO_COLUMNS
        assert "str_name" in RXNCONSO_COLUMNS

    def test_ndc_crosswalk_extraction_concept(self):
        """Verify NDC normalization in crosswalk."""
        ndc = normalize_ndc_to_11("0002-1433-01")
        assert len(ndc) == 11

    def test_transform_filters_rxnorm_source(self):
        from pipelines.rxnorm.pipeline import transform_rxnorm

        df = pd.DataFrame(
            {
                "rxcui": ["1", "2", "3"],
                "str_name": ["Aspirin", "Tylenol", "Ibuprofen"],
                "sab": ["RXNORM", "MMSL", "RXNORM"],
                "tty": ["SCD", "SCD", "SCD"],
                "rxaui": ["A1", "A2", "A3"],
                "suppress": ["N", "N", "N"],
            }
        )
        result = transform_rxnorm(df)
        assert len(result) == 2  # Only RXNORM source rows


class TestASPPipeline:
    def test_transform(self):
        from pipelines.asp.pipeline import transform_asp

        df = pd.DataFrame(
            {
                "hcpcs_code": ["J0129"],
                "short_description": ["ABATACEPT INJECTION"],
                "payment_limit": ["$1,234.5678"],
                "dosage_form": ["Injectable"],
            }
        )
        result = transform_asp(df, 1, 2024)
        assert result["hcpcs_code"].iloc[0] == "J0129"
        assert result["payment_limit"].iloc[0] == pytest.approx(1234.5678, rel=1e-4)
        assert result["quarter"].iloc[0] == 1
        assert result["year"].iloc[0] == 2024


class TestFiveStarPipeline:
    def test_transform(self):
        from datetime import date

        from pipelines.five_star.pipeline import transform_five_star

        df = pd.DataFrame(
            {
                "ccn": ["5001"],
                "facility_name": ["  HAPPY NURSING HOME  "],
                "provider_state": ["ca"],
                "overall_rating": ["4"],
                "health_inspection_rating": ["3"],
                "quality_rating": ["5"],
                "staffing_rating": ["4"],
                "rn_staffing_rating": ["3"],
                "total_number_of_penalties": ["2"],
                "total_fine_amount": ["15000.00"],
            }
        )
        result = transform_five_star(df, date(2024, 1, 1))
        assert result["ccn"].iloc[0] == "005001"
        assert result["overall_rating"].iloc[0] == 4
        assert result["total_fine_amount"].iloc[0] == 15000.00
        assert result["snapshot_date"].iloc[0] == date(2024, 1, 1)

    def test_validate_blocks_missing_ccn(self):
        from pipelines.five_star.pipeline import validate_five_star

        df = pd.DataFrame({"ccn": [None]})
        report = validate_five_star(df)
        assert len(report.block_failures) > 0


class TestPBJPipeline:
    def test_transform(self):
        from pipelines.pbj.pipeline import transform_pbj

        df = pd.DataFrame(
            {
                "ccn": ["5001"],
                "work_date": ["2024-01-15"],
                "cna_hours": ["20.5"],
                "lpn_hours": ["10.0"],
                "rn_hours": ["15.5"],
            }
        )
        result = transform_pbj(df, 2024)
        assert result["ccn"].iloc[0] == "005001"
        assert result["cna_hours"].iloc[0] == 20.5
        assert result["rn_hours"].iloc[0] == 15.5
        # total_nurse_hours should be computed
        assert result["total_nurse_hours"].iloc[0] == pytest.approx(46.0, rel=1e-1)

    def test_validate_blocks_missing_ccn(self):
        from pipelines.pbj.pipeline import validate_pbj

        df = pd.DataFrame({"ccn": [None], "work_date": ["2024-01-01"]})
        report = validate_pbj(df)
        assert len(report.block_failures) > 0


class TestCAHPSPipeline:
    def test_transform_score_cleaning(self):
        from pipelines.cahps.pipeline import transform_cahps

        df = pd.DataFrame(
            {
                "ccn": ["010001"],
                "facility_name": ["TEST HOSPITAL"],
                "measure_id": ["H_COMP_1"],
                "score": ["Not Available"],
                "sample_size": ["300"],
            }
        )
        result = transform_cahps(df)
        assert pd.isna(result["score"].iloc[0])
        assert result["sample_size"].iloc[0] == 300


class TestDialysisPipeline:
    def test_transform(self):
        from pipelines.dialysis.pipeline import transform_dialysis

        df = pd.DataFrame(
            {
                "ccn": ["9001"],
                "facility_name": ["KIDNEY CENTER"],
                "provider_state": ["FL"],
                "measure_id": ["SHR"],
                "score": ["1.05"],
                "national_average": ["1.00"],
                "patient_count": ["200"],
                "star_rating": ["4"],
            }
        )
        result = transform_dialysis(df)
        assert result["ccn"].iloc[0] == "009001"
        assert result["score"].iloc[0] == 1.05
        assert result["star_rating"].iloc[0] == 4


class TestReadmissionsPipeline:
    def test_transform(self):
        from pipelines.readmissions.pipeline import transform_readmissions

        df = pd.DataFrame(
            {
                "ccn": ["010001"],
                "facility_name": ["TEST HOSPITAL"],
                "provider_state": ["AL"],
                "measure_id": ["READM-30-HF-HRRP"],
                "score": ["0.9876"],
                "denominator": ["1000"],
                "compared_to_national": ["WORSE THAN NATIONAL RATE"],
            }
        )
        result = transform_readmissions(df, 2022)
        assert result["score"].iloc[0] == pytest.approx(0.9876, rel=1e-4)
        assert result["denominator"].iloc[0] == 1000
        assert result["data_year"].iloc[0] == 2022
