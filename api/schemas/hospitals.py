"""Hospital domain Pydantic schemas."""

from pydantic import BaseModel


class HospitalFinancialProfile(BaseModel):
    """Hospital financial profile from cost reports."""

    ccn: str
    facility_name: str | None = None
    provider_state: str | None = None
    hospital_type: str | None = None
    ownership_type: str | None = None
    data_year: int | None = None
    cms_overall_rating: int | None = None
    total_patient_revenue: float | None = None
    total_operating_expenses: float | None = None
    net_income: float | None = None
    operating_margin: float | None = None
    cost_to_charge_ratio: float | None = None
    total_beds_available: int | None = None
    total_discharges: int | None = None
    occupancy_rate: float | None = None
    revenue_per_discharge: float | None = None

    model_config = {"from_attributes": True}


class HospitalPerformance(BaseModel):
    """Hospital discharge performance with DRG mix."""

    ccn: str
    facility_name: str | None = None
    provider_state: str | None = None
    data_year: int | None = None
    unique_drg_count: int | None = None
    total_discharges: int | None = None
    case_mix_index: float | None = None
    total_medicare_payments: float | None = None
    avg_payment_per_discharge: float | None = None

    model_config = {"from_attributes": True}


class HospitalReadmission(BaseModel):
    """Hospital readmission summary."""

    ccn: str
    facility_name: str | None = None
    provider_state: str | None = None
    data_year: int | None = None
    measure_count: int | None = None
    avg_readmission_rate: float | None = None
    measures_worse_than_national: int | None = None
    measures_better_than_national: int | None = None
    has_penalty_risk: bool | None = None

    model_config = {"from_attributes": True}


class HospitalChargeVariation(BaseModel):
    """Hospital charge variation by DRG."""

    ccn: str
    facility_name: str | None = None
    drg_code: str
    drg_description: str | None = None
    data_year: int | None = None
    total_discharges: int | None = None
    avg_covered_charges: float | None = None
    avg_total_payments: float | None = None
    charge_to_payment_ratio: float | None = None

    model_config = {"from_attributes": True}
