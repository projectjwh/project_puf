# 2. System Architecture

[← Back to Index](index.md) | [← Executive Summary](01-executive-summary.md)

---

## Component Architecture

```d2
direction: right

external: External Sources {
  style.fill: "#fef3c7"
  style.stroke: "#f59e0b"
  cms: CMS {shape: cloud}
  fda: FDA {shape: cloud}
  hud: HUD {shape: cloud}
  census: Census {shape: cloud}
  nucc: NUCC {shape: cloud}
  dartmouth: Dartmouth {shape: cloud}
}

ingestion: Ingestion Layer {
  style.fill: "#dbeafe"
  style.stroke: "#3b82f6"
  pipelines: "Python Pipelines\n(48 sources)" {shape: hexagon}
  prefect: "Prefect 3.x\nOrchestration" {shape: hexagon}
  validation: "BLOCK/WARN\nValidation" {shape: hexagon}
  prefect -> pipelines: schedules
  pipelines -> validation: every load
}

storage: Storage Layer {
  style.fill: "#dcfce7"
  style.stroke: "#22c55e"
  postgres: "PostgreSQL 16\n(OLTP)" {shape: cylinder}
  pgbouncer: "PgBouncer\n(Connection Pool)" {shape: diamond}
  parquet: "Parquet Files\n(zstd compressed)" {shape: stored_data}
  duckdb: "DuckDB\n(OLAP)" {shape: cylinder}
  dbt: "dbt-core\n(SQL transforms)" {shape: hexagon}
  pgbouncer -> postgres: transaction mode
  dbt -> postgres: staging → mart
  duckdb -> parquet: columnar scan
}

serving: Serving Layer {
  style.fill: "#fce7f3"
  style.stroke: "#ec4899"
  api: "FastAPI\n28 endpoints" {shape: rectangle}
  router: "Dual-Engine\nRouter" {shape: diamond}
  api -> router: query
  router -> storage.postgres: lookups, pagination
  router -> storage.duckdb: analytics, aggregation
}

presentation: Presentation Layer {
  style.fill: "#f3e8ff"
  style.stroke: "#a855f7"
  frontend: "Next.js\n8 pages" {shape: rectangle}
}

external.cms -> ingestion.pipelines: HTTP download
external.fda -> ingestion.pipelines
external.hud -> ingestion.pipelines
external.census -> ingestion.pipelines
ingestion.pipelines -> storage.postgres: "COPY to staging/reference"
ingestion.pipelines -> storage.parquet: "Write Parquet"
serving.api -> storage.pgbouncer: pooled reads
presentation.frontend -> serving.api: "REST /api/v1/*"
```

Full diagram: [`diagrams/system-architecture.d2`](diagrams/system-architecture.d2)

---

## Data Flow (8 Stages)

```d2
direction: right

stage1: "1. Discover\n(sources.yaml)" {style.fill: "#fef3c7"}
stage2: "2. Acquire\n(httpx + retry)" {style.fill: "#fed7aa"}
stage3: "3. Validate\n(BLOCK/WARN)" {style.fill: "#fecaca"}
stage4: "4. Transform\n(pandas)" {style.fill: "#e9d5ff"}
stage5: "5. Load\n(COPY to PG)" {style.fill: "#dbeafe"}
stage6: "6. Store\n(Parquet zstd)" {style.fill: "#bbf7d0"}
stage7: "7. Model\n(dbt-core)" {style.fill: "#a7f3d0"}
stage8: "8. Serve\n(FastAPI)" {style.fill: "#bfdbfe"}

stage1 -> stage2 -> stage3 -> stage4 -> stage5 -> stage7 -> stage8
stage4 -> stage6 -> stage8: "DuckDB reads Parquet" {style.stroke-dash: 5}
```

Full diagram: [`diagrams/data-flow-pipeline.d2`](diagrams/data-flow-pipeline.d2)

| Stage | Technology | Input | Output |
|-------|-----------|-------|--------|
| 1. Discover | `config/sources.yaml` | Source definition | URL, format, schedule |
| 2. Acquire | httpx (3 retries: 5m, 15m, 45m) | HTTP download | Raw files + SHA-256 |
| 3. Validate | pandas + custom framework | DataFrame | BLOCK/WARN results |
| 4. Transform | pandas + PyArrow | Normalized DF | Typed columns, derived fields |
| 5. Load | psycopg2 COPY protocol | DataFrame | PG staging/reference tables |
| 6. Store | PyArrow writer | DataFrame | zstd Parquet files |
| 7. Model | dbt-core | PG tables | staging → intermediate → mart |
| 8. Serve | FastAPI + DuckDB | PG marts + Parquet | JSON API responses |

---

## Dual-Engine Query Routing

The API routes queries to two engines based on query pattern:

| Query Pattern | Engine | Rationale |
|--------------|--------|-----------|
| Single-row lookup by key (NPI, CCN) | PostgreSQL | Indexed B-tree, <10ms |
| Filtered list with pagination | PostgreSQL | WHERE + LIMIT/OFFSET |
| Small GROUP BY (per state, per year) | PostgreSQL | Mart tables pre-aggregated |
| Large analytical aggregation | DuckDB | Columnar scan on Parquet |
| Cross-year trend analysis | DuckDB | Full-table scan efficient |
| Full-table export | DuckDB | No connection pool pressure |

Implementation: `api/services/database.py`

---

## Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Dual query engine | PostgreSQL + DuckDB | Avoid expensive OLAP queries on OLTP database |
| dbt for transforms | dbt-core + dbt-postgres | SQL-based, testable, documented lineage |
| Prefect for orchestration | Prefect 3.x OSS | Free tier, Python-native, UI included |
| Parquet as interchange | zstd-compressed Parquet | Columnar, splittable, DuckDB-native |
| PgBouncer pooling | Transaction mode | Handles bursty API connections without exhausting PG |
| Monorepo structure | Single repo, no `src/` wrapper | Flat, readable, co-located |

---

**Next:** [Infrastructure →](03-infrastructure.md)
