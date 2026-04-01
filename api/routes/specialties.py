"""Specialty endpoints — taxonomy listing, comparison."""

from pydantic import BaseModel
from fastapi import APIRouter, Query

from api.services.database import query_pg

router = APIRouter()


class SpecialtySummary(BaseModel):
    specialty_classification: str
    provider_count: int
    total_services: float | None = None
    total_medicare_payments: float | None = None
    avg_payment_per_provider: float | None = None

    model_config = {"from_attributes": True}


class SpecialtyDetail(BaseModel):
    specialty_classification: str
    provider_count: int
    total_services: float | None = None
    total_medicare_payments: float | None = None
    avg_payment_per_provider: float | None = None
    total_drug_cost: float | None = None
    avg_generic_rate: float | None = None
    opioid_prescriber_count: int | None = None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[SpecialtySummary])
async def list_specialties(
    min_providers: int = Query(10, ge=1, description="Minimum provider count"),
) -> list[SpecialtySummary]:
    """List specialties with aggregate provider counts and payments."""
    rows = query_pg(
        """
        SELECT
            specialty_classification,
            COUNT(*) as provider_count,
            SUM(total_services_rendered) as total_services,
            SUM(total_medicare_payments) as total_medicare_payments,
            ROUND(AVG(total_medicare_payments)::numeric, 2) as avg_payment_per_provider
        FROM mart.mart_provider__practice_profile
        WHERE specialty_classification IS NOT NULL
        GROUP BY specialty_classification
        HAVING COUNT(*) >= :min_providers
        ORDER BY total_medicare_payments DESC NULLS LAST
        """,
        {"min_providers": min_providers},
    )
    return [SpecialtySummary(**r) for r in rows]


@router.get("/{specialty}", response_model=SpecialtyDetail)
async def get_specialty(specialty: str) -> SpecialtyDetail:
    """Get detailed metrics for a specific specialty."""
    from fastapi import HTTPException

    rows = query_pg(
        """
        SELECT
            specialty_classification,
            COUNT(*) as provider_count,
            SUM(total_services_rendered) as total_services,
            SUM(total_medicare_payments) as total_medicare_payments,
            ROUND(AVG(total_medicare_payments)::numeric, 2) as avg_payment_per_provider,
            SUM(total_drug_cost) as total_drug_cost,
            ROUND(AVG(generic_rate_pct)::numeric, 1) as avg_generic_rate,
            COUNT(CASE WHEN has_opioid_prescriptions THEN 1 END) as opioid_prescriber_count
        FROM mart.mart_provider__practice_profile
        WHERE specialty_classification ILIKE :specialty
        GROUP BY specialty_classification
        """,
        {"specialty": f"%{specialty}%"},
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"Specialty '{specialty}' not found")
    return SpecialtyDetail(**rows[0])
