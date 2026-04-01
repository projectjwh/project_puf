"""Tests for pipelines._common.transform."""

import pandas as pd
import pytest

from pipelines._common.transform import (
    add_data_year,
    add_snapshot_metadata,
    cast_types,
    clean_string_columns,
    compute_totals_from_averages,
    extract_zip5,
    normalize_fips_county,
    normalize_fips_state,
    normalize_ndc_to_11,
    normalize_npi,
    rename_columns,
    standardize_flags,
)


class TestNormalizeNpi:
    def test_valid_10_digit(self):
        s = pd.Series(["1234567890", "0987654321"])
        result = normalize_npi(s)
        assert result.tolist() == ["1234567890", "0987654321"]

    def test_pads_short_npi(self):
        s = pd.Series(["123456789"])
        result = normalize_npi(s)
        assert result.iloc[0] == "0123456789"

    def test_strips_whitespace(self):
        s = pd.Series(["  1234567890  "])
        result = normalize_npi(s)
        assert result.iloc[0] == "1234567890"

    def test_invalidates_non_numeric(self):
        s = pd.Series(["ABCDEFGHIJ"])
        result = normalize_npi(s)
        assert pd.isna(result.iloc[0])


class TestNormalizeFips:
    def test_state_padding(self):
        s = pd.Series(["6", "36", "1"])
        result = normalize_fips_state(s)
        assert result.tolist() == ["06", "36", "01"]

    def test_county_padding(self):
        s = pd.Series(["1001", "06001", "36061"])
        result = normalize_fips_county(s)
        assert result.tolist() == ["01001", "06001", "36061"]


class TestExtractZip5:
    def test_zip_plus_4(self):
        s = pd.Series(["90210-1234", "10001-0000"])
        result = extract_zip5(s)
        assert result.tolist() == ["90210", "10001"]

    def test_already_5_digit(self):
        s = pd.Series(["90210", "10001"])
        result = extract_zip5(s)
        assert result.tolist() == ["90210", "10001"]


class TestNormalizeNdc:
    def test_11_digit_passthrough(self):
        assert normalize_ndc_to_11("00002410101") == "00002410101"

    def test_10_digit_normalization(self):
        # 10-digit with 5-4-1 format → pad package
        result = normalize_ndc_to_11("1234567890")
        assert len(result) == 11

    def test_dashes_stripped(self):
        assert normalize_ndc_to_11("00002-4101-01") == "00002410101"


class TestRenameColumns:
    def test_renames_existing(self):
        df = pd.DataFrame({"old_name": [1, 2], "keep_this": [3, 4]})
        result = rename_columns(df, {"old_name": "new_name"})
        assert "new_name" in result.columns
        assert "keep_this" in result.columns

    def test_ignores_missing(self):
        df = pd.DataFrame({"col_a": [1]})
        result = rename_columns(df, {"nonexistent": "new_name"})
        assert list(result.columns) == ["col_a"]


class TestCastTypes:
    def test_string_cast(self):
        df = pd.DataFrame({"val": [1, 2, 3]})
        result = cast_types(df, {"val": "str"})
        assert result["val"].dtype == object

    def test_int_cast(self):
        df = pd.DataFrame({"val": ["1", "2", "bad"]})
        result = cast_types(df, {"val": "int"})
        assert result["val"].iloc[0] == 1
        assert pd.isna(result["val"].iloc[2])

    def test_float_cast(self):
        df = pd.DataFrame({"val": ["1.5", "2.7", "N/A"]})
        result = cast_types(df, {"val": "float"})
        assert result["val"].iloc[0] == pytest.approx(1.5)


class TestCleanStringColumns:
    def test_strips_and_uppercases(self):
        df = pd.DataFrame({"name": ["  john  ", "  Jane Doe  "]})
        result = clean_string_columns(df, ["name"])
        assert result["name"].tolist() == ["JOHN", "JANE DOE"]


class TestStandardizeFlags:
    def test_y_n_to_bool(self):
        df = pd.DataFrame({"flag": ["Y", "N", "Y", None]})
        result = standardize_flags(df, ["flag"])
        assert result["flag"].iloc[0] == True  # noqa: E712 — nullable boolean
        assert result["flag"].iloc[1] == False  # noqa: E712


class TestComputeTotalsFromAverages:
    def test_basic_computation(self, sample_partb_df):
        result = compute_totals_from_averages(
            sample_partb_df,
            avg_col="avg_submitted_charge_amount",
            count_col="service_count",
            total_col="total_submitted_charge",
        )
        # 150.00 * 500 = 75000.00
        assert result["total_submitted_charge"].iloc[0] == pytest.approx(75000.0)
        # 250.00 * 200 = 50000.00
        assert result["total_submitted_charge"].iloc[1] == pytest.approx(50000.0)


class TestSnapshotMetadata:
    def test_adds_loaded_at(self):
        df = pd.DataFrame({"val": [1]})
        result = add_snapshot_metadata(df, source="test")
        assert "_loaded_at" in result.columns
        assert "_source" in result.columns
        assert result["_source"].iloc[0] == "test"

    def test_adds_data_year(self):
        df = pd.DataFrame({"val": [1]})
        result = add_data_year(df, 2022)
        assert result["data_year"].iloc[0] == 2022

    def test_does_not_overwrite_data_year(self):
        df = pd.DataFrame({"val": [1], "data_year": [2021]})
        result = add_data_year(df, 2022)
        assert result["data_year"].iloc[0] == 2021
