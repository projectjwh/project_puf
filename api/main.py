"""FastAPI application for Project PUF.

Dual-engine query routing:
  - PostgreSQL: provider lookups, filtered lists, small aggregations
  - DuckDB: large analytical queries on Parquet files
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    catalog,
    drugs,
    geographic,
    health,
    hospitals,
    national,
    opioid,
    postacute,
    procedures,
    providers,
    specialties,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    # Startup: connections are lazy-initialized on first use
    yield
    # Shutdown: close database connections
    from api.services.database import close_all

    close_all()


app = FastAPI(
    title="Project PUF — Public Healthcare Data API",
    description=(
        "Interactive API for querying Medicare provider, utilization, "
        "geographic, and prescribing data from CMS public use files."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(health.router, tags=["health"])
app.include_router(providers.router, prefix="/api/v1/providers", tags=["providers"])
app.include_router(geographic.router, prefix="/api/v1/geographic", tags=["geographic"])
app.include_router(national.router, prefix="/api/v1/national", tags=["national"])
app.include_router(opioid.router, prefix="/api/v1/opioid", tags=["opioid"])
app.include_router(specialties.router, prefix="/api/v1/specialties", tags=["specialties"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["catalog"])
app.include_router(hospitals.router, prefix="/api/v1/hospitals", tags=["hospitals"])
app.include_router(drugs.router, prefix="/api/v1/drugs", tags=["drugs"])
app.include_router(postacute.router, prefix="/api/v1/postacute", tags=["postacute"])
app.include_router(procedures.router, prefix="/api/v1/procedures", tags=["procedures"])
