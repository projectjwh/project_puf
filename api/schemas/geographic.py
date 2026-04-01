"""Pydantic schemas for geographic endpoints."""

from pydantic import BaseModel


class StateSpending(BaseModel):
    """State-level spending variation."""
    state_fips: str
    state_name: str | None = None
    state_abbreviation: str | None = None
    census_region: str | None = None
    data_year: int

    total_beneficiaries: int | None = None
    ma_participation_rate: float | None = None
    actual_per_capita_costs: float | None = None
    standardized_per_capita_costs: float | None = None
    spending_index: float | None = None
    standardized_spending_index: float | None = None

    # Service breakdown
    ip_per_capita_costs: float | None = None
    op_per_capita_costs: float | None = None
    snf_per_capita_costs: float | None = None
    partb_per_capita_costs: float | None = None
    partd_per_capita_costs: float | None = None

    # Provider supply
    provider_count: int | None = None
    providers_per_1000_benes: float | None = None

    model_config = {"from_attributes": True}


class StateSummary(BaseModel):
    """Lightweight state summary for maps/dropdowns."""
    state_fips: str
    state_name: str | None = None
    state_abbreviation: str | None = None
    data_year: int
    total_beneficiaries: int | None = None
    total_providers: int | None = None
    actual_per_capita_costs: float | None = None
    spending_index: float | None = None
    ma_participation_rate: float | None = None

    model_config = {"from_attributes": True}
