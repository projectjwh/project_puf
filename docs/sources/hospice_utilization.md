# Data Source: Hospice Utilization

## Overview
- **Publisher**: Centers for Medicare & Medicaid Services (CMS)
- **Program**: Medicare Part A (Hospice Benefit)
- **URL**: https://data.cms.gov/provider-summary-by-type-of-service/medicare-hospice/ (NEEDS VERIFICATION)
- **Update Frequency**: Annual (typically released 1.5–2 years after the service year)
- **Current Coverage**: 2013–2022 (latest year NEEDS VERIFICATION)
- **Access Level**: Public Use File
- **File Format**: CSV download; CMS Data API
- **Approximate Size**: ~5,000–6,000 rows per year in agency-level summary (one row per hospice); provider-and-service detail files larger; ~10–50 MB

## Purpose & Policy Context

The Medicare Hospice PUF was released as part of the CMS transparency initiative. The Medicare hospice benefit, established by the Tax Equity and Fiscal Responsibility Act of 1982 (TEFRA) and made permanent in 1986, provides palliative care to terminally ill beneficiaries with a life expectancy of six months or less who elect to forgo curative treatment. Hospice is the only Medicare benefit that requires the beneficiary to choose to enroll and to formally elect to waive other Medicare Part A benefits for the terminal illness.

This data answers questions about hospice utilization patterns: which agencies provide hospice services, how many beneficiaries they serve, the distribution of care across levels of service (routine home care, continuous home care, inpatient respite, general inpatient care), length of stay patterns, and payment amounts. Hospice utilization has grown significantly — from about 25% of Medicare decedents in the early 2000s to over 50% by the 2020s — making it an increasingly important component of end-of-life care spending.

In the transparency landscape, hospice data is distinctive because it reflects end-of-life care choices and patterns. It is policy-relevant in several dimensions: the adequacy of the per-diem payment rates, the prevalence of very long hospice stays (which raise questions about appropriate enrollment), the rise of for-profit hospice providers (which now constitute the majority of hospice agencies), and disparities in hospice access by race, geography, and diagnosis. The OIG has identified hospice as a sector with growing fraud concerns, particularly around enrollment of patients who are not terminally ill. Key legislation: TEFRA 1982 (created hospice benefit), BBA 1997 (payment reforms), ACA 2010 (transparency, face-to-face recertification requirements), the Hospice CARE Act proposals (various years).

## Contents

| Column Group | Description | Key Fields |
|---|---|---|
| Agency Identity | Hospice identification | `Rndrng_Prvdr_CCN`, `Rndrng_Prvdr_Org_Name`, `Rndrng_Prvdr_St`, `Rndrng_Prvdr_City`, `Rndrng_Prvdr_State_Abrvtn`, `Rndrng_Prvdr_State_FIPS`, `Rndrng_Prvdr_Zip5` |
| Agency Characteristics | Hospice attributes | `Rndrng_Prvdr_RUCA`, `Rndrng_Prvdr_Type` |
| Beneficiary Counts | Volume | `Tot_Benes`, `Tot_Bene_Days` |
| Level of Care | Service distribution | `Tot_Rtn_Hm_Care_Days` (routine home care), `Tot_Cntns_Hm_Care_Days` (continuous home care), `Tot_IP_Rspte_Days` (inpatient respite), `Tot_Gnrl_IP_Days` (general inpatient) |
| Length of Stay | Duration metrics | `Avg_Elos` (average election length of stay), days distribution categories |
| Diagnosis | Primary terminal diagnosis | `Prncpl_Dgnss_Cd` or diagnosis category fields (cancer, dementia, heart failure, etc.) — varies by file format |
| Payment | Dollar amounts | `Tot_Mdcr_Pymt_Amt`, `Avg_Mdcr_Pymt_Per_Day`, `Tot_Mdcr_Stdzd_Pymt_Amt` |
| Discharge | How episodes ended | Live discharge vs. death counts (in some file formats) |

## Key Identifiers

| Identifier | Type | Links To |
|---|---|---|
| `Rndrng_Prvdr_CCN` | CMS Certification Number (6-digit, typically [state code] + "5" for hospice) | Care Compare Hospice data, Provider of Services file, Medicare Cost Reports (Hospice) |
| `Rndrng_Prvdr_State_FIPS` | FIPS State Code | Geographic Variation data, Census data |
| `Rndrng_Prvdr_Zip5` | 5-digit ZIP code | Geographic crosswalks |

## Relationships

| Related Source | Join Key | Relationship Type |
|---|---|---|
| Hospital Compare / Care Compare (Hospice section) | `Rndrng_Prvdr_CCN` = Hospice CCN | Direct — quality measures for hospice agencies (CAHPS Hospice Survey, HIS quality measures) |
| Medicare Inpatient Hospitals | Indirect (hospice elections often follow hospitalization) | Contextual — transition from curative to palliative care |
| Medicare Geographic Variation | `Rndrng_Prvdr_State_FIPS` = state/county FIPS | Contextual — `Hospice_Mdcr_Pymt_PC` provides population-level hospice spending |
| Medicare Spending Per Beneficiary | Indirect (hospice election affects MSPB) | Contextual — hospice election can reduce MSPB by avoiding re-hospitalization |
| Provider of Services (POS) | `Rndrng_Prvdr_CCN` = `PRVDR_NUM` | Direct — ownership type, certification date, bed count (if inpatient facility) |
| Medicare Cost Reports (Hospice) | `Rndrng_Prvdr_CCN` = `Provider_CCN` | Direct — financial performance of hospice agencies |
| SNF Utilization | Indirect (some hospice patients reside in SNFs) | Contextual — hospice in nursing homes |

## Data Quality Notes

- **Level-of-care distribution**: The vast majority (~98%) of hospice days are routine home care (RHC), the lowest-intensity and lowest-paid level. Small shifts in the percentage of general inpatient (GIP) or continuous home care (CHC) days have outsized effects on average per-day payments and should be analyzed carefully.
- **Length of stay bimodality**: Hospice length of stay has a bimodal distribution — many beneficiaries enroll very late (last 3-7 days of life) while others have very long stays (>180 days). Average length of stay can be misleading; median and distribution categories are more informative.
- **For-profit vs. nonprofit**: The hospice industry has seen rapid growth in for-profit providers. OIG and MedPAC research shows that for-profit hospices tend to have longer stays, more patients with diagnoses associated with longer prognoses (e.g., dementia vs. cancer), and potentially different quality profiles. Ownership type is available through the Provider of Services file.
- **Live discharge rates**: High live discharge rates (beneficiaries who leave hospice alive, either by choice or because they stabilized) may indicate either good screening or potential issues with enrollment appropriateness.
- **Diagnosis coding**: The terminal diagnosis is the primary diagnosis for which hospice care is elected. Diagnosis categories in the PUF may be aggregated (e.g., "cancer," "dementia," "heart disease") rather than using specific ICD-10 codes.
- **Suppression**: Standard CMS cell suppression (11-beneficiary minimum).
- **Excludes**: Medicare Advantage beneficiaries who elect hospice have their hospice services carved out to FFS Medicare, so they ARE included in this data (unlike most other service categories). This is an important distinction. However, supplemental benefits provided by MA plans are not captured.
- **COVID-19 impact**: Hospice utilization was significantly affected by COVID-19, both through direct deaths and through pandemic-related changes in care-seeking behavior. 2020 and 2021 data should be interpreted with caution.

## Use Cases

1. **End-of-life care patterns**: Analyze geographic and demographic variation in hospice utilization, length of stay, and timing of hospice election relative to death.
2. **For-profit vs. nonprofit comparison**: Compare utilization patterns, service mix, length of stay, and diagnosis profiles across ownership types.
3. **Quality-utilization linkage**: Join with Care Compare hospice quality data to study whether agencies with different utilization profiles deliver different quality.
4. **Fraud risk indicators**: Identify agencies with unusual patterns: very long average stays, concentration in high-reimbursement diagnoses, high live discharge rates.
5. **Post-acute care pathway analysis**: Study hospice as one option in the post-acute continuum (vs. SNF, home health, readmission).
6. **Market analysis**: Map hospice provider density and competition by geography, tracking new entrants and exits.

## Regulatory Notes

- **Hospice election**: Unique among Medicare benefits, hospice requires the beneficiary to formally elect the benefit and waive Part A coverage for curative treatment of the terminal illness. This election is documented and can be revoked.
- **Certification and recertification**: The terminal illness prognosis (six months or less) must be certified by a physician. The ACA added a face-to-face encounter requirement for recertification after 180 days. Recertification is required at specified intervals (90 days, 90 days, then 60-day periods).
- **Per-diem payment**: Hospice is paid on a per-diem basis with four levels of care: Routine Home Care (lowest rate), Continuous Home Care (highest rate, requires 8+ hours of predominantly nursing care), Inpatient Respite (short-term facility placement to relieve caregivers), and General Inpatient Care (facility-based for symptom management). MedPAC has proposed restructuring these rates.
- **Cap amount**: Each hospice is subject to an aggregate annual per-beneficiary cap. Agencies exceeding the cap must return excess payments. This creates financial pressure to manage long-stay patients.
- **Privacy protections**: Standard CMS cell suppression. No patient-level data. Aggregate agency-level reporting only.
- **Terms of use**: Standard CMS PUF terms. No DUA required.
- **Citation**: "Centers for Medicare & Medicaid Services. Medicare Hospice Utilization, [YEAR]."

## Verification Needed

- [ ] Confirm current URL on data.cms.gov
- [ ] Verify most recent data year available
- [ ] Check whether CMS has added additional data elements (e.g., race/ethnicity breakdowns, setting of care at election)
- [ ] Confirm diagnosis category definitions and whether ICD-10 codes are now included
- [ ] Verify column naming conventions match other provider-type PUFs
- [ ] Check if CMS has added COVID-19-specific indicators or adjustments
- [ ] Confirm whether the dataset includes both the agency-level summary and a detail-level file
- [ ] Verify the current hospice per-diem payment rates and aggregate cap amount
- [ ] Check if any new levels of care or payment categories have been introduced
