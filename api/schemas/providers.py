"""Pydantic schemas for provider endpoints."""

from datetime import date

from pydantic import BaseModel, Field


class ProviderProfile(BaseModel):
    """Full provider practice profile (from mart_provider__practice_profile)."""
    npi: str = Field(..., description="10-digit NPI")
    entity_type: str | None = None
    display_name: str
    provider_last_name: str | None = None
    provider_first_name: str | None = None
    provider_credential: str | None = None
    provider_organization_name: str | None = None
    gender: str | None = None

    # Location
    practice_address_line_1: str | None = None
    practice_city: str | None = None
    practice_state: str | None = None
    practice_zip5: str | None = None
    state_fips: str | None = None
    state_name: str | None = None
    census_region: str | None = None

    # Specialty
    primary_taxonomy_code: str | None = None
    specialty_classification: str | None = None
    specialty_specialization: str | None = None
    specialty_display_name: str | None = None
    taxonomy_count: int | None = None

    # Attributes
    is_individual: bool | None = None
    is_organization: bool | None = None
    enumeration_date: date | None = None
    years_since_enumeration: float | None = None

    # Part B utilization
    total_services_rendered: float | None = None
    total_beneficiaries_served: int | None = None
    total_medicare_payments: float | None = None
    unique_hcpcs_count: int | None = None
    payment_per_beneficiary: float | None = None
    em_services_pct: float | None = None
    medicare_provider_type: str | None = None

    # Part D prescribing
    total_drugs_prescribed: int | None = None
    total_drug_cost: float | None = None
    unique_drugs_prescribed: int | None = None
    generic_rate_pct: float | None = None
    has_opioid_prescriptions: bool | None = None
    opioid_claims: int | None = None
    opioid_claim_rate_pct: float | None = None

    # Data flags
    has_part_b_data: bool | None = None
    has_part_d_data: bool | None = None

    model_config = {"from_attributes": True}


class ProviderSummary(BaseModel):
    """Compact provider listing for search results."""
    npi: str
    display_name: str
    entity_type: str | None = None
    practice_state: str | None = None
    practice_city: str | None = None
    specialty_classification: str | None = None
    total_medicare_payments: float | None = None

    model_config = {"from_attributes": True}


class ProviderSearchResponse(BaseModel):
    """Paginated provider search results."""
    items: list[ProviderSummary]
    total: int
    page: int
    page_size: int
    has_next: bool
