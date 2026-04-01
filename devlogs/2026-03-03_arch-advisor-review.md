# Architecture Review: Project PUF Initial Stack
Date: 2026-03-03
Agent: Arch Advisor
Status: Initial Review (Wave 1)

> **Verification Note**: WebSearch and WebFetch were unavailable during this review. All
> recommendations are based on ecosystem knowledge current to early 2025. Before locking
> in any tool, the team should verify the latest release date, license status, and any
> breaking changes for each major dependency. Specific items flagged for re-verification
> are marked with `[VERIFY]`.

---

## Proposed Stack

| # | Layer | Technology | Version/Variant | Verdict |
|---|-------|-----------|----------------|---------|
| 1 | Backend language | Python | 3.12+ | RETAIN |
| 2 | Frontend language | TypeScript | 5.x+ | RETAIN |
| 3 | Workflow orchestration | **Prefect** (OSS) | 3.x `[VERIFY]` | RETAIN |
| 4 | ETL/ELT transforms | **dbt-core** | 1.9+ `[VERIFY]` | WATCH |
| 5 | Data validation | **Pydantic** + **Pandera** | Pydantic v2, Pandera 0.20+ | RETAIN |
| 6 | File format | **Parquet** | via PyArrow / DuckDB | RETAIN |
| 7 | OLTP database | **PostgreSQL** | 16+ | RETAIN |
| 8 | OLAP engine | **DuckDB** (embedded) | 1.1+ `[VERIFY]` | RETAIN |
| 9 | Object storage | **Local filesystem** (MVP) | — | RETAIN |
| 10 | Cache | **Valkey** | 8.x `[VERIFY]` | RETAIN |
| 11 | Data catalog | **Deferred** (custom metadata in Postgres) | — | RETAIN |
| 12 | Schema versioning | **Alembic** (Postgres migrations) | 1.13+ | RETAIN |
| 13 | Lake format | **Deferred** (raw Parquet on local FS) | — | WATCH |
| 14 | Lake query engine | **DuckDB** | (same as #8) | RETAIN |
| 15 | Metrics | **Prometheus** | 2.x `[VERIFY]` | WATCH |
| 16 | Dashboards | **Grafana** | 11.x+ `[VERIFY]` | RETAIN |
| 17 | Logging | **Structured logging** (Python `structlog` → JSON files) | MVP | RETAIN |
| 18 | Tracing | **OpenTelemetry** (SDK only, no collector for MVP) | — | WATCH |
| 19 | API framework | **FastAPI** | 0.115+ `[VERIFY]` | RETAIN |
| 20 | Task scheduling | **APScheduler** | 4.x `[VERIFY]` | RETAIN |
| 21 | Authentication | **Deferred** (public data, no auth for MVP) | — | RETAIN |
| 22 | Frontend framework | **Next.js** | 15.x `[VERIFY]` | RETAIN |
| 23 | Visualization | **Apache ECharts** | 5.x | RETAIN |
| 24 | BI/dashboards | **Deferred** (Superset in Wave 2+) | — | WATCH |
| 25 | Data tables | **TanStack Table** | v8 | RETAIN |
| 26 | Styling | **Tailwind CSS** | 4.x `[VERIFY]` | RETAIN |
| 27 | Containerization | **Docker + Docker Compose** | Compose v2 | RETAIN |
| 28 | CI/CD | **GitHub Actions** | — | RETAIN |
| 29 | Secret management | **SOPS + Age** | — | RETAIN |
| 30 | BI tool | **Apache Superset** | 4.x `[VERIFY]` | WATCH |

---

## Detailed Evaluation

### 1. Backend Language: Python 3.12+ — RETAIN

**Reasoning**: Non-negotiable for this project. The entire data ecosystem (Airflow/Prefect, dbt, DuckDB Python bindings, pandas, PyArrow, Pydantic, FastAPI) is Python-native. Python 3.12 brought significant performance improvements (faster interpreter, better error messages). Python 3.13 may be available by now with the experimental JIT.

**Exit path**: Individual services could be rewritten in Go/Rust if CPU-bound bottlenecks emerge, but this is unlikely for a data platform that delegates heavy lifting to DuckDB and Postgres.

### 2. Frontend Language: TypeScript 5.x — RETAIN

**Reasoning**: Industry consensus for frontend development. Provides type safety that catches errors before runtime. Non-negotiable for any serious frontend.

**Exit path**: TypeScript compiles to JavaScript; there is zero lock-in.

### 3. Workflow Orchestration: Prefect (OSS) — RETAIN

**Reasoning**: I am making a deliberate departure from the reference stack default of Apache Airflow. Here is why:

| Factor | Airflow | Prefect |
|--------|---------|---------|
| Setup complexity | Heavy — needs scheduler, webserver, metadata DB, Celery/executor | Lightweight — `pip install prefect`, run |
| DAG authoring | DAG files with decorators, must be in dags/ folder, parsed on schedule | Pure Python functions with `@flow` / `@task` decorators, anywhere |
| Local dev experience | Painful on Windows (needs WSL2 or Docker) | Runs natively on Windows, no special setup |
| Solo/small team fit | Designed for platform teams | Designed for individual devs scaling up |
| Observability | Good built-in UI | Excellent built-in UI (Prefect server, free self-hosted) |
| Scale ceiling | Production-proven at massive scale | Production-proven at smaller-to-medium scale |
| Python version support | Sometimes lags | Generally current |
| Open-source status | Apache 2.0, fully open | Apache 2.0, fully open core; Cloud is paid but not required |

For a solo developer on Windows 11 building an MVP with ~20 data source pipelines, Prefect's developer experience advantage is decisive. Airflow is the right answer for a team of 10 running 500 DAGs — it is overkill here.

`[VERIFY]` Confirm Prefect 3.x is GA, that `prefect server start` still provides a fully functional free self-hosted orchestrator, and that no critical features have been paywalled.

**Scale trigger for re-evaluation**: If the platform grows to 100+ pipelines with complex inter-dependencies and multi-team ownership, re-evaluate Airflow.

**Exit path**: Both Prefect and Airflow orchestrate Python callables. Migration means rewriting decorators and flow definitions, not business logic.

### 4. ETL/ELT Transforms: dbt-core — WATCH

**Reasoning**: dbt-core is the community standard for SQL-first data transformations. It provides version-controlled, tested, documented SQL models in a staging-intermediate-mart pattern that aligns perfectly with Schema Smith's 3-layer model design.

**Why WATCH, not RETAIN**: dbt Labs has been evolving its licensing and business model. dbt Cloud continues to add features not available in dbt-core. There have been community concerns about the open-core boundary shifting. Additionally, **SQLMesh** has been gaining traction as a fully open alternative with better performance characteristics (virtual environments, built-in column-level lineage).

`[VERIFY]` Check current dbt-core license status. If dbt-core has moved to a restrictive license (BSL, SSPL, etc.), immediately REPLACE with SQLMesh. Also verify SQLMesh maturity — if it has reached 1.0, it may be the better pick outright.

**Recommendation**: Start with dbt-core. If licensing concerns materialize, SQLMesh is a clean migration target because both operate on SQL model files with similar patterns.

**Exit path**: dbt models are SQL files with Jinja templating. SQLMesh can import dbt projects directly.

### 5. Data Validation: Pydantic v2 + Pandera — RETAIN

**Reasoning**: Two-layer validation strategy:
- **Pydantic v2**: Validates API payloads, configuration files, pipeline parameters, and any structured data at application boundaries. Rust-powered core in v2 makes it extremely fast.
- **Pandera**: Validates DataFrame schemas (column types, value ranges, nullability, custom checks) within data pipelines. Works with pandas and polars DataFrames.

Great Expectations was the reference default but is heavier than needed for MVP. It shines when you need data quality dashboards, expectation suites stored as artifacts, and integration with a data catalog. That is Wave 2+ territory. Pandera gives you the validation with less overhead.

**Exit path**: Pydantic is a general Python library with no lock-in. Pandera decorators can be replaced with Great Expectations suites if richer features are needed later.

### 6. File Format: Parquet — RETAIN

**Reasoning**: Universal standard for columnar data storage. Every tool in this stack reads/writes Parquet natively (DuckDB, pandas, polars, PyArrow, dbt, Spark). Excellent compression. No viable alternative for this use case.

**Exit path**: Parquet is an open Apache standard read by everything. Zero lock-in.

### 7. OLTP Database: PostgreSQL 16+ — RETAIN

**Reasoning**: The most capable open-source relational database. JSON/JSONB support, full-text search, extensive extension ecosystem (PostGIS, pg_trgm, TimescaleDB if needed), ACID compliance. Handles metadata, application state, user data, and even moderate analytical queries.

For MVP, a single Postgres instance handles: application metadata, pipeline state, data catalog metadata, and small-to-medium reference tables. This avoids the complexity of multiple database engines.

**Exit path**: Standard SQL. Any RDBMS migration is straightforward with Alembic-managed schemas.

### 8. OLAP Engine: DuckDB (embedded) — RETAIN

**Reasoning**: This is a critical architectural decision and DuckDB is the right call for Project PUF. Here is the analysis:

- **CMS PUF datasets are 1-10GB CSV files.** DuckDB can query these directly, no loading step required.
- **DuckDB reads Parquet, CSV, JSON natively.** `SELECT * FROM 'file.parquet' WHERE state = 'CA'` just works.
- **Embedded = zero infrastructure.** No server to maintain. It is a library that runs in-process.
- **SQL interface.** Standard SQL with extensions for analytics (window functions, CTEs, etc.).
- **Python integration.** `import duckdb; duckdb.sql("SELECT ...")` — trivial to integrate with FastAPI.
- **Performance.** On 1-10GB datasets, DuckDB often outperforms Postgres for analytical queries by 10-100x due to columnar execution and vectorized processing.

DuckDB handles the "query engine over data lake" role AND the "analytical database" role, collapsing two stack layers into one.

**Scale trigger**: If datasets grow beyond 50-100GB or concurrent query load exceeds what a single machine can handle, evaluate ClickHouse (server-mode columnar OLAP). DuckDB is single-machine by design.

`[VERIFY]` Confirm DuckDB's latest version, Iceberg/Delta support maturity, and any licensing changes.

**Exit path**: DuckDB uses standard SQL. Queries port to ClickHouse or Trino with minimal rewriting.

### 9. Object Storage: Local Filesystem (MVP) — RETAIN

**Reasoning**: MinIO is the right long-term answer, but for MVP on a single Windows 11 machine, it is unnecessary overhead. Raw Parquet files organized in a directory structure (`data/raw/`, `data/processed/`, `data/mart/`) are sufficient.

The key discipline: organize files as if they are in S3 buckets from day one. Use path patterns like `data/raw/{source}/{year}/{filename}.parquet`. When MinIO or S3 is introduced later, the migration is a path prefix change.

**Scale trigger**: When the project moves to multi-machine deployment or needs S3-compatible API access, introduce MinIO.

**Exit path**: Copy files to MinIO/S3. Update path references.

### 10. Cache: Valkey — RETAIN

**Reasoning**: Valkey is the Linux Foundation fork of Redis, created after Redis switched to a dual-license model (RSALv2/SSPLv1) in March 2024. Valkey is wire-compatible with Redis, BSD-licensed, and backed by AWS, Google, and others.

For an open-source-first project, Valkey is the correct choice over Redis. They are API-identical, so any Redis client library works.

For MVP, caching may not even be needed initially. DuckDB queries on local Parquet files are fast enough. Defer actual deployment until API response times justify it.

`[VERIFY]` Confirm Valkey has reached stable releases and that the ecosystem (client libraries, documentation) is mature.

**Exit path**: Valkey IS Redis (protocol-compatible). Switching between them is a configuration change.

### 11. Data Catalog: Deferred (Custom Postgres Tables) — RETAIN

**Reasoning**: DataHub and OpenMetadata are powerful data catalog platforms, but they are heavy infrastructure for an MVP with ~20 data sources. DataHub requires Kafka, Elasticsearch, MySQL/Postgres, and a Java backend. That is a significant ops burden for a solo developer.

**MVP approach**: Store catalog metadata in Postgres tables:
- `catalog_sources` — source name, URL, update cadence, description
- `catalog_columns` — column name, type, description, source_id
- `catalog_lineage` — upstream/downstream relationships
- `catalog_quality` — latest validation results

This is queryable, version-controlled (via Alembic migrations), and sufficient for the MVP data catalog UI.

**Scale trigger**: When the number of data sources exceeds 50 or when automated lineage tracking becomes critical, introduce DataHub or OpenMetadata.

**Exit path**: Postgres metadata tables can be exported as DataHub ingestion metadata.

### 12. Schema Versioning: Alembic — RETAIN

**Reasoning**: Alembic is the standard database migration tool for SQLAlchemy/Python projects. It handles schema versioning with auto-generated migration scripts, rollback support, and branch management.

Combined with dbt for transformation-layer models, this covers both the application schema (Alembic) and the analytical schema (dbt) versioning needs.

**Exit path**: Migration scripts are SQL. Portable to any migration tool.

### 13. Lake Format: Deferred (Raw Parquet) — WATCH

**Reasoning**: Apache Iceberg is the right long-term lake table format, but it adds complexity that is not justified at MVP scale.

What Iceberg provides: ACID transactions on data lake files, time travel, schema evolution, partition evolution. These matter when multiple writers are updating the same datasets concurrently and you need transactional guarantees.

At MVP scale (~20 PUF sources, single writer, batch updates), raw Parquet files organized by convention provide the same functionality. Schema evolution is handled by pipeline code. "Time travel" is handled by keeping historical Parquet snapshots.

**Scale trigger**: When concurrent writers, streaming ingestion, or regulatory requirements for point-in-time queries emerge, introduce Iceberg.

`[VERIFY]` Confirm DuckDB's Iceberg extension is stable and production-ready, so the migration path is smooth when the time comes.

**Exit path**: Parquet files are the storage format underneath Iceberg. Migration means registering existing Parquet files as Iceberg tables.

### 14. Lake Query Engine: DuckDB — RETAIN

**Reasoning**: Same instance as #8. DuckDB queries Parquet files directly with SQL, eliminating the need for a separate lake query engine. At the data volumes Project PUF will see in the MVP (total dataset size likely under 100GB), DuckDB is more than sufficient.

Trino or Spark are the right answers at 1TB+ with concurrent users. Not here, not yet.

**Exit path**: Standard SQL. Queries port to Trino with minor dialect adjustments.

### 15. Metrics: Prometheus — WATCH

**Reasoning**: Prometheus is the industry standard for metrics collection. It is free, open-source, and integrates perfectly with Grafana.

**Why WATCH**: Prometheus is designed for cloud-native/Kubernetes environments with pull-based metric collection. For an MVP running on a single Windows 11 machine with Docker Compose, it may be more infrastructure than needed.

**MVP alternative**: Start with application-level metrics emitted as structured log lines (JSON). Grafana can read these from Loki or even from JSON files. Introduce Prometheus when the application is containerized and has multiple services to monitor.

**Scale trigger**: When the stack has 5+ services and needs real-time metric dashboards.

**Exit path**: OpenTelemetry metrics export to any backend (Prometheus, VictoriaMetrics, etc.).

### 16. Dashboards: Grafana — RETAIN

**Reasoning**: Grafana is the universal observability dashboard. Free, open-source (AGPL), connects to Prometheus, Loki, Postgres, DuckDB (via plugin), and dozens of other data sources. The Grafana + Loki + Prometheus stack (often called "PLG stack") is the open-source standard for observability.

Runs well in Docker on Windows.

**Exit path**: Dashboard definitions are JSON, exportable. Data sources are standard protocols.

### 17. Logging: Structured Logging (structlog) — RETAIN

**Reasoning**: For MVP, the logging strategy should be:
1. Use Python's `structlog` library to emit JSON-structured log lines
2. Write logs to files (or stdout in containers)
3. Optionally aggregate with Loki when Grafana is set up

This avoids deploying Loki, Elasticsearch, or any log aggregation infrastructure at MVP. Structured JSON logs are searchable with `jq`, parseable by any tool, and ready to be ingested by Loki when the time comes.

`structlog` is actively maintained, widely used, and trivially simple to integrate.

**Scale trigger**: When log volume or the need for cross-service log correlation justifies Loki deployment.

**Exit path**: JSON logs are a universal format. Any aggregator can ingest them.

### 18. Tracing: OpenTelemetry SDK — WATCH

**Reasoning**: OpenTelemetry is the CNCF standard for distributed tracing. For MVP, install the SDK and instrument the FastAPI application. This adds trace context to requests at near-zero cost.

Deploy the collector and Jaeger backend later, when there are multiple services to trace across.

**Why WATCH**: OTel is still evolving rapidly. The Python SDK has had breaking changes between versions. Pin versions carefully.

`[VERIFY]` Confirm OpenTelemetry Python SDK stability and recommended version.

**Exit path**: OTel is vendor-neutral by design. Export to any backend.

### 19. API Framework: FastAPI — RETAIN

**Reasoning**: FastAPI is the clear winner for Python APIs in 2025-2026:
- Async-native (built on Starlette/ASGI)
- Automatic OpenAPI documentation
- Pydantic-native request/response validation
- Massive community and ecosystem
- Excellent performance for Python

`[VERIFY]` Confirm FastAPI version and any major API changes (e.g., Pydantic v2 migration should be complete by now).

**Exit path**: Standard Python ASGI application. Migration to Litestar or Django is function-by-function.

### 20. Task Scheduling: APScheduler — RETAIN

**Reasoning**: For MVP, data acquisition pipelines (downloading CMS PUF files) need to run on schedules. APScheduler provides cron-like scheduling within the Python process, with persistent job stores (Postgres-backed).

This avoids needing Celery + message broker for simple scheduled tasks. Prefect can also handle scheduling, so there is overlap — use APScheduler for lightweight periodic tasks (health checks, cache warming) and Prefect for data pipeline orchestration.

`[VERIFY]` APScheduler 4.x was in development — confirm if it has reached stable release. If not, APScheduler 3.x is battle-tested.

**Exit path**: Scheduling logic is configuration, not business logic. Trivially portable.

### 21. Authentication: Deferred — RETAIN

**Reasoning**: Project PUF serves PUBLIC healthcare data. There is no PII, no PHI, no access restrictions on CMS Public Use Files. Authentication is not needed for MVP.

If auth becomes necessary (e.g., user accounts for saved queries, API rate limiting), introduce it then. Keycloak or Authelia are the right open-source answers.

**Exit path**: N/A — nothing to migrate from.

### 22. Frontend Framework: Next.js — RETAIN

**Reasoning**: Next.js remains the dominant React meta-framework with:
- Server-side rendering (SSR) for SEO and initial load performance
- API routes for BFF (backend-for-frontend) pattern
- Static generation for documentation/landing pages
- Massive ecosystem and community
- App Router with React Server Components

`[VERIFY]` Confirm Next.js latest version and that the App Router is stable and community-recommended. SvelteKit is a viable alternative if the developer has SvelteKit experience, but the React ecosystem advantage (component libraries, hiring, tutorials) favors Next.js for most teams.

**Exit path**: React components are portable. Next.js-specific features (API routes, SSR) would need reimplementation.

### 23. Visualization: Apache ECharts — RETAIN

**Reasoning**: ECharts is the richest open-source charting library available:
- 20+ chart types out of the box (bar, line, scatter, map, treemap, sankey, heatmap, etc.)
- Handles large datasets with progressive rendering
- Interactive tooltips, zoom, brush selection
- Active Apache project with regular releases
- React wrapper available (`echarts-for-react`)

D3.js is more powerful but requires significantly more development time for each chart. For a data platform MVP, ECharts' out-of-the-box chart types are a major time saver.

**Exit path**: Chart configurations are JSON objects. Migration means rewriting chart configs, not data pipelines.

### 24. BI Tool: Apache Superset — WATCH (Deferred)

**Reasoning**: Superset is a powerful open-source BI platform, but it is heavy infrastructure (Python backend, Postgres metadata, Redis, Celery). For MVP, the custom Next.js frontend with ECharts provides sufficient visualization capability.

**Scale trigger**: When the project needs ad-hoc SQL exploration by non-technical users, drag-and-drop dashboard building, or embedded analytics.

`[VERIFY]` Confirm Superset's latest version and resource requirements. Metabase is lighter and may be a better fit if the user base stays small.

**Exit path**: Superset connects to databases via SQLAlchemy. No data lock-in.

### 25. Data Tables: TanStack Table v8 — RETAIN

**Reasoning**: TanStack Table is the standard headless table library for React:
- Virtual scrolling for 100k+ rows
- Sorting, filtering, pagination, grouping
- Column resizing, reordering, pinning
- Headless = full styling control with Tailwind

AG Grid Community is the alternative, but its API is more opinionated and the community edition has feature limitations.

**Exit path**: Headless library — no UI lock-in. Table logic is separate from rendering.

### 26. Styling: Tailwind CSS — RETAIN

**Reasoning**: Tailwind CSS is the dominant utility-first CSS framework:
- Rapid prototyping
- No naming convention debates
- Excellent tree-shaking (tiny production bundles)
- Works perfectly with Next.js and any component library

`[VERIFY]` Tailwind CSS 4.x may have shipped — confirm compatibility with Next.js.

**Exit path**: Tailwind classes can be incrementally replaced with CSS modules or styled-components. No lock-in.

### 27. Containerization: Docker + Docker Compose — RETAIN

**Reasoning**: Docker is the universal containerization standard. Docker Compose v2 handles multi-container development environments. Every tool in this stack has official Docker images.

On Windows 11, Docker Desktop is the standard path. Note that Docker Desktop requires a paid license for companies with >250 employees or >$10M revenue. For a solo project, the free Personal tier applies.

**Alternative**: Podman is daemonless and fully open-source but has rougher Windows support. Not worth the friction for MVP.

**Exit path**: Dockerfiles and Compose files are portable to Podman or any OCI-compatible runtime.

### 28. CI/CD: GitHub Actions — RETAIN

**Reasoning**: Free for public repositories (2,000 minutes/month for private repos on free tier). Integrated with GitHub. YAML-based workflow definitions. Massive marketplace of actions.

If the repository is public (reasonable for a public data platform), CI/CD is completely free.

**Exit path**: GitHub Actions workflows are YAML files. Logic ports to any CI system.

### 29. Secret Management: SOPS + Age — RETAIN

**Reasoning**: SOPS (Secrets OPerationS) encrypts secret values within YAML/JSON files using Age (a modern encryption tool). Encrypted files can be committed to git. This is the simplest secret management approach that is actually secure.

For MVP with no cloud deployment, this is sufficient. HashiCorp Vault is overkill.

**Exit path**: Secrets are just key-value pairs. Portable to any secret manager.

### 30. BI Tool: Apache Superset — WATCH

(See #24 above — this is the same entry, included in the table for completeness as a Wave 2+ consideration.)

---

## Scaling Assessment

### Current Scale (MVP)
- **Data volume**: ~20 CMS PUF sources, 1-10GB each = ~50-100GB total raw data
- **Users**: 1 developer, 0-10 early users
- **Query load**: Single-digit concurrent queries
- **Update frequency**: Monthly/quarterly (CMS release cadence)
- **Infrastructure**: Single Windows 11 machine, Docker Compose

### Projected 6-Month Scale
- **Data volume**: ~200GB (more historical years, additional sources)
- **Users**: 10-100 (if published publicly)
- **Query load**: Low tens of concurrent queries
- **Update frequency**: Weekly pipeline runs, quarterly new data
- **Infrastructure**: Single machine, possibly cloud VM for serving

### Projected 18-Month Scale
- **Data volume**: ~500GB-1TB (full PUF catalog + Medicaid + state data)
- **Users**: 100-1,000
- **Query load**: Tens to low hundreds of concurrent queries
- **Update frequency**: Daily pipeline checks, automated ingestion
- **Infrastructure**: Small cloud deployment (1-3 VMs or managed services)

### First Bottleneck
**DuckDB concurrent query handling** will be the first component to hit a wall. DuckDB is single-process and optimized for single-user analytical workloads. When concurrent API users exceed ~10-20 simultaneous complex queries, response times will degrade.

**Mitigation path**:
1. First: Cache frequently-run queries (Valkey)
2. Second: Pre-compute common aggregations as materialized Parquet files
3. Third: Introduce ClickHouse as a serving layer for high-concurrency queries, keeping DuckDB for pipeline processing

**Estimated trigger point**: ~50 concurrent users running analytical queries.

---

## Lock-in Risk

| Technology | Lock-in Level | Exit Path |
|-----------|--------------|-----------|
| Python | LOW | Standard language, massive ecosystem |
| TypeScript | LOW | Compiles to JavaScript, standard |
| PostgreSQL | LOW | Standard SQL, Alembic migrations portable |
| DuckDB | LOW | Standard SQL, reads open formats (Parquet) |
| FastAPI | LOW | Standard ASGI, Pydantic models portable |
| Prefect | MEDIUM | Flow/task decorators are Prefect-specific; business logic in plain Python is portable |
| dbt-core | MEDIUM | SQL models with Jinja templating; SQLMesh can import dbt projects |
| Next.js | MEDIUM | React components portable; Next.js-specific features (SSR, API routes) need reimplementation |
| Docker | LOW | OCI standard, portable to Podman/containerd |
| GitHub Actions | LOW | YAML workflows, logic ports to any CI |
| Tailwind CSS | LOW | Utility classes, no runtime dependency |
| Apache ECharts | LOW | JSON chart configs, standard canvas/SVG rendering |
| Grafana | LOW | Dashboard JSON, standard data source protocols |
| SOPS + Age | LOW | Encrypted files, secrets are key-value pairs |
| Parquet | LOW | Open Apache standard, universal read support |

**Overall lock-in risk: LOW.** The stack is composed of open standards and open-source tools with clear exit paths. The highest lock-in items (Prefect, dbt, Next.js) are at MEDIUM level with documented migration targets.

---

## Cost Projection

### MVP Phase: $0

| Item | Cost | Notes |
|------|------|-------|
| Python, TypeScript, all libraries | $0 | Open source |
| PostgreSQL | $0 | Self-hosted via Docker |
| DuckDB | $0 | MIT license, embedded |
| Prefect Server | $0 | Self-hosted, Apache 2.0 |
| Docker Desktop | $0 | Free for personal use / small business |
| GitHub Actions | $0 | Free for public repos; 2000 min/mo for private |
| Grafana | $0 | AGPL, self-hosted |
| All other tools | $0 | Open source |
| **Total** | **$0** | |

### Growth Phase (10x scale, ~18 months): $50-200/month

| Item | Cost | Notes |
|------|------|-------|
| Cloud VM (serving) | $20-80/mo | 4-8 vCPU, 16-32GB RAM (Hetzner, DigitalOcean) |
| Cloud VM (database) | $20-60/mo | Managed Postgres or self-hosted |
| Object storage | $5-20/mo | S3/MinIO for Parquet storage |
| Domain + DNS | $1-5/mo | Standard web hosting |
| **Total** | **$50-200/mo** | |

### Key Cost Drivers
1. **Compute for concurrent queries** — DuckDB/ClickHouse needs RAM proportional to dataset size
2. **Storage** — Parquet files are compressed but grow with historical data retention
3. **Egress** — if cloud-hosted, data transfer costs for API responses
4. **Managed services** — if choosing managed Postgres vs. self-hosted

---

## Windows 11 Compatibility Notes

### Runs Natively on Windows (no WSL2 needed)
| Tool | Windows Support | Notes |
|------|----------------|-------|
| Python 3.12+ | Excellent | Native installer, `py` launcher |
| Node.js / npm | Excellent | Native installer |
| DuckDB | Excellent | Native Windows binaries, pip install |
| PostgreSQL | Good | Native Windows installer, or Docker |
| FastAPI | Excellent | Pure Python, runs anywhere |
| Prefect | Good | `pip install prefect`, runs natively |
| dbt-core | Good | Pure Python |
| Pydantic, Pandera | Excellent | Pure Python |
| Git | Good | Git for Windows |

### Requires Docker Desktop (or WSL2)
| Tool | Reason | Docker Image Available |
|------|--------|----------------------|
| PostgreSQL (production-like) | Consistent config, extensions | `postgres:16` |
| Grafana | Linux-native | `grafana/grafana` |
| Prometheus | Linux-native | `prom/prometheus` |
| Valkey/Redis | Linux-native | `valkey/valkey` |
| Loki | Linux-native | `grafana/loki` |
| MinIO | Linux-native | `minio/minio` |

### Docker Desktop Considerations
- **License**: Free for personal use, education, small business (<250 employees, <$10M revenue). This project qualifies.
- **Resource allocation**: Default 2GB RAM for Docker VM is too low. Recommend 4-8GB for running Postgres + Grafana + other services.
- **WSL2 backend**: Docker Desktop on Windows uses WSL2 as its backend. Ensure WSL2 is installed and updated.
- **File system performance**: Volumes mounted from Windows filesystem (`/mnt/c/...`) have ~10x slower I/O than volumes inside WSL2 filesystem. For large Parquet files, consider storing data inside WSL2 filesystem or using Docker named volumes.
- **Disk space**: Docker images accumulate. Run `docker system prune` periodically.

### Windows-Specific Gotchas
1. **Path separators**: Python handles `/` and `\` well, but some tools (especially shell scripts) may break. Always use `pathlib.Path` in Python code.
2. **Line endings**: Configure Git with `git config --global core.autocrlf input` to avoid CRLF issues in Docker containers.
3. **Port conflicts**: Windows may have services on common ports (5432 for Postgres, 3000 for Node). Check with `netstat -aon | findstr :<port>`.
4. **Long paths**: Enable long paths in Git (`git config --global core.longpaths true`) and Windows (Group Policy > Enable Win32 long paths).
5. **Virtual environments**: Use `python -m venv .venv` and activate with `.venv\Scripts\activate` (not `source .venv/bin/activate` which is Unix-only in some shells).

---

## MVP Simplification Recommendations

### The Minimal Viable Stack (Wave 1 — Start Here)

These are the only tools needed to build a working MVP:

```
Python 3.12+          — backend runtime
FastAPI               — API server
DuckDB                — analytical queries on Parquet files
PostgreSQL            — application metadata, catalog
Pydantic v2           — data validation
structlog             — structured JSON logging
Prefect (or scripts)  — pipeline orchestration
Parquet (via PyArrow)  — data storage format
Local filesystem       — file storage

Node.js + TypeScript  — frontend runtime
Next.js               — frontend framework
Tailwind CSS          — styling
Apache ECharts        — charts
TanStack Table        — data tables

Docker + Compose      — containerization
```

**That is 14 tools, not 30.** Everything else is deferred.

### What to Defer

| Tool | Defer Until | Why |
|------|------------|-----|
| dbt-core | Wave 2: when you have 5+ transformation models | Raw SQL in DuckDB is fine for early transforms |
| Pandera | Wave 2: when pipeline validation needs formalization | Pydantic handles API-level validation |
| Valkey/Redis | Wave 2: when API response times need caching | DuckDB on local Parquet is fast enough |
| Grafana + Prometheus | Wave 2: when you need observability dashboards | JSON log files + `jq` are sufficient initially |
| Loki | Wave 2: when log aggregation across services is needed | Stdout logging in Docker is sufficient |
| OpenTelemetry | Wave 2: when multi-service tracing is needed | Single-service MVP does not need tracing |
| MinIO | Wave 3: when local FS is no longer sufficient | Local Parquet files with S3-like path conventions |
| Apache Iceberg | Wave 3: when ACID transactions on lake files are needed | Raw Parquet is fine for single-writer pipelines |
| Apache Superset | Wave 3: when non-technical users need ad-hoc BI | Custom frontend covers MVP analytics |
| DataHub/OpenMetadata | Wave 3: when 50+ data sources need cataloging | Postgres metadata tables for MVP |
| Keycloak/Auth | Wave 3: when user accounts are needed | Public data, no auth for MVP |
| Kubernetes | Not until cloud deployment at scale | Docker Compose handles single-machine deployment |
| Terraform/OpenTofu | Not until cloud infrastructure exists | Nothing to manage yet |

### Wave Progression

**Wave 1** (MVP, $0, single machine):
> Python + FastAPI + DuckDB + Postgres + Prefect + Next.js + ECharts + Docker Compose

**Wave 2** (Enhanced, $0, single machine):
> Add: dbt-core, Pandera, Grafana + Prometheus, Valkey, structlog → Loki

**Wave 3** (Production, $50-200/mo, cloud deployment):
> Add: MinIO/S3, Iceberg, Superset, DataHub, auth, OTel + Jaeger

---

## Overall Verdict: SOUND

The proposed stack is **architecturally sound** with strong MVP simplification potential. Key strengths:

1. **Stack narrowness**: The Wave 1 minimal stack uses 14 tools, most of which are standard/non-negotiable (Python, TypeScript, Docker, Git).
2. **$0 cost**: Every component is open-source with no mandatory paid tiers at MVP scale.
3. **DuckDB as centerpiece**: Using DuckDB as both the analytical engine and the lake query engine collapses two stack layers into one, avoiding significant infrastructure complexity.
4. **Prefect over Airflow**: The right call for a solo developer on Windows. Airflow can be introduced later if scale demands it.
5. **Deferred complexity**: 16 tools are explicitly deferred to Wave 2/3, each with a clear trigger point for introduction.
6. **Low lock-in**: No technology in the stack has a lock-in level above MEDIUM, and every component has a documented exit path.
7. **Windows-compatible**: The core development stack runs natively on Windows 11, with Docker Desktop handling the Linux-native services.

### Concerns to Monitor

1. `[VERIFY]` dbt-core licensing trajectory — if restrictive license adopted, pivot to SQLMesh
2. `[VERIFY]` Prefect 3.x — confirm fully functional self-hosted server remains free
3. `[VERIFY]` DuckDB concurrent query limitations — first scaling bottleneck
4. `[VERIFY]` Valkey ecosystem maturity — confirm client library support

---

## Action Items

### Immediate (Before Writing Code)
- [ ] **Verify tool versions**: Run `[VERIFY]` checks on all flagged tools using web search
- [ ] **Install Python 3.12+**: Confirm installed version, set up virtual environment tooling (venv or uv)
- [ ] **Install Node.js 20 LTS+**: Confirm installed version, set up npm/pnpm
- [ ] **Install Docker Desktop**: Confirm WSL2 backend, allocate 4-8GB RAM
- [ ] **Install DuckDB**: `pip install duckdb` — test with a sample CMS CSV file
- [ ] **Install Git**: Configure `core.autocrlf=input`, `core.longpaths=true`
- [ ] **Create `docker-compose.yml`**: PostgreSQL 16 as first service
- [ ] **Create Python project structure**: `pyproject.toml`, virtual environment, FastAPI hello-world

### Wave 1 (First 2-4 Weeks)
- [ ] Set up Prefect with first data acquisition pipeline (download one PUF source)
- [ ] Set up FastAPI with DuckDB query endpoint
- [ ] Set up Next.js frontend with one chart (ECharts) and one table (TanStack)
- [ ] Set up structured logging (structlog)
- [ ] Implement basic data catalog in Postgres

### Wave 2 (Months 2-3)
- [ ] Introduce dbt-core (or SQLMesh) for transformation models
- [ ] Introduce Pandera for pipeline validation
- [ ] Deploy Grafana + Prometheus for observability
- [ ] Introduce Valkey caching if API latency requires it

### Defer (Wave 3+)
- [ ] MinIO / S3 object storage
- [ ] Apache Iceberg table format
- [ ] Apache Superset BI layer
- [ ] DataHub data catalog
- [ ] Authentication (Keycloak/Authelia)
- [ ] Cloud deployment
- [ ] Kubernetes orchestration

---

*This review was produced by the Arch Advisor subagent as part of the PUF Foundation Sprint (Wave 1). Items marked `[VERIFY]` require web search confirmation before stack lock-in.*
