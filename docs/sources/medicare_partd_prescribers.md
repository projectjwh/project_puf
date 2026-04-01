# Data Source: Medicare Part D Prescribers — by Provider and Drug

## Overview
- **Publisher**: Centers for Medicare & Medicaid Services (CMS)
- **Program**: Medicare Part D (Prescription Drug Benefit)
- **URL**: https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/ (NEEDS VERIFICATION)
- **Update Frequency**: Annual (typically released 1.5–2 years after the service year)
- **Current Coverage**: 2013–2022 (latest year NEEDS VERIFICATION)
- **Access Level**: Public Use File
- **File Format**: CSV download; also available via CMS Data API (JSON/CSV endpoints)
- **Approximate Size**: ~25 million rows per year (provider-drug grain); ~4–6 GB per annual file uncompressed

## Purpose & Policy Context

The Medicare Part D Prescriber PUF was first released in 2015 (covering 2013 data) as part of the broader CMS transparency initiative mandated by ACA Section 10332. The Medicare Prescription Drug, Improvement, and Modernization Act of 2003 (MMA) created the Part D benefit effective January 2006, establishing the program whose claims this dataset summarizes. Before the PUF existed, prescriber-level Medicare drug data was essentially invisible to the public.

The dataset answers critical questions about prescription drug utilization within Medicare: which providers prescribe which drugs, in what volume, at what cost, and to how many beneficiaries. It supports analysis of prescribing patterns, opioid prescribing surveillance, generic vs. brand-name utilization, and the impact of drug pricing on Medicare spending. CMS also publishes a companion "by Provider" summary that aggregates across all drugs per provider, but the "by Provider and Drug" file is the most granular PUF available.

In the broader transparency ecosystem, this dataset is the drug-side complement to the Part B utilization data (which covers procedures and services). Together they provide a comprehensive view of a provider's Medicare practice. The data became especially policy-relevant during the opioid crisis (CMS added opioid-specific fields), in debates over Medicare drug price negotiation (Inflation Reduction Act of 2022), and in analyses of biosimilar adoption. Key legislation: MMA 2003 (created Part D), ACA 2010 (transparency mandate), the SUPPORT Act of 2018 (opioid-related provisions), and the Inflation Reduction Act of 2022 (drug price negotiation).

## Contents

| Column Group | Description | Key Fields |
|---|---|---|
| Provider Identity | Prescriber identification | `Prscrbr_NPI`, `Prscrbr_Last_Org_Name`, `Prscrbr_First_Name`, `Prscrbr_Crdntls`, `Prscrbr_Gndr` |
| Provider Location | Prescriber geography | `Prscrbr_St1`, `Prscrbr_St2`, `Prscrbr_City`, `Prscrbr_State_Abrvtn`, `Prscrbr_State_FIPS`, `Prscrbr_Zip5`, `Prscrbr_RUCA` |
| Provider Type | Specialty classification | `Prscrbr_Type`, `Prscrbr_Ent_Cd` (Individual vs Organization) |
| Drug Identity | What was prescribed | `Brnd_Name`, `Gnrc_Name`, `Drug_HCPCS_Cd` (if applicable) |
| Utilization | Volume and beneficiary counts | `Tot_Clms` (total claims/prescriptions), `Tot_30day_Fills` (total 30-day fill equivalents), `Tot_Benes` (total beneficiaries), `Tot_Day_Suply` (total day supply) |
| Cost | Dollar amounts | `Tot_Drug_Cst` (total drug cost), `GE65_Tot_Drug_Cst` (cost for 65+ beneficiaries), `GE65_Sprsn_Flag` |
| Beneficiary Demographics | Age breakdown flags | `GE65_Tot_Clms`, `GE65_Tot_30day_Fills`, `GE65_Tot_Benes`, `GE65_Tot_Day_Suply`, `GE65_Sprsn_Flag` |
| Opioid Indicators | Opioid-specific flags | `Opioid_Drug_Flag`, `Opioid_LA_Drug_Flag` (long-acting), `Antbtc_Drug_Flag`, `Opioid_Prscrbr_Rate` (in provider-level summary) |

## Key Identifiers

| Identifier | Type | Links To |
|---|---|---|
| `Prscrbr_NPI` | National Provider Identifier (10-digit) | NPPES, PECOS, Part B Utilization, Open Payments, all provider-level CMS datasets |
| `Brnd_Name` | Drug brand name | FDA NDC directory, drug reference databases |
| `Gnrc_Name` | Drug generic name | FDA NDC directory, pharmacological classifications (ATC) |
| `Prscrbr_State_FIPS` | FIPS State Code | Geographic Variation, Census data |
| `Prscrbr_Zip5` | 5-digit ZIP code | Geographic crosswalks |

## Relationships

| Related Source | Join Key | Relationship Type |
|---|---|---|
| Medicare Part B Utilization | `Prscrbr_NPI` = `Rndrng_NPI` | Direct — same provider, links prescribing patterns to procedure billing |
| NPPES (NPI Registry) | `Prscrbr_NPI` = `NPI` | Direct — enriches provider demographics, taxonomy, addresses |
| Open Payments (Sunshine Act) | `Prscrbr_NPI` = `Covered_Recipient_NPI` | Direct — links industry payments to prescribing patterns |
| Physician Compare / PECOS | `Prscrbr_NPI` = `NPI` | Direct — adds quality scores, group affiliations |
| Medicare Geographic Variation | `Prscrbr_State_FIPS` = state/county FIPS | Contextual — population-level drug spending context |
| FDA NDC Directory | `Brnd_Name` / `Gnrc_Name` (text match) | Contextual — drug classification, manufacturer, NDC codes |
| Medicare Part D Spending Dashboard | `Gnrc_Name` (text match) | Contextual — national spending trends per drug |

## Data Quality Notes

- **Suppression**: Rows with fewer than 11 claims or fewer than 11 beneficiaries for a given provider-drug combination are suppressed. This is the most aggressive suppression in any CMS PUF due to the sensitivity of prescription data.
- **Brand vs. Generic naming**: The same molecule may appear under multiple brand names or slightly different generic name strings. Text normalization is essential for drug-level aggregation.
- **No NDC codes**: The dataset uses brand/generic name pairs, not National Drug Codes (NDCs). This makes precise drug product identification (e.g., specific manufacturer, dosage form, strength) impossible from this dataset alone.
- **Part D only**: Excludes drugs covered under Part B (physician-administered drugs like chemotherapy infusions, which appear in the Part B utilization data with `HCPCS_Drug_Ind` = "Y"). Also excludes drugs not covered by Part D (e.g., benzodiazepines were excluded until 2013, barbiturates).
- **Cost definition**: `Tot_Drug_Cst` includes ingredient cost, dispensing fee, sales tax, and any applicable vaccine administration fee. It represents total cost, not just Medicare's share.
- **Year-over-year changes**: CMS added opioid flags around 2017. Earlier years lack these fields. Column naming conventions may vary between early and recent releases.
- **Excludes**: Medicare Advantage Part D (MA-PD) claims in some years — verify whether CMS has incorporated these. Claims from non-retail pharmacies may have different patterns.

## Use Cases

1. **Opioid prescribing surveillance**: Identify high-volume opioid prescribers by geography and specialty for public health monitoring and intervention targeting.
2. **Generic utilization analysis**: Calculate brand-to-generic ratios by provider, specialty, and geography to measure generic adoption and potential cost savings.
3. **Drug cost trending**: Track year-over-year cost changes for specific drugs to quantify price inflation at the provider level.
4. **Prescriber profiling**: Build comprehensive provider profiles combining Part D prescribing with Part B service patterns.
5. **Biosimilar adoption tracking**: Measure uptake of biosimilar drugs vs. reference biologics after market entry.
6. **Fraud, waste, and abuse detection**: Flag statistical outliers in prescribing volume or cost that warrant further investigation.

## Regulatory Notes

- **Privacy protections**: Aggressive cell suppression (11-claim/11-beneficiary minimum). No beneficiary-level data. The sensitivity of prescription data means CMS applies extra caution.
- **Terms of use**: Standard CMS PUF terms. No DUA required. Re-identification of beneficiaries is strictly prohibited. CMS specifically warns against using this data to infer individual patient medication regimens.
- **Part D program context**: Part D is administered through private plan sponsors (PDPs and MA-PDs). CMS aggregates claims across all Part D plans per prescriber. The data reflects what was dispensed and paid, not what was prescribed and rejected or abandoned.
- **Citation**: "Centers for Medicare & Medicaid Services. Medicare Part D Prescribers — by Provider and Drug, [YEAR]."

## Verification Needed

- [ ] Confirm current URL on data.cms.gov
- [ ] Verify most recent data year available (likely 2022 or 2023)
- [ ] Check whether MA-PD claims are now included in the PUF
- [ ] Confirm whether new drug classification flags have been added (e.g., antipsychotics, antibiotics expanded)
- [ ] Verify whether CMS has added NDC-level data or drug classification codes
- [ ] Check if Inflation Reduction Act negotiated drug prices affect data presentation
- [ ] Confirm suppression thresholds remain unchanged
- [ ] Check file size for most recent year
