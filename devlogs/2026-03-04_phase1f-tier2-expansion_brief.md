# Phase 1f: Tier 2 Expansion — Brief

**Date**: 2026-03-04
**Phase**: 1f — 26 Tier 2 Pipeline Modules + New Intermediate/Mart Models + New API Routes + New Frontend Pages
**Status**: IN PROGRESS

---

## Context

Phases 1a–1e are complete (198 tests passing, 11 skipped). The platform has:
- 20 pipeline modules (14 Tier 1 reference + 3 Tier 1 utilization + 3 Tier 1 identity)
- 16 dbt models (5 staging, 5 intermediate, 6 mart)
- 7 API route modules, 5 frontend pages
- Dual-engine (PG + DuckDB) serving layer

Phase 1f expands to the remaining 26 Tier 2 sources across 10 domain groups.

## Approach

### Build Order (grouped by domain dependency)

| Group | Sources | New Pipelines | Key Transforms |
|-------|---------|--------------|----------------|
| 1. Provider Enrichment | pecos, ordering_referring | 2 | Reassignment chains, eligibility flags |
| 2. Code Systems | apc | 1 | APC-HCPCS mapping |
| 3. Geographic | hrr_hsa, census | 2 | HRR/HSA ZIP crosswalk, population denominators |
| 4. Institutional Utilization | inpatient, snf, hha, hospice | 4 | DRG weight join, CCN-based, averages→totals |
| 5. Fee Schedules | clfs, dmepos_fees, snf_pps | 3 | Rate lookup tables |
| 6. Drug/Prescribing | sdud, rxnorm, asp | 3 | NDC normalization, RxNorm crosswalk, quarterly cadence |
| 7. Quality | five_star, pbj, cahps, dialysis, readmissions | 5 | Star ratings, staffing→daily→quarterly, measure pivots |
| 8. Hospital Financial | cost_reports_snf/hha/hospice, hospital_general | 4 | Same HCRIS pattern as hospital, general info merge |
| 9. Charges + DME | charges, dme | 2 | Charge variation, supplier utilization |
| 10. Medicare Advantage | ma_enrollment, ma_benchmarks | 2 | County penetration rates, benchmark comparison |

### New dbt Models (planned)

**Staging** (ephemeral, 12 new): inpatient, snf, hha, hospice, sdud, five_star, pbj, cahps, dialysis, readmissions, hospital_general, charges

**Intermediate** (8 new):
- `int_hospital_discharges` — DRG weight, CMI computation from inpatient
- `int_hospital_readmissions` — Penalty calculation
- `int_nursing_home_staffing` — Daily→quarterly aggregation from PBJ
- `int_nursing_home_quality` — Five-star + staffing merge
- `int_drug_utilization_medicaid` — SDUD normalized, NDC→ingredient
- `int_drug_pricing` — ASP + NDC crosswalk
- `int_patient_experience` — CAHPS measure pivot
- `int_ma_market` — County penetration from enrollment

**Mart** (10 new):
- `mart_hospital__financial_profile` — Enable existing placeholder + enrich
- `mart_hospital__performance` — Discharges + DRG mix
- `mart_hospital__readmissions` — Penalty amounts + rates
- `mart_hospital__charge_variation` — Billed vs. expected
- `mart_drug__medicaid_utilization` — State-level Medicaid drug spending
- `mart_drug__price_trends` — ASP quarterly trends
- `mart_postacute__snf_quality` — Star ratings + staffing
- `mart_postacute__hha_quality` — HHA quality metrics
- `mart_postacute__hospice_quality` — Hospice quality metrics
- `mart_ma__market_penetration` — County MA enrollment share

### New API Routes (3 new route modules)
- `api/routes/hospitals.py` — Financial profile, performance, readmissions, charges
- `api/routes/drugs.py` — Medicaid utilization, price trends
- `api/routes/postacute.py` — SNF/HHA/Hospice quality

### New Frontend Pages (3 new)
- `frontend/app/hospitals/page.tsx` — Hospital Comparison dashboard
- `frontend/app/drugs/page.tsx` — Drug Spending Explorer
- `frontend/app/postacute/page.tsx` — Post-Acute Care dashboard

### Alembic Migration
- Migration 010: Staging tables for all Tier 2 sources

## Risks

1. **Volume**: 26 pipelines is substantial — use established patterns to minimize per-module effort
2. **HCRIS variants**: SNF/HHA/Hospice cost reports use same HCRIS structure but different worksheet mappings
3. **Quarterly sources**: SDUD (5M/quarter) needs careful partition strategy
4. **RxNorm format**: RRF format is unusual (pipe-delimited), needs custom reader

## Success Criteria

- [ ] 26 new pipeline modules with validate/transform/run
- [ ] 10 new Alembic migrations for staging tables
- [ ] 12 new staging dbt models (ephemeral)
- [ ] 8 new intermediate dbt models
- [ ] 10 new mart dbt models
- [ ] 3 new API route modules
- [ ] 3 new frontend pages
- [ ] All tests passing (target: 300+)
- [ ] 40+ active sources in catalog
