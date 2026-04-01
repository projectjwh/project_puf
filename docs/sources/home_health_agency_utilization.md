# Data Source: Home Health Agency (HHA) Utilization

## Overview
- **Publisher**: Centers for Medicare & Medicaid Services (CMS)
- **Program**: Medicare Part A (primarily) and Part B (some home health services)
- **URL**: https://data.cms.gov/provider-summary-by-type-of-service/medicare-home-health-agencies/ (NEEDS VERIFICATION)
- **Update Frequency**: Annual (typically released 1.5–2 years after the service year)
- **Current Coverage**: 2013–2022 (latest year NEEDS VERIFICATION)
- **Access Level**: Public Use File
- **File Format**: CSV download; CMS Data API
- **Approximate Size**: ~300,000–500,000 rows per year (provider-HCPCS grain in the by-provider-and-service file) or ~10,000–12,000 rows in the agency-level summary; ~50–200 MB

## Purpose & Policy Context

The Home Health Agency (HHA) PUF was released as part of the CMS transparency initiative driven by ACA Section 10332. Home health care is a critical component of Medicare's post-acute care continuum: after a hospitalization or in lieu of institutional care, Medicare beneficiaries can receive skilled nursing, physical therapy, occupational therapy, speech-language pathology, medical social services, and home health aide services in their homes, delivered by Medicare-certified home health agencies.

This data answers questions about which home health agencies serve which populations, what services they provide, how much Medicare pays, and how utilization varies geographically. Home health has been a persistent target of fraud enforcement — CMS and OIG have identified patterns of unnecessary services, billing for services not rendered, and agency proliferation in certain markets (notably South Florida, Texas, and Michigan). The data supports both transparency and program integrity goals.

Home health payment has undergone major policy changes. The Balanced Budget Act of 1997 established the Home Health Prospective Payment System (HH PPS), which pays per 60-day episode. The Bipartisan Budget Act of 2018 mandated the Patient-Driven Groupings Model (PDGM), implemented January 1, 2020, which fundamentally changed home health payment from 60-day episodes to 30-day periods and shifted the case-mix classification from therapy utilization to clinical characteristics and functional status. This is a critical schema break in the data. Key legislation: BBA 1997 (HH PPS), ACA 2010 (transparency, face-to-face encounter requirements), Bipartisan Budget Act of 2018 (PDGM mandate), IMPACT Act of 2014 (standardized patient assessment data).

## Contents

| Column Group | Description | Key Fields |
|---|---|---|
| Agency Identity | HHA identification | `Rndrng_Prvdr_CCN`, `Rndrng_Prvdr_Org_Name`, `Rndrng_Prvdr_St`, `Rndrng_Prvdr_City`, `Rndrng_Prvdr_State_Abrvtn`, `Rndrng_Prvdr_State_FIPS`, `Rndrng_Prvdr_Zip5` |
| Agency Characteristics | Agency attributes | `Rndrng_Prvdr_RUCA`, `Rndrng_Prvdr_Type` |
| Utilization | Volume metrics | `Tot_Epsd` (total episodes), `Tot_Benes` (total beneficiaries), `Tot_HH_Chrg_Amt`, `Tot_HH_Mdcr_Pymt_Amt`, `Tot_HH_Mdcr_Stdzd_Pymt_Amt` |
| Episode Characteristics | Episode-level detail | `Avg_HH_Epsd_Per_Bene` (average episodes per beneficiary), various visit count fields |
| Visit Counts by Discipline | Service breakdown | `Tot_Sklnd_Nrsng_Vsts`, `Tot_PT_Vsts`, `Tot_OT_Vsts`, `Tot_ST_Vsts`, `Tot_HH_Aide_Vsts`, `Tot_Mdcl_Scl_Srvcs_Vsts` |
| Payment | Dollar amounts | `Avg_HH_Mdcr_Pymt_Amt` (average payment per episode), `Avg_HH_Mdcr_Stdzd_Pymt_Amt` (standardized) |

## Key Identifiers

| Identifier | Type | Links To |
|---|---|---|
| `Rndrng_Prvdr_CCN` | CMS Certification Number (6-digit, typically starting with state code + "7") | Care Compare Home Health data, Provider of Services file, Medicare Cost Reports |
| `Rndrng_Prvdr_State_FIPS` | FIPS State Code | Geographic Variation, Census data |
| `Rndrng_Prvdr_Zip5` | 5-digit ZIP code | Geographic crosswalks |

## Relationships

| Related Source | Join Key | Relationship Type |
|---|---|---|
| Hospital Compare / Care Compare (Home Health section) | `Rndrng_Prvdr_CCN` = Home Health CCN | Direct — quality measures for home health agencies (OASIS-based outcomes, patient experience HHCAHPS) |
| Medicare Inpatient Hospitals | Indirect (post-discharge referral patterns) | Contextual — home health as post-acute care after hospitalization |
| Medicare Spending Per Beneficiary | Indirect (home health costs contribute to MSPB) | Contextual — home health as component of episode spending |
| Medicare Geographic Variation | `Rndrng_Prvdr_State_FIPS` = state/county FIPS | Contextual — `HH_Mdcr_Pymt_PC` in geographic variation provides population context |
| NPPES | Organizational NPI crosswalk (CCN-to-NPI) | Contextual — agency NPI linkage |
| Medicare Cost Reports (Home Health) | `Rndrng_Prvdr_CCN` = `Provider_CCN` | Direct — financial data for the agency |
| Provider of Services (POS) | `Rndrng_Prvdr_CCN` = `PRVDR_NUM` | Direct — agency characteristics (ownership, certification date) |

## Data Quality Notes

- **PDGM transition (2020)**: The shift from 60-day episodes to 30-day payment periods fundamentally changes how utilization and payment should be interpreted starting in 2020. Pre-2020 and post-2020 data are not directly comparable without adjustment.
- **Suppression**: Standard CMS cell suppression applies (11-beneficiary minimum for agency-service combinations).
- **CCN-based identification**: Home health agencies are identified by CCN, not NPI, in this dataset. The CCN format for HHAs typically uses the pattern [state code][7xxx]. Joining to NPI-based datasets requires a CCN-to-NPI crosswalk (available via NPPES or PECOS).
- **Visit counts vs. episodes**: The data reports both episode counts and visit counts by discipline. An episode may contain varying numbers of visits. High visits-per-episode may indicate either clinical complexity or potential overutilization.
- **Geographic assignment**: Agencies are assigned to their business address location, which may differ from the areas where they actually provide services. HHAs can serve beneficiaries across county and state lines.
- **Excludes**: Medicare Advantage home health (which is covered by MA plans, not FFS), home health provided by hospital-based agencies may be reported differently than freestanding agencies, non-Medicare home care services.
- **Outlier payments**: Medicare home health includes outlier adjustments for unusually costly episodes. These can skew average payment amounts for agencies with high-acuity populations.
- **Fraud prevalence**: Home health has historically high fraud rates. CMS has implemented enhanced enrollment screening, moratoriums in high-fraud areas, and prior authorization pilots. These program integrity measures affect the data (e.g., agency closures, reduced utilization in moratorium areas).

## Use Cases

1. **Post-acute care analysis**: Study home health utilization as a component of the post-acute care pathway after hospitalization, alongside SNF and other PAC settings.
2. **Geographic variation in home health use**: Identify areas with unusually high or low home health utilization rates, controlling for population health needs.
3. **Service mix analysis**: Examine the distribution of skilled nursing vs. therapy visits across agencies and regions, especially pre- vs. post-PDGM.
4. **Agency profiling**: Identify agencies with outlier patterns in episodes per beneficiary, visits per episode, or payment per episode.
5. **Fraud risk scoring**: Combine utilization data with agency characteristics and geographic fraud risk factors to score agencies for potential program integrity concerns.
6. **PDGM impact evaluation**: Compare pre-2020 and post-2020 utilization and payment patterns to assess the impact of the PDGM payment reform.

## Regulatory Notes

- **Certification requirements**: HHAs must be Medicare-certified (survey and certification process) and meet Conditions of Participation (CoPs). Only certified agencies appear in this dataset.
- **Face-to-face encounter**: Since 2011 (ACA requirement), a physician must document a face-to-face encounter with the beneficiary before certifying the need for home health services. This requirement was intended to reduce inappropriate utilization.
- **OASIS assessment**: HHAs must complete the Outcome and Assessment Information Set (OASIS) for each patient. OASIS data feeds into quality measures reported on Care Compare but is not included in this utilization PUF.
- **Privacy protections**: Standard CMS cell suppression. Agency-level data only; no patient-level information.
- **Terms of use**: Standard CMS PUF terms. No DUA required.
- **Citation**: "Centers for Medicare & Medicaid Services. Medicare Home Health Agency Utilization, [YEAR]."

## Verification Needed

- [ ] Confirm current URL on data.cms.gov
- [ ] Verify most recent data year available
- [ ] Confirm whether PDGM transition is reflected in data structure (30-day periods vs. 60-day episodes post-2020)
- [ ] Check if CMS has added PDGM-specific fields (clinical grouping, admission source, timing)
- [ ] Verify column naming conventions
- [ ] Check whether CMS has added quality-linked fields to the utilization PUF
- [ ] Confirm whether moratorium areas are documented in the data
- [ ] Verify file size and row counts for most recent year
- [ ] Check if agency-level summary and provider-service detail files are both still available
