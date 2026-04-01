"""Hospital API routes — financial profiles, performance, readmissions, charges."""

from fastapi import APIRouter, Query

from api.schemas.hospitals import (
    HospitalChargeVariation,
    HospitalFinancialProfile,
    HospitalPerformance,
    HospitalReadmission,
)
from api.services.database import query_pg

router = APIRouter()


@router.get("/financial", response_model=list[HospitalFinancialProfile])
async def get_hospital_financials(
    data_year: int = Query(2022, description="Data year"),
    state: str | None = Query(None, description="Filter by state"),
    limit: int = Query(100, le=500),
):
    """Get hospital financial profiles from cost reports."""
    sql = """
        SELECT ccn, facility_name, provider_state, hospital_type,
               ownership_type, data_year, cms_overall_rating,
               total_patient_revenue, total_operating_expenses, net_income,
               operating_margin, cost_to_charge_ratio, total_beds_available,
               total_discharges, occupancy_rate, revenue_per_discharge
        FROM mart.mart_hospital__financial_profile
        WHERE data_year = :data_year
    """
    params: dict = {"data_year": data_year}
    if state:
        sql += " AND provider_state = :state"
        params["state"] = state.upper()
    sql += " ORDER BY total_patient_revenue DESC NULLS LAST LIMIT :limit"
    params["limit"] = limit
    return query_pg(sql, params)


@router.get("/financial/{ccn}", response_model=HospitalFinancialProfile)
async def get_hospital_financial_by_ccn(ccn: str, data_year: int = Query(2022)):
    """Get financial profile for a specific hospital."""
    sql = """
        SELECT * FROM mart.mart_hospital__financial_profile
        WHERE ccn = :ccn AND data_year = :data_year
    """
    rows = query_pg(sql, {"ccn": ccn.zfill(6), "data_year": data_year})
    if not rows:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Hospital {ccn} not found")
    return rows[0]


@router.get("/performance", response_model=list[HospitalPerformance])
async def get_hospital_performance(
    data_year: int = Query(2022),
    state: str | None = Query(None),
    limit: int = Query(100, le=500),
):
    """Get hospital discharge performance with case mix index."""
    sql = """
        SELECT ccn, facility_name, provider_state, data_year,
               unique_drg_count, total_discharges, case_mix_index,
               total_medicare_payments, avg_payment_per_discharge
        FROM mart.mart_hospital__performance
        WHERE data_year = :data_year
    """
    params: dict = {"data_year": data_year}
    if state:
        sql += " AND provider_state = :state"
        params["state"] = state.upper()
    sql += " ORDER BY total_discharges DESC NULLS LAST LIMIT :limit"
    params["limit"] = limit
    return query_pg(sql, params)


@router.get("/readmissions", response_model=list[HospitalReadmission])
async def get_hospital_readmissions(
    data_year: int = Query(2022),
    state: str | None = Query(None),
    penalty_risk_only: bool = Query(False),
):
    """Get hospital readmission data with penalty risk flags."""
    sql = """
        SELECT ccn, facility_name, provider_state, data_year,
               measure_count, avg_readmission_rate,
               measures_worse_than_national, measures_better_than_national,
               has_penalty_risk
        FROM mart.mart_hospital__readmissions
        WHERE data_year = :data_year
    """
    params: dict = {"data_year": data_year}
    if state:
        sql += " AND provider_state = :state"
        params["state"] = state.upper()
    if penalty_risk_only:
        sql += " AND has_penalty_risk = true"
    sql += " ORDER BY avg_readmission_rate DESC NULLS LAST"
    return query_pg(sql, params)


@router.get("/charges", response_model=list[HospitalChargeVariation])
async def get_charge_variation(
    data_year: int = Query(2022),
    ccn: str | None = Query(None, description="Filter by hospital CCN"),
    drg_code: str | None = Query(None, description="Filter by DRG"),
    limit: int = Query(100, le=500),
):
    """Get hospital charge variation by DRG."""
    sql = """
        SELECT ccn, facility_name, drg_code, drg_description, data_year,
               total_discharges, avg_covered_charges, avg_total_payments,
               charge_to_payment_ratio
        FROM mart.mart_hospital__charge_variation
        WHERE data_year = :data_year
    """
    params: dict = {"data_year": data_year}
    if ccn:
        sql += " AND ccn = :ccn"
        params["ccn"] = ccn.zfill(6)
    if drg_code:
        sql += " AND drg_code = :drg_code"
        params["drg_code"] = drg_code
    sql += " ORDER BY charge_to_payment_ratio DESC NULLS LAST LIMIT :limit"
    params["limit"] = limit
    return query_pg(sql, params)
