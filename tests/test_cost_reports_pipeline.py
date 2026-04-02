"""Tests for Cost Reports pipeline transforms."""

import pandas as pd
import pytest

from pipelines.cost_reports.pipeline import (
    extract_financial_metrics,
    transform_cost_reports,
    validate_cost_reports,
)


@pytest.fixture
def rpt_df():
    return pd.DataFrame(
        {
            "rpt_rec_num": ["100001", "100002"],
            "ccn": ["50001", "330001"],
            "report_status_code": ["1", "1"],
            "fiscal_year_begin": ["10/01/2021", "10/01/2021"],
            "fiscal_year_end": ["09/30/2022", "09/30/2022"],
            "last_report": ["Y", "Y"],
        }
    )


@pytest.fixture
def nmrc_df():
    """Simulated NMRC data with worksheet/line/column values."""
    return pd.DataFrame(
        {
            "RPT_REC_NUM": ["100001", "100001", "100001", "100001"],
            "WKSHT_CD": ["S300001", "S300001", "S300001", "S300001"],
            "LINE_NUM": ["0010", "0010", "0020", "0030"],
            "CLMN_NUM": ["0010", "0020", "0010", "0010"],
            "ITM_VAL_NUM": ["50000000", "55000000", "48000000", "7000000"],
        }
    )


class TestTransformCostReports:
    def test_ccn_padding(self, rpt_df):
        result = transform_cost_reports(rpt_df, 2022)
        assert result.iloc[0]["ccn"] == "050001"

    def test_data_year_added(self, rpt_df):
        result = transform_cost_reports(rpt_df, 2022)
        assert result.iloc[0]["data_year"] == 2022


class TestExtractFinancialMetrics:
    def test_metric_extraction(self, rpt_df, nmrc_df):
        rpt_df = transform_cost_reports(rpt_df, 2022)
        result = extract_financial_metrics(rpt_df, nmrc_df)

        # Check that financial metrics were extracted for rpt_rec_num 100001
        row = result[result["rpt_rec_num"] == 100001]
        assert len(row) == 1
        assert row.iloc[0]["total_patient_revenue"] == 50_000_000
        assert row.iloc[0]["total_operating_revenue"] == 55_000_000
        assert row.iloc[0]["total_operating_expenses"] == 48_000_000
        assert row.iloc[0]["net_income"] == 7_000_000

    def test_operating_margin(self, rpt_df, nmrc_df):
        rpt_df = transform_cost_reports(rpt_df, 2022)
        result = extract_financial_metrics(rpt_df, nmrc_df)

        row = result[result["rpt_rec_num"] == 100001]
        # Operating margin = (55M - 48M) / 55M = 0.1273
        assert row.iloc[0]["operating_margin"] == pytest.approx(0.1273, abs=0.001)


class TestValidateCostReports:
    def test_valid_data(self, rpt_df):
        report = validate_cost_reports(rpt_df)
        block_failures = [r for r in report.block_failures if "row_count" not in r.rule_name]
        assert len(block_failures) == 0
