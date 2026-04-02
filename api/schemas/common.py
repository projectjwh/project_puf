"""Shared Pydantic schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    pg_connected: bool
    duckdb_connected: bool


class CatalogSource(BaseModel):
    """Data source catalog entry."""

    source_name: str
    short_name: str
    publisher: str | None = None
    update_frequency: str | None = None
    tier: int | None = None
    last_loaded: str | None = None
    row_count: int | None = None

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    status_code: int


class PaginationParams(BaseModel):
    """Common pagination parameters."""

    page: int = 1
    page_size: int = 25

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
