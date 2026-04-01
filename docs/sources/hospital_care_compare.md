# Data Source: Hospital Compare / Care Compare (Quality Metrics)

## Overview
- **Publisher**: Centers for Medicare & Medicaid Services (CMS)
- **Program**: Cross-program (Medicare Part A, Part B, and CMS quality programs)
- **URL**: https://data.cms.gov/provider-data/ (Care Compare data downloads); https://www.medicare.gov/care-compare/ (consumer-facing portal) (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly (some measures updated annually)
- **Current Coverage**: Varies by measure — some go back to 2005; most current data covers 2019–2023 reporting periods (NEEDS VERIFICATION)
- **Access Level**: Public Use File
- **File Format**: CSV download (multiple files per data category); API available
- **Approximate Size**: Varies widely — the full Hospital Compare archive is ~500 MB across dozens of CSV files; individual files range from 1 MB to 100 MB

## Purpose & Policy Context

Hospital Compare launched in 2005 as a joint initiative between CMS and the Hospital Quality Alliance (HQA). It was mandated by Section 501(b) of the Medicare Prescription Drug, Improvement, and Modernization Act of 2003 (MMA), which required CMS to establish a plan for hospital quality reporting. The Deficit Reduction Act of 2005 and the ACA further expanded quality reporting requirements. In 2020, CMS consolidated Hospital Compare, Physician Compare, Nursing Home Compare, and other provider comparison tools into a unified platform called **Care Compare**.

The system answers the fundamental consumer question: "How good is this hospital?" It reports on process measures (did the hospital follow clinical guidelines?), outcome measures (did patients get better or worse?), patient experience (HCAHPS survey), efficiency (Medicare Spending Per Beneficiary), safety (HAIs, PSIs), and timely/effective care. Beyond consumer use, it is the foundation for Medicare's pay-for-performance programs: the Hospital Value-Based Purchasing (VBP) Program, the Hospital Readmissions Reduction Program (HRRP), and the Hospital-Acquired Condition (HAC) Reduction Program — all of which adjust Medicare payments based on quality performance.

Within the transparency landscape, this dataset converts raw claims and clinical data into standardized quality measures that can be compared across hospitals. When joined with inpatient utilization and payment data, it enables the essential cost-quality analysis: are more expensive hospitals actually delivering better care? The data also supports CMS's Star Ratings system, which distills dozens of measures into a single 1-to-5 star summary rating. Key legislation: MMA 2003, Deficit Reduction Act 2005, ACA 2010 (Sections 3001-3008 created VBP, HRRP, HAC programs), the Improving Medicare Post-Acute Care Transformation (IMPACT) Act of 2014.

## Contents

| Column Group | Description | Key Fields |
|---|---|---|
| Hospital Identity | Facility identification | `Facility_ID` (CCN), `Facility_Name`, `Address`, `City`, `State`, `ZIP_Code`, `County_Name`, `Phone_Number` |
| Hospital Characteristics | Facility attributes | `Hospital_Type`, `Hospital_Ownership`, `Emergency_Services`, `Hospital_overall_rating` (Star Rating) |
| Process Measures | Clinical guideline adherence | Measure-specific columns (e.g., `IMM_3` immunization rates, `SEP_1` sepsis bundle compliance) |
| Outcome Measures | Mortality and complications | `MORT_30_AMI`, `MORT_30_HF`, `MORT_30_PN` (30-day mortality rates), `COMP_HIP_KNEE` (complications) |
| Readmission Measures | Return visit rates | `READM_30_AMI`, `READM_30_HF`, `READM_30_PN`, `READM_30_HOSP_WIDE` (30-day readmission rates) |
| Patient Experience (HCAHPS) | Survey results | `H_COMP_1_*` through `H_COMP_7_*` (communication, responsiveness, cleanliness, noise, etc.), `H_STAR_RATING` |
| Safety | Infection and harm rates | `HAI_1_*` through `HAI_6_*` (healthcare-associated infection measures: CLABSI, CAUTI, SSI, MRSA, C.diff) |
| Efficiency | Spending measures | `MSPB_1` (Medicare Spending Per Beneficiary) |
| Structural | Facility capabilities | `Registry_*` fields (participation in clinical registries) |

## Key Identifiers

| Identifier | Type | Links To |
|---|---|---|
| `Facility_ID` | CMS Certification Number (CCN, 6-digit) | Inpatient Hospital data, Medicare Cost Reports, Provider of Services, SNF data, HHA data |
| `State` | State abbreviation | Geographic Variation, all state-level datasets |
| `ZIP_Code` | 5-digit ZIP | Geographic crosswalks |
| `County_Name` | County name (text) | County-level datasets (needs FIPS crosswalk for reliable joins) |

## Relationships

| Related Source | Join Key | Relationship Type |
|---|---|---|
| Medicare Inpatient Hospitals | `Facility_ID` = `Rndrng_Prvdr_CCN` | Direct — links quality metrics to cost and utilization |
| Medicare Spending Per Beneficiary | `Facility_ID` = `Facility_ID` | Direct — episode-level spending context |
| Provider of Services (POS) file | `Facility_ID` = `PRVDR_NUM` | Direct — detailed facility characteristics |
| Medicare Cost Reports | `Facility_ID` = `Provider_CCN` | Direct — financial performance context |
| Medicare Geographic Variation | State / County FIPS | Contextual — population health context for quality measures |
| SNF Utilization | Indirect via post-acute referral patterns | Contextual — quality of post-acute destinations |
| Physician Compare / PECOS | Indirect (physicians practicing at rated hospitals) | Contextual — provider-facility linkage |

## Data Quality Notes

- **Multiple file structure**: Care Compare data is not a single file. It is distributed across dozens of CSV files organized by measure category (General Information, Timely and Effective Care, Complications and Deaths, Readmissions and Deaths, Patient Experience, etc.). Each must be joined via `Facility_ID`.
- **Measure lifecycle**: Quality measures are added, modified, and retired regularly. A measure present in 2018 may not exist in 2023, and vice versa. CMS publishes measure ID crosswalks.
- **Reporting periods**: Different measures cover different time windows. Mortality measures may use 3 years of data while process measures use a quarter. Comparing measures requires understanding their temporal alignment.
- **"Not Available" values**: Many cells contain "Not Available" when a hospital had too few cases, was too new, or did not report. This is distinct from suppression — it means the measure could not be reliably calculated.
- **Star Ratings methodology**: The overall hospital star rating uses a complex clustering algorithm that has changed over time (most recently in 2021). Star ratings are controversial and their methodology should be understood before use.
- **Excludes**: VA hospitals, military hospitals, and most specialty hospitals (psychiatric, rehabilitation, long-term care). Critical Access Hospitals are included for some measures but not all. Maryland all-payer hospitals have limited measure reporting.
- **HCAHPS survey bias**: Patient experience scores are adjusted for patient mix but remain subject to response bias and cultural differences in survey completion.

## Use Cases

1. **Hospital quality comparison**: Rank hospitals within a market or nationally on outcome, process, and experience measures.
2. **Value analysis**: Join with inpatient cost data to identify high-value hospitals (good outcomes, reasonable costs) and low-value hospitals (poor outcomes, high costs).
3. **Pay-for-performance impact**: Track how VBP, HRRP, and HAC program penalties correlate with quality improvement over time.
4. **Star rating analysis**: Decompose the overall star rating to understand which measure groups drive high or low ratings.
5. **Geographic quality variation**: Map quality measures to identify regions with systematically better or worse hospital performance.
6. **Safety monitoring**: Track healthcare-associated infection trends across hospitals and regions.

## Regulatory Notes

- **Privacy protections**: All measures are reported at the hospital level (not patient level). Measures with too few cases to calculate reliable rates are suppressed or marked "Not Available."
- **Mandatory reporting**: Most IPPS hospitals are required to report quality data or face a 2% Medicare payment reduction under the Hospital Inpatient Quality Reporting (IQR) program. This creates near-universal reporting for IPPS hospitals.
- **Terms of use**: CMS PUF standard terms apply. No DUA required. Data is intended for public use and consumer decision-making.
- **CMS Star Ratings**: The overall star rating is a CMS-calculated composite. Hospitals may display it but cannot modify the methodology. The American Hospital Association (AHA) has historically challenged the star rating methodology.
- **Citation**: "Centers for Medicare & Medicaid Services. Care Compare: Hospital Data, [YEAR/QUARTER]."

## Verification Needed

- [ ] Confirm current URL structure on data.cms.gov (CMS restructured provider data pages ~2022–2023)
- [ ] Verify the most recent quarterly data release
- [ ] Confirm which measures are currently active vs. retired (CMS measure lifecycle changes frequently)
- [ ] Check whether the star rating methodology has changed since 2021
- [ ] Verify the complete list of CSV files in the current data download package
- [ ] Confirm whether CMS has added any health equity measures or social determinants data
- [ ] Check if new measures related to COVID-19, maternal health, or behavioral health have been added
- [ ] Verify API access points and rate limits for Care Compare data
