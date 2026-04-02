"""Procedure endpoints -- HCPCS lookup, top procedures, price variation."""

from fastapi import APIRouter, HTTPException, Query

from api.schemas.procedures import (
    ProcedureDetail,
    ProcedurePriceVariation,
    ProcedureTopResponse,
    ProcedureTopResult,
)
from api.services.database import query_pg

router = APIRouter()


@router.get("/top", response_model=ProcedureTopResponse)
async def get_top_procedures(
    data_year: int = Query(2022, description="Data year"),
    sort_by: str = Query(
        "total_services",
        description="Sort field: total_services, total_medicare_payment, provider_count",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> ProcedureTopResponse:
    """Get top procedures by volume or cost with pagination."""
    allowed_sorts = {"total_services", "total_medicare_payment", "provider_count"}
    if sort_by not in allowed_sorts:
        raise HTTPException(
            status_code=400,
            detail=f"sort_by must be one of: {', '.join(sorted(allowed_sorts))}",
        )

    offset = (page - 1) * page_size
    params: dict = {"data_year": data_year, "limit": page_size, "offset": offset}

    # Count query
    count_rows = query_pg(
        """
        SELECT COUNT(*) as total
        FROM mart.mart_procedure__utilization_trends
        WHERE data_year = :data_year
        """,
        {"data_year": data_year},
    )
    total = count_rows[0]["total"] if count_rows else 0

    # Data query -- sort_by is validated above, safe for interpolation
    rows = query_pg(
        f"""
        SELECT hcpcs_code, hcpcs_description, data_year,
               total_services, total_medicare_payment, provider_count,
               avg_payment_per_service, total_rvu, yoy_services_change_pct
        FROM mart.mart_procedure__utilization_trends
        WHERE data_year = :data_year
        ORDER BY {sort_by} DESC NULLS LAST
        LIMIT :limit OFFSET :offset
        """,
        params,
    )

    items = [ProcedureTopResult(**r) for r in rows]
    return ProcedureTopResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
    )


@router.get("/variation/{hcpcs_code}", response_model=list[ProcedurePriceVariation])
async def get_price_variation(
    hcpcs_code: str,
    data_year: int = Query(2022, description="Data year"),
    state: str | None = Query(None, description="Filter by state abbreviation"),
) -> list[ProcedurePriceVariation]:
    """Get price variation for a procedure across states."""
    sql = """
        SELECT hcpcs_code, hcpcs_description, provider_state, data_year,
               provider_count, total_services, total_medicare_payment,
               avg_payment, min_payment, max_payment, stddev_payment,
               p25_payment, p75_payment, coefficient_of_variation
        FROM mart.mart_procedure__price_variation
        WHERE hcpcs_code = :hcpcs_code
          AND data_year = :data_year
    """
    params: dict = {"hcpcs_code": hcpcs_code.upper(), "data_year": data_year}

    if state:
        sql += " AND provider_state = :state"
        params["state"] = state.upper()

    sql += " ORDER BY avg_payment DESC NULLS LAST"

    rows = query_pg(sql, params)
    return [ProcedurePriceVariation(**r) for r in rows]


@router.get("/{hcpcs_code}", response_model=list[ProcedureDetail])
async def get_procedure(
    hcpcs_code: str,
    data_year: int | None = Query(None, description="Filter by specific year"),
) -> list[ProcedureDetail]:
    """Lookup a single procedure by HCPCS code. Returns all years unless filtered."""
    sql = """
        SELECT hcpcs_code, hcpcs_description, data_year,
               total_services, total_beneficiaries, provider_count,
               total_submitted_charge, total_medicare_payment, total_medicare_standardized,
               avg_payment_per_service, avg_charge_per_service, avg_payment_per_beneficiary,
               pct_office, pct_facility,
               work_rvu, facility_pe_rvu, malpractice_rvu, total_rvu,
               conversion_factor, total_rvu_volume,
               yoy_services_change_pct, yoy_payment_change_pct
        FROM mart.mart_procedure__utilization_trends
        WHERE hcpcs_code = :hcpcs_code
    """
    params: dict = {"hcpcs_code": hcpcs_code.upper()}

    if data_year is not None:
        sql += " AND data_year = :data_year"
        params["data_year"] = data_year

    sql += " ORDER BY data_year DESC"

    rows = query_pg(sql, params)
    if not rows:
        raise HTTPException(status_code=404, detail=f"Procedure {hcpcs_code.upper()} not found")

    return [ProcedureDetail(**r) for r in rows]
