# Data Source: Medicare Spending Per Beneficiary (MSPB)

## Overview
- **Publisher**: Centers for Medicare & Medicaid Services (CMS)
- **Program**: Medicare Parts A and B (FFS)
- **URL**: https://data.cms.gov/provider-data/dataset/rrqw-56er (Hospital-level MSPB); also part of Care Compare hospital data downloads (NEEDS VERIFICATION)
- **Update Frequency**: Annual (measure period typically covers 3 years; updated annually with rolling window)
- **Current Coverage**: Reporting periods beginning ~2014 through most recent; each report uses a 3-year measurement window (NEEDS VERIFICATION)
- **Access Level**: Public Use File
- **File Format**: CSV download; available within Care Compare data packages
- **Approximate Size**: ~4,000–5,000 rows per release (one row per hospital); <10 MB per file

## Purpose & Policy Context

The Medicare Spending Per Beneficiary (MSPB) measure was developed by CMS as part of the Hospital Value-Based Purchasing (VBP) Program, which was established by the ACA Section 3001 (codified at 42 USC 1395ww(o)). The VBP Program ties a portion of Medicare inpatient payments to hospital performance on quality and efficiency measures. MSPB is the primary efficiency measure, designed to capture the total cost of care associated with a hospitalization, including services provided during the inpatient stay and in the 30 days before and after discharge.

The measure answers a specific policy question: how much does Medicare spend on a beneficiary's episode of care at this hospital compared to the national median? A hospital with an MSPB ratio greater than 1.0 spends more than the median; below 1.0 is less. This captures not just the inpatient stay costs but also pre-admission workup and post-discharge care (readmissions, SNF, home health, physician visits, etc.), holding the hospital accountable for the full care episode.

In the transparency landscape, MSPB bridges the gap between provider-level cost data (which shows what individual providers bill) and population-level spending data (which shows area averages). It is inherently an episode-based measure, providing a more clinically meaningful unit of analysis than per-service or per-beneficiary-per-year spending. The measure directly feeds into hospital VBP payment adjustments, making it both an accountability tool and a transparency tool. Key legislation: ACA Section 3001 (VBP Program), ACA Section 3025 (Hospital Readmissions Reduction Program, which MSPB complements).

## Contents

| Column Group | Description | Key Fields |
|---|---|---|
| Hospital Identity | Facility identification | `Facility_ID` (CCN), `Facility_Name`, `Address`, `City`, `State`, `ZIP_Code` |
| Measure Details | MSPB measure identification | `Measure_ID` (typically `MSPB_1`), `Measure_Name` |
| Performance | MSPB results | `Score` (MSPB ratio: hospital spending relative to national median), `Footnote`, `Start_Date`, `End_Date` |
| Comparison | National benchmarks | Comparison to national rate (e.g., "Above", "Below", "No Different") |

## Key Identifiers

| Identifier | Type | Links To |
|---|---|---|
| `Facility_ID` | CMS Certification Number (CCN, 6-digit) | Hospital Compare, Inpatient Hospital data, Medicare Cost Reports, Provider of Services |
| `State` | State abbreviation | Geographic Variation, all state-level datasets |
| `ZIP_Code` | 5-digit ZIP | Geographic crosswalks |
| `Measure_ID` | CMS measure identifier (`MSPB_1`) | Care Compare measure catalog |

## Relationships

| Related Source | Join Key | Relationship Type |
|---|---|---|
| Hospital Compare / Care Compare | `Facility_ID` = `Facility_ID` | Direct — MSPB is one of many hospital quality/efficiency measures |
| Medicare Inpatient Hospitals | `Facility_ID` = `Rndrng_Prvdr_CCN` | Direct — inpatient cost data for the same hospitals |
| Medicare Cost Reports | `Facility_ID` = `Provider_CCN` | Direct — hospital financial data provides context for MSPB |
| Medicare Geographic Variation | State / County FIPS crosswalk | Contextual — population-level spending context |
| SNF Utilization | Indirect via post-discharge patterns | Contextual — SNF costs are a major driver of MSPB |
| HHA Utilization | Indirect via post-discharge patterns | Contextual — home health costs contribute to MSPB |
| Hospice Utilization | Indirect via post-discharge patterns | Contextual — hospice election affects MSPB |

## Data Quality Notes

- **Ratio, not dollars**: The published MSPB value is a ratio relative to the national median, not a dollar amount. The national median spending amount is published separately. To calculate dollar spending, multiply the ratio by the national median.
- **Episode definition**: An MSPB episode begins 3 days before admission and ends 30 days after discharge. It includes all Part A and Part B FFS claims in that window. This means a single beneficiary contributes to the MSPB of every hospital where they have an eligible inpatient stay.
- **Risk adjustment**: MSPB is adjusted for age, sex, HCC risk score, and enrollment status. It is NOT adjusted for geographic payment differences (wage index, DSH) because CMS wants to capture real spending differences, including those driven by price.
- **Small sample suppression**: Hospitals with too few episodes (generally fewer than 25) are not reported.
- **Rolling measurement window**: Each annual release uses a 3-year measurement window (e.g., 2019–2021 for a 2023 release). This smooths year-to-year variation but also means the data reflects a blended period.
- **Excludes**: Medicare Advantage beneficiaries, episodes with a principal diagnosis of psychiatric or rehabilitation, beneficiaries enrolled in Medicare for less than 30 days post-discharge, episodes where the beneficiary died during the stay.
- **Post-acute care dominance**: Post-discharge spending (SNF, home health, readmissions) often comprises a large share of MSPB variation. Hospitals in areas with high post-acute use may show high MSPB even if their inpatient costs are reasonable.
- **Not comparable across hospital types**: MSPB does not control for hospital type (teaching vs. community), ownership, or case mix beyond the risk adjustment. Comparing a large urban academic medical center to a small community hospital requires caution.

## Use Cases

1. **Hospital efficiency benchmarking**: Identify hospitals with above- or below-median episode spending relative to risk-adjusted expectations.
2. **Post-acute care analysis**: Decompose MSPB into inpatient vs. post-acute components to understand where spending variation originates.
3. **VBP program analysis**: Study how hospitals respond to financial incentives tied to MSPB performance.
4. **Episode-based spending research**: Use MSPB as a standardized episode cost measure for health services research.
5. **Readmission cost impact**: Quantify the cost consequences of readmissions within the MSPB episode window.

## Regulatory Notes

- **VBP program integration**: MSPB directly affects hospital Medicare payments through the VBP Program. Poor performance results in payment reductions (up to 2% of base DRG payments). This creates strong incentives for hospitals to monitor and manage their MSPB.
- **Privacy protections**: Hospital-level aggregate data only. No patient-level information. Small sample hospitals are excluded.
- **Terms of use**: Standard CMS PUF terms. No DUA required.
- **Methodology documentation**: CMS publishes detailed MSPB measure specifications through QualityNet. Understanding the risk adjustment and episode construction methodology is essential for proper interpretation.
- **Citation**: "Centers for Medicare & Medicaid Services. Medicare Spending Per Beneficiary (MSPB) Measure, [YEAR]."

## Verification Needed

- [ ] Confirm current URL on data.cms.gov or within Care Compare data packages
- [ ] Verify most recent measurement period
- [ ] Check whether CMS has changed the MSPB methodology (episode window, risk adjustment model)
- [ ] Confirm whether MSPB is still reported as a ratio or if CMS now also reports dollar amounts
- [ ] Verify the minimum episode threshold for reporting
- [ ] Check if CMS has added condition-specific MSPB measures (e.g., MSPB for joint replacement episodes)
- [ ] Confirm whether the measure is still part of VBP or has been removed/replaced
- [ ] Check if post-2020 data has COVID-era adjustments or exclusions
