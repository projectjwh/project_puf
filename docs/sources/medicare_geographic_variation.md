# Data Source: Medicare Geographic Variation — by National, State, and County

## Overview
- **Publisher**: Centers for Medicare & Medicaid Services (CMS)
- **Program**: Medicare (Parts A, B, and D; FFS and MA)
- **URL**: https://data.cms.gov/summary-statistics-on-beneficiary-use-of-health-services/medicare-geographic-variation/ (NEEDS VERIFICATION)
- **Update Frequency**: Annual (typically released 1.5–2 years after the data year)
- **Current Coverage**: 2007–2022 (latest year NEEDS VERIFICATION)
- **Access Level**: Public Use File
- **File Format**: CSV download; CMS Data API
- **Approximate Size**: National file is small (~1 row per year); State file ~50 rows per year; County file ~3,200 rows per year. Total dataset is compact — well under 100 MB across all files and years.

## Purpose & Policy Context

The Medicare Geographic Variation PUF is the modern descendant of a research tradition pioneered by John Wennberg and the Dartmouth Atlas of Health Care, which since the 1990s has documented dramatic, unexplained geographic variation in Medicare spending and utilization. CMS created this official dataset to make geographic variation analysis accessible without requiring researchers to process raw claims data themselves.

The data answers the question: how do Medicare spending, utilization, and beneficiary characteristics differ across geographic units (nation, state, county)? It aggregates claims and enrollment data to produce per-beneficiary standardized spending, service utilization rates (hospitalizations, ER visits, procedures, imaging), and beneficiary demographic/health status profiles for each geographic area. This enables researchers and policymakers to ask whether variation is driven by differences in health needs, practice patterns, prices, or insurance coverage.

In the transparency ecosystem, this dataset provides essential contextual denominator data. While provider-level datasets (Part B, Inpatient, Part D) show what individual providers bill, the Geographic Variation data shows what the broader population in an area consumes. This context is critical for interpreting provider-level data — a provider in a high-utilization area may simply reflect local norms. The dataset directly supports the policy debate over geographic payment adjustments, accountable care organizations (ACOs), and value-based care models. Key legislation: The ACA (created ACOs, which target geographic variation), MACRA 2015 (payment reform), and ongoing Congressional debates about Medicare geographic payment fairness.

## Contents

| Column Group | Description | Key Fields |
|---|---|---|
| Geography | Area identification | `State` / `State_FIPS`, `County` / `County_FIPS`, `BENE_GEO_LVL` (National/State/County) |
| Beneficiary Demographics | Population characteristics | `Benes_FFS_Cnt`, `Benes_MA_Cnt`, `Benes_Dual_Cnt`, `Benes_Age_LT65_Cnt`, `Benes_Age_65_74_Cnt`, `Benes_Age_75_84_Cnt`, `Benes_Age_GT84_Cnt` |
| Health Status | Risk and chronic conditions | `Benes_Avg_HCC_Scr` (average HCC risk score), `Benes_FFS_Pct_*` (percent with various chronic conditions) |
| Spending - Total | Aggregate per-capita spending | `Tot_Mdcr_Stdzd_Pymt_PC`, `Tot_Mdcr_Pymt_PC` (per capita actual and standardized payments) |
| Spending - By Service | Service category spending | `IP_Mdcr_Pymt_PC` (inpatient), `PAC_Mdcr_Pymt_PC` (post-acute), `Phys_Mdcr_Pymt_PC` (physician), `OP_Mdcr_Pymt_PC` (outpatient), `HH_Mdcr_Pymt_PC` (home health), `Hospice_Mdcr_Pymt_PC`, `DME_Mdcr_Pymt_PC`, `PartD_Mdcr_Pymt_PC` |
| Utilization | Service use rates | `IP_Cvrd_Days_Per_1000`, `IP_Cvrd_Stays_Per_1000`, `ER_Visits_Per_1000`, `Phys_Events_Per_1000`, etc. |
| Quality Proxies | Crude outcome indicators | `Acute_Hosp_Readmsn_Pct` (readmission rate), `ER_Visits_Per_1000` (as access/quality proxy) |

## Key Identifiers

| Identifier | Type | Links To |
|---|---|---|
| `State_FIPS` | 2-digit FIPS state code | All CMS datasets with state FIPS, Census/ACS data |
| `County_FIPS` | 5-digit FIPS county code | Census data, AHRF, Dartmouth Atlas, all county-level health data |
| `BENE_GEO_LVL` | Geography level indicator | Internal use — distinguishes national, state, county rows |

## Relationships

| Related Source | Join Key | Relationship Type |
|---|---|---|
| Medicare Part B Utilization | `State_FIPS` = `Rndrng_Prvdr_State_FIPS` (aggregated) | Contextual — provides population context for provider-level data |
| Medicare Part D Prescribers | `State_FIPS` = `Prscrbr_State_FIPS` (aggregated) | Contextual — population drug spending context |
| Medicare Inpatient Hospitals | `State_FIPS` = `Rndrng_Prvdr_State_FIPS` (aggregated) | Contextual — population hospitalization context |
| Hospital Compare / Care Compare | State / County | Contextual — regional quality context |
| Medicare Spending Per Beneficiary | National / state level | Contextual — episode-level vs. population-level spending |
| Census / ACS Data | `County_FIPS` | Contextual — socioeconomic and demographic context |
| Area Health Resources File (AHRF) | `County_FIPS` | Contextual — provider supply, hospital beds, health resources per county |
| Dartmouth Atlas | HRR/HSA crosswalks via county | Contextual — historical geographic variation research |
| Medicare Advantage Enrollment | `State_FIPS` / `County_FIPS` | Direct — MA penetration rates affect FFS utilization |

## Data Quality Notes

- **FFS vs. MA split**: The dataset reports FFS and MA beneficiary counts separately. Most utilization and spending measures apply only to FFS beneficiaries because CMS does not receive encounter-level claims from MA plans (historically). As MA enrollment has grown past 50% of Medicare, FFS-only measures become less representative of the total Medicare population.
- **Standardized vs. actual spending**: Standardized spending (`_Stdzd_`) removes geographic price adjustments, isolating utilization differences. Actual spending (`_Pymt_`) reflects real dollars flowing. Both are useful for different questions.
- **County assignment**: Beneficiaries are assigned to counties based on their mailing address in CMS enrollment records, not where they receive care. Cross-border care seeking is not reflected.
- **Small county suppression**: Counties with very few beneficiaries may have data suppressed or may show highly volatile rates.
- **HCC risk scores**: The average Hierarchical Condition Category (HCC) risk score is a critical confounder. High-spending areas may simply have sicker populations. Always account for risk scores when comparing areas.
- **Excludes**: Beneficiaries enrolled in Medicare for less than a full year (in some calculations), beneficiaries without Part A and Part B, and ESRD-only beneficiaries may be handled differently across years.
- **No sub-county geography**: The most granular level is county. ZIP-code or census tract level data is not available in this PUF.

## Use Cases

1. **Geographic variation research**: Replicate and extend Dartmouth Atlas-style analyses using official CMS data at national, state, and county levels.
2. **Population health context**: Use as denominator data when analyzing provider-level datasets — understand the population a provider serves.
3. **MA penetration impact**: Study how Medicare Advantage market share in a county correlates with FFS utilization and spending patterns.
4. **Chronic disease burden mapping**: Map prevalence of chronic conditions (diabetes, heart failure, COPD) across counties.
5. **Policy targeting**: Identify high-cost, high-utilization areas for ACO development, value-based care interventions, or fraud investigation.
6. **Health equity analysis**: Compare spending and utilization across counties with different racial, income, and rural/urban compositions (when joined with Census data).

## Regulatory Notes

- **Privacy protections**: All data is aggregated to the county level or higher. No individual beneficiary data is included. Small cell sizes may be suppressed.
- **Terms of use**: Standard CMS PUF terms. No DUA required.
- **Methodological documentation**: CMS publishes detailed methodology documents explaining how each measure is calculated, including which claims types are included, how beneficiaries are attributed to geographies, and how standardization is performed. These documents are essential reading before using the data.
- **Citation**: "Centers for Medicare & Medicaid Services. Medicare Geographic Variation — by National, State, and County, [YEAR]."

## Verification Needed

- [ ] Confirm current URL on data.cms.gov
- [ ] Verify most recent data year available
- [ ] Check whether CMS has added sub-county geography (ZIP, ZCTA, HRR/HSA)
- [ ] Verify whether MA encounter data is now incorporated into any utilization measures
- [ ] Check for new measures (e.g., social determinants, telehealth utilization, COVID impact)
- [ ] Confirm whether the county-level file uses 5-digit FIPS or separate state/county FIPS fields
- [ ] Verify whether the HCC risk score version is documented (CMS-HCC V22 vs. V24 vs. V28)
- [ ] Check if CMS has added race/ethnicity breakdowns at the geographic level
