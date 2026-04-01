"""National KPI endpoints."""

from fastapi import APIRouter, Query

from api.schemas.national import NationalKPI
from api.services.database import query_pg

router = APIRouter()


@router.get("/kpis", response_model=list[NationalKPI])
async def get_national_kpis() -> list[NationalKPI]:
    """Get national KPI summary for all available years."""
    rows = query_pg(
        """
        SELECT * FROM mart.mart_national__kpi_summary
        ORDER BY data_year DESC
        """
    )
    return [NationalKPI(**r) for r in rows]


@router.get("/kpis/{data_year}", response_model=NationalKPI)
async def get_national_kpi_year(data_year: int) -> NationalKPI:
    """Get national KPIs for a specific year."""
    from fastapi import HTTPException

    rows = query_pg(
        """
        SELECT * FROM mart.mart_national__kpi_summary
        WHERE data_year = :data_year
        """,
        {"data_year": data_year},
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for year {data_year}")
    return NationalKPI(**rows[0])
