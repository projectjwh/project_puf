# Phase 1d: Utilization Data — Brief

**Date**: 2026-03-04
**Phase**: 1d — Part B, Part D, Geographic Variation
**Status**: PLANNING

---

## Context

Phase 1c delivered core identity (NPPES, POS, Cost Reports) with 154 passing tests. Phase 1d adds the three analytical workhorses: Medicare Part B utilization (10M rows/year), Part D prescriber data (25M rows/year), and Geographic Variation (3.3K rows/year). These are the primary fact tables that power provider profiles, geographic comparisons, and opioid monitoring.

## Key Challenges

1. **Part B: TOTALS from AVERAGES** — Source provides `average_Medicare_allowed_amt` and `number_of_services`. Must compute `total_allowed = avg * count`. Without this, aggregation across providers/specialties is impossible.
2. **Part D: Opioid flagging** — Must flag opioid prescribers using drug classification or opioid_prescriber_rate field. Critical for opioid monitoring mart.
3. **Scale** — Part B 10M rows/year, Part D 25M rows/year. Need partitioned staging tables and efficient Parquet writes.
4. **Cross-source joins** — Practice profile mart needs Part B + Part D + NPPES in one row per NPI per year.

## Approach

### Alembic Migration 009: Partitioned Staging Tables
- `staging.stg_cms__part_b_utilization` — PARTITION BY RANGE (data_year), ~10M rows/year
- `staging.stg_cms__part_d_prescribers` — PARTITION BY RANGE (data_year), ~25M rows/year
- `staging.stg_cms__geographic_variation` — Small table, no partitioning needed

### Pipeline Modules
- `pipelines/partb/pipeline.py` — Acquire, validate, transform Part B Provider Utilization
- `pipelines/partd/pipeline.py` — Acquire, validate, transform Part D Prescriber data
- `pipelines/geovar/pipeline.py` — Acquire, validate, transform Geographic Variation

### dbt Models
**Staging** (views reading from pipeline-loaded tables):
- `stg_cms__part_b_utilization` — Type-safe view with column rename
- `stg_cms__part_d_prescribers` — Type-safe view with column rename
- `stg_cms__geographic_variation` — Type-safe view

**Intermediate** (where value is created):
- `int_provider_services` — TOTALS from averages, service categorization
- `int_provider_prescriptions` — Cost-per-unit, opioid flags, brand/generic split
- `int_geographic_benchmarks` — Per-capita spending, MA penetration context

**Mart** (API-ready):
- `mart_provider__practice_profile` — Updated with Part B + Part D summary columns
- `mart_national__kpi_summary` — 1 row per year, national aggregates
- `mart_geographic__spending_variation` — State-level spending with benchmarks
- `mart_geographic__by_state` — State summary with provider counts
- `mart_opioid__by_state` — State opioid prescribing metrics
- `mart_opioid__top_prescribers` — High-volume opioid prescribers

### Parquet Export
- `scripts/export_marts_to_parquet.py` — Export mart tables to Parquet for DuckDB

### Prefect Flows
- `flows/partb_flow.py`, `flows/partd_flow.py`, `flows/geovar_flow.py`
- `flows/utilization_flow.py` — Orchestration: pipelines → dbt run → parquet export

## Success Criteria
- Part B pipeline handles 10M+ rows with derived totals
- Part D pipeline flags opioid prescribers
- `mart_provider__practice_profile` has Part B + Part D columns per NPI
- `mart_national__kpi_summary` produces 1 row per year
- All dbt tests pass
- Parquet export works for DuckDB queries
- All pytest tests pass
