"""Drug domain Pydantic schemas."""

from pydantic import BaseModel


class MedicaidDrugUtilization(BaseModel):
    """State-level Medicaid drug utilization."""

    state: str
    state_name: str | None = None
    data_year: int | None = None
    unique_drugs: int | None = None
    total_prescriptions: int | None = None
    total_reimbursed: float | None = None
    avg_cost_per_prescription: float | None = None
    medicaid_share_pct: float | None = None

    model_config = {"from_attributes": True}


class DrugPriceTrend(BaseModel):
    """ASP quarterly price trend."""

    hcpcs_code: str
    short_description: str | None = None
    payment_limit: float | None = None
    dosage_form: str | None = None
    quarter: int | None = None
    year: int | None = None

    model_config = {"from_attributes": True}
