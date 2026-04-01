# 11. Operations

[← Back to Index](index.md) | [← Testing](10-testing.md)

---

## Configuration Management

### Configuration Files

| File | Path | Sections | Purpose |
|------|------|----------|---------|
| `sources.yaml` | `config/sources.yaml` | 11 categories, 48 source definitions | Source registry: URLs, formats, schedules, validation bounds |
| `database.yaml` | `config/database.yaml` | `postgresql`, `schemas`, `roles`, `duckdb` | Database connection, schema list, RBAC roles, DuckDB Parquet paths |
| `pipeline.yaml` | `config/pipeline.yaml` | `acquisition`, `validation`, `transformation`, `storage`, `logging` | Retry policy, validation thresholds, Parquet compression, storage paths |
| `docker-compose.yml` | `config/docker-compose.yml` | 6 services, 1 volume | Container orchestration, PG tuning, environment variables |

### Configuration Loading Chain

Source: `pipelines/_common/config.py`

```
config/sources.yaml ──┐
config/database.yaml ──┤──▶ _load_yaml() ──▶ Pydantic models ──▶ @lru_cache
config/pipeline.yaml ──┘
                                                    │
                                          Environment variables
                                          override YAML defaults
                                          (${PUF_DB_HOST:-localhost})
```

Key Pydantic settings models:

| Model | Purpose |
|-------|---------|
| `DatabaseSettings` | PG connection params, `.dsn` and `.pgbouncer_dsn` properties |
| `PipelineSettings` | Aggregates retry, Parquet, storage, hash, quarantine, escalation settings |
| `SourceDefinition` | Per-source metadata: name, publisher, format, tier, validation bounds |
| `RetryConfig` | `max_attempts=3`, `delay_seconds=[300, 900, 2700]` |
| `ParquetConfig` | `compression="zstd"`, `row_group_size=500000` |
| `StoragePaths` | Base paths for raw, processed, mart, archive, reference |

### Type Standards

Source: `config/pipeline.yaml`

| Healthcare Type | SQL Type | Width |
|----------------|----------|-------|
| NPI | `VARCHAR(10)` | 10 digits |
| HCPCS | `VARCHAR(5)` | 5 characters |
| FIPS State | `VARCHAR(2)` | 2 digits |
| FIPS County | `VARCHAR(5)` | 5 digits |
| Money | `DECIMAL(18,2)` | 18 total, 2 decimal |
| Rate | `DECIMAL(7,4)` | 7 total, 4 decimal |

---

## Security & Access Control

### RBAC Model

Four PostgreSQL roles implement principle of least privilege. See [RBAC Access Matrix diagram](diagrams/rbac-access-matrix.d2).

| Role | Description | Privileges |
|------|-------------|-----------|
| `puf_pipeline` | Pipeline execution | CRUD on `catalog`, `reference`, `staging` |
| `puf_dbt` | dbt transformations | CRUD on `staging`, `intermediate`, `mart`; SELECT on `reference`, `catalog` |
| `puf_api` | API read access | SELECT on `mart`, `reference`, `catalog` |
| `puf_admin` | Admin / migrations | Superuser (all privileges) |

**Key constraints**:
- API role (`puf_api`) has **no write access** — read-only on mart, reference, catalog
- Pipeline role (`puf_pipeline`) cannot modify mart tables — only dbt can write mart data
- dbt role (`puf_dbt`) cannot modify reference data — pipelines own reference loading
- Only `puf_admin` can run DDL (migrations, schema changes)

### Network Security

| Control | Implementation |
|---------|---------------|
| Connection pooling | PgBouncer transaction mode prevents connection exhaustion |
| CORS | Restricted to `localhost:3000` and `127.0.0.1:3000` |
| Docker networking | Services communicate over internal Docker network; only necessary ports exposed |
| Data volumes | API container mounts `data/` as read-only (`:ro`) |

### Secret Management

| Secret | Storage | Notes |
|--------|---------|-------|
| Database password | `.env` file (gitignored) | Defaults to `puf_dev_password` for local dev |
| API keys | Not required | All data sources are public, no authentication needed |
| User authentication | Not implemented | Phase 1 is local/single-user |

---

## Observability & Monitoring

### Structured Logging

Source: `pipelines/_common/logging.py`

All pipeline operations emit JSON-structured logs via structlog:

```json
{
  "event": "validation_failed",
  "source": "nppes",
  "stage": "validate",
  "run_id": "20260305-001",
  "severity": "WARN",
  "rule": "row_count_range",
  "metric": "7500000",
  "threshold": "[7000000, 10000000]",
  "timestamp": "2026-03-05T14:32:01Z",
  "level": "warning"
}
```

Every log entry includes bound context fields: `source`, `data_year`, `run_id`, `stage`.

Log output: JSON to stderr + file at `logs/pipeline.log`.

### Pipeline Execution Tracking

`catalog.pipeline_runs` records every pipeline execution:

- **Stages tracked**: acquire, validate, transform, load
- **Status values**: running, success, failed, skipped
- **Metrics**: rows_processed, rows_loaded, file_hash, file_size_bytes, duration_seconds

`catalog.pipeline_failures` classifies errors by type (download, validation, transform, load) and retryability.

### Health Endpoint

`GET /health` returns application status with database connectivity:

```json
{
  "status": "healthy",
  "postgres": true,
  "duckdb": true,
  "version": "0.1.0"
}
```

### Prefect UI

Prefect server at `http://localhost:4200` provides:

- Flow run history and status
- Task-level timing and dependency visualization
- Failure inspection and retry triggers
- Scheduled flow monitoring

### Future Monitoring

Directory `monitoring/` is reserved for Prometheus/Grafana configuration (not yet implemented in Phase 1).

---

## Data Governance & Catalog

### Catalog Schema

7 tables in the `catalog` schema provide a complete governance layer. See [Catalog ER diagram](diagrams/catalog-er.d2) and [Database Architecture](04-database.md#catalog-schema-7-tables) for full column details.

```
sources (48 entries) ─┬→ source_columns (column metadata)
                      ├→ data_freshness (SHA-256 staleness tracking)
                      └→ pipeline_runs (execution log)
                              ├→ pipeline_failures (error classification)
                              ├→ validation_runs (quality scores)
                              └→ quarantine_rows (failed rows as JSON)
```

### SHA-256 Freshness Tracking

`catalog.data_freshness` tracks whether source data has changed since last load:

1. On acquisition, compute SHA-256 hash of downloaded file
2. Compare against `latest_file_hash` in `data_freshness`
3. If hash matches → skip processing (data unchanged)
4. If hash differs → proceed with full pipeline, update hash

This prevents unnecessary reprocessing of static data (e.g., FIPS codes, place of service codes).

### BLOCK/WARN Validation Governance

Every pipeline load runs through the validation framework:

1. **BLOCK failures** → Pipeline halts, `pipeline_failures` entry created, no data loaded
2. **WARN failures** → Pipeline continues, `validation_runs` entries logged, metrics tracked
3. **Escalation** → If >10% of rows fail WARN rules, severity escalates to BLOCK

All validation results are persisted in `catalog.validation_runs` for audit trails.

### Quarantine Framework

When `quarantine_enabled: true` (default in `pipeline.yaml`):

- Rows failing validation are serialized as JSON and stored in `catalog.quarantine_rows`
- Each quarantined row links to its `run_id` and `source_id`
- Failure reason and rule name are recorded for investigation
- Quarantined rows are excluded from the loaded dataset

---

**Next:** [Source Inventory →](12-source-inventory.md)
