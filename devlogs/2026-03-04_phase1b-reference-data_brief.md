# Phase 1b: Reference Data — 14 Tier 1 Code Systems & Geography — Brief

**Date**: 2026-03-04
**Task**: Build 14 reference data pipeline modules, 3 Alembic migrations, Prefect orchestration
**Depends on**: Phase 1a (foundation) — COMPLETE

## Context

Phase 1a established the foundation: config loading, validation framework, transform utilities, Alembic setup, Docker Compose. Phase 1b populates the `reference` schema with 14 Tier 1 code systems and geographic lookups that every downstream pipeline depends on.

## Scope

### 14 Reference Sources → 17 Reference Tables

**Geographic (5 tables from 5 sources)**:
| Source | Table | Rows | Format |
|--------|-------|------|--------|
| Census FIPS | `ref_state_fips` | ~56 | CSV |
| Census FIPS | `ref_county_fips` | ~3,250 | CSV |
| HUD ZIP-County | `ref_zip_county_crosswalk` | ~50,000 | XLSX |
| Census CBSA | `ref_cbsa` | ~2,000 | XLSX |
| USDA RUCA | `ref_ruca` | ~75,000 | XLSX |

**Code Systems (7 tables from 7 sources)**:
| Source | Table | Rows | Format |
|--------|-------|------|--------|
| CMS ICD-10-CM | `ref_icd10_cm` | ~72,000 | ZIP/TXT |
| CMS ICD-10-PCS | `ref_icd10_pcs` | ~78,000 | ZIP/TXT |
| CMS HCPCS | `ref_hcpcs_codes` | ~7,500 | ZIP/TXT |
| CMS MS-DRG | `ref_msdrg` | ~800 | ZIP/XLSX |
| FDA NDC | `ref_ndc` | ~300,000 | ZIP/TXT |
| NUCC Taxonomy | `ref_nucc_taxonomy` | ~900 | CSV |
| CMS POS Codes | `ref_place_of_service` | ~100 | CSV |

**Fee Schedules (3 tables from 3 sources)**:
| Source | Table | Rows | Format |
|--------|-------|------|--------|
| CMS RVU | `ref_rvu_fee_schedule` | ~16,000 | ZIP/CSV |
| CMS Wage Index | `ref_wage_index` | ~4,000 | XLSX |
| CMS IPPS | `ref_ipps_rates` | ~800 | XLSX |

### Deliverables
1. Alembic migrations 005 (geographic), 006 (code systems), 007 (fee schedules)
2. 14 pipeline modules: `pipelines/{source}/pipeline.py`
3. Shared reference pipeline runner: `pipelines/_common/reference.py`
4. Prefect flow: `flows/reference_flow.py`
5. Tests: `tests/test_reference_pipelines.py`

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pipeline structure | Single `pipeline.py` per source | Reference sources are small; one file is sufficient |
| Shared runner | `_common/reference.py` with generic load pattern | Avoid duplicating acquire→validate→transform→load across 14 modules |
| Migration grouping | 3 migrations by domain | Geographic, codes, fees are logical groups |
| Table naming | `ref_{domain}` prefix | Schema Smith convention |

## Approach
1. Write Alembic migrations with exact DDL for all 17 tables
2. Write shared reference pipeline runner
3. Write 14 per-source pipeline modules (column mappings, validation rules, transforms)
4. Write Prefect flow orchestrating all 14
5. Write tests validating transforms and column mappings

## Success Criteria
- [ ] `alembic upgrade head` creates 17 reference tables
- [ ] Each pipeline module can be imported and defines required config
- [ ] Prefect flow dispatches to all 14 sources
- [ ] Tests pass for column mappings and transforms
