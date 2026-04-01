# Phase 1f: Tier 2 Expansion — Retrospective

**Date**: 2026-03-04
**Phase**: 1f of 6 (Phase 1a–1f)
**Status**: COMPLETE

---

## Outcome

Delivered 28 new pipeline modules covering all 26 Tier 2 data sources (some sources like cost reports have shared implementations), plus 24 new dbt models, 3 new API route modules, 3 new frontend pages, and 60 new tests. Full test suite: **258 passed, 11 skipped**.

### Artifact Count

| Category | Count |
|----------|-------|
| Alembic migrations | 1 (010) |
| Pipeline modules | 28 (56 files) |
| dbt staging models | 6 |
| dbt intermediate models | 9 (8 new + 1 rewrite) |
| dbt mart models | 10 |
| API schema modules | 3 |
| API route modules | 3 |
| Frontend pages | 3 |
| Test files | 4 (60 tests) |
| Config updates | 4 (sources.yml, dbt_project.yml, main.py, sidebar.tsx) |

### Source Coverage

40+ sources now have pipeline modules (14 Tier 1 + 28 Tier 2 modules). Tier 2 covers:
- **Provider enrichment**: PECOS, Ordering/Referring
- **Code systems**: APC
- **Utilization**: Inpatient, SNF, HHA, Hospice, DME, Charges
- **Geographic**: HRR/HSA, Census
- **Fee schedules**: CLFS, DMEPOS, SNF PPS
- **Drug/prescribing**: SDUD, RxNorm, ASP
- **Quality**: Five-Star, PBJ, CAHPS, Dialysis, Readmissions
- **Hospital financial**: Cost Reports (SNF/HHA/Hospice), Hospital General
- **MA**: MA Enrollment, MA Benchmarks

---

## What Worked

1. **Pattern reuse from Tier 1 was highly effective**. The `_common/transform.py` utilities (normalize_npi, normalize_fips_county, compute_totals_from_averages, strip_currency, etc.) meant most pipeline transforms were 30-50 lines. The pattern established in Phases 1b-1d paid dividends.

2. **Cost report code reuse**. SNF/HHA/Hospice cost reports share the same HCRIS structure, so importing `RPT_COLUMN_MAPPING`, `extract_financial_metrics`, and `transform_cost_reports` from the hospital cost reports module eliminated duplication.

3. **Grouping pipelines by domain** for implementation kept context coherent — all drug pipelines built together, all quality pipelines together. This caught cross-pipeline consistency issues early (e.g., ensuring all quality pipelines use the same CCN padding).

4. **Partitioned table DDL** using raw SQL in Alembic (via `op.execute()`) for tables that need PARTITION BY RANGE, while using `op.create_table` for simple tables. Clean separation.

5. **Test organization by domain** (4 test files, one per domain cluster) mirrors the pipeline grouping and keeps test files manageable at ~160-175 lines each.

---

## What Didn't Work / Lessons

1. **No Prefect flows created for Tier 2**. Unlike Phase 1d which had individual flows + a combined `utilization_flow.py`, Phase 1f deferred flow orchestration. This is acceptable for now since the focus was on pipeline correctness, but flows will be needed before production.

2. **STATE_ABBREV_TO_FIPS duplication**. Multiple pipeline modules independently define state-to-FIPS mappings. This should be centralized in `_common/transform.py` or a `_common/lookups.py` module. Not blocking but creates maintenance risk.

3. **dbt model testing gap**. The 60 new tests cover Python pipeline logic (transforms, validation). dbt model SQL logic is not tested via pytest — it relies on `dbt test` which requires a live database. Need to add dbt test YAML for the new models.

---

## Patterns Discovered

1. **Three pipeline archetypes emerged across all 28 modules**:
   - **Utilization pipelines** (Inpatient, SNF, HHA, Hospice, DME, Charges, SDUD): averages→totals, CCN/NPI normalization, year tagging, state FIPS derivation
   - **Reference/fee pipelines** (APC, CLFS, DMEPOS, SNF PPS, ASP, RxNorm): currency stripping, code normalization, effective year/quarter tagging
   - **Quality pipelines** (Five-Star, PBJ, CAHPS, Dialysis, Readmissions): score cleaning ("Not Available"→null), rating casting, snapshot date handling

2. **Validation pattern is consistent**: Every pipeline has `validate_{name}()` returning a report object with `block_failures` (nulls in PK columns) and `warnings`. BLOCK = pipeline stops, WARN = pipeline continues with log.

3. **Cross-source intermediate models** are where the real analytical value lives:
   - `int_nursing_home_quality` = Five-Star + PBJ staffing → staffing_consistency_flag
   - `int_hospital_financials` = Hospital + SNF + HHA + Hospice cost reports → unified financial view
   - `int_drug_utilization_medicaid` = SDUD aggregated → cost_per_prescription

---

## Verification

- [x] 258 tests passed, 11 skipped (60 new Tier 2 tests)
- [x] 28 pipeline modules importable and transforms produce expected outputs
- [x] All validation functions catch missing PKs
- [x] 3 new frontend pages created (hospitals, drugs, postacute)
- [x] 3 new API route modules registered in main.py
- [x] Sidebar updated with new navigation items

---

## Phase 1 Summary (All Sub-Phases Complete)

| Phase | Delivered | Tests |
|-------|-----------|-------|
| 1a: Foundation | Docker, Alembic, shared utilities, config | 38 |
| 1b: Reference Data | 14 Tier 1 pipeline modules, 26 ref tables | 97 |
| 1c: Core Identity | NPPES, POS, Cost Reports, dbt project | 135 |
| 1d: Utilization | Part B, Part D, GeoVar, mart models | 198 |
| 1e: API + Frontend | FastAPI, Next.js, 5 pages, 8 routes | 198 |
| 1f: Tier 2 Expansion | 28 pipelines, 24 dbt models, 3 pages | **258** |

**Total**: 45 data source pipelines, 40+ dbt models, 11 API route modules, 8 frontend pages, 258 tests passing.
