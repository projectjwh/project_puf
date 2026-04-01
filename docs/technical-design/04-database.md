# 4. Database Architecture

[← Back to Index](index.md) | [← Infrastructure](03-infrastructure.md)

---

## Schema Layout

```d2
puf: "PostgreSQL: puf" {
  style.fill: "#f0f9ff"
  style.stroke: "#0284c7"

  catalog: "catalog\n7 tables" {style.fill: "#fef3c7"; style.stroke: "#f59e0b"}
  reference: "reference\n26 tables" {style.fill: "#dcfce7"; style.stroke: "#16a34a"}
  staging: "staging\nviews + tables" {style.fill: "#dbeafe"; style.stroke: "#2563eb"}
  intermediate: "intermediate\n13 tables" {style.fill: "#e0e7ff"; style.stroke: "#4f46e5"}
  mart: "mart\n16 tables" {style.fill: "#f3e8ff"; style.stroke: "#7c3aed"}
  metadata: "metadata\n2 tables" {style.fill: "#f1f5f9"; style.stroke: "#64748b"}
  raw: "raw\n(reserved)" {style.fill: "#f8fafc"; style.stroke: "#94a3b8"}

  reference -> staging: "lookups" {style.stroke-dash: 3}
  staging -> intermediate: "dbt joins"
  intermediate -> mart: "dbt shapes"
}
```

Full diagram: [`diagrams/schema-layout.d2`](diagrams/schema-layout.d2)

| Schema | Purpose | Managed By |
|--------|---------|-----------|
| `catalog` | Pipeline metadata, governance, lineage, quality tracking | Alembic + pipelines |
| `reference` | Shared code lookups, geographic dimensions, fee schedules | Pipelines (direct load) |
| `staging` | 1:1 source mirrors with schema contracts | dbt (views/ephemeral) + pipelines (partitioned tables) |
| `intermediate` | Business logic joins, derived metrics, enrichment | dbt (materialized tables) |
| `mart` | Pre-aggregated, indexed, API-ready analytics tables | dbt (materialized tables) |
| `metadata` | Alembic version tracking, dbt run log | Alembic, dbt |
| `raw` | Reserved for future use | — |

---

## RBAC Roles

Source: `config/database.yaml`

```d2
direction: right

pipeline: "puf_pipeline" {
  style.fill: "#dbeafe"
  grants: "CRUD: catalog, reference, staging"
}
dbt: "puf_dbt" {
  style.fill: "#dcfce7"
  grants: "CRUD: staging, intermediate, mart\nSELECT: reference, catalog"
}
api: "puf_api" {
  style.fill: "#fce7f3"
  grants: "SELECT: mart, reference, catalog\nNO WRITE ACCESS"
}
admin: "puf_admin" {
  style.fill: "#fef3c7"
  grants: "SUPERUSER\nMigrations, DDL"
}
```

Full diagram: [`diagrams/rbac-access-matrix.d2`](diagrams/rbac-access-matrix.d2)

| Role | Description | Privileges |
|------|-------------|-----------|
| `puf_pipeline` | Pipeline execution | CRUD on `catalog`, `reference`, `staging` |
| `puf_dbt` | dbt transformations | CRUD on `staging`, `intermediate`, `mart`; SELECT on `reference`, `catalog` |
| `puf_api` | API read access | SELECT on `mart`, `reference`, `catalog` |
| `puf_admin` | Admin / migrations | Superuser (all privileges) |

**Principle**: Least privilege. The API role has no write access. Pipelines cannot touch mart tables. dbt cannot modify reference data.

---

## Catalog Schema (7 Tables)

Source: `pipelines/alembic/versions/003_create_catalog_tables.py`

Full ER diagram: [`diagrams/catalog-er.d2`](diagrams/catalog-er.d2)

### `catalog.sources`

Source registry — one row per data source.

| Column | Type | Constraint |
|--------|------|-----------|
| `source_id` | INTEGER | PK, auto |
| `source_name` | VARCHAR(100) | NOT NULL, UNIQUE |
| `short_name` | VARCHAR(50) | NOT NULL, UNIQUE |
| `publisher` | VARCHAR(50) | NOT NULL |
| `category` | VARCHAR(50) | NOT NULL |
| `download_url` | TEXT | |
| `format` | VARCHAR(20) | |
| `update_frequency` | VARCHAR(20) | |
| `tier` | SMALLINT | NOT NULL, default 1 |
| `status` | VARCHAR(20) | NOT NULL, default 'active' |
| `primary_key_columns` | TEXT | JSON array |
| `notes` | TEXT | |
| `created_at` | TIMESTAMP | default NOW() |
| `updated_at` | TIMESTAMP | default NOW() |

### `catalog.source_columns`

Column-level metadata per source.

| Column | Type | Notes |
|--------|------|-------|
| `column_id` | INTEGER | PK |
| `source_id` | INTEGER | FK → sources |
| `column_name` | VARCHAR(200) | Canonical name |
| `source_column_name` | VARCHAR(200) | Original name from publisher |
| `data_type` | VARCHAR(50) | |
| `is_nullable` | BOOLEAN | default true |
| `is_primary_key` | BOOLEAN | default false |
| `description` | TEXT | |
| `validation_regex` | VARCHAR(200) | |

### `catalog.pipeline_runs`

Execution log — one row per pipeline stage execution.

| Column | Type | Notes |
|--------|------|-------|
| `run_id` | INTEGER | PK |
| `source_id` | INTEGER | FK → sources |
| `run_date` | DATE | |
| `data_year` | SMALLINT | |
| `data_quarter` | SMALLINT | |
| `stage` | VARCHAR(20) | acquire, validate, transform, load |
| `status` | VARCHAR(20) | running, success, failed, skipped |
| `rows_processed` | BIGINT | |
| `rows_loaded` | BIGINT | |
| `file_hash` | VARCHAR(64) | SHA-256 |
| `file_size_bytes` | BIGINT | |
| `duration_seconds` | DECIMAL(10,2) | |
| `error_message` | TEXT | |
| `started_at` | TIMESTAMP | |
| `completed_at` | TIMESTAMP | |

Indexes: `(source_id, run_date)`, `(status)`

### `catalog.pipeline_failures`

Classified failure details linked to runs.

| Column | Type | Notes |
|--------|------|-------|
| `failure_id` | INTEGER | PK |
| `run_id` | INTEGER | FK → pipeline_runs |
| `error_type` | VARCHAR(50) | download, validation, transform, load |
| `error_class` | VARCHAR(100) | e.g., ConnectionError, SchemaViolation |
| `error_message` | TEXT | |
| `error_detail` | TEXT | Full traceback |
| `is_retryable` | BOOLEAN | default false |

### `catalog.validation_runs`

Per-load quality scores from the validation framework.

| Column | Type | Notes |
|--------|------|-------|
| `validation_id` | INTEGER | PK |
| `run_id` | INTEGER | FK → pipeline_runs |
| `rule_name` | VARCHAR(100) | |
| `severity` | VARCHAR(10) | BLOCK, WARN, INFO |
| `passed` | BOOLEAN | |
| `metric_value` | TEXT | |
| `threshold` | TEXT | |
| `message` | TEXT | |
| `rows_affected` | BIGINT | |

Indexes: `(run_id)`, `(severity, passed)`

### `catalog.quarantine_rows`

Rows failing validation, serialized as JSON for investigation.

| Column | Type | Notes |
|--------|------|-------|
| `quarantine_id` | BIGINT | PK |
| `run_id` | INTEGER | FK → pipeline_runs |
| `source_id` | INTEGER | FK → sources |
| `rule_name` | VARCHAR(100) | |
| `row_data` | TEXT | JSON serialized row |
| `failure_reason` | TEXT | |

### `catalog.data_freshness`

SHA-256-based staleness tracking per source per year.

| Column | Type | Notes |
|--------|------|-------|
| `freshness_id` | INTEGER | PK |
| `source_id` | INTEGER | FK → sources |
| `data_year` | SMALLINT | |
| `last_checked_at` | TIMESTAMP | |
| `last_changed_at` | TIMESTAMP | |
| `last_loaded_at` | TIMESTAMP | |
| `latest_file_hash` | VARCHAR(64) | SHA-256 |
| `is_stale` | BOOLEAN | |
| `staleness_days` | INTEGER | |

Unique constraint: `(source_id, data_year)`

---

## Reference Schema

26 tables loaded by pipelines, covering:

| Category | Tables | Examples |
|----------|--------|---------|
| Geographic | FIPS, ZIP-County, CBSA, RUCA, HRR/HSA, Census | `reference.fips_states`, `reference.zip_county_crosswalk` |
| Code Systems | ICD-10-CM, ICD-10-PCS, HCPCS, MS-DRG, NDC, Taxonomy, POS Codes | `reference.icd10cm_codes`, `reference.ndc_directory` |
| Fee Schedules | RVU, Wage Index, IPPS Rates | `reference.rvu_values`, `reference.wage_index` |
| Provider | NPPES, POS Facilities, PECOS | `reference.nppes_providers` |
| Quality | Five-Star, Readmissions, CAHPS, Dialysis, PBJ | Loaded to staging directly |

---

## Staging Tables — Partitioning Strategy

Large utilization tables use per-year loading:

```
staging.stg_part_b_utilization     -- ~10M rows/year
staging.stg_part_d_prescribers     -- ~25M rows/year
staging.stg_geographic_variation   -- ~3.3K rows/year
staging.stg_inpatient              -- ~200K rows/year
```

dbt staging models are ephemeral (compile-time only) — the actual tables are loaded by pipelines with `_loaded_at` timestamps and `data_year` partitioning columns.

---

## Alembic Migration Sequence

Source: `pipelines/alembic/versions/`

| Migration | Description |
|-----------|-------------|
| 001 | Create 7 database schemas |
| 002 | Create 4 RBAC roles with schema-level grants |
| 003 | Create catalog schema (7 tables) |
| 004 | Create metadata schema (Alembic version, dbt run metadata) |
| 005 | Create geographic reference tables (FIPS, ZIP-County, CBSA, RUCA) |
| 006 | Create code system reference tables (ICD-10, HCPCS, MS-DRG, NDC, taxonomy, POS) |
| 007 | Create fee schedule reference tables (RVU, wage index, IPPS rates) |
| 008 | Create provider/facility reference tables (NPPES, POS facilities) |
| 009 | Create staging tables for utilization data (Part B, Part D, GeoVar) with yearly partitioning |
| 010 | Create Tier 2 staging and reference tables (quality, additional sources) |

Run with: `make migrate` or `alembic -c pipelines/alembic/alembic.ini upgrade head`

---

**Next:** [Pipelines →](05-pipelines.md)
