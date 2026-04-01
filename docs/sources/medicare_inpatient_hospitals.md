# Data Source: Medicare Inpatient Hospitals — by Provider and Service

## Overview
- **Publisher**: Centers for Medicare & Medicaid Services (CMS)
- **Program**: Medicare Part A (Hospital Insurance)
- **URL**: https://data.cms.gov/provider-summary-by-type-of-service/medicare-inpatient-hospitals/ (NEEDS VERIFICATION)
- **Update Frequency**: Annual (typically released 1.5–2 years after the discharge year)
- **Current Coverage**: 2013–2022 (latest year NEEDS VERIFICATION)
- **Access Level**: Public Use File
- **File Format**: CSV download; also available via CMS Data API (JSON/CSV endpoints)
- **Approximate Size**: ~200,000–300,000 rows per year (provider-DRG grain); ~50–150 MB per annual file

## Purpose & Policy Context

The Medicare Inpatient Hospitals PUF was released as part of the same transparency wave as the physician-level data, driven by ACA Section 10332 and the 2013 court ruling enabling provider-level payment disclosure. The dataset provides hospital-level information about inpatient stays paid under Medicare's Inpatient Prospective Payment System (IPPS), broken down by Medicare Severity Diagnosis Related Group (MS-DRG).

This data answers fundamental questions about hospital utilization: which hospitals treat which conditions, how much Medicare pays for specific DRGs at each hospital, and how charges and payments vary across institutions. The IPPS system, established by the Social Security Amendments of 1983 (PL 98-21), fundamentally changed hospital payment from cost-based reimbursement to prospective per-case payment. Understanding how DRG payments vary across hospitals is central to evaluating whether IPPS achieves its policy goals of cost control and equity.

In the transparency ecosystem, this dataset complements Hospital Compare quality metrics (enabling cost-quality comparisons), the Medicare Cost Reports (which provide hospital financial data), and the physician-level Part B data (which covers outpatient professional services). It is essential for studying hospital market concentration, price variation, and the effects of hospital consolidation on Medicare spending. Key legislation includes the Social Security Amendments of 1983 (IPPS creation), the ACA (transparency mandate), and the Bipartisan Budget Act of 2018 (site-neutral payment policies).

## Contents

| Column Group | Description | Key Fields |
|---|---|---|
| Provider Identity | Hospital identification | `Rndrng_Prvdr_CCN`, `Rndrng_Prvdr_Org_Name`, `Rndrng_Prvdr_St`, `Rndrng_Prvdr_City`, `Rndrng_Prvdr_State_Abrvtn`, `Rndrng_Prvdr_State_FIPS`, `Rndrng_Prvdr_Zip5` |
| Provider Characteristics | Hospital attributes | `Rndrng_Prvdr_RUCA`, `Rndrng_Prvdr_Type` (hospital type classification) |
| DRG Identity | Diagnosis group | `DRG_Cd`, `DRG_Desc` |
| Utilization | Volume metrics | `Tot_Dschrgs` (total discharges) |
| Payment | Dollar amounts | `Avg_Submtd_Cvrd_Chrg` (average covered charges), `Avg_Tot_Pymt_Amt` (average total payments including beneficiary and third-party), `Avg_Mdcr_Pymt_Amt` (average Medicare payment) |

## Key Identifiers

| Identifier | Type | Links To |
|---|---|---|
| `Rndrng_Prvdr_CCN` | CMS Certification Number (6-digit) | Hospital Compare, Medicare Cost Reports, Provider of Services file, all hospital-level CMS datasets |
| `DRG_Cd` | MS-DRG Code (3-digit) | MS-DRG reference tables, ICD-to-DRG crosswalks |
| `Rndrng_Prvdr_State_FIPS` | FIPS State Code | Geographic Variation data, Census data |
| `Rndrng_Prvdr_Zip5` | 5-digit ZIP code | Geographic crosswalks |

## Relationships

| Related Source | Join Key | Relationship Type |
|---|---|---|
| Hospital Compare / Care Compare | `Rndrng_Prvdr_CCN` = `Facility_ID` / `CMS_Certification_Number` | Direct — links cost data to quality metrics |
| Medicare Cost Reports | `Rndrng_Prvdr_CCN` = `Provider_CCN` | Direct — adds financial context (margins, cost-to-charge ratios) |
| Provider of Services (POS) file | `Rndrng_Prvdr_CCN` = `PRVDR_NUM` | Direct — adds bed count, ownership type, teaching status |
| Medicare Geographic Variation | `Rndrng_Prvdr_State_FIPS` = state/county FIPS | Contextual — population-level spending context |
| Medicare Spending Per Beneficiary | `Rndrng_Prvdr_CCN` = `Facility_ID` | Direct — episode-based spending around hospitalizations |
| SNF Utilization | Indirect via discharge patterns | Contextual — post-acute care patterns after inpatient stays |
| NPPES | Indirect (hospitals have organizational NPIs) | Contextual — organizational NPI lookup |

## Data Quality Notes

- **Suppression**: Rows with fewer than 11 discharges for a given DRG at a hospital are suppressed to protect patient privacy. This disproportionately affects small rural hospitals and rare DRGs.
- **IPPS hospitals only**: Critical Access Hospitals (CAHs), which are paid on a cost basis rather than IPPS, are excluded from this dataset. This creates a systematic gap in rural hospital coverage since most CAHs are rural.
- **Charge vs. Payment confusion**: `Avg_Submtd_Cvrd_Chrg` reflects hospital chargemaster prices, which are notoriously inflated and not what Medicare actually pays. Always use `Avg_Mdcr_Pymt_Amt` for actual Medicare payment analysis.
- **DRG version changes**: MS-DRGs are updated annually (added, deleted, split, merged). Longitudinal analysis requires crosswalking DRG codes across years.
- **Total payment vs. Medicare payment**: `Avg_Tot_Pymt_Amt` includes beneficiary cost-sharing and third-party payments, while `Avg_Mdcr_Pymt_Amt` is Medicare's portion only.
- **Excludes**: Medicare Advantage discharges, Maryland waiver hospitals (paid under a different system), outpatient services, observation stays (which are technically outpatient), and transfers between hospitals (complex payment rules apply).
- **No severity adjustment within DRG**: While DRGs incorporate severity (the "MS" in MS-DRG), within a single DRG the data does not break down by comorbidity burden or patient demographics.

## Use Cases

1. **Hospital price transparency**: Compare what different hospitals charge and what Medicare pays for the same DRG to quantify price variation.
2. **Market concentration analysis**: Identify hospitals with dominant market share for specific DRGs in a geographic area.
3. **Cost-quality correlation**: Join with Hospital Compare to determine whether higher-cost hospitals deliver better outcomes.
4. **DRG trend analysis**: Track shifts in case mix (e.g., increasing sepsis coding, decreasing elective admissions) over time.
5. **Policy impact assessment**: Evaluate the effects of readmission penalties, value-based purchasing, or site-neutral payment proposals on hospital billing patterns.

## Regulatory Notes

- **Privacy protections**: All cells with fewer than 11 discharges are suppressed per CMS cell suppression policy. No patient-level data is released.
- **Terms of use**: Standard CMS PUF terms apply. No DUA required. Re-identification of beneficiaries is prohibited.
- **IPPS payment context**: Payment amounts reflect the IPPS methodology including base DRG payment, geographic adjustments (wage index), add-on payments (teaching, DSH, outliers), and sequestration reductions. Understanding IPPS is essential for interpreting the payment fields.
- **Citation**: CMS requests acknowledgment as the data source. Standard citation: "Centers for Medicare & Medicaid Services. Medicare Inpatient Hospitals — by Provider and Service, [YEAR]."

## Verification Needed

- [ ] Confirm current URL on data.cms.gov
- [ ] Verify most recent data year available (likely 2022 or 2023)
- [ ] Check whether CMS has added new fields (e.g., uncompensated care indicators)
- [ ] Confirm whether Critical Access Hospitals remain excluded or if CMS has added a separate CAH dataset
- [ ] Verify the current MS-DRG version in use (v41 was FY2024)
- [ ] Check if column naming convention matches current Part B convention
- [ ] Confirm suppression threshold is still 11 discharges
- [ ] Check if Maryland all-payer model hospitals are now included in any form
