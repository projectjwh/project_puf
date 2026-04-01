# Phase 1c: Core Identity — NPPES, POS, Cost Reports + dbt Init — Brief

**Date**: 2026-03-04
**Task**: 3 heavyweight pipelines, dbt project, staging/intermediate/mart models
**Depends on**: Phase 1a (foundation), Phase 1b (reference tables)

## Scope

### 3 Heavyweight Pipelines
| Source | Volume | Complexity |
|--------|--------|-----------|
| NPPES | 8M rows, 8-10 GB | 330→40 column pruning, taxonomy extraction, deactivation filter |
| POS Facilities | 300K rows | Quarterly updates, facility type classification |
| Cost Reports | 6K rows/year | Multi-worksheet extraction, financial metric derivation |

### dbt Project Initialization
- `models/dbt_project.yml` and `models/profiles.yml`
- Source definitions for staging schema
- 3 staging models (1:1 source mirrors)
- 2 intermediate models (business logic layer)
- Provider reference mart

### Alembic Migration 008
- `ref_providers` (~8M rows, master provider dimension)
- `ref_provider_taxonomies` (NPI × taxonomy unpivot)
- `ref_pos_facilities` (~300K rows)

## Success Criteria
- [ ] NPPES pipeline: acquire, validate, transform, write Parquet
- [ ] POS pipeline: acquire, validate, transform, write Parquet
- [ ] Cost Reports pipeline: acquire, validate, extract financials
- [ ] `dbt run` compiles all models (SQL valid)
- [ ] `dbt test` passes schema tests
- [ ] All unit tests pass
