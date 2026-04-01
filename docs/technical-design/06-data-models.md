# 6. Data Model Layers

[← Back to Index](index.md) | [← Pipelines](05-pipelines.md)

---

## dbt DAG

Full diagram: [`diagrams/dbt-dag.d2`](diagrams/dbt-dag.d2)

```d2
direction: right

staging: "Staging\n(11 models)" {style.fill: "#f8fafc"}
intermediate: "Intermediate\n(13 models)" {style.fill: "#f0f9ff"}
mart: "Mart\n(16 models)" {style.fill: "#fefce8"}

staging -> intermediate: "joins + aggregation"
intermediate -> mart: "shaping + indexing"
```

---

## Layer Architecture

| Layer | Materialization | Value-Add |
|-------|----------------|-----------|
| Staging | View / Ephemeral | Type-safe schema contracts, column renaming, deduplication |
| Intermediate | Table | Cross-source joins, aggregation from line-item to entity-level, computed metrics |
| Mart | Table + Indexes | Pre-shaped for API response, indexed for <10ms lookups, no joins needed at query time |

---

## Staging Layer (11 Models)

Source: `models/staging/cms/`

| Model | Grain | Source | Materialization |
|-------|-------|--------|----------------|
| `stg_cms__nppes` | NPI | NPPES provider file | View |
| `stg_cms__pos_facilities` | CCN | Provider of Services | View |
| `stg_cms__part_b_utilization` | NPI × HCPCS × POS × year | Part B utilization | Ephemeral |
| `stg_cms__part_d_prescribers` | NPI × drug × year | Part D prescribers | Ephemeral |
| `stg_cms__geographic_variation` | geo_level × FIPS × year | Geographic Variation PUF | Ephemeral |
| `stg_cms__inpatient` | CCN × DRG × year | Inpatient utilization | Ephemeral |
| `stg_cms__five_star` | CCN | Nursing Home Five-Star | Ephemeral |
| `stg_cms__readmissions` | CCN × measure_id | Hospital readmissions | Ephemeral |
| `stg_cms__cahps` | CCN × measure_id | CAHPS patient experience | Ephemeral |
| `stg_cms__sdud` | state × NDC × year × quarter | State Drug Utilization | Ephemeral |
| `stg_cms__charges` | CCN × DRG × year | Inpatient charges | Ephemeral |

---

## Intermediate Layer (13 Models)

Source: `models/intermediate/`

| Model | Grain | Sources Joined | Value-Add |
|-------|-------|---------------|-----------|
| `int_providers` | NPI | NPPES + taxonomy + FIPS | Provider identity with specialty descriptions and geographic context |
| `int_provider_services` | NPI × year | Part B (line-item → provider) | Provider-level service aggregation from TOTALS, service mix categorization |
| `int_provider_prescriptions` | NPI × year | Part D (drug → provider) | Opioid metrics, brand/generic split, cost-per-claim |
| `int_geographic_benchmarks` | state_fips × year | GeoVar + states | State spending indices (state / national ratio), MA penetration |
| `int_hospital_discharges` | CCN × year | Inpatient + DRG weights | Case mix index (CMI), DRG-weighted revenue |
| `int_hospital_readmissions` | CCN | Readmissions measures | Excess readmission ratio, penalty estimation |
| `int_hospital_financials` | CCN × year | Cost reports + POS | Operating margin, cost-to-charge ratio, occupancy rate |
| `int_nursing_home_staffing` | CCN × quarter | PBJ daily → quarterly | Daily staffing hours → quarterly averages, RN ratio |
| `int_nursing_home_quality` | CCN | Five-Star + staffing | Combined quality ratings + actual staffing data |
| `int_drug_utilization_medicaid` | state × NDC × year | SDUD quarterly → annual | Annual aggregation, suppression filtering, unit cost |
| `int_drug_pricing` | HCPCS × quarter × year | ASP + NDC crosswalk | ASP linked to NDC via RxNorm for cross-dataset analysis |
| `int_patient_experience` | CCN | CAHPS long → wide | Pivoted measures for hospital comparison |
| `int_ma_market` | county_fips × year | MA enrollment monthly → annual | Annual enrollment averages, penetration rates |

---

## Mart Layer (16 Models)

Source: `models/marts/`

### Provider Marts (`marts/provider/`)

| Model | Grain | Indexes | API Endpoint |
|-------|-------|---------|-------------|
| `mart_provider__practice_profile` | NPI | NPI (unique), state, taxonomy | `GET /api/v1/providers/{npi}`, `GET /api/v1/providers/` |

### National Marts (`marts/national/`)

| Model | Grain | Indexes | API Endpoint |
|-------|-------|---------|-------------|
| `mart_national__kpi_summary` | data_year | year | `GET /api/v1/national/kpis` |

### Geographic Marts (`marts/geographic/`)

| Model | Grain | Indexes | API Endpoint |
|-------|-------|---------|-------------|
| `mart_geographic__spending_variation` | state_fips × year | (state, year), year, region | `GET /api/v1/geographic/spending` |
| `mart_geographic__by_state` | state_fips × year | (state, year), abbreviation | `GET /api/v1/geographic/states` |

### Opioid Marts (`marts/opioid/`)

| Model | Grain | Indexes | API Endpoint |
|-------|-------|---------|-------------|
| `mart_opioid__by_state` | state_fips × year | (state, year) | `GET /api/v1/opioid/by-state` |
| `mart_opioid__top_prescribers` | NPI × year | (year, state), NPI | `GET /api/v1/opioid/top-prescribers` |

### Hospital Marts (`marts/hospital/`)

| Model | Grain | Indexes | API Endpoint |
|-------|-------|---------|-------------|
| `mart_hospital__financial_profile` | CCN × year | (CCN, year), state | `GET /api/v1/hospitals/financial` |
| `mart_hospital__performance` | CCN × year | (CCN, year), state | `GET /api/v1/hospitals/performance` |
| `mart_hospital__readmissions` | CCN × year | (CCN, year), state | `GET /api/v1/hospitals/readmissions` |
| `mart_hospital__charge_variation` | CCN × DRG × year | (CCN, year), DRG | `GET /api/v1/hospitals/charges` |

### Drug Marts (`marts/drug/`)

| Model | Grain | Indexes | API Endpoint |
|-------|-------|---------|-------------|
| `mart_drug__medicaid_utilization` | state × year | (state, year) | `GET /api/v1/drugs/medicaid-utilization` |
| `mart_drug__price_trends` | HCPCS × quarter × year | HCPCS, (quarter, year) | `GET /api/v1/drugs/price-trends` |

### Post-Acute Marts (`marts/postacute/`)

| Model | Grain | Indexes | API Endpoint |
|-------|-------|---------|-------------|
| `mart_postacute__snf_quality` | CCN | CCN, state | `GET /api/v1/postacute/snf` |
| `mart_postacute__hha_quality` | CCN × year | (CCN, year), state | `GET /api/v1/postacute/hha` |
| `mart_postacute__hospice_quality` | CCN × year | (CCN, year), state | `GET /api/v1/postacute/hospice` |

### Medicare Advantage Marts (`marts/ma/`)

| Model | Grain | Indexes | API Endpoint |
|-------|-------|---------|-------------|
| `mart_ma__market_penetration` | county_fips × year | (county, year) | — (future) |

---

## dbt Configuration

Source: `models/dbt_project.yml`

| Setting | Value |
|---------|-------|
| Profile | `project_puf` |
| Staging materialization | View (default) |
| Intermediate materialization | Table |
| Mart materialization | Table |
| Default `min_data_year` | 2020 |
| Default `max_data_year` | 2022 |

Tag hierarchy: `cms`, `staging`, `intermediate`, `mart`, `provider`, `geographic`, `national`, `opioid`, `hospital`, `drug`, `postacute`, `medicare_advantage`, `quality`, `reference`

---

**Next:** [Cross-Source Joins →](07-cross-source-joins.md)
