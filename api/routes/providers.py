"""Provider endpoints — NPI lookup, search, by-specialty."""

from fastapi import APIRouter, HTTPException, Query

from api.schemas.providers import ProviderProfile, ProviderSearchResponse, ProviderSummary
from api.services.database import query_pg

router = APIRouter()


@router.get("/{npi}", response_model=ProviderProfile)
async def get_provider(npi: str) -> ProviderProfile:
    """Lookup a single provider by NPI. Target: <10ms."""
    if not npi.isdigit() or len(npi) != 10:
        raise HTTPException(status_code=400, detail="NPI must be a 10-digit number")

    rows = query_pg(
        """
        SELECT * FROM mart.mart_provider__practice_profile
        WHERE npi = :npi
        """,
        {"npi": npi},
    )

    if not rows:
        raise HTTPException(status_code=404, detail=f"Provider {npi} not found")

    return ProviderProfile(**rows[0])


@router.get("", response_model=ProviderSearchResponse)
async def search_providers(
    state: str | None = Query(None, description="2-letter state abbreviation"),
    specialty: str | None = Query(None, description="Taxonomy classification"),
    name: str | None = Query(None, description="Provider name (partial match)"),
    entity_type: str | None = Query(None, description="Individual or Organization"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> ProviderSearchResponse:
    """Search providers with filters and pagination."""
    conditions = []
    params: dict = {}

    if state:
        conditions.append("practice_state = :state")
        params["state"] = state.upper()
    if specialty:
        conditions.append("specialty_classification ILIKE :specialty")
        params["specialty"] = f"%{specialty}%"
    if name:
        conditions.append("display_name ILIKE :name")
        params["name"] = f"%{name.upper()}%"
    if entity_type:
        conditions.append("entity_type = :entity_type")
        params["entity_type"] = entity_type

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    # Count query
    count_rows = query_pg(
        f"SELECT COUNT(*) as total FROM mart.mart_provider__practice_profile {where}",
        params,
    )
    total = count_rows[0]["total"] if count_rows else 0

    # Data query
    rows = query_pg(
        f"""
        SELECT npi, display_name, entity_type, practice_state, practice_city,
               specialty_classification, total_medicare_payments
        FROM mart.mart_provider__practice_profile
        {where}
        ORDER BY display_name
        LIMIT :limit OFFSET :offset
        """,
        params,
    )

    items = [ProviderSummary(**r) for r in rows]
    return ProviderSearchResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
    )


@router.get("/by-specialty/{specialty}", response_model=list[ProviderSummary])
async def providers_by_specialty(
    specialty: str,
    state: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> list[ProviderSummary]:
    """Get top providers by specialty, optionally filtered by state."""
    params: dict = {"specialty": f"%{specialty}%", "limit": limit}
    state_filter = ""
    if state:
        state_filter = "AND practice_state = :state"
        params["state"] = state.upper()

    rows = query_pg(
        f"""
        SELECT npi, display_name, entity_type, practice_state, practice_city,
               specialty_classification, total_medicare_payments
        FROM mart.mart_provider__practice_profile
        WHERE specialty_classification ILIKE :specialty {state_filter}
        ORDER BY total_medicare_payments DESC NULLS LAST
        LIMIT :limit
        """,
        params,
    )
    return [ProviderSummary(**r) for r in rows]
