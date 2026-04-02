"""Data catalog endpoints — source registry and freshness."""

from fastapi import APIRouter

from api.schemas.common import CatalogSource
from api.services.database import query_pg

router = APIRouter()


@router.get("/sources", response_model=list[CatalogSource])
async def list_sources() -> list[CatalogSource]:
    """List all data sources in the catalog."""
    try:
        rows = query_pg(
            """
            SELECT
                source_name, short_name, publisher,
                update_frequency, tier,
                last_loaded_at::text as last_loaded,
                last_row_count as row_count
            FROM catalog.sources
            ORDER BY tier, source_name
            """
        )
        return [CatalogSource(**r) for r in rows]
    except Exception:
        # Catalog tables may not be populated yet; return config-based list
        from pipelines._common.config import get_sources

        sources = get_sources()
        return [
            CatalogSource(
                source_name=s.name,
                short_name=s.short_name,
                publisher=s.publisher,
                update_frequency=s.update_frequency,
                tier=s.tier,
            )
            for s in sources.values()
        ]


@router.get("/freshness")
async def get_data_freshness() -> list[dict]:
    """Get data freshness status for all sources."""
    try:
        rows = query_pg(
            """
            SELECT
                source_name, short_name,
                last_checked_at::text as last_checked,
                last_changed_at::text as last_changed,
                is_stale
            FROM catalog.data_freshness
            ORDER BY is_stale DESC, source_name
            """
        )
        return rows
    except Exception:
        return []
