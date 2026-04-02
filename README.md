# Project PUF

Public Healthcare Data Repository -- an interactive platform for accessing, visualizing, and querying publicly available Medicare, Medicaid, and federal healthcare data.

48 data sources. Dual-engine serving (PostgreSQL + DuckDB). Automated pipelines with full integrity tracking. FastAPI backend. Next.js frontend.

## Architecture

```
                        config/sources.yaml (48 sources)
                                |
                    pipelines/_common/ (shared utilities)
                    acquire | validate | transform | db
                                |
                    pipelines/<source>/pipeline.py (per-source)
                                |
                    catalog.pipeline_runs  -----> catalog.validation_runs
                    catalog.data_freshness        catalog.quarantine_rows
                                |
                +---------+-----+------+---------+
                |         |            |         |
            Parquet   PostgreSQL    DuckDB    Prefect
            (archive)  (staging)   (OLAP)    (orchestration)
                          |
                    dbt (staging -> intermediate -> mart)
                          |
                    FastAPI (28 endpoints)
                          |
                    Next.js (8 pages)
```

| Layer | Technology |
|-------|------------|
| Orchestration | Prefect 3.x |
| Database (OLTP) | PostgreSQL 16 + PgBouncer |
| Database (OLAP) | DuckDB (embedded) |
| Transformations | dbt-core |
| API | FastAPI |
| Frontend | Next.js 15 (App Router) |
| Data format | Parquet (zstd) |
| Logging | structlog (JSON) |
| CI/CD | GitHub Actions (lint, typecheck, test) |

## Quick Start

```bash
# Clone
git clone https://github.com/projectjwh/project_puf.git
cd project_puf

# Install
pip install -e ".[dev]"

# Start services (PostgreSQL, PgBouncer, Prefect, API, Frontend)
docker compose -f config/docker-compose.yml up -d

# Run migrations (11 versions: schemas, roles, catalog, reference, staging, tier2, etag)
export PUF_DB_PASSWORD=puf_dev_password
alembic -c pipelines/alembic/alembic.ini upgrade head

# Seed the source catalog (enables pipeline run tracking)
make seed-catalog

# Verify
curl http://localhost:8000/health
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API + Swagger | http://localhost:8000/docs |
| Prefect UI | http://localhost:4200 |

See [docs/technical-design/how-to-run.md](docs/technical-design/how-to-run.md) for detailed Windows setup, prerequisites, and troubleshooting.

## Data Sources

48 public healthcare data sources organized into tiers:

| Category | Tier 1 (implemented) | Tier 2 (stubs) |
|----------|---------------------|----------------|
| Provider Identity | NPPES, POS, PECOS, Ordering/Referring | -- |
| Code Systems | ICD-10-CM/PCS, HCPCS, MS-DRG, NDC, Taxonomy, POS Codes | APC |
| Geographic | FIPS, ZIP-County, CBSA, RUCA | HRR/HSA, Census |
| Utilization | Part B, Part D, GeoVar | Inpatient, SNF, HHA, Hospice, DME |
| Cost Reports | Hospital | SNF, HHA, Hospice |
| Quality | -- | Five-Star, CAHPS, Readmissions, Dialysis |
| Drug/Prescribing | -- | SDUD, RxNorm, ASP |
| Medicare Advantage | -- | MA Enrollment, MA Benchmarks |

All sources are configured in [`config/sources.yaml`](config/sources.yaml) with download URLs, schedules, validation bounds, and tier classification.

## Loading Data

```bash
# 1. Load reference data first (FIPS, ICD-10, HCPCS, NDC, taxonomy, etc.)
python -m flows.reference_flow

# 2. Load provider data
python -m flows.nppes_flow           # ~8M providers
python -m flows.pos_flow             # ~300K facilities
python -m flows.cost_reports_flow    # Hospital financials

# 3. Load utilization + run dbt + export Parquet
python -m flows.utilization_flow --data-year 2022

# Or run individual utilization pipelines
python -m flows.partb_flow --data-year 2022
python -m flows.partd_flow --data-year 2022
python -m flows.geovar_flow --data-year 2022

# 4. Run dbt models manually
make dbt-run
```

## Pipeline Integrity

Every pipeline execution is fully tracked through 7 catalog tables:

### Run Tracking

Every pipeline records its lifecycle to `catalog.pipeline_runs`:

```sql
-- What ran, when, and how long?
SELECT source_id, run_date, stage, status, rows_loaded, duration_seconds
FROM catalog.pipeline_runs
ORDER BY started_at DESC;
```

### Validation Persistence

All validation checks (BLOCK/WARN) are persisted to `catalog.validation_runs`:

```sql
-- Which checks failed on the last Part B run?
SELECT rule_name, severity, passed, metric_value, threshold, message
FROM catalog.validation_runs v
JOIN catalog.pipeline_runs r ON v.run_id = r.run_id
WHERE r.source_id = (SELECT source_id FROM catalog.sources WHERE short_name = 'partb')
ORDER BY r.started_at DESC, v.validation_id;
```

22 validation rules with two severity levels:
- **BLOCK**: Stops the pipeline. Data not loaded. (e.g., missing NPI column, null primary keys)
- **WARN**: Pipeline continues. Metrics recorded. Escalates to BLOCK if >10% of rows fail.

### Quarantine

Rows that fail validation are quarantined (not silently dropped):

```sql
-- What rows were quarantined and why?
SELECT rule_name, failure_reason, row_data::json->>'npi' as npi
FROM catalog.quarantine_rows
WHERE run_id = 42
LIMIT 10;
```

Row-level checks that trigger quarantine: `not_null`, `format`, `value_set`, `referential_integrity`.

### Failure Classification

Pipeline failures are classified and recorded in `catalog.pipeline_failures`:

| Error Type | Example | Retryable |
|-----------|---------|-----------|
| `download` | ConnectError, 503 | Yes |
| `validation` | BLOCK rule failed | No |
| `load` | PostgreSQL connection lost | Yes |
| `transform` | dbt model failed | No |

```sql
-- Which sources keep failing?
SELECT s.short_name, f.error_type, f.is_retryable, f.error_message
FROM catalog.pipeline_failures f
JOIN catalog.pipeline_runs r ON f.run_id = r.run_id
JOIN catalog.sources s ON r.source_id = s.source_id
ORDER BY f.created_at DESC;
```

### Data Freshness

`catalog.data_freshness` tracks when each source was last checked and loaded:

```sql
-- What's stale?
SELECT s.short_name, f.last_loaded_at, f.last_checked_at, f.latest_file_hash
FROM catalog.data_freshness f
JOIN catalog.sources s ON f.source_id = s.source_id
ORDER BY f.last_loaded_at ASC NULLS FIRST;
```

### Download Resilience

Downloads retry automatically on network failures:

- Retries on `ConnectError`, `TimeoutException`, HTTP 5xx (configurable in `config/pipeline.yaml`)
- Does NOT retry 4xx errors (not transient)
- Default: 3 attempts with [300, 900, 2700] second delays
- ETag/Last-Modified pre-check before downloading (saves bandwidth on large files like Part B at 1.5-4GB)

## API

28 read-only endpoints across 9 domains. All under `/api/v1/`.

| Domain | Endpoints | Example |
|--------|-----------|---------|
| Providers | 3 | `GET /api/v1/providers/1234567890` |
| Geographic | 3 | `GET /api/v1/geographic/spending?data_year=2022` |
| National | 2 | `GET /api/v1/national/kpis` |
| Opioid | 3 | `GET /api/v1/opioid/top-prescribers?state=CA` |
| Hospitals | 5 | `GET /api/v1/hospitals/financial?state=NY` |
| Drugs | 3 | `GET /api/v1/drugs/price-trends/J0178` |
| Post-Acute | 4 | `GET /api/v1/postacute/snf` |
| Specialties | 2 | `GET /api/v1/specialties/` |
| Catalog | 2 | `GET /api/v1/catalog/freshness` |

Full interactive docs at http://localhost:8000/docs (Swagger UI).

## dbt Models

47 models in 3 layers:

| Layer | Count | Materialization | Purpose |
|-------|-------|----------------|---------|
| Staging | 16 | view / ephemeral | 1:1 schema contracts on pipeline output |
| Intermediate | 13 | table | Cross-source joins, aggregations |
| Marts | 16+ | table (indexed) | Pre-shaped for API, <10ms lookups |

Key cross-source joins:
- **Provider enrichment**: NPPES + Taxonomy + FIPS (NPI hub)
- **Utilization profile**: Part B + Part D joined on NPI per year
- **Hospital financials**: Cost Reports + POS Facilities joined on CCN
- **Geographic benchmarks**: GeoVar + FIPS states (spending indices)

```bash
make dbt-run    # Run all models
make dbt-test   # Run column tests (unique, not_null, accepted_values)
```

## Development

### Tests

```bash
make test          # Unit tests only (299 passing)
make test-all      # Include integration tests
make test-cov      # Coverage report
```

### Code Quality

```bash
make lint          # ruff check (0 errors)
make format        # ruff format
make typecheck     # mypy (0 errors, strict on _common/)
```

### CI/CD

GitHub Actions runs on every push to `main` and every PR:

| Job | Tool | What |
|-----|------|------|
| `lint` | ruff | Lint + format check |
| `typecheck` | mypy | Type annotations |
| `test` | pytest | 299 unit tests |

### Project Structure

```
Project_PUF/
  config/
    sources.yaml          # 48 data source definitions
    pipeline.yaml         # Retry, validation, storage config
    database.yaml         # PostgreSQL, DuckDB, RBAC config
    docker-compose.yml    # 6 services
  pipelines/
    _common/              # Shared utilities
      acquire.py          # Download with retry + ETag
      validate.py         # 22 validation rules + quarantine
      transform.py        # NPI/FIPS/NDC normalization
      catalog.py          # Pipeline run tracking + freshness
      db.py               # PostgreSQL COPY + DuckDB + Parquet
      reference.py        # Generic reference pipeline runner
      config.py           # Pydantic settings from YAML
      logging.py          # structlog JSON setup
    <source>/pipeline.py  # 48 per-source pipeline modules
    alembic/versions/     # 11 schema migrations
  flows/                  # 8 Prefect orchestration flows
  models/                 # dbt project (staging/intermediate/marts)
  api/                    # FastAPI (routes, schemas, services)
  frontend/               # Next.js 15 (8 pages, 5 components)
  tests/                  # 299 tests across 16 files
  scripts/
    seed_catalog_sources.py   # Populate catalog.sources from YAML
    export_marts_to_parquet.py  # Export mart tables for DuckDB
  docs/
    technical-design/     # 12 design docs + diagrams
    sources/              # 14 source domain docs
  devlogs/                # Brief/retro for every task
```

### Database Schemas

| Schema | Purpose | Access |
|--------|---------|--------|
| `catalog` | Pipeline metadata, validation, quarantine, freshness | pipeline (RW), api (RO) |
| `reference` | Code lookups (FIPS, taxonomy, ICD-10, fees) | pipeline (RW), dbt (RO) |
| `staging` | 1:1 source mirrors | pipeline (RW), dbt (RW) |
| `intermediate` | Derived metrics, cross-source joins | dbt (RW) |
| `mart` | API-ready, indexed tables | dbt (RW), api (RO) |

4 RBAC roles enforce least privilege: `puf_pipeline`, `puf_dbt`, `puf_api`, `puf_admin`.

## Makefile Reference

| Target | Description |
|--------|-------------|
| `make up` / `make down` | Start/stop Docker services |
| `make migrate` | Run Alembic migrations |
| `make seed-catalog` | Seed catalog.sources from sources.yaml |
| `make test` / `make test-all` | Run unit / all tests |
| `make lint` / `make format` | Lint / auto-format |
| `make typecheck` | mypy type checking |
| `make dbt-run` / `make dbt-test` | Run / test dbt models |
| `make db-shell` | Open psql shell |
| `make clean` | Remove caches |

## License

MIT
