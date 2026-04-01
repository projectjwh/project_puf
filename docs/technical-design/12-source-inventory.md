# 12. Source Inventory

[← Back to Index](index.md) | [← Operations](11-operations.md)

---

## Complete Source Registry (48 Sources, 11 Categories)

Source: `config/sources.yaml`

---

### Provider Identity (4 Sources)

| Source | Short Name | Publisher | Format | Frequency | Volume | Primary Key | Tier |
|--------|-----------|-----------|--------|-----------|--------|-------------|------|
| National Plan & Provider Enumeration System | `nppes` | CMS | csv_zip | Monthly | 8M | NPI | 1 |
| Provider of Services - Current Files | `pos` | CMS | csv | Quarterly | 300K | PRVDR_NUM | 1 |
| Provider Enrollment (PECOS) | `pecos` | CMS | csv | Monthly | 2M | NPI | 2 |
| Ordering and Referring Physicians | `ordering_referring` | CMS | csv | Quarterly | 1.5M | NPI | 2 |

### Code Systems (8 Sources)

| Source | Short Name | Publisher | Format | Frequency | Volume | Primary Key | Tier |
|--------|-----------|-----------|--------|-----------|--------|-------------|------|
| ICD-10-CM Diagnosis Codes | `icd10cm` | CMS | zip_txt | Annual | 72K | icd10_cm_code | 1 |
| ICD-10-PCS Procedure Codes | `icd10pcs` | CMS | zip_txt | Annual | 78K | icd10_pcs_code | 1 |
| HCPCS Level II Codes | `hcpcs` | CMS | zip_txt | Quarterly | 7.5K | hcpcs_code | 1 |
| MS-DRG Grouper | `msdrg` | CMS | zip_xlsx | Annual | 800 | drg_code | 1 |
| National Drug Code Directory | `ndc` | FDA | zip_txt | Weekly | 300K | ndc_code | 1 |
| NUCC Healthcare Provider Taxonomy | `taxonomy` | NUCC | csv | Biannual | 900 | taxonomy_code | 1 |
| Place of Service Codes | `pos_codes` | CMS | csv | Annual | 100 | pos_code | 1 |
| Ambulatory Payment Classification | `apc` | CMS | xlsx | Annual | 5K | apc_code | 2 |

### Geographic (7 Sources)

| Source | Short Name | Publisher | Format | Frequency | Volume | Primary Key | Tier |
|--------|-----------|-----------|--------|-----------|--------|-------------|------|
| FIPS State and County Codes | `fips` | Census | csv | Decennial | 3.3K | fips_code | 1 |
| ZIP-County Crosswalk | `zip_county` | HUD | xlsx | Quarterly | 50K | zip_code, county_fips | 1 |
| Core-Based Statistical Areas | `cbsa` | Census | xlsx | Annual | 2K | cbsa_code | 1 |
| Rural-Urban Commuting Area Codes | `ruca` | USDA | xlsx | Decennial | 75K | zip_code | 1 |
| Hospital Referral Regions / HSAs | `hrr_hsa` | Dartmouth | csv | Static | 6.5K | zip_code | 2 |
| Census Population Estimates | `census` | Census | csv | Annual | 3.3K | fips_code, year | 2 |
| Medicare Geographic Variation | `geovar` | CMS | csv | Annual | 3.3K | bene_geo_lvl, state_fips, county_fips | 1 |

### Utilization (6 Sources)

| Source | Short Name | Publisher | Format | Frequency | Volume | Primary Key | Tier |
|--------|-----------|-----------|--------|-----------|--------|-------------|------|
| Medicare Part B Physician/Supplier | `partb` | CMS | csv | Annual | 10M | NPI, HCPCS, POS, year | 1 |
| Medicare Part D Prescribers | `partd` | CMS | csv | Annual | 25M | NPI, brand, generic, year | 1 |
| Medicare Inpatient Hospitals | `inpatient` | CMS | csv | Annual | 200K | CCN, DRG, year | 2 |
| Skilled Nursing Facility Utilization | `snf` | CMS | csv | Annual | 15K | CCN, year | 2 |
| Home Health Agency Utilization | `hha` | CMS | csv | Annual | 10K | CCN, year | 2 |
| Hospice Utilization | `hospice` | CMS | csv | Annual | 5K | CCN, year | 2 |

### Fee Schedules (6 Sources)

| Source | Short Name | Publisher | Format | Frequency | Volume | Primary Key | Tier |
|--------|-----------|-----------|--------|-----------|--------|-------------|------|
| Physician Fee Schedule - RVUs | `rvu` | CMS | zip_csv | Annual | 16K | hcpcs_code, modifier | 1 |
| Hospital Wage Index | `wage_index` | CMS | xlsx | Annual | 4K | cbsa_code | 1 |
| IPPS Rates | `ipps` | CMS | xlsx | Annual | 800 | drg_code, fiscal_year | 1 |
| Clinical Laboratory Fee Schedule | `clfs` | CMS | zip_csv | Annual | 3K | hcpcs_code | 2 |
| DMEPOS Fee Schedule | `dmepos_fees` | CMS | zip_csv | Quarterly | 10K | hcpcs_code, modifier, state | 2 |
| SNF PPS | `snf_pps` | CMS | xlsx | Annual | 1K | pdpm_group, fiscal_year | 2 |

### Drug / Prescribing (3 Sources)

| Source | Short Name | Publisher | Format | Frequency | Volume | Primary Key | Tier |
|--------|-----------|-----------|--------|-----------|--------|-------------|------|
| State Drug Utilization Data (Medicaid) | `sdud` | CMS | csv | Quarterly | 5M/qtr | NDC, state, year, quarter | 2 |
| RxNorm Drug Names and Codes | `rxnorm` | NLM | zip_rrf | Monthly | 400K | rxcui | 2 |
| Average Sales Price Drug Pricing | `asp` | CMS | xlsx | Quarterly | 800 | hcpcs_code, quarter, year | 2 |

### Quality (5 Sources)

| Source | Short Name | Publisher | Format | Frequency | Volume | Primary Key | Tier |
|--------|-----------|-----------|--------|-----------|--------|-------------|------|
| Nursing Home Five-Star Rating | `five_star` | CMS | csv | Monthly | 15K | CCN | 2 |
| Payroll-Based Journal Staffing | `pbj` | CMS | csv | Quarterly | 5.5M | CCN, work_date | 2 |
| CAHPS Hospital Patient Experience | `cahps` | CMS | csv | Annual | 4.5K | CCN, measure_id | 2 |
| Dialysis Facility Quality | `dialysis` | CMS | csv | Annual | 7.5K | CCN, measure_id | 2 |
| Hospital Readmissions Reduction | `readmissions` | CMS | csv | Annual | 3.5K | CCN, measure_id | 2 |

### Hospital / Financial (5 Sources)

| Source | Short Name | Publisher | Format | Frequency | Volume | Primary Key | Tier |
|--------|-----------|-----------|--------|-----------|--------|-------------|------|
| Hospital Cost Reports (HCRIS) | `cost_reports` | CMS | csv_zip | Quarterly | 6K/yr | rpt_rec_num | 1 |
| SNF Cost Reports | `cost_reports_snf` | CMS | csv_zip | Quarterly | 15K | rpt_rec_num | 2 |
| HHA Cost Reports | `cost_reports_hha` | CMS | csv_zip | Quarterly | 10K | rpt_rec_num | 2 |
| Hospice Cost Reports | `cost_reports_hospice` | CMS | csv_zip | Quarterly | 5K | rpt_rec_num | 2 |
| Hospital General Information | `hospital_general` | CMS | csv | Quarterly | 5K | CCN | 2 |

### Charges (1 Source)

| Source | Short Name | Publisher | Format | Frequency | Volume | Primary Key | Tier |
|--------|-----------|-----------|--------|-----------|--------|-------------|------|
| Inpatient Hospital Charge Data | `charges` | CMS | csv | Annual | 200K | CCN, DRG, year | 2 |

### DME (1 Source)

| Source | Short Name | Publisher | Format | Frequency | Volume | Primary Key | Tier |
|--------|-----------|-----------|--------|-----------|--------|-------------|------|
| DME Supplier Utilization | `dme` | CMS | csv | Annual | 500K | referring_npi, supplier_npi, hcpcs_code, year | 2 |

### Medicare Advantage (2 Sources)

| Source | Short Name | Publisher | Format | Frequency | Volume | Primary Key | Tier |
|--------|-----------|-----------|--------|-----------|--------|-------------|------|
| MA Enrollment by County | `ma_enrollment` | CMS | csv | Monthly | 50K/mo | contract_id, plan_id, county_fips, year_month | 2 |
| MA County Rate Books / Benchmarks | `ma_benchmarks` | CMS | xlsx | Annual | 3.3K | county_fips, year | 2 |

---

**Next:** [Appendices →](appendices.md)
