# Technical Design Catalog — Project PUF

> **Public Healthcare Data Repository**
> Version 0.2.0 — Phase 2 In Progress
> Last updated: 2026-04-02

---

## Platform Metrics

| Metric | Count |
|--------|-------|
| Data sources registered | 48 across 11 categories |
| Python data pipelines | 48 source-specific + 8 shared modules |
| Prefect orchestration flows | 8 |
| Alembic database migrations | 11 |
| dbt SQL models | 53 (16 staging, 16 intermediate, 20 mart, 1 snapshot) |
| API endpoints | 32 (all GET, read-only) |
| Frontend pages | 8 + root redirect |
| Reusable UI components | 5 |
| Automated tests | 364 (last run: 364 passed, 2 skipped) |
| CI/CD | GitHub Actions (lint + typecheck + test) |
| Pipeline integrity | Full catalog tracking on all Tier 1 pipelines |

---

## System Architecture

```d2
direction: right

sources: "48 External\nSources" {shape: cloud; style.fill: "#fef3c7"}
pipelines: "Python Pipelines\n+ Prefect" {shape: hexagon; style.fill: "#dbeafe"}
postgres: "PostgreSQL 16\n(staging → mart)" {shape: cylinder; style.fill: "#dcfce7"}
parquet: "Parquet Files\n(zstd)" {shape: stored_data; style.fill: "#dcfce7"}
dbt: "dbt-core\n(40 models)" {shape: hexagon; style.fill: "#a7f3d0"}
api: "FastAPI\n(28 endpoints)" {shape: rectangle; style.fill: "#fce7f3"}
duckdb: "DuckDB\n(OLAP)" {shape: cylinder; style.fill: "#dcfce7"}
frontend: "Next.js\n(8 pages)" {shape: rectangle; style.fill: "#f3e8ff"}

sources -> pipelines: "HTTP download"
pipelines -> postgres: "COPY to staging"
pipelines -> parquet: "Write Parquet"
postgres -> dbt: "staging → mart"
dbt -> postgres
api -> postgres: "lookups"
api -> duckdb: "analytics"
duckdb -> parquet: "columnar scan"
frontend -> api: "REST /api/v1/*"
```

Full diagram: [`diagrams/system-architecture.d2`](diagrams/system-architecture.d2)

---

## Document Catalog

| # | Document | Description |
|---|----------|-------------|
| — | **[How to Run](how-to-run.md)** | **Setup, installation, loading data, development workflow** |
| 1 | [Executive Summary](01-executive-summary.md) | Mission, scope, technology stack |
| 2 | [System Architecture](02-system-architecture.md) | Component architecture, data flow, dual-engine routing, decisions |
| 3 | [Infrastructure](03-infrastructure.md) | Docker stack, PG tuning, PgBouncer, Makefile, environment |
| 4 | [Database](04-database.md) | Schemas, RBAC, catalog tables, reference inventory, migrations |
| 5 | [Pipelines](05-pipelines.md) | Shared utils, lifecycle, validation framework, Prefect flows |
| 6 | [Data Models](06-data-models.md) | dbt layers, staging/intermediate/mart inventories, DAG |
| 7 | [Cross-Source Joins](07-cross-source-joins.md) | Join matrix + join graph showing how datasets connect |
| 8 | [API](08-api.md) | FastAPI, dual-engine, 28 endpoints, Pydantic schemas |
| 9 | [Frontend](09-frontend.md) | Pages, components, utilities, component tree |
| 10 | [Testing](10-testing.md) | 258 tests across 16 files, markers, fixtures, config |
| 11 | [Operations](11-operations.md) | Config management, security, observability, governance |
| 12 | [Source Inventory](12-source-inventory.md) | All 48 sources across 11 categories |
| 13 | [Pipeline Integrity](13-pipeline-integrity.md) | Catalog tracking, validation persistence, quarantine, download resilience |
| 14 | [Analytical Domains](14-analytical-domains.md) | UniProvDB SCD, Provider Profiles+, Procedure Analytics, Population, Geography |
| — | [Appendices](appendices.md) | Directory tree, naming conventions, glossary |

---

## Quick Start

```bash
# Start all services
make up

# Run migrations
make migrate

# Load reference data (Prefect flow)
python -m flows.reference_flow

# Run full utilization refresh
python -m flows.utilization_flow --data-year 2022

# Run dbt models
make dbt-run

# Start API (auto-starts via Docker, or manually)
uvicorn api.main:app --reload --port 8000

# Run tests
make test
```

---

## Key Diagrams

| Diagram | File | Renders |
|---------|------|---------|
| System Architecture | [`diagrams/system-architecture.d2`](diagrams/system-architecture.d2) | Component layers + data flow |
| Data Flow Pipeline | [`diagrams/data-flow-pipeline.d2`](diagrams/data-flow-pipeline.d2) | 8-stage lifecycle |
| Deployment Topology | [`diagrams/deployment-topology.d2`](diagrams/deployment-topology.d2) | Docker services + ports |
| Catalog ER | [`diagrams/catalog-er.d2`](diagrams/catalog-er.d2) | 7 catalog tables with FKs |
| Schema Layout | [`diagrams/schema-layout.d2`](diagrams/schema-layout.d2) | 7 PG schemas |
| RBAC Matrix | [`diagrams/rbac-access-matrix.d2`](diagrams/rbac-access-matrix.d2) | 4 roles × 7 schemas |
| dbt DAG | [`diagrams/dbt-dag.d2`](diagrams/dbt-dag.d2) | 40-model lineage |
| Pipeline State Machine | [`diagrams/pipeline-state-machine.d2`](diagrams/pipeline-state-machine.d2) | Stage transitions |
| Dual-Engine Sequence | [`diagrams/dual-engine-sequence.d2`](diagrams/dual-engine-sequence.d2) | PG vs DuckDB routing |
| Prefect Orchestration | [`diagrams/prefect-orchestration.d2`](diagrams/prefect-orchestration.d2) | 8 flows + dependencies |
| Cross-Source Joins | [`diagrams/cross-source-joins.d2`](diagrams/cross-source-joins.d2) | Source → model graph |
| API Route Tree | [`diagrams/api-route-tree.d2`](diagrams/api-route-tree.d2) | 28 endpoints hierarchy |
| Frontend Pages | [`diagrams/frontend-pages.d2`](diagrams/frontend-pages.d2) | Page → API → component tree |

---

## Rendering D2 Diagrams

```bash
# Install d2 CLI
curl -fsSL https://d2lang.com/install.sh | sh -s --

# Render single diagram to SVG
d2 docs/technical-design/diagrams/system-architecture.d2 system-architecture.svg

# Render all diagrams
for f in docs/technical-design/diagrams/*.d2; do
  d2 "$f" "${f%.d2}.svg"
done

# Watch mode (live reload)
d2 --watch docs/technical-design/diagrams/system-architecture.d2
```

D2 fenced code blocks (`\`\`\`d2`) also render natively in Terrastruct and compatible Markdown viewers.
