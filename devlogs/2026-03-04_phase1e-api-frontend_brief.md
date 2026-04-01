# Phase 1e: API + Frontend MVP — Brief

**Date**: 2026-03-04
**Phase**: 1e — FastAPI Backend + Next.js Frontend
**Status**: PLANNING

---

## Context

Phase 1d delivered all utilization data pipelines with 185 passing tests. The data layer is complete:
- 8 Alembic migrations (9 including utilization staging)
- 17+ pipeline modules loading reference, identity, and utilization data
- dbt models across staging → intermediate → mart
- Parquet export for DuckDB analytical queries

Phase 1e builds the serving and presentation layers.

## Approach

### FastAPI Backend
- Dual query engine: PostgreSQL (lookups, filtered lists) + DuckDB (heavy analytics on Parquet)
- 7 route modules: providers, geographic, national, opioid, specialties, catalog, health
- Pydantic v2 response schemas
- Query service layer abstracting PG vs DuckDB routing

### Next.js Frontend
- Next.js 15 with App Router
- 5 pages: National Dashboard, Provider Lookup, Geographic Explorer, Specialty Comparison, Opioid Monitor
- Reusable components: data-table, kpi-card, chart-wrapper, filter-bar, state-map, sidebar/nav
- Tailwind CSS for styling
- ECharts for visualizations

## Success Criteria
- All 5 frontend pages render with mock/structured data
- API serves all 7 route groups with proper response shapes
- Provider NPI lookup endpoint functional
- Full stack starts with `docker compose up`
- API docs at :8000/docs
