"""Tests for pipelines._common.config.compute_data_year."""

from datetime import date

import pytest

from pipelines._common.config import compute_data_year


class TestComputeDataYear:
    """Verify data_year derivation from source lag_months configuration."""

    def test_lag_24_months_partb(self):
        """Part B (lag_months=24): 2026-04-02 -> data_year=2024."""
        result = compute_data_year("partb", date(2026, 4, 2))
        assert result == 2024

    def test_lag_0_months_nppes(self):
        """NPPES (lag_months=0): 2026-04-02 -> data_year=2026."""
        result = compute_data_year("nppes", date(2026, 4, 2))
        assert result == 2026

    def test_lag_6_months_quarterly(self):
        """Census population (lag_months=6): 2026-04-02 -> data_year=2025."""
        result = compute_data_year("census", date(2026, 4, 2))
        assert result == 2025

    def test_lag_24_months_geovar(self):
        """GeoVar (lag_months=24): same lag as Part B."""
        result = compute_data_year("geovar", date(2026, 7, 1))
        assert result == 2024

    def test_lag_3_months_pos(self):
        """POS facilities (lag_months=3): 2026-04-02 -> data_year=2026."""
        result = compute_data_year("pos", date(2026, 4, 2))
        assert result == 2026

    def test_lag_24_months_early_january(self):
        """Part B (lag_months=24) on Jan 15 2026 -> 2024.

        720 days before 2026-01-15 = ~2024-01-27.
        """
        result = compute_data_year("partb", date(2026, 1, 15))
        assert result == 2024

    def test_lag_6_months_crosses_year_boundary(self):
        """Census (lag_months=6): 2026-03-01 -> subtracts 180 days -> 2025-09-03 -> 2025."""
        result = compute_data_year("census", date(2026, 3, 1))
        assert result == 2025

    def test_defaults_to_today_when_no_date(self):
        """When run_date is None, uses today — just verify no crash."""
        result = compute_data_year("nppes")
        assert isinstance(result, int)
        assert result > 2020

    def test_unknown_source_raises(self):
        """Source not in sources.yaml raises KeyError."""
        with pytest.raises(KeyError, match="not_a_real_source"):
            compute_data_year("not_a_real_source", date(2026, 4, 2))

    def test_lag_1_month_pecos(self):
        """PECOS (lag_months=1): 2026-04-02 -> data_year=2026."""
        result = compute_data_year("pecos", date(2026, 4, 2))
        assert result == 2026

    def test_lag_12_months_cahps(self):
        """CAHPS (lag_months=12): 2026-04-02 -> subtracts ~360 days -> ~2025-04-07 -> 2025."""
        result = compute_data_year("cahps", date(2026, 4, 2))
        assert result == 2025
