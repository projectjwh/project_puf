"""Opioid monitoring endpoints."""

from fastapi import APIRouter, Query

from api.schemas.opioid import OpioidByState, OpioidTopPrescriber
from api.services.database import query_pg

router = APIRouter()


@router.get("/by-state", response_model=list[OpioidByState])
async def get_opioid_by_state(
    data_year: int = Query(..., description="Data year"),
) -> list[OpioidByState]:
    """Get opioid prescribing metrics by state."""
    rows = query_pg(
        """
        SELECT * FROM mart.mart_opioid__by_state
        WHERE data_year = :data_year
        ORDER BY opioid_claim_share_pct DESC NULLS LAST
        """,
        {"data_year": data_year},
    )
    return [OpioidByState(**r) for r in rows]


@router.get("/top-prescribers", response_model=list[OpioidTopPrescriber])
async def get_top_opioid_prescribers(
    data_year: int = Query(..., description="Data year"),
    state: str | None = Query(None, description="State abbreviation filter"),
    limit: int = Query(100, ge=1, le=500),
) -> list[OpioidTopPrescriber]:
    """Get top opioid prescribers ranked by claim volume."""
    params: dict = {"data_year": data_year, "limit": limit}
    state_filter = ""
    if state:
        state_filter = "AND practice_state = :state"
        params["state"] = state.upper()

    rows = query_pg(
        f"""
        SELECT * FROM mart.mart_opioid__top_prescribers
        WHERE data_year = :data_year {state_filter}
        ORDER BY opioid_claims DESC NULLS LAST
        LIMIT :limit
        """,
        params,
    )
    return [OpioidTopPrescriber(**r) for r in rows]


@router.get("/by-state/{state_fips}", response_model=list[OpioidByState])
async def get_state_opioid_trend(state_fips: str) -> list[OpioidByState]:
    """Get opioid metrics for a single state across all years."""
    rows = query_pg(
        """
        SELECT * FROM mart.mart_opioid__by_state
        WHERE state_fips = :state_fips
        ORDER BY data_year
        """,
        {"state_fips": state_fips},
    )
    return [OpioidByState(**r) for r in rows]
