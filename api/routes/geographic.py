"""Geographic endpoints — state spending, variation analysis."""

from fastapi import APIRouter, Query

from api.schemas.geographic import StateSpending, StateSummary
from api.services.database import query_pg

router = APIRouter()


@router.get("/spending", response_model=list[StateSpending])
async def get_spending_variation(
    data_year: int = Query(..., description="Data year"),
    region: str | None = Query(None, description="Census region filter"),
) -> list[StateSpending]:
    """Get state-level spending variation for a given year."""
    params: dict = {"data_year": data_year}
    region_filter = ""
    if region:
        region_filter = "AND census_region = :region"
        params["region"] = region

    rows = query_pg(
        f"""
        SELECT * FROM mart.mart_geographic__spending_variation
        WHERE data_year = :data_year {region_filter}
        ORDER BY spending_index DESC NULLS LAST
        """,
        params,
    )
    return [StateSpending(**r) for r in rows]


@router.get("/states", response_model=list[StateSummary])
async def get_states(
    data_year: int = Query(..., description="Data year"),
) -> list[StateSummary]:
    """Get lightweight state summaries for maps and dropdowns."""
    rows = query_pg(
        """
        SELECT state_fips, state_name, state_abbreviation, data_year,
               total_beneficiaries, total_providers,
               actual_per_capita_costs, spending_index, ma_participation_rate
        FROM mart.mart_geographic__by_state
        WHERE data_year = :data_year
        ORDER BY state_name
        """,
        {"data_year": data_year},
    )
    return [StateSummary(**r) for r in rows]


@router.get("/states/{state_fips}", response_model=list[StateSpending])
async def get_state_trend(
    state_fips: str,
) -> list[StateSpending]:
    """Get spending variation for a single state across all years."""
    rows = query_pg(
        """
        SELECT * FROM mart.mart_geographic__spending_variation
        WHERE state_fips = :state_fips
        ORDER BY data_year
        """,
        {"state_fips": state_fips},
    )
    return [StateSpending(**r) for r in rows]
