# 14 — Analytical Domains

[← Back to Index](index.md)

> Phase 2A | Completed 2026-04-02

---

## Overview

Five analytical domains expand the platform from a data pipeline into a healthcare analytics database. Three P0 domains are implemented; two P1 domains are planned.

## Domain Map

```
                    ┌──────────────────────────────────────────┐
                    │         UniProvDB (SCD Type 2)           │
                    │   NPI × validity period — change history │
                    └──────────────┬───────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
    ┌────┴─────┐          ┌────────┴────────┐        ┌───────┴───────┐
    │ Provider │          │   Procedure     │        │  Population   │
    │ Profiles+│          │   Analytics     │        │  Analytics    │
    │ quality  │          │   HCPCS-level   │        │  aggregates   │
    │ + cost   │          │   price, mix    │        │  by geography │
    └────┬─────┘          └────────┬────────┘        └───────┬───────┘
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                    ┌──────────────┴───────────────────────────┐
                    │        County Geography                  │
                    │   Sub-state variation + provider supply  │
                    └──────────────────────────────────────────┘
```

---

## Domain 1: UniProvDB — SCD Provider History (P0, Complete)

**Purpose**: Track provider attribute changes over time using SCD Type 2.

**Tracked Attributes**: `primary_taxonomy_code`, `practice_state`, `practice_zip5`, `is_active`, `entity_type`

### Models

| Model | Grain | Layer | Materialization |
|-------|-------|-------|----------------|
| `snp_provider_history` | NPI × validity period | snapshot | dbt snapshot (SCD2) |
| `mart_provider__historical_profile` | NPI × dbt_valid_from | mart | table (indexed) |
| `mart_provider__practice_profile` | NPI (latest) | mart | table (extended) |

### New Fields on Practice Profile

| Column | Source | Description |
|--------|--------|-------------|
| `provider_versions` | Snapshot aggregate | Total historical records for this NPI |
| `first_seen_date` | Snapshot min(dbt_valid_from) | Earliest appearance in the system |
| `state_changes` | Snapshot distinct(practice_state) | Number of practice state changes |
| `specialty_changes` | Snapshot distinct(taxonomy_code) | Number of taxonomy changes |

### Historical Profile Features

- `version_number` — sequential version per NPI
- `is_current` — True for the active record
- `days_in_version` — Duration of each state
- `previous_state` / `previous_taxonomy` — LAG window functions
- `is_state_change` / `is_taxonomy_change` — Change detection flags

### Key Files

- `models/snapshots/snp_provider_history.sql`
- `models/marts/provider/mart_provider__historical_profile.sql`
- `models/marts/provider/mart_provider__practice_profile.sql` (extended)

---

## Domain 3: Provider Profiles+ — Quality & Cost Overlay (P0, Complete)

**Purpose**: Complete the provider profile with quality scores and readmission metrics.

### New Pipelines

| Pipeline | Source | Key Columns | Catalog Wired |
|----------|--------|-------------|---------------|
| `five_star` | CMS Five-Star Ratings | ccn, overall_rating, health/staffing/quality ratings | Yes |
| `readmissions` | CMS Readmissions | ccn, measure_id, score, compared_to_national | Yes |

Both pipelines follow the full integrity pattern: `record_pipeline_run` → validate with `persist()` → `apply_quarantine` → transform → load → `complete_pipeline_run` + `update_data_freshness`.

### Models

| Model | Grain | Layer | Description |
|-------|-------|-------|-------------|
| `int_provider_quality` | CCN | intermediate | Merges Five-Star + Readmissions + POS facilities |

### Quality Tiers

| Tier | Five-Star | Readmission |
|------|-----------|-------------|
| HIGH | Overall 4-5 stars | N/A |
| MEDIUM | Overall 3 stars | AVERAGE |
| LOW | Overall 1-2 stars | N/A |
| AT_RISK | N/A | Worse than national on any measure |
| ABOVE_AVERAGE | N/A | Better than national on all measures |

### API Additions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v1/providers/compare` | GET | Compare up to 10 providers by NPI (comma-separated) |

### Key Files

- `pipelines/five_star/pipeline.py`
- `pipelines/readmissions/pipeline.py`
- `models/intermediate/int_provider_quality.sql`
- `api/routes/providers.py` (compare endpoint)
- `api/schemas/providers.py` (ProviderCompareResponse)

---

## Domain 4: Procedure-Level Analytics (P0, Complete)

**Purpose**: Expose HCPCS-level detail from Part B staging (~10M rows/year) as analytical marts.

### Models

| Model | Grain | Layer | Description |
|-------|-------|-------|-------------|
| `int_procedure_utilization` | HCPCS × year | intermediate | National procedure summary: volume, payments, provider count, place-of-service mix |
| `int_procedure_by_specialty` | HCPCS × taxonomy × year | intermediate | Procedure ownership by specialty |
| `mart_procedure__utilization_trends` | HCPCS × year | mart | RVU-weighted trends, YOY change |
| `mart_procedure__price_variation` | HCPCS × state × year | mart | Price spread: avg, min, max, p25, p75, stddev, CV |
| `mart_procedure__specialty_mix` | HCPCS × specialty × year | mart | Services share %, payment share %, specialty rank |

### Key Metrics

| Metric | Model | Description |
|--------|-------|-------------|
| `total_services` | utilization_trends | National volume for a procedure |
| `avg_payment_per_service` | utilization_trends | National average Medicare payment |
| `total_rvu` | utilization_trends | RVU complexity weighting (from ref_rvu) |
| `coefficient_of_variation` | price_variation | Price consistency (stddev / avg) |
| `pct_office` / `pct_facility` | utilization_trends | Place-of-service distribution |
| `services_share_pct` | specialty_mix | What % of this procedure does each specialty own? |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v1/procedures/{hcpcs_code}` | GET | Full detail for a single procedure |
| `GET /api/v1/procedures/top` | GET | Top procedures by volume/cost (paginated, sortable) |
| `GET /api/v1/procedures/variation/{hcpcs_code}` | GET | State-level price variation for a procedure |

### Key Files

- `models/intermediate/int_procedure_utilization.sql`
- `models/intermediate/int_procedure_by_specialty.sql`
- `models/marts/procedure/mart_procedure__utilization_trends.sql`
- `models/marts/procedure/mart_procedure__price_variation.sql`
- `models/marts/procedure/mart_procedure__specialty_mix.sql`
- `api/routes/procedures.py`
- `api/schemas/procedures.py`

---

## Domain 2: Population Analytics (P1, Planned)

**Purpose**: Beneficiary population analysis from public aggregates. NOT individual-level MBSF.

**What's available**: State/county beneficiary counts, chronic condition prevalence rates, HCC risk scores, FFS/MA market share, per-capita cost benchmarks.

**What requires DUA**: Individual BENE_ID, individual chronic condition flags, beneficiary journey analysis.

**Planned models**: `int_beneficiary_population`, `mart_population__state_profile`, `mart_population__county_profile`

**Blocked by**: MA Enrollment pipeline implementation (Tier 2 stub → Tier 1)

---

## Domain 5: County Geography (P1, Planned)

**Purpose**: Extend geographic analysis from state-level to county-level.

**Current state**: GeoVar source has county data but `int_geographic_benchmarks` filters to state-only.

**Planned models**: `int_county_profile`, `mart_geographic__county_variation`, `mart_geographic__provider_supply`

**Dependencies**: County data already in staging. CBSA/RUCA reference tables already loaded.

---

## Model Inventory Update

| Layer | Phase 1 | Phase 2A Added | Total |
|-------|---------|----------------|-------|
| Snapshots | 0 | 1 | **1** |
| Staging | 16 | 0 | **16** |
| Intermediate | 13 | 3 | **16** |
| Marts | 16 | 4 | **20** |
| **Total** | **45** | **8** | **53** |

## API Inventory Update

| Phase 1 | Phase 2A Added | Total |
|---------|----------------|-------|
| 28 endpoints | 4 endpoints | **32** |
