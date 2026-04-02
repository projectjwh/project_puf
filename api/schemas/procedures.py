"""Pydantic schemas for procedure endpoints."""

from pydantic import BaseModel, Field


class ProcedureDetail(BaseModel):
    """Full procedure profile (from mart_procedure__utilization_trends)."""

    hcpcs_code: str = Field(..., description="HCPCS/CPT procedure code")
    hcpcs_description: str | None = None
    data_year: int

    # Volume
    total_services: float | None = None
    total_beneficiaries: float | None = None
    provider_count: int | None = None

    # Payment
    total_submitted_charge: float | None = None
    total_medicare_payment: float | None = None
    total_medicare_standardized: float | None = None
    avg_payment_per_service: float | None = None
    avg_charge_per_service: float | None = None
    avg_payment_per_beneficiary: float | None = None

    # Place-of-service mix
    pct_office: float | None = None
    pct_facility: float | None = None

    # RVU complexity
    work_rvu: float | None = None
    facility_pe_rvu: float | None = None
    malpractice_rvu: float | None = None
    total_rvu: float | None = None
    conversion_factor: float | None = None
    total_rvu_volume: float | None = None

    # YOY trends
    yoy_services_change_pct: float | None = None
    yoy_payment_change_pct: float | None = None

    model_config = {"from_attributes": True}


class ProcedureTopResult(BaseModel):
    """Compact procedure listing for top-N queries."""

    hcpcs_code: str
    hcpcs_description: str | None = None
    data_year: int
    total_services: float | None = None
    total_medicare_payment: float | None = None
    provider_count: int | None = None
    avg_payment_per_service: float | None = None
    total_rvu: float | None = None
    yoy_services_change_pct: float | None = None

    model_config = {"from_attributes": True}


class ProcedureTopResponse(BaseModel):
    """Paginated top procedure results."""

    items: list[ProcedureTopResult]
    total: int
    page: int
    page_size: int
    has_next: bool


class ProcedurePriceVariation(BaseModel):
    """Price variation for a procedure across states."""

    hcpcs_code: str
    hcpcs_description: str | None = None
    provider_state: str
    data_year: int

    # Volume
    provider_count: int | None = None
    total_services: float | None = None
    total_medicare_payment: float | None = None

    # Price distribution
    avg_payment: float | None = None
    min_payment: float | None = None
    max_payment: float | None = None
    stddev_payment: float | None = None
    p25_payment: float | None = None
    p75_payment: float | None = None
    coefficient_of_variation: float | None = None

    model_config = {"from_attributes": True}
