# Antagonist Audit Report — 2026-04-02

Covers all Phase 2 code (commits 1cc14c2..c6f9991, 10 commits).

---

## QA Gate Report — Mei-Lin Chang

| Gate | Status | Details |
|------|--------|---------|
| 1. CI passes | **PASS** | 0 lint, 0 format, 0 type, 484 passed |
| 2. No regressions | **PASS** | 484 >= baseline 484 |
| 3. New code has tests | **PASS** | All new modules have test files |
| 4. Pipeline integrity wired | **WARN** | 8/10 large pipelines wired. Missing: `inpatient` (224 LOC), `sdud` (201 LOC) — these are Tier 2 stubs, not Tier 1 |
| 5. Validation coverage | **PASS** | All 8 Tier 1 pipelines have validate_*() with required_columns + not_null + row_count |
| 6. No hardcoded config | **BLOCKED** | 10 pipeline files still have `year - 2` hardcoded. `alembic/env.py` and `config.py` have default password. |
| 7. Migration reversibility | **PASS** | All 12 migrations have downgrade() |

**Verdict: BLOCKED** — Gate 6 violations must be addressed.

### Gate 6 Violations (Hardcoded Config)

**`year - 2` hardcoded in 10 pipeline run() functions:**
- `pipelines/charges/pipeline.py:122`
- `pipelines/cost_reports/pipeline.py:191` (Tier 1!)
- `pipelines/cost_reports_hha/pipeline.py:64`
- `pipelines/cost_reports_hospice/pipeline.py:64`
- `pipelines/cost_reports_snf/pipeline.py:75`
- `pipelines/dme/pipeline.py:104`
- `pipelines/geovar/pipeline.py:198` (Tier 1!)
- `pipelines/hha/pipeline.py:147`
- `pipelines/hospice/pipeline.py:147`
- `pipelines/inpatient/pipeline.py:187`

**Fix**: Replace with `compute_data_year(source, run_date)` from `config.py`. Sprint 4 added this function and wired it into FLOWS but missed the pipeline `run()` fallback defaults.

**Default password in code:**
- `pipelines/alembic/env.py:15` — `os.environ.get("PUF_DB_PASSWORD", "puf_dev_password")`
- `pipelines/_common/config.py:46` — `password: str = "puf_dev_password"`

**Severity**: Low for public data project. The password is for local Docker dev only and is documented in `.env.example`. Still, production deployments should require the env var without fallback.

---

## Red Team Report — Yuki Tanaka

### CRITICAL

*None found.*

### HIGH

**H1: Partial file on download failure — no cleanup**
- `pipelines/_common/acquire.py:67` — `_do_download()` writes to `dest_path` via `open(dest_path, "wb")`. If the stream fails mid-write, a partial file remains on disk. Next run may find this file and attempt to process it.
- Scenario: Network drops at 80% of a 4GB Part B download. Retry re-downloads from scratch (good), but the partial file from the first attempt is still on disk.
- Blast radius: One pipeline, one data year.
- Fix: Delete `dest_path` in a `finally` block if download didn't complete, or use a temp file and rename on success.
- Owner: @pipeline-engineer

**H2: `get_pg_engine()` creates a new engine per call — no connection pooling reuse**
- `pipelines/_common/db.py:29` — Every call creates a new `create_engine()`. No singleton or `lru_cache`. In a pipeline that calls `copy_dataframe_to_pg()` + `execute_sql()` + catalog writes, this creates 4+ separate connection pools.
- Scenario: 6 parallel pipeline tasks, each creating 4 engines = 24 connection pools with `pool_pre_ping=True` pinging on every checkout.
- Blast radius: Connection exhaustion, PostgreSQL `max_connections` hit.
- Fix: Add `@lru_cache` to `get_pg_engine()` or use a module-level singleton.
- Owner: @platform-engineer

**H3: SQL injection surface in COPY statement**
- `pipelines/_common/db.py:128` — `f"COPY {schema}.{table_name} FROM STDIN ..."` uses f-string interpolation for schema and table names. These come from pipeline code (not user input), but a malformed source name could inject SQL.
- Scenario: If `source_name` ever contained `;DROP TABLE` (extremely unlikely from sources.yaml), it could execute arbitrary SQL.
- Blast radius: Full database.
- Fix: Validate schema/table names against allowlist, or use `psycopg2.sql.Identifier()`.
- Owner: @pipeline-engineer

### MEDIUM

**M1: Contract validation is a no-op when contract file is missing**
- `pipelines/_common/validate.py` `_load_contract()` returns `{}` if file not found. `validate_against_contract()` silently returns. New sources without contracts pass unchecked.
- Fix: Log WARN (already done), but consider making missing contract a BLOCK for Tier 1 sources.

**M2: `record_pipeline_run()` returns -1 silently when catalog.sources isn't seeded**
- All downstream catalog functions check `if run_id < 0: return` — the entire audit trail is silently disabled.
- Fix: `seed_catalog_sources.py` must be a required post-migration step. Add to `make migrate` or as an Alembic data migration.

**M3: 8 bare `except Exception` blocks in _common/ that log warnings but swallow errors**
- `acquire.py` (3), `baselines.py` (1), `db.py` (2), `dbt_runner.py` (1), `reference.py` (1)
- These are intentional (graceful degradation), but they make debugging harder. A catalog write failure during a pipeline run is invisible unless you check logs.

**M4: Snapshot SCD runs are not idempotent**
- `snp_provider_history` uses dbt's check strategy. Running `dbt snapshot` twice on the same data is safe. But running it twice on DIFFERENT data in the same day creates two valid_from entries with the same date.
- Fix: Ensure snapshot runs are gated by data freshness (only snapshot after new data is loaded).

### LOW

**L1: `STATE_ABBREV_TO_FIPS` duplicated in 4 files** — nppes, partb, partd, inpatient. Should be in `_common/constants.py`.

**L2: DuckDB connection created per call** — `get_duckdb_connection()` returns a new `:memory:` connection each time. No state persistence between reads.

**L3: No `.env` validation on startup** — If required env vars are missing, errors surface deep in pipeline execution, not at startup.

### Acknowledged Strengths

- Validation framework with BLOCK/WARN/quarantine is production-grade
- Catalog tracking on all Tier 1 pipelines is thorough
- tenacity retry with configurable delays is well-implemented
- ETag pre-check before large downloads is a smart bandwidth optimization
- Chunked COPY with savepoints is a genuine reliability improvement
- Circuit breaker pattern prevents repeated failures from wasting resources
- Data contracts with schema drift detection are forward-looking

---

## Incident Commander Report — Rafael Costa

### Scenario 1: Database Connection Exhaustion
- **Trigger**: 6+ parallel pipeline tasks, each creating multiple SQLAlchemy engines
- **Probability**: Likely (under concurrent Prefect execution)
- **Severity**: HIGH
- **Blast radius**: All pipelines stall. API may also be affected if PgBouncer pool is saturated.
- **Current mitigation**: PgBouncer with pool_size=20 for apps. COPY uses direct connection (bypasses PgBouncer).
- **Gap**: `get_pg_engine()` has no caching — creates new pool per call.
- **Recommended fix**: Singleton engine with `@lru_cache`. Prefect concurrency tags (already added in Sprint 4) limit parallel db-write tasks to 4.

### Scenario 2: Silent Data Corruption (Hash-Passes-But-Data-Wrong)
- **Trigger**: CMS silently corrects a few rows in a file without changing the filename or Content-Length, but ETag/hash changes.
- **Probability**: Possible (CMS does make mid-cycle corrections)
- **Severity**: MEDIUM
- **Blast radius**: One source, one data year. Downstream marts reflect corrected data after next load.
- **Current mitigation**: SHA-256 hash detects ANY change. ETag pre-check catches remote changes. Validation rules catch structural issues.
- **Gap**: No row-level diff detection. Can't answer "what changed between this load and last?"
- **Recommended fix**: Phase 3 — store row counts and key metric snapshots per load for diff detection.

### Scenario 3: Catalog Write Failure Mid-Pipeline
- **Trigger**: PostgreSQL goes down between `record_pipeline_run()` and `complete_pipeline_run()`.
- **Probability**: Unlikely (local Docker, health checks)
- **Severity**: MEDIUM
- **Blast radius**: Orphaned `pipeline_runs` row with status='running' that never completes. Data may have been loaded but `data_freshness` not updated.
- **Current mitigation**: All catalog writes are wrapped in try/except with warnings. Pipeline continues even if catalog is down.
- **Gap**: No cleanup job for orphaned 'running' records. No health check on catalog writes.
- **Recommended fix**: Add a `catalog.cleanup_orphaned_runs()` function that marks 'running' records older than 1 hour as 'unknown'.

### Scenario 4: Large File Download Failure at 99%
- **Trigger**: Network drops after downloading 3.8GB of a 4GB Part B file.
- **Probability**: Possible (large files on unreliable networks)
- **Severity**: LOW
- **Blast radius**: One pipeline, one run. Retry re-downloads from scratch.
- **Current mitigation**: tenacity retry (3 attempts). Hash check after download.
- **Gap**: No resume capability (HTTP Range headers). Partial file not cleaned up (see Red Team H1).
- **Recommended fix**: Phase 3 — HTTP Range resume. Immediate: cleanup partial files on failure.

### Scenario 5: dbt Model Failure Leaving Stale Marts
- **Trigger**: One intermediate model fails (e.g., `int_provider_services` has a SQL error). dbt continues with other models. Mart models that depend on the failed intermediate use stale data.
- **Probability**: Possible (during schema changes)
- **Severity**: HIGH
- **Blast radius**: All marts downstream of the failed model serve stale data. API returns outdated results.
- **Current mitigation**: `dbt_runner.py` captures per-model success/failure. Classifies errors.
- **Gap**: No alerting when a model fails. No staleness flag on mart tables. API serves whatever's in the mart table with no freshness indicator.
- **Recommended fix**: Add `_dbt_last_run_at` column to mart tables. API should surface data freshness. Alert on dbt model failures.

---

## Summary of Findings

| Severity | Count | Source |
|----------|-------|--------|
| QA BLOCKED | 1 | Gate 6: hardcoded `year - 2` in 10 pipelines |
| RED TEAM HIGH | 3 | H1 (partial file), H2 (engine singleton), H3 (SQL injection surface) |
| RED TEAM MEDIUM | 4 | M1-M4 |
| RED TEAM LOW | 3 | L1-L3 |
| INCIDENT HIGH | 2 | Connection exhaustion, stale marts after dbt failure |
| INCIDENT MEDIUM | 2 | Catalog write failure, silent data correction |
| INCIDENT LOW | 1 | Partial download cleanup |

## Recommended Fix Priority

| Priority | Finding | Owner | Effort |
|----------|---------|-------|--------|
| 1 | Fix `year - 2` hardcode in 10 pipelines (Gate 6) | @pipeline-engineer | 30 min |
| 2 | Add `@lru_cache` to `get_pg_engine()` (H2, Incident 1) | @platform-engineer | 10 min |
| 3 | Delete partial file on download failure (H1, Incident 4) | @pipeline-engineer | 15 min |
| 4 | Validate schema/table names in COPY (H3) | @pipeline-engineer | 15 min |
| 5 | Add `seed-catalog` to `make migrate` (M2) | @platform-engineer | 5 min |
| 6 | Centralize STATE_ABBREV_TO_FIPS (L1) | @pipeline-engineer | 20 min |
