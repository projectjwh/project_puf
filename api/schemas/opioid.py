"""Pydantic schemas for opioid monitoring endpoints."""

from pydantic import BaseModel


class OpioidByState(BaseModel):
    """State-level opioid prescribing metrics."""
    state_fips: str
    state_name: str | None = None
    state_abbreviation: str | None = None
    data_year: int

    total_prescribers: int | None = None
    opioid_prescribers: int | None = None
    high_opioid_prescribers: int | None = None
    opioid_prescriber_rate_pct: float | None = None

    total_opioid_claims: int | None = None
    opioid_claim_share_pct: float | None = None
    total_opioid_drug_cost: float | None = None
    opioid_cost_share_pct: float | None = None

    model_config = {"from_attributes": True}


class OpioidTopPrescriber(BaseModel):
    """Individual opioid prescriber with ranking."""
    prescriber_npi: str
    data_year: int
    display_name: str | None = None
    specialty_classification: str | None = None
    practice_state: str | None = None
    practice_city: str | None = None

    total_claims: int | None = None
    opioid_claims: int | None = None
    opioid_claim_rate_pct: float | None = None
    opioid_drug_cost: float | None = None
    generic_rate_pct: float | None = None
    state_opioid_rank: int | None = None

    model_config = {"from_attributes": True}
