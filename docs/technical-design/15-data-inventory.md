# 15 — Data Inventory

[← Back to Index](index.md)

> Last updated: 2026-04-03

---

## Overview

48 public healthcare data sources across 9 domains, connected through 3 hub identifiers (NPI, CCN, FIPS). 53 dbt models transform raw data into 20 API-ready marts.

## Join Topology

```
                    NPI (Provider Hub — 8M)
                    /        |          \
              Part B     Part D      DME
            (10M/yr)   (25M/yr)   (500K/yr)
                |
            HCPCS ←→ RVU (complexity)
                |
            Procedure Marts

                    CCN (Facility Hub — 300K)
                    /     |      |      \
            Inpatient  Cost   Quality  Post-Acute
            (200K/yr) Reports (15K)  (SNF/HHA/Hospice)
                |
            DRG ←→ MS-DRG weights (case mix)

                    FIPS (Geographic Hub — 3.3K)
                    /        |           \
              GeoVar    MA Enrollment   Census
            (state/co)  (county/mo)    (county/yr)
                |
            ZIP ←→ County crosswalk (50K)
```

---

## Sources by Domain

### Provider Identity (4 sources)

| Source | Tier | Volume | Key | Fields |
|--------|------|--------|-----|--------|
| NPPES | 1 | 8M NPIs | NPI | Name, address, taxonomy (15 slots), credentials, gender, enumeration date, active status |
| POS | 1 | 300K facilities | CCN | Facility type, beds, ownership, emergency services, certification |
| PECOS | 2 | 2M | NPI | Enrollment, chain/ownership relationships |
| Ordering/Referring | 2 | 1.5M | NPI | Physician ordering/referring eligibility |

### Utilization (6 sources)

| Source | Tier | Volume/yr | Grain | Fields |
|--------|------|-----------|-------|--------|
| Part B | 1 | 10M | NPI×HCPCS×POS×year | Services, beneficiaries, avg/total charges, avg/total payments (standardized) |
| Part D | 1 | 25M | NPI×drug×year | Claims, drug cost, day supply, opioid flags, brand/generic, beneficiaries |
| GeoVar | 1 | 3.3K | state/county×year | Per-capita spending (8 service types), utilization rates, MA penetration, HCC risk |
| Inpatient | 2 | 200K | CCN×DRG×year | Discharges, charges, payments by DRG |
| SNF/HHA/Hospice | 2 | 30K combined | CCN×year | Post-acute utilization by facility |
| DME | 2 | 500K | NPI×HCPCS×year | DME supplier utilization, referring/supplying NPI |

### Code Systems (8 sources)

| Source | Tier | Volume | Key | Fields |
|--------|------|--------|-----|--------|
| ICD-10-CM | 1 | 72K codes | icd10_cm_code | Diagnosis codes, descriptions, chapters, billable status |
| ICD-10-PCS | 1 | 78K codes | icd10_pcs_code | Procedure codes, descriptions, sections, body systems |
| HCPCS | 1 | 7.5K codes | hcpcs_code | Procedure codes, descriptions, drug indicators |
| MS-DRG | 1 | 800 codes | drg_code | DRG descriptions, relative weights, MDC, LOS |
| NDC | 1 | 300K codes | ndc_code | Drug identifiers, brand/generic, dosage, DEA schedule, opioid flags |
| Taxonomy | 1 | 900 codes | taxonomy_code | Provider specialty classifications |
| POS Codes | 1 | 100 codes | pos_code | Service location codes |
| APC | 2 | 5K codes | apc_code | Outpatient procedure codes, payment indicators |

### Geographic (7 sources)

| Source | Tier | Volume | Key | Fields |
|--------|------|--------|-----|--------|
| FIPS | 1 | 3.3K | fips_code | State/county names, regions, divisions |
| ZIP-County | 1 | 50K | zip_code×county_fips | ZIP to county mapping, ratios |
| CBSA | 1 | 2K | cbsa_code | Metro/micro area codes |
| RUCA | 1 | 75K | zip_code | Rural-urban classification |
| HRR/HSA | 2 | 6.5K | zip_code | Hospital referral regions |
| Census | 2 | 3.3K | fips_code×year | County population estimates |
| GeoVar | 1 | (listed under Utilization) | | |

### Fee Schedules (6 sources)

| Source | Tier | Volume | Key | Fields |
|--------|------|--------|-----|--------|
| RVU | 1 | 16K | hcpcs_code×modifier | Work, practice expense, malpractice RVU |
| Wage Index | 1 | 4K | cbsa_code | Geographic wage adjustment |
| IPPS | 1 | 800 | drg_code×year | DRG base rates, payment multipliers |
| CLFS | 2 | 3K | hcpcs_code | Lab test payment rates |
| DMEPOS | 2 | 10K | hcpcs_code×state | DME payment rates |
| SNF PPS | 2 | 1K | pdpm_group×year | SNF payment group rates |

### Hospital/Financial (5 sources)

| Source | Tier | Volume/yr | Key | Fields |
|--------|------|-----------|-----|--------|
| Cost Reports (Hospital) | 1 | 6K | rpt_rec_num | Revenue, expenses, net income, beds, discharges, occupancy |
| Cost Reports (SNF) | 2 | 15K | rpt_rec_num | SNF financials |
| Cost Reports (HHA) | 2 | 10K | rpt_rec_num | HHA financials |
| Cost Reports (Hospice) | 2 | 5K | rpt_rec_num | Hospice financials |
| Hospital General | 2 | 5K | ccn | Hospital type, ownership, overall rating |

### Quality (5 sources, all Tier 2)

| Source | Tier | Volume | Key | Fields |
|--------|------|--------|-----|--------|
| Five-Star | 2 | 15K | ccn | Overall/health/staffing/quality ratings, penalties |
| PBJ Staffing | 2 | 5.5M/qtr | ccn×date | Daily RN/LPN/CNA hours |
| CAHPS | 2 | 4.5K | ccn×measure | Patient experience scores |
| Dialysis | 2 | 7.5K | ccn×measure | Dialysis quality measures |
| Readmissions | 2 | 3.5K | ccn×measure | Readmission rates, national comparison, penalties |

### Drug/Prescribing (3 sources, all Tier 2)

| Source | Tier | Volume | Key | Fields |
|--------|------|--------|-----|--------|
| SDUD (Medicaid) | 2 | 5M/qtr | state×ndc×quarter | Prescriptions, reimbursement, units |
| RxNorm | 2 | 400K | rxcui | Drug name normalization |
| ASP Pricing | 2 | 800 | hcpcs_code×quarter | Part B drug payment limits |

### Medicare Advantage (2 sources, all Tier 2)

| Source | Tier | Volume | Key | Fields |
|--------|------|--------|-----|--------|
| MA Enrollment | 2 | 50K/mo | contract×plan×county | Enrollment counts, penetration |
| MA Benchmarks | 2 | 3.3K/yr | county_fips×year | FFS per capita, MA benchmark, quality bonuses |

---

## dbt Model Inventory (53 models)

### Snapshot (1)

| Model | Grain | Tracks |
|-------|-------|--------|
| `snp_provider_history` | NPI × validity period | taxonomy, practice_state, practice_zip5, is_active, entity_type |

### Staging (16)

1:1 schema contracts on pipeline-loaded tables: NPPES, POS, Part B, Part D, GeoVar, Inpatient, Cost Reports, Five-Star, Readmissions, CAHPS, Charges, SDUD (+ 4 ephemeral refs).

### Intermediate (16)

| Model | Grain | Sources Joined | Key Output |
|-------|-------|---------------|------------|
| `int_providers` | NPI | NPPES + Taxonomy + FIPS | specialty_classification, census_region |
| `int_provider_services` | NPI×year | Part B | total_services, total_payments, service_mix % |
| `int_provider_prescriptions` | NPI×year | Part D | total_claims, opioid_rate, is_high_opioid |
| `int_provider_quality` | CCN | Five-Star + Readmissions + POS | quality_tier, penalty_risk |
| `int_geographic_benchmarks` | state×year | GeoVar + FIPS + national | spending_index, ma_penetration_index |
| `int_hospital_financials` | CCN×year | Cost Reports + POS | operating_margin, cost_to_charge_ratio |
| `int_hospital_discharges` | CCN×year | Inpatient + DRG + POS | case_mix_index, avg_payment_per_discharge |
| `int_hospital_readmissions` | CCN | Readmissions + POS | avg_readmission_rate, has_penalty_risk |
| `int_nursing_home_quality` | CCN | Five-Star + Staffing | overall_rating, staffing_consistency |
| `int_nursing_home_staffing` | CCN×quarter | PBJ daily→quarterly | avg_daily_rn/lpn/cna_hours |
| `int_procedure_utilization` | HCPCS×year | Part B national | provider_count, pct_office, avg_payment |
| `int_procedure_by_specialty` | HCPCS×specialty×year | Part B + Providers | services_by_specialty |
| `int_drug_utilization_medicaid` | state×NDC×year | SDUD + FIPS | cost_per_prescription |
| `int_drug_pricing` | HCPCS×quarter×year | ASP | payment_limit |
| `int_ma_market` | county×year | MA Enrollment + Benchmarks | penetration_rate, benchmark_to_ffs |
| `int_patient_experience` | CCN | CAHPS + POS | nurse/doctor/staff scores |

### Marts (20)

| Domain | Model | Grain | Key Metrics |
|--------|-------|-------|-------------|
| Provider | `mart_provider__practice_profile` | NPI (latest) | Identity + Part B + Part D fused, SCD summary |
| Provider | `mart_provider__historical_profile` | NPI×period | Change detection, version history |
| Hospital | `mart_hospital__financial_profile` | CCN×year | Revenue, margin, occupancy |
| Hospital | `mart_hospital__performance` | CCN×year | Case mix, discharges, quality |
| Hospital | `mart_hospital__readmissions` | CCN×year | Readmission rates, penalty risk |
| Hospital | `mart_hospital__charge_variation` | CCN×DRG×year | Charge spread by DRG |
| Post-Acute | `mart_postacute__snf_quality` | CCN | Ratings + staffing |
| Post-Acute | `mart_postacute__hha_quality` | CCN | HHA quality metrics |
| Post-Acute | `mart_postacute__hospice_quality` | CCN | Hospice quality metrics |
| Geographic | `mart_geographic__spending_variation` | state×year | Spending indices, service breakdown |
| Geographic | `mart_geographic__by_state` | state×year | Beneficiaries, providers, utilization |
| Procedure | `mart_procedure__utilization_trends` | HCPCS×year | Volume, RVU complexity, YOY change |
| Procedure | `mart_procedure__price_variation` | HCPCS×state×year | Price spread (avg, p25, p75, CV) |
| Procedure | `mart_procedure__specialty_mix` | HCPCS×specialty×year | Services share %, payment share % |
| Opioid | `mart_opioid__by_state` | state×year | Opioid claims, prescriber rates |
| Opioid | `mart_opioid__top_prescribers` | NPI×year | Top opioid prescribers |
| Drug | `mart_drug__medicaid_utilization` | state×NDC×year | Medicaid drug spend |
| Drug | `mart_drug__price_trends` | HCPCS×quarter×year | ASP pricing trends |
| MA | `mart_ma__market_penetration` | county×year | Enrollment, penetration, benchmark |
| National | `mart_national__kpi_summary` | year | Macro KPIs |

---

## Analytical Questions the Data Answers

| Question | Data Sources | Mart |
|----------|-------------|------|
| "Who is this provider and what do they bill?" | NPPES + Part B | `mart_provider__practice_profile` |
| "Is this provider a high opioid prescriber?" | Part D | `mart_opioid__top_prescribers` |
| "How has this provider changed over time?" | NPPES SCD | `mart_provider__historical_profile` |
| "What's this hospital's financial health?" | Cost Reports + POS | `mart_hospital__financial_profile` |
| "Is this hospital at readmission penalty risk?" | Readmissions | `mart_hospital__readmissions` |
| "Which procedures have the most price variation?" | Part B | `mart_procedure__price_variation` |
| "Which specialties own which procedures?" | Part B + Taxonomy | `mart_procedure__specialty_mix` |
| "Which states spend the most per capita?" | GeoVar | `mart_geographic__spending_variation` |
| "What's the MA vs FFS split by county?" | MA Enrollment | `mart_ma__market_penetration` |
| "What does Medicaid spend on drugs by state?" | SDUD | `mart_drug__medicaid_utilization` |
| "What are the national Medicare KPIs this year?" | Multiple | `mart_national__kpi_summary` |
