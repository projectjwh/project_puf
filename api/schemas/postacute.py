"""Post-acute care domain Pydantic schemas."""

from pydantic import BaseModel


class SNFQuality(BaseModel):
    """Skilled Nursing Facility quality summary."""

    ccn: str
    facility_name: str | None = None
    provider_state: str | None = None
    overall_rating: int | None = None
    health_inspection_rating: int | None = None
    quality_rating: int | None = None
    staffing_rating: int | None = None
    rn_staffing_rating: int | None = None
    total_number_of_penalties: int | None = None
    total_fine_amount: float | None = None
    actual_avg_daily_rn_hours: float | None = None
    actual_rn_ratio: float | None = None
    staffing_consistency_flag: str | None = None

    model_config = {"from_attributes": True}


class HHAQuality(BaseModel):
    """Home Health Agency quality summary."""

    ccn: str
    facility_name: str | None = None
    provider_state: str | None = None
    data_year: int | None = None
    total_episodes: int | None = None
    total_hha_medicare_payment: float | None = None
    total_hha_visits: int | None = None
    avg_visits_per_episode: float | None = None
    avg_payment_per_episode: float | None = None

    model_config = {"from_attributes": True}


class HospiceQuality(BaseModel):
    """Hospice quality summary."""

    ccn: str
    facility_name: str | None = None
    provider_state: str | None = None
    data_year: int | None = None
    total_beneficiaries: int | None = None
    total_hospice_medicare_payment: float | None = None
    total_hospice_days: int | None = None
    avg_length_of_stay: float | None = None
    avg_payment_per_beneficiary: float | None = None

    model_config = {"from_attributes": True}
