"""Pydantic schemas for national KPI endpoints."""

from pydantic import BaseModel


class NationalKPI(BaseModel):
    """National KPI summary for a single year."""
    data_year: int

    # Provider counts
    active_providers_partb: int | None = None
    active_prescribers: int | None = None

    # Part B
    national_total_services: float | None = None
    national_total_beneficiaries: int | None = None
    national_total_medicare_payments: float | None = None
    avg_payment_per_beneficiary: float | None = None

    # Part D
    national_total_rx_claims: int | None = None
    national_total_drug_cost: float | None = None
    avg_generic_rate: float | None = None

    # Opioid
    national_opioid_claims: int | None = None
    opioid_prescribers: int | None = None
    high_opioid_prescribers: int | None = None

    # GeoVar
    national_per_capita_costs: float | None = None
    national_ma_rate: float | None = None

    # YOY
    yoy_payment_change_pct: float | None = None
    yoy_drug_cost_change_pct: float | None = None

    model_config = {"from_attributes": True}
