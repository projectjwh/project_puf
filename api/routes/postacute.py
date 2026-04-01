"""Post-acute care API routes — SNF, HHA, Hospice quality."""

from fastapi import APIRouter, Query

from api.schemas.postacute import HHAQuality, HospiceQuality, SNFQuality
from api.services.database import query_pg

router = APIRouter()


@router.get("/snf", response_model=list[SNFQuality])
async def get_snf_quality(
    state: str | None = Query(None, description="Filter by state"),
    min_rating: int | None = Query(None, description="Minimum overall rating (1-5)"),
    limit: int = Query(100, le=500),
):
    """Get Skilled Nursing Facility quality ratings."""
    sql = """
        SELECT ccn, facility_name, provider_state,
               overall_rating, health_inspection_rating, quality_rating,
               staffing_rating, rn_staffing_rating,
               total_number_of_penalties, total_fine_amount,
               actual_avg_daily_rn_hours, actual_rn_ratio,
               staffing_consistency_flag
        FROM mart.mart_postacute__snf_quality
        WHERE 1=1
    """
    params: dict = {}
    if state:
        sql += " AND provider_state = :state"
        params["state"] = state.upper()
    if min_rating:
        sql += " AND overall_rating >= :min_rating"
        params["min_rating"] = min_rating
    sql += " ORDER BY overall_rating DESC NULLS LAST LIMIT :limit"
    params["limit"] = limit
    return query_pg(sql, params)


@router.get("/snf/{ccn}", response_model=SNFQuality)
async def get_snf_by_ccn(ccn: str):
    """Get quality details for a specific SNF."""
    sql = """
        SELECT * FROM mart.mart_postacute__snf_quality
        WHERE ccn = :ccn
    """
    rows = query_pg(sql, {"ccn": ccn.zfill(6)})
    if not rows:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"SNF {ccn} not found")
    return rows[0]


@router.get("/hha", response_model=list[HHAQuality])
async def get_hha_quality(
    data_year: int = Query(2022),
    state: str | None = Query(None),
    limit: int = Query(100, le=500),
):
    """Get Home Health Agency quality data."""
    sql = """
        SELECT ccn, facility_name, provider_state, data_year,
               total_episodes, total_hha_medicare_payment, total_hha_visits,
               avg_visits_per_episode, avg_payment_per_episode
        FROM mart.mart_postacute__hha_quality
        WHERE data_year = :data_year
    """
    params: dict = {"data_year": data_year}
    if state:
        sql += " AND provider_state = :state"
        params["state"] = state.upper()
    sql += " ORDER BY total_episodes DESC NULLS LAST LIMIT :limit"
    params["limit"] = limit
    return query_pg(sql, params)


@router.get("/hospice", response_model=list[HospiceQuality])
async def get_hospice_quality(
    data_year: int = Query(2022),
    state: str | None = Query(None),
    limit: int = Query(100, le=500),
):
    """Get Hospice quality data."""
    sql = """
        SELECT ccn, facility_name, provider_state, data_year,
               total_beneficiaries, total_hospice_medicare_payment,
               total_hospice_days, avg_length_of_stay, avg_payment_per_beneficiary
        FROM mart.mart_postacute__hospice_quality
        WHERE data_year = :data_year
    """
    params: dict = {"data_year": data_year}
    if state:
        sql += " AND provider_state = :state"
        params["state"] = state.upper()
    sql += " ORDER BY total_beneficiaries DESC NULLS LAST LIMIT :limit"
    params["limit"] = limit
    return query_pg(sql, params)
