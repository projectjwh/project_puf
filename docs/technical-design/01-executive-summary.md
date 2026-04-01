# 1. Executive Summary

[← Back to Index](index.md)

---

## Mission

Project PUF is an interactive platform for accessing, visualizing, and querying publicly available healthcare data across Medicare, Medicaid, and related federal programs. It transforms scattered government data files into a unified, queryable system with an analytical API and dashboard frontend.

---

## Phase 1 Scope

Phase 1 delivers a complete data platform covering the full lifecycle from CMS data acquisition through interactive frontend dashboards:

| Metric | Count |
|--------|-------|
| Data sources registered | 48 across 11 categories |
| Python data pipelines | 48 source-specific + 7 shared modules |
| Prefect orchestration flows | 8 |
| Alembic database migrations | 10 |
| dbt SQL models | 40 (11 staging, 13 intermediate, 16 mart) |
| API endpoints | 28 (all GET, read-only) |
| Frontend pages | 8 + root redirect |
| Reusable UI components | 4 |
| Automated tests | 258 (last run: 258 passed, 11 skipped) |

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Language | Python | ≥3.12 | Pipelines, API |
| Language | TypeScript | — | Frontend |
| Orchestration | Prefect | 3.x | Flow scheduling and monitoring |
| OLTP Database | PostgreSQL | 16 (Alpine) | Transactional storage, lookups |
| OLAP Engine | DuckDB | ≥1.1 | Analytical queries on Parquet |
| Connection Pool | PgBouncer | latest | Transaction-mode pooling |
| Transformations | dbt-core + dbt-postgres | ≥1.9 | SQL model layers |
| API Framework | FastAPI | ≥0.115 | REST API |
| Frontend | Next.js (App Router) | 13+ | React dashboard |
| Data Processing | pandas + PyArrow | ≥2.2 / ≥18.0 | DataFrames, Parquet I/O |
| Validation | Pydantic + Pandera | ≥2.0 / ≥0.21 | Schema validation |
| Logging | structlog | ≥24.0 | JSON structured logging |
| HTTP Client | httpx | ≥0.28 | Data downloads |
| Migrations | Alembic | ≥1.14 | Database schema versioning |
| Linter/Formatter | Ruff | ≥0.9 | Code quality |
| Type Checker | mypy | ≥1.14 | Static analysis |
| Testing | pytest | ≥8.0 | Test framework |
| Containerization | Docker Compose | — | Local development stack |

---

**Next:** [System Architecture →](02-system-architecture.md)
