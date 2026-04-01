"""Drug API routes — Medicaid utilization, price trends."""

from fastapi import APIRouter, Query

from api.schemas.drugs import DrugPriceTrend, MedicaidDrugUtilization
from api.services.database import query_pg

router = APIRouter()


@router.get("/medicaid-utilization", response_model=list[MedicaidDrugUtilization])
async def get_medicaid_drug_utilization(
    data_year: int = Query(2022, description="Data year"),
    state: str | None = Query(None, description="Filter by state"),
):
    """Get state-level Medicaid drug utilization data."""
    sql = """
        SELECT state, state_name, data_year, unique_drugs,
               total_prescriptions, total_reimbursed,
               avg_cost_per_prescription, medicaid_share_pct
        FROM mart.mart_drug__medicaid_utilization
        WHERE data_year = :data_year
    """
    params: dict = {"data_year": data_year}
    if state:
        sql += " AND state = :state"
        params["state"] = state.upper()
    sql += " ORDER BY total_reimbursed DESC NULLS LAST"
    return query_pg(sql, params)


@router.get("/price-trends", response_model=list[DrugPriceTrend])
async def get_drug_price_trends(
    hcpcs_code: str | None = Query(None, description="Filter by HCPCS code"),
    year: int | None = Query(None, description="Filter by year"),
    limit: int = Query(100, le=500),
):
    """Get ASP drug price trends."""
    sql = """
        SELECT hcpcs_code, short_description, payment_limit,
               dosage_form, quarter, year
        FROM mart.mart_drug__price_trends
        WHERE 1=1
    """
    params: dict = {}
    if hcpcs_code:
        sql += " AND hcpcs_code = :hcpcs_code"
        params["hcpcs_code"] = hcpcs_code.upper()
    if year:
        sql += " AND year = :year"
        params["year"] = year
    sql += " ORDER BY hcpcs_code, year, quarter LIMIT :limit"
    params["limit"] = limit
    return query_pg(sql, params)


@router.get("/price-trends/{hcpcs_code}", response_model=list[DrugPriceTrend])
async def get_drug_price_by_code(hcpcs_code: str):
    """Get price trend for a specific drug (HCPCS code)."""
    sql = """
        SELECT hcpcs_code, short_description, payment_limit,
               dosage_form, quarter, year
        FROM mart.mart_drug__price_trends
        WHERE hcpcs_code = :hcpcs_code
        ORDER BY year, quarter
    """
    return query_pg(sql, {"hcpcs_code": hcpcs_code.upper()})
