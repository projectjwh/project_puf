"""Health check endpoint."""

from fastapi import APIRouter

from api.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Application health check with database connectivity status."""
    pg_ok = False
    duckdb_ok = False

    try:
        from api.services.database import query_pg
        query_pg("SELECT 1")
        pg_ok = True
    except Exception:
        pass

    try:
        from api.services.database import query_duckdb
        query_duckdb("SELECT 1")
        duckdb_ok = True
    except Exception:
        pass

    status = "healthy" if pg_ok else "degraded"
    return HealthResponse(
        status=status,
        version="0.1.0",
        pg_connected=pg_ok,
        duckdb_connected=duckdb_ok,
    )
