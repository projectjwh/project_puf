# Data Source: Skilled Nursing Facility (SNF) Utilization

## Overview
- **Publisher**: Centers for Medicare & Medicaid Services (CMS)
- **Program**: Medicare Part A (SNF Benefit)
- **URL**: https://data.cms.gov/provider-summary-by-type-of-service/medicare-skilled-nursing-facilities/ (NEEDS VERIFICATION)
- **Update Frequency**: Annual (typically released 1.5–2 years after the service year)
- **Current Coverage**: 2013–2022 (latest year NEEDS VERIFICATION)
- **Access Level**: Public Use File
- **File Format**: CSV download; CMS Data API
- **Approximate Size**: ~15,000–16,000 rows per year in facility-level summary (one row per SNF); ~50–150 MB

## Purpose & Policy Context

The Skilled Nursing Facility (SNF) PUF was released as part of the ACA-driven CMS transparency initiative. SNFs provide short-term, post-acute rehabilitation and skilled nursing care to Medicare beneficiaries, typically following a qualifying inpatient hospital stay of at least 3 consecutive days (the "3-day rule," though this was waived for some ACO models). Medicare Part A covers up to 100 days of SNF care per benefit period: full coverage for the first 20 days, with a daily coinsurance for days 21–100.

This data answers questions about how many beneficiaries each SNF serves, how long they stay, what Medicare pays, and how utilization patterns vary across facilities and geography. SNF care is one of Medicare's largest spending categories — approximately $28–30 billion annually — and has been a target of both payment reform and quality improvement efforts.

The SNF payment system underwent a major reform with the Patient-Driven Payment Model (PDPM), implemented October 1, 2019. PDPM replaced the Resource Utilization Group (RUG-IV) system, which had been criticized for incentivizing therapy provision regardless of patient need. PDPM classifies patients based on clinical characteristics and pays separate per-diem rates for five components: physical therapy, occupational therapy, speech-language pathology, nursing, and non-therapy ancillaries. This is a significant schema break in the data, similar to the PDGM transition in home health. Key legislation: BBA 1997 (SNF PPS establishment), ACA 2010 (transparency, VBP for SNFs), Bipartisan Budget Act of 2018 (PDPM mandate), IMPACT Act of 2014 (standardized patient assessment data), the Protecting Access to Medicare Act of 2014 (Pama, SNF payment provisions).

## Contents

| Column Group | Description | Key Fields |
|---|---|---|
| Facility Identity | SNF identification | `Rndrng_Prvdr_CCN`, `Rndrng_Prvdr_Org_Name`, `Rndrng_Prvdr_St`, `Rndrng_Prvdr_City`, `Rndrng_Prvdr_State_Abrvtn`, `Rndrng_Prvdr_State_FIPS`, `Rndrng_Prvdr_Zip5` |
| Facility Characteristics | SNF attributes | `Rndrng_Prvdr_RUCA`, `Rndrng_Prvdr_Type` |
| Beneficiary Counts | Volume | `Tot_Benes` (total distinct beneficiaries), `Tot_Stays` (total SNF stays) |
| Utilization | Length of stay | `Tot_Cvrd_Days` (total covered days), `Avg_Cvrd_Days_Per_Stay` (average covered days per stay) |
| Payment | Dollar amounts | `Tot_Mdcr_Pymt_Amt`, `Avg_Mdcr_Pymt_Per_Day`, `Avg_Mdcr_Pymt_Per_Stay`, `Tot_Mdcr_Stdzd_Pymt_Amt` |
| Charges | Billed amounts | `Tot_Sbmtd_Chrg_Amt`, `Avg_Sbmtd_Chrg_Per_Day` |

## Key Identifiers

| Identifier | Type | Links To |
|---|---|---|
| `Rndrng_Prvdr_CCN` | CMS Certification Number (6-digit, typically [state code] + facility type indicator) | Nursing Home Compare (Care Compare), Provider of Services, Medicare Cost Reports (SNF), Minimum Data Set (MDS) quality measures |
| `Rndrng_Prvdr_State_FIPS` | FIPS State Code | Geographic Variation data, Census data |
| `Rndrng_Prvdr_Zip5` | 5-digit ZIP code | Geographic crosswalks |

## Relationships

| Related Source | Join Key | Relationship Type |
|---|---|---|
| Nursing Home Compare / Care Compare (Nursing Home section) | `Rndrng_Prvdr_CCN` = `Federal_Provider_Number` | Direct — quality ratings (5-star), staffing data, inspection results, quality measures |
| Medicare Inpatient Hospitals | Indirect (SNF stays follow qualifying hospital stays) | Hierarchical — SNFs are downstream of hospitals in the post-acute pathway |
| Medicare Spending Per Beneficiary | Indirect (SNF costs are a major component of MSPB) | Contextual — SNF spending contributes significantly to episode-based spending |
| Medicare Geographic Variation | `Rndrng_Prvdr_State_FIPS` = state/county FIPS | Contextual — `PAC_Mdcr_Pymt_PC` includes SNF spending in population-level context |
| HHA Utilization | Indirect (home health may follow SNF discharge) | Contextual — alternative/sequential post-acute pathways |
| Hospice Utilization | Indirect (some hospice patients reside in SNFs) | Contextual — hospice overlay on SNF care |
| Provider of Services (POS) | `Rndrng_Prvdr_CCN` = `PRVDR_NUM` | Direct — ownership, bed count, certification date, dual SNF/NF status |
| Medicare Cost Reports (SNF) | `Rndrng_Prvdr_CCN` = `Provider_CCN` | Direct — financial data, staffing, cost structure |
| Minimum Data Set (MDS) quality data | `Rndrng_Prvdr_CCN` | Direct — resident assessment data feeds quality measures |

## Data Quality Notes

- **PDPM transition (October 2019)**: The shift from RUG-IV to PDPM changed the unit of payment and classification methodology. FY2020 data spans the transition (Q1 under RUG-IV, Q2–Q4 under PDPM). Longitudinal analysis across this boundary requires careful handling.
- **SNF vs. nursing facility distinction**: Many facilities are dually certified as both SNFs (Medicare) and nursing facilities (NF, Medicaid). The PUF covers only the Medicare SNF portion. The same physical facility may also have Medicaid-covered long-term care residents not reflected in this data.
- **3-day qualifying stay**: Medicare SNF coverage traditionally requires a preceding 3-day inpatient hospital stay. Some waiver programs (e.g., certain ACO models) have eliminated this requirement, which may affect utilization patterns in some areas.
- **100-day benefit limit**: Medicare covers up to 100 days per benefit period. Average length of stay (~25–30 days) is well below this maximum, but the distribution is skewed — many stays are short (rehabilitation after joint replacement) while some approach the maximum.
- **Suppression**: Standard CMS cell suppression (11-beneficiary minimum).
- **CCN-based identification**: Like other institutional providers, SNFs are identified by CCN, not NPI. NPI crosswalk needed for joining to provider-level datasets.
- **Excludes**: Medicare Advantage SNF stays (processed by MA plans), Medicaid-only nursing facility stays, swing bed hospital stays (small hospitals that can furnish SNF-level care using their inpatient beds), and non-Medicare-certified nursing homes.
- **COVID-19 impact**: SNFs were severely affected by COVID-19. Utilization dropped significantly in 2020 due to admission moratoriums, and mortality was extremely high. 2020–2021 data reflects pandemic conditions, not normal operations.

## Use Cases

1. **Post-acute care analysis**: Study SNF utilization as part of the post-acute care pathway, including length of stay, payment, and geographic variation.
2. **Quality-cost correlation**: Join with Nursing Home Compare star ratings to study whether higher-quality SNFs have different utilization or cost profiles.
3. **PDPM impact evaluation**: Compare pre-PDPM and post-PDPM utilization and payment patterns to assess the impact of the payment model change.
4. **Market analysis**: Map SNF capacity, occupancy patterns, and market concentration by geography.
5. **Referral pattern analysis**: Study which hospitals refer to which SNFs (requires additional data linkage, but utilization data provides the SNF side).
6. **Length of stay management**: Identify facilities with unusually long or short stays relative to peers, controlling for case mix.
7. **COVID-19 impact assessment**: Quantify the pandemic's effect on SNF utilization, payment, and the post-acute care market.

## Regulatory Notes

- **Conditions of Participation**: SNFs must meet Medicare Conditions of Participation (CoPs) including staffing, care planning, resident rights, and physical environment standards. Compliance is monitored through state surveys.
- **SNF Value-Based Purchasing (VBP)**: Established by the Protecting Access to Medicare Act of 2014 (PAMA), the SNF VBP Program adjusts payments based on hospital readmission rates from SNFs. This creates financial incentives for SNFs to reduce avoidable readmissions.
- **5-Star Quality Rating System**: CMS publishes a composite quality rating for nursing homes based on health inspections, staffing, and quality measures. This is available through Nursing Home Compare / Care Compare and is joinable to the utilization data.
- **Minimum Data Set (MDS)**: SNFs must complete the MDS patient assessment instrument for all residents. MDS data feeds into quality measures and PDPM patient classification. The MDS itself is not a PUF but its derived measures are publicly available.
- **Privacy protections**: Standard CMS cell suppression. Facility-level aggregate data only.
- **Terms of use**: Standard CMS PUF terms. No DUA required.
- **Citation**: "Centers for Medicare & Medicaid Services. Medicare Skilled Nursing Facility Utilization, [YEAR]."

## Verification Needed

- [ ] Confirm current URL on data.cms.gov
- [ ] Verify most recent data year available
- [ ] Check whether PDPM transition has changed the file structure or field definitions
- [ ] Verify whether CMS has added case-mix or PDPM classification data to the PUF
- [ ] Confirm column naming conventions match other institutional provider PUFs
- [ ] Check if CMS has added COVID-19-specific fields or adjustments
- [ ] Verify whether the 3-day qualifying stay waiver has been permanently adopted and its data impact
- [ ] Check if SNF VBP scores are linked or included in the utilization PUF
- [ ] Confirm suppression thresholds
- [ ] Verify whether swing bed stays are reported in a separate dataset or included
