# 13 — Pipeline Integrity System

[← Back to Index](index.md)

> Phase 2, Sprints 0-3 | Completed 2026-04-01

---

## Overview

Every pipeline execution in Project PUF is **fully tracked, validated, auditable, and recoverable**. This document describes the integrity system built in Phase 2.

## Architecture

```
Pipeline run()
    │
    ├─ record_pipeline_run()          → catalog.pipeline_runs
    │
    ├─ validate_<source>()
    │   ├─ 22 validation rules        → catalog.validation_runs
    │   ├─ quarantine masks           → catalog.quarantine_rows
    │   └─ raise_if_blocked()         (persists before raising)
    │
    ├─ apply_quarantine()             → removes bad rows, writes JSON to catalog
    │
    ├─ transform + load
    │
    ├─ update_data_freshness()        → catalog.data_freshness
    │
    └─ complete_pipeline_run()        → catalog.pipeline_runs (success/failed)
        └─ record_pipeline_failure()  → catalog.pipeline_failures (on error)
```

## Catalog Tables (Migration 003)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `catalog.sources` | 48 registered data sources | source_id, short_name, tier |
| `catalog.pipeline_runs` | Every execution | run_id, source_id, status, rows_loaded, duration_seconds |
| `catalog.pipeline_failures` | Classified errors | error_type, error_class, is_retryable |
| `catalog.validation_runs` | Every check result | rule_name, severity, passed, metric_value, rows_affected |
| `catalog.quarantine_rows` | Failed rows (JSON) | rule_name, row_data, failure_reason |
| `catalog.data_freshness` | Staleness tracking | last_loaded_at, latest_file_hash, latest_etag |
| `catalog.source_columns` | Column metadata | column_name, data_type, validation_regex |

## Validation Framework

### 22 Rules

| Rule | Severity | Quarantines |
|------|----------|-------------|
| `check_required_columns` | BLOCK | No (aggregate) |
| `check_column_not_null` | BLOCK/WARN | Yes |
| `check_column_format` | BLOCK/WARN | Yes |
| `check_uniqueness` | BLOCK/WARN | No (aggregate) |
| `check_row_count` | WARN | No (aggregate) |
| `check_value_set` | BLOCK/WARN | Yes |
| `check_null_rate` | WARN | No (aggregate) |
| `check_value_range` | WARN | No (aggregate) |
| `check_referential_integrity` | WARN | Yes |
| `check_row_count_delta` | WARN | No (aggregate) |

### Severity Behavior

- **BLOCK**: Pipeline halts. Validation results persisted before raising. No data loaded.
- **WARN**: Pipeline continues. Metrics recorded. Escalates to BLOCK if >10% of rows fail (`warn_escalation_threshold` in `pipeline.yaml`).

### Quarantine Flow

1. Row-level checks capture boolean masks on the DataFrame
2. `ValidationReport` accumulates masks keyed by rule name
3. `apply_quarantine()` OR's all masks, writes failing rows to `catalog.quarantine_rows` as JSON
4. Returns clean DataFrame (bad rows removed, not silently dropped)

## Download Resilience

| Feature | Implementation | Config |
|---------|---------------|--------|
| Retry | tenacity with configurable attempts/delays | `pipeline.yaml` → retry.max_attempts, retry.delay_seconds |
| ETag pre-check | HTTP HEAD before full download | Stored in `catalog.data_freshness.latest_etag` |
| Hash dedup | SHA-256 post-download check | `catalog.data_freshness.latest_file_hash` |
| Size validation | Per-source min/max GB bounds | `sources.yaml` → file_size.min_gb, max_gb |

Retries on: `ConnectError`, `TimeoutException`, HTTP 5xx. Does NOT retry 4xx.

## Failure Classification

| Error Type | Example | Retryable |
|-----------|---------|-----------|
| `download` | ConnectError, 503 Service Unavailable | Yes |
| `validation` | BLOCK rule failed (null primary keys) | No |
| `load` | PostgreSQL connection lost during COPY | Yes |
| `transform` | dbt model compile/runtime error | No |
| `unknown` | Unclassified exception | No |

## Key Files

| File | Purpose |
|------|---------|
| `pipelines/_common/catalog.py` | All catalog write functions |
| `pipelines/_common/validate.py` | 22 validation rules, ValidationReport, apply_quarantine |
| `pipelines/_common/acquire.py` | Download with retry, ETag check, hash dedup |
| `pipelines/_common/db.py` | PostgreSQL COPY, DuckDB Parquet with lineage metadata |
| `config/pipeline.yaml` | Retry config, validation thresholds, storage paths |
| `scripts/seed_catalog_sources.py` | Populate catalog.sources from sources.yaml |

## Operational Queries

```sql
-- Recent pipeline failures
SELECT s.short_name, r.status, r.error_message, r.duration_seconds
FROM catalog.pipeline_runs r
JOIN catalog.sources s ON r.source_id = s.source_id
WHERE r.status = 'failed'
ORDER BY r.started_at DESC LIMIT 10;

-- Validation failure hotspots
SELECT rule_name, severity, COUNT(*) as failures
FROM catalog.validation_runs WHERE NOT passed
GROUP BY rule_name, severity ORDER BY failures DESC;

-- Stale sources
SELECT s.short_name, f.last_loaded_at,
       EXTRACT(DAYS FROM NOW() - f.last_loaded_at) AS days_stale
FROM catalog.data_freshness f
JOIN catalog.sources s ON f.source_id = s.source_id
ORDER BY days_stale DESC NULLS FIRST;

-- Quarantine volume
SELECT s.short_name, q.rule_name, COUNT(*) as quarantined
FROM catalog.quarantine_rows q
JOIN catalog.sources s ON q.source_id = s.source_id
GROUP BY s.short_name, q.rule_name ORDER BY quarantined DESC;
```
