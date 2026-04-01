# Phase 1d: Utilization Data — Retrospective

**Date**: 2026-03-04
**Phase**: 1d — Part B, Part D, Geographic Variation
**Status**: COMPLETE

---

## Outcome

All Phase 1d deliverables built and tested. **185 tests passing, 2 skipped** (Prefect not installed).

### Deliverables

| Artifact | Status | Notes |
|----------|--------|-------|
| Alembic migration 009 | Done | Partitioned Part B (6 yearly partitions), Part D (6 yearly partitions), GeoVar |
| Part B pipeline | Done | TOTALS from averages (critical), state FIPS, NPI normalization |
| Part D pipeline | Done | Opioid flagging, brand/generic classification, cost-per-claim derivation |
| GeoVar pipeline | Done | State/county FIPS derivation, rate rounding, per-capita spending |
| dbt staging models | Done | 3 ephemeral models (Part B, Part D, GeoVar) referencing pipeline-loaded tables |
| dbt intermediate models | Done | int_provider_services, int_provider_prescriptions, int_geographic_benchmarks |
| dbt mart models | Done | 6 marts: practice_profile (updated), national KPI, geographic spending+state, opioid state+prescribers |
| Parquet export script | Done | scripts/export_marts_to_parquet.py with CLI |
| Prefect flows | Done | 3 source flows + utilization_flow orchestrator (parallel ingestion) |
| Tests | Done | 31 new tests across 3 test files |
| dbt schema docs | Done | schema.yml for all staging, intermediate, and mart models |

### Test Suite Summary
- Phase 1a common utilities: 65 tests
- Phase 1b reference pipelines: 64 tests
- Phase 1c identity pipelines: 19 tests
- Phase 1d utilization pipelines: 31 tests
- Prefect flow tests: 2 skipped
- **Total: 185 passed, 2 skipped**

---

## What Worked

1. **compute_totals_from_averages reuse** — The shared utility from `_common/transform.py` made the critical Part B total computation a one-liner per field.
2. **Ephemeral staging models** — Since pipelines write directly to partitioned staging tables, using dbt ephemeral models avoids double-materialization while providing named refs for downstream.
3. **Intermediate aggregation pattern** — `int_provider_services` (NPI × year) and `int_provider_prescriptions` (NPI × year) provide clean aggregation boundaries. Marts then join these pre-aggregated tables rather than scanning raw fact tables.
4. **Cross-source mart join** — `mart_provider__practice_profile` joins NPPES identity + Part B services + Part D prescribing on NPI, creating a complete provider profile in one row.
5. **Service categorization in SQL** — E&M, drug, imaging, surgical classification using HCPCS ranges works well in the intermediate model.
6. **Spending indices** — GeoVar intermediate computes state/national ratios, making geographic comparison trivial in the mart layer.

## What Didn't Work

1. **numeric_casting test assumption** — Test assumed `number_of_services` would be float64 after pd.to_numeric, but integer-valued series stay int64. Fixed by using `pd.api.types.is_numeric_dtype()` instead of checking specific dtype strings.

## Lessons Learned

1. **pd.to_numeric preserves int dtype for integer-valued strings** — "150" → int64, not float64. Only strings with decimals or NaN produce float64. Test with `is_numeric_dtype()` rather than exact dtype matching.
2. **Partitioned tables need raw SQL in Alembic** — SQLAlchemy's `op.create_table` doesn't support `PARTITION BY RANGE`. Use `op.execute()` for partition DDL.
3. **Ephemeral dbt models work well as documentation-only refs** — When data is pipeline-loaded (not dbt-loaded), ephemeral models serve as named references without materializing duplicate data.

## Architecture Decisions

1. **Part B/D use `if_exists="append"`** — Unlike reference tables (replace), utilization tables append by year, supporting multi-year loads without data loss.
2. **Opioid flag from source field** — Part D provides `Opioid_Drug_Flag` directly, which is more reliable than maintaining our own opioid drug list.
3. **Brand/generic heuristic** — `drug_name != generic_name` → brand. Simple and effective for Part D data where both fields are always populated.
4. **Spending index** — `state_per_capita / national_per_capita` provides intuitive >1 (above average) / <1 (below) comparison.

---

## Phase 1d File Count

| Category | Files Created | Files Updated |
|----------|--------------|---------------|
| Alembic | 1 | 0 |
| Pipelines | 6 (3 modules + 3 __init__) | 0 |
| dbt staging | 3 | 2 (sources.yml, schema.yml) |
| dbt intermediate | 3 | 1 (schema.yml) |
| dbt mart | 5 | 2 (practice_profile.sql, provider/schema.yml) |
| dbt mart schema | 3 | 0 |
| dbt config | 0 | 1 (dbt_project.yml) |
| Flows | 4 | 0 |
| Scripts | 1 | 0 |
| Tests | 3 | 0 |
| **Total** | **29** | **6** |

## Next Phase

Phase 1e: API + Frontend MVP. Key challenges:
- FastAPI with dual query engine (PostgreSQL for lookups, DuckDB for analytics)
- 7 route modules (providers, geographic, national, opioid, specialties, catalog, health)
- Next.js 15 with 5 pages (National Dashboard, Provider Lookup, Geographic Explorer, Specialty Comparison, Opioid Monitor)
