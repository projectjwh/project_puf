# Raw & Foundational Healthcare Data Source Inventory

> **Domain Scholar Output** | Created: 2026-03-04 | Status: CATALOGED (67 sources)
> This inventory catalogs raw, foundational data sources -- the building blocks of the U.S. healthcare data ecosystem.
> These are identity registries, code systems, fee schedules, enrollment files, cost reports, and granular claims data.
> Distinct from the pre-aggregated summary PUFs cataloged in the initial 12-source inventory.

> **Web access unavailable.** All URLs, file sizes, and schema details are based on domain knowledge and flagged for verification.

---

## Table of Contents

1. [Provider Identity & Enrollment](#1-provider-identity--enrollment)
2. [Facility & Organizational Data](#2-facility--organizational-data)
3. [Code Systems & Terminologies](#3-code-systems--terminologies)
4. [Fee Schedules & Payment Rules](#4-fee-schedules--payment-rules)
5. [Geographic & Demographic Reference](#5-geographic--demographic-reference)
6. [Claims & Utilization (Raw/Granular)](#6-claims--utilization-rawgranular)
7. [Enrollment & Beneficiary Data](#7-enrollment--beneficiary-data)
8. [Quality & Outcomes](#8-quality--outcomes)
9. [Open Data Portals](#9-open-data-portals)
10. [Regulatory & Administrative Reference](#10-regulatory--administrative-reference)
11. [Priority Ranking](#priority-ranking)

---

## 1. Provider Identity & Enrollment

---

### 1.1 NPPES (National Plan and Provider Enumeration System) — Full NPI Registry

- **Category**: Provider Identity
- **Publisher**: CMS (Centers for Medicare & Medicaid Services)
- **Access Level**: Fully Public
- **Format**: CSV (single large file + monthly deactivation updates); also available via NPPES API (REST/JSON)
- **URL**: https://download.cms.gov/nppes/NPI_Files.html (NEEDS VERIFICATION)
- **Update Frequency**: Monthly (full replacement file); weekly incremental updates
- **Size Estimate**: ~8 million rows; ~8-10 GB uncompressed
- **Key Fields**: `NPI`, `Entity_Type_Code`, `Provider_Organization_Name`, `Provider_Last_Name`, `Provider_First_Name`, `Healthcare_Provider_Taxonomy_Code_1` through `_15`, `Provider_Business_Practice_Location_Address_*`, `Provider_Enumeration_Date`, `NPI_Deactivation_Date`
- **What It Contains**: Every National Provider Identifier ever issued under HIPAA, including individual practitioners (Type 1) and organizations (Type 2). Each record includes the provider's name, credentials, practice address, mailing address, up to 15 taxonomy codes (specialty classifications), other provider identifiers (legacy IDs), enumeration/deactivation dates, and authorized official information for organizations.
- **What It Does NOT Contain**: No claims data, no payment amounts, no patient counts, no quality scores. Does not indicate whether a provider actually participates in Medicare -- only that they have an NPI. No historical snapshots (current state only; old data is overwritten when providers update their records).
- **Why It Matters for Project PUF**: The universal provider identity hub. Every NPI-bearing dataset in the CMS ecosystem joins to NPPES. It is the single most foundational reference table for the entire platform.
- **Dependencies**: Upstream: none (it IS the identity source). Downstream: enables enrichment of Part B Utilization, Part D Prescribers, DME Suppliers, and all other NPI-keyed datasets. Requires NUCC Taxonomy codes for specialty interpretation.
- **Regulatory Basis**: HIPAA (1996), 45 CFR Part 162, Subpart D -- Standard Unique Health Identifier for Health Care Providers. NPI mandate effective May 23, 2007.

#### Verification Needed
- [ ] Confirm bulk download URL at download.cms.gov is still active
- [ ] Verify current file column structure (CMS has occasionally added fields)
- [ ] Check NPPES API rate limits and availability
- [ ] Confirm whether replacement files still include deactivated NPIs or if those are separate

---

### 1.2 PECOS (Provider Enrollment, Chain, and Ownership System)

- **Category**: Provider Identity / Enrollment
- **Publisher**: CMS
- **Access Level**: Partially Public (public enrollment data available; full PECOS internal system is not public)
- **Format**: CSV via data.cms.gov; also accessible through CMS API
- **URL**: https://data.cms.gov/provider-characteristics/medicare-provider-supplier-enrollment/ (NEEDS VERIFICATION)
- **Update Frequency**: Monthly to quarterly
- **Size Estimate**: ~2-3 million rows for provider enrollment; reassignment file may be separate
- **Key Fields**: `NPI`, `PAC_ID` (Provider Associate Control ID), `Enrollment_ID`, `Provider_Type`, `Specialty`, `State`, `Reassignment_NPI` (individual-to-organization billing relationships)
- **What It Contains**: Medicare-specific enrollment information for every provider and supplier enrolled in the Medicare program. Includes enrollment status, specialty designation (CMS specialty codes), practice locations, group practice affiliations, and reassignment relationships (which individual NPIs bill through which organizational NPIs). Also includes chain and ownership data for institutional providers.
- **What It Does NOT Contain**: No claims or payment data. Does not cover non-Medicare providers (unlike NPPES which covers all HIPAA-covered entities). The full PECOS system contains more detailed ownership and management information than the public extracts.
- **Why It Matters for Project PUF**: Filters the NPPES universe to Medicare-participating providers. The reassignment data is critical for understanding group practice structures. Chain/ownership data reveals corporate consolidation patterns.
- **Dependencies**: Upstream: NPPES (NPI is the linking key). Downstream: enables Medicare-specific provider filtering for all utilization datasets.
- **Regulatory Basis**: Social Security Act Section 1866(j); 42 CFR Part 424, Subpart P -- Medicare enrollment requirements. ACA Section 6401 strengthened enrollment screening.

#### Verification Needed
- [ ] Confirm which PECOS datasets are publicly downloadable vs. API-only
- [ ] Verify whether reassignment data is included in public extracts
- [ ] Check if chain/ownership data is available publicly or requires DUA
- [ ] Confirm PAC_ID is still the primary group practice linkage mechanism

---

### 1.3 Provider of Services (POS) File

- **Category**: Provider Identity / Facility
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV (historical files may be fixed-width)
- **URL**: https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-hospital-and-non-hospital-facilities (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly
- **Size Estimate**: ~200,000-300,000 rows per file; ~100-500 MB
- **Key Fields**: `CCN` (CMS Certification Number, also called Provider Number), `Provider_Name`, `Provider_Type`, `State_Code`, `City`, `ZIP`, `County_Code`, `Bed_Count`, `Ownership_Type`, `Certification_Date`
- **What It Contains**: Master list of all Medicare- and Medicaid-certified institutional providers (hospitals, SNFs, HHAs, hospices, dialysis facilities, ASCs, FQHCs, RHCs, etc.). Each record includes the facility's CCN, name, address, provider type, bed count (for applicable types), ownership type (government, proprietary, non-profit), certification and survey dates, and participation status.
- **What It Does NOT Contain**: No claims, utilization, or payment data. No quality metrics. Limited operational detail (no staffing, no financial data). Does not include non-certified providers.
- **Why It Matters for Project PUF**: The institutional provider identity hub. CCN is the join key for all facility-level datasets (Inpatient Hospitals, SNF, HHA, Hospice, Care Compare, Cost Reports). POS is to facilities what NPPES is to individual providers.
- **Dependencies**: Upstream: CMS certification/survey process. Downstream: enables enrichment of all CCN-keyed datasets. Links to CASPER for survey detail.
- **Regulatory Basis**: Social Security Act Sections 1861, 1864, 1865 -- Medicare Conditions of Participation and certification requirements. 42 CFR Parts 482-486 (various provider types).

#### Verification Needed
- [ ] Confirm current POS file download location on data.cms.gov
- [ ] Verify whether current and historical POS files are both available
- [ ] Check if POS file now includes additional provider types (e.g., opioid treatment programs)
- [ ] Confirm column name structure and format (CSV vs. fixed-width for historical files)

---

### 1.4 Medicare Opt-Out Affidavits

- **Category**: Provider Identity / Enrollment
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV or Excel
- **URL**: https://data.cms.gov/provider-characteristics/medicare-provider-supplier-enrollment/opt-out-affidavits (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly
- **Size Estimate**: ~30,000-50,000 rows; <10 MB
- **Key Fields**: `NPI`, `First_Name`, `Last_Name`, `Specialty`, `Optout_Effective_Date`, `Optout_End_Date`, `Order_Referring_Eligible`
- **What It Contains**: List of physicians and practitioners who have formally opted out of the Medicare program. These providers have signed private contracts with Medicare beneficiaries and cannot bill Medicare (except for emergency/urgent care). Includes the provider's NPI, name, specialty, opt-out effective and end dates, and whether they are eligible to order/refer.
- **What It Does NOT Contain**: No reason for opting out. No claims data (by definition, opted-out providers do not generate Medicare claims). No patient volume data.
- **Why It Matters for Project PUF**: Important for provider universe accuracy -- these providers should be excluded from Medicare utilization analyses. Also analytically interesting: the opt-out population is growing and concentrated in psychiatry and certain specialties.
- **Dependencies**: Upstream: NPPES (NPI key). Downstream: used as an exclusion filter for Medicare provider analyses.
- **Regulatory Basis**: Social Security Act Section 1802(b); 42 CFR 405.440 -- Medicare private contracts and opt-out provisions. Balanced Budget Act of 1997 created the opt-out mechanism.

#### Verification Needed
- [ ] Confirm current download location and format
- [ ] Verify whether historical opt-out files are available or only current state
- [ ] Check if the file now includes additional fields (e.g., state of practice)

---

### 1.5 Ordering & Referring Provider File

- **Category**: Provider Identity / Enrollment
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://data.cms.gov/provider-characteristics/medicare-provider-supplier-enrollment/order-and-referring (NEEDS VERIFICATION)
- **Update Frequency**: Monthly to quarterly
- **Size Estimate**: ~1.5-2 million rows; ~100-200 MB
- **Key Fields**: `NPI`, `Last_Name`, `First_Name`, `Specialty`
- **What It Contains**: List of all providers who are eligible to order and refer items or services for Medicare beneficiaries. This is a compliance file -- providers not on this list cannot have their orders/referrals honored by Medicare. Includes the provider's NPI, name, and specialty.
- **What It Does NOT Contain**: No claims or utilization data. No practice address information. Very sparse -- essentially just a validated list of eligible NPIs.
- **Why It Matters for Project PUF**: Important for referral pattern analysis and for validating the provider universe. When analyzing DME referrals or lab orders, this file confirms which providers were eligible to make those referrals.
- **Dependencies**: Upstream: PECOS enrollment data. Downstream: validates referring NPIs in DME and lab utilization data.
- **Regulatory Basis**: ACA Section 6405 -- requirement that Medicare claims for DMEPOS, home health, and other ordered/referred services include the NPI of an eligible ordering/referring provider.

#### Verification Needed
- [ ] Confirm current download URL
- [ ] Check update frequency (monthly vs. quarterly)
- [ ] Verify whether the file includes enrollment date or just current eligibility

---

### 1.6 Medicare Deactivated NPI Report

- **Category**: Provider Identity
- **Publisher**: CMS / NPPES
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://download.cms.gov/nppes/NPI_Files.html (part of NPPES downloads) (NEEDS VERIFICATION)
- **Update Frequency**: Monthly (as part of NPPES update cycle)
- **Size Estimate**: ~3-4 million cumulative deactivated NPIs; ~50-100 MB
- **Key Fields**: `NPI`, `NPI_Deactivation_Date`, `NPI_Deactivation_Reason_Code`
- **What It Contains**: List of all NPIs that have been deactivated, including the deactivation date and reason code. Reasons include: provider deceased, business dissolved, no response to CMS correspondence, or voluntary deactivation. Some deactivated NPIs are later reactivated.
- **What It Does NOT Contain**: No detail on why the provider was deactivated beyond the reason code. No forwarding information to successor NPIs.
- **Why It Matters for Project PUF**: Essential for data quality -- deactivated NPIs should not appear in current utilization data. A deactivated NPI appearing in active claims is a potential fraud indicator.
- **Dependencies**: Upstream: NPPES. Downstream: data quality filter for all NPI-keyed datasets.
- **Regulatory Basis**: 45 CFR 162.410 -- NPI deactivation and reactivation procedures under HIPAA.

#### Verification Needed
- [ ] Confirm whether deactivation report is a separate download or embedded in the main NPPES file
- [ ] Verify deactivation reason code values
- [ ] Check if reactivated NPIs are included with reactivation dates

---

## 2. Facility & Organizational Data

---

### 2.1 Provider of Services (POS) File — Current & Historical

- **Category**: Facility / Organizational
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV (current); fixed-width text (some historical files)
- **URL**: https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-hospital-and-non-hospital-facilities (NEEDS VERIFICATION); historical files at https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/Provider-of-Services (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly (current); historical files are static snapshots
- **Size Estimate**: ~200,000-300,000 rows per quarterly file; historical archive spans 2000-present
- **Key Fields**: `CCN`, `Provider_Name`, `State_Code`, `City`, `ZIP`, `County_Code`, `Provider_Type`, `Ownership_Type`, `Bed_Count`, `Certification_Date`, `Fiscal_Year_End`, `Termination_Date`
- **What It Contains**: Complete census of all Medicare/Medicaid-certified institutional providers across all types: short-term acute care hospitals, critical access hospitals, long-term care hospitals, psychiatric hospitals, rehabilitation hospitals, skilled nursing facilities, home health agencies, hospices, ambulatory surgical centers, end-stage renal disease facilities, federally qualified health centers, rural health clinics, community mental health centers, organ procurement organizations, and more. Historical files enable longitudinal tracking of facility openings, closings, ownership changes, and bed count changes.
- **What It Does NOT Contain**: No financial data, no utilization/claims data, no quality metrics. No staffing data. Provider type classification is broad (does not capture sub-specialization within a type).
- **Why It Matters for Project PUF**: The historical POS file is irreplaceable for longitudinal facility analysis -- tracking hospital closures, ownership consolidation, and bed capacity changes over time. The current file serves as the master facility reference dimension.
- **Dependencies**: Upstream: CMS survey and certification process. Downstream: reference dimension for all CCN-keyed datasets (Cost Reports, Quality measures, Utilization PUFs).
- **Regulatory Basis**: Social Security Act Sections 1861, 1864, 1865; 42 CFR Parts 482-486.

#### Verification Needed
- [ ] Confirm availability of historical POS files and years covered
- [ ] Verify format differences between current and historical files
- [ ] Check if the "Other Facilities" file is separate from the "Hospital" file

---

### 2.2 Hospital General Information (Care Compare)

- **Category**: Facility / Organizational
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://data.cms.gov/provider-data/dataset/xubh-q36u (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly (as part of Care Compare refresh)
- **Size Estimate**: ~5,000-7,000 rows; <10 MB
- **Key Fields**: `Facility_ID` (CCN), `Facility_Name`, `Address`, `City`, `State`, `ZIP_Code`, `County_Name`, `Phone_Number`, `Hospital_Type`, `Hospital_Ownership`, `Emergency_Services`, `Hospital_Overall_Rating`
- **What It Contains**: Basic profile information for all Medicare-certified hospitals, including name, address, phone, hospital type (acute care, critical access, psychiatric, children's, VA), ownership type (government-federal/state/local, proprietary, church, non-profit), whether emergency services are available, and the overall hospital star rating.
- **What It Does NOT Contain**: No financial data, no detailed utilization, no individual quality measures (those are in separate Care Compare files). No bed counts (those are in POS).
- **Why It Matters for Project PUF**: Clean, consumer-friendly hospital reference file. The hospital type and ownership classifications are useful for stratifying analyses. The overall star rating provides a quick quality indicator.
- **Dependencies**: Upstream: POS file (CCN source), CMS Star Ratings methodology. Downstream: enriches all hospital-level analyses.
- **Regulatory Basis**: ACA Section 3001 -- Hospital Value-Based Purchasing; CMS hospital star rating methodology.

#### Verification Needed
- [ ] Confirm dataset identifier on data.cms.gov
- [ ] Verify whether this file includes all hospital types or only acute care
- [ ] Check if the overall star rating field is still included in this file or moved

---

### 2.3 CMS CASPER (Certification and Survey Provider Enhanced Reports)

- **Category**: Facility / Organizational / Quality
- **Publisher**: CMS (via state survey agencies)
- **Access Level**: Public (some reports); some require FOIA request
- **Format**: CSV / fixed-width / PDF (varies by report type)
- **URL**: https://data.cms.gov/provider-characteristics/ (various datasets) (NEEDS VERIFICATION); CASPER data also distributed through OSCAR (Online Survey, Certification, and Reporting system)
- **Update Frequency**: Varies by provider type; survey data updated as surveys are completed
- **Size Estimate**: Varies widely by report type; nursing home CASPER data alone is several hundred MB
- **Key Fields**: `CCN`, `Survey_Date`, `Deficiency_Code`, `Scope_Severity`, `Provider_Type`, `Bed_Count`, `Resident_Count`
- **What It Contains**: Survey and certification data from state health department inspections of Medicare/Medicaid-certified facilities. For nursing homes, this is the most detailed public source of deficiency citations, complaint investigations, and certification status. Includes deficiency codes, scope/severity ratings, plans of correction, and survey dates. For hospitals and other facility types, survey data is less publicly available.
- **What It Does NOT Contain**: Raw survey reports (narratives) are generally available only through FOIA. Does not include financial data or claims data.
- **Why It Matters for Project PUF**: Critical for quality analysis, especially for nursing homes. Deficiency data is the basis for CMS's Five-Star Quality Rating system. Understanding survey findings contextualizes quality scores.
- **Dependencies**: Upstream: state survey agency inspections. Downstream: feeds into Five-Star ratings, Care Compare quality data, and nursing home penalty data.
- **Regulatory Basis**: Social Security Act Section 1819 (SNFs), Section 1861 (hospitals); 42 CFR Parts 488, 489 -- survey and certification procedures.

#### Verification Needed
- [ ] Clarify which CASPER/OSCAR data is freely downloadable vs. requires FOIA
- [ ] Confirm current terminology (CASPER vs. iQIES transition)
- [ ] Verify availability of hospital survey data vs. nursing home survey data
- [ ] Check if CMS has transitioned from CASPER to the iQIES system and what that means for data access

---

### 2.4 Skilled Nursing Facility (SNF) Provider Data

- **Category**: Facility / Organizational
- **Publisher**: CMS (Nursing Home Compare / Care Compare)
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://data.cms.gov/provider-data/topics/nursing-homes (NEEDS VERIFICATION)
- **Update Frequency**: Monthly to quarterly
- **Size Estimate**: ~15,000-16,000 facilities; multiple files totaling ~200-500 MB
- **Key Fields**: `Federal_Provider_Number` (CCN), `Provider_Name`, `Provider_Address`, `Provider_State`, `Overall_Rating`, `Health_Inspection_Rating`, `Staffing_Rating`, `Quality_Measure_Rating`, `Ownership_Type`, `Number_of_Certified_Beds`, `Number_of_Residents`
- **What It Contains**: Comprehensive facility-level data for all Medicare/Medicaid-certified nursing homes. Multiple files cover: provider information, health inspection deficiencies, staffing levels (RN, LPN, CNA hours per resident day), quality measures (falls, pressure ulcers, UTIs, etc.), penalty history (fines, payment denials), and ownership information including multi-facility chains.
- **What It Does NOT Contain**: No individual resident/patient data. No claims data. Staffing data is from Payroll-Based Journal (PBJ) but aggregated to facility level.
- **Why It Matters for Project PUF**: Nursing homes are a major spending category and frequent target of policy reform. This data enables quality-staffing-spending triangulation when combined with SNF cost reports and utilization data.
- **Dependencies**: Upstream: CASPER/iQIES survey data, PBJ staffing data, MDS quality measures. Downstream: enriches SNF utilization and cost report analyses.
- **Regulatory Basis**: Nursing Home Reform Act of 1987 (OBRA '87); ACA Section 6104 (staffing disclosure); 42 CFR Part 483 -- Requirements for Long-Term Care Facilities.

#### Verification Needed
- [ ] Confirm current Care Compare nursing home data file structure
- [ ] Verify PBJ staffing data availability in downloadable format
- [ ] Check if ownership/chain data is still included in public files
- [ ] Confirm penalty data availability and format

---

### 2.5 Home Health Agency (HHA) Provider Data

- **Category**: Facility / Organizational
- **Publisher**: CMS (Home Health Compare / Care Compare)
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://data.cms.gov/provider-data/topics/home-health-services (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly
- **Size Estimate**: ~10,000-12,000 agencies; ~50-100 MB
- **Key Fields**: `CCN`, `Provider_Name`, `State`, `City`, `ZIP`, `Quality_of_Patient_Care_Star_Rating`, `Offers_Nursing_Care`, `Offers_Physical_Therapy`, `Type_of_Ownership`
- **What It Contains**: Provider information and quality measures for all Medicare-certified home health agencies. Includes patient experience (HHCAHPS), quality of care measures (timely initiation, improvement in mobility, etc.), and agency characteristics.
- **What It Does NOT Contain**: No claims data, no episode-level detail, no patient-level data. Does not include non-Medicare home health activity.
- **Why It Matters for Project PUF**: Home health is a key post-acute care setting. Agency-level quality data combined with HHA utilization PUFs and cost reports enables comprehensive post-acute analysis.
- **Dependencies**: Upstream: OASIS assessments, HHCAHPS surveys. Downstream: enriches HHA utilization and cost analyses.
- **Regulatory Basis**: Social Security Act Section 1895 (HHA PPS); ACA Section 3131; 42 CFR Part 484 -- Conditions of Participation for Home Health Agencies.

#### Verification Needed
- [ ] Confirm current Care Compare HHA data structure
- [ ] Verify HHCAHPS data availability in downloadable format
- [ ] Check if OASIS-derived quality measures are all publicly available

---

### 2.6 Hospice Provider Data

- **Category**: Facility / Organizational
- **Publisher**: CMS (Hospice Compare / Care Compare)
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://data.cms.gov/provider-data/topics/hospice-care (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly
- **Size Estimate**: ~5,000-6,000 hospices; ~20-50 MB
- **Key Fields**: `CCN`, `Facility_Name`, `State`, `Measure_Code`, `Score`
- **What It Contains**: Provider information and quality measures for all Medicare-certified hospice providers. Includes CAHPS Hospice Survey results, Hospice Item Set (HIS) quality measures (pain screening, dyspnea treatment, etc.), and general provider information.
- **What It Does NOT Contain**: No claims data, no patient-level data, no length-of-stay distributions. Does not capture hospice revocation or live discharge rates in easily accessible form.
- **Why It Matters for Project PUF**: Hospice is the fastest-growing Medicare benefit. Quality data combined with hospice utilization and cost reports enables end-of-life care analysis.
- **Dependencies**: Upstream: HIS assessments, CAHPS Hospice Survey. Downstream: enriches hospice utilization and cost analyses.
- **Regulatory Basis**: Social Security Act Section 1814(a)(7); 42 CFR Part 418 -- Conditions of Participation for Hospice Care.

#### Verification Needed
- [ ] Confirm current Care Compare hospice data structure
- [ ] Verify whether CAHPS Hospice data is included in downloadable files
- [ ] Check availability of HIS-derived quality measures

---

### 2.7 Dialysis Facility Data

- **Category**: Facility / Organizational
- **Publisher**: CMS (Dialysis Facility Compare / Care Compare)
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://data.cms.gov/provider-data/topics/dialysis-facilities (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly
- **Size Estimate**: ~7,500-8,000 facilities; ~50-100 MB
- **Key Fields**: `CCN`, `Facility_Name`, `State`, `Five_Star_Rating`, `Patient_Transfusion_Rate`, `Kt/V_Dialysis_Adequacy`, `Infection_Rate`, `Network`, `Chain_Owned`
- **What It Contains**: Provider information and quality measures for all Medicare-certified ESRD (End-Stage Renal Disease) dialysis facilities. Includes clinical quality measures (dialysis adequacy, anemia management, infection rates, mortality, hospitalization), patient survey data, and facility characteristics including whether the facility is chain-owned (relevant given DaVita/Fresenius market dominance).
- **What It Does NOT Contain**: No individual patient data, no claims data, no detailed treatment records. Does not capture home dialysis vs. in-center modality mix in easily accessible form.
- **Why It Matters for Project PUF**: ESRD is the only condition-based Medicare entitlement. Dialysis is highly concentrated (two companies control ~70% of facilities). Quality-cost analysis in this domain has direct policy implications.
- **Dependencies**: Upstream: CROWNWeb clinical data, facility surveys, ESRD Network data. Downstream: enriches ESRD-specific cost and utilization analyses.
- **Regulatory Basis**: Social Security Act Section 1881 -- ESRD provisions; 42 CFR Part 494 -- Conditions for Coverage for ESRD Facilities.

#### Verification Needed
- [ ] Confirm current Care Compare dialysis data structure
- [ ] Verify whether chain ownership data is still included
- [ ] Check availability of modality-specific (home vs. in-center) data

---

### 2.8 Nursing Home Staffing Data (Payroll-Based Journal)

- **Category**: Facility / Organizational / Staffing
- **Publisher**: CMS
- **Access Level**: Fully Public (aggregated); raw PBJ submissions are not public
- **Format**: CSV
- **URL**: https://data.cms.gov/quality-of-care/payroll-based-journal-daily-nurse-staffing (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly
- **Size Estimate**: ~15,000 facilities x 365 days = ~5.5 million rows per year for daily data; ~2-5 GB
- **Key Fields**: `CCN`, `Work_Date`, `Hours_per_Resident_per_Day` (by staff type: RN, LPN, CNA, PT, OT), `MDScensus` (resident count)
- **What It Contains**: Daily staffing levels for all Medicare/Medicaid-certified nursing homes, derived from Payroll-Based Journal electronic submissions. Staff categories include registered nurses, licensed practical nurses, certified nursing assistants, physical therapists, and other staff types. Data is reported as hours per resident per day, allowing comparison across facility sizes.
- **What It Does NOT Contain**: No individual staff identifiers, no wage data, no agency/contract staffing detail (this is a known limitation -- facilities may underreport contract staff). No weekend-specific staffing breakdowns in summary files.
- **Why It Matters for Project PUF**: Staffing is the strongest predictor of nursing home quality. This dataset, combined with quality measures and cost reports, enables the staffing-quality-cost triangle analysis that drives policy.
- **Dependencies**: Upstream: PBJ electronic submissions from facilities. Downstream: feeds Five-Star staffing component, enables staffing-quality correlation analyses.
- **Regulatory Basis**: ACA Section 6106 -- requirement for nursing facilities to submit direct care staffing information based on payroll and other verifiable auditable data.

#### Verification Needed
- [ ] Confirm daily vs. quarterly aggregation in public files
- [ ] Verify whether the daily-level PBJ data is still publicly available or only quarterly summaries
- [ ] Check if contract/agency staffing is now separately reported

---

## 3. Code Systems & Terminologies

---

### 3.1 ICD-10-CM (International Classification of Diseases, 10th Revision, Clinical Modification)

- **Category**: Code System / Diagnosis
- **Publisher**: CDC (National Center for Health Statistics) in cooperation with CMS
- **Access Level**: Fully Public
- **Format**: XML, TXT (tabular list), PDF (coding guidelines); ZIP archive containing multiple files
- **URL**: https://www.cms.gov/medicare/coding-billing/icd-10-codes (NEEDS VERIFICATION); also at https://www.cdc.gov/nchs/icd/icd-10-cm.htm (NEEDS VERIFICATION)
- **Update Frequency**: Annual (effective October 1 each fiscal year)
- **Size Estimate**: ~72,000+ diagnosis codes; code table files are ~10-30 MB
- **Key Fields**: `ICD-10-CM_Code`, `Description` (short and long), `Chapter`, `Code_Range`, `Valid_for_Reporting_Flag`
- **What It Contains**: The complete set of diagnosis codes used in the U.S. healthcare system for morbidity coding. Includes the tabular list of all codes with descriptions, the alphabetic index, coding guidelines, and General Equivalence Mappings (GEMs) that crosswalk between ICD-9-CM and ICD-10-CM. Each annual release includes new, revised, and deleted codes.
- **What It Does NOT Contain**: Not a clinical terminology -- codes are designed for classification, not for capturing clinical detail. Does not include external cause codes in all contexts. GEMs are approximate, not exact equivalences.
- **Why It Matters for Project PUF**: Diagnosis codes appear in virtually every claims dataset. ICD-10-CM is the lookup table that translates diagnosis codes into human-readable conditions. Essential for any condition-based analysis.
- **Dependencies**: Upstream: WHO ICD-10 (international base). Downstream: used by all claims data, Chronic Conditions algorithms, CMS-HCC risk adjustment, DRG grouper logic.
- **Regulatory Basis**: HIPAA (1996) mandated ICD-10 adoption; final rule published January 2009; effective October 1, 2015 (after multiple delays).

#### Verification Needed
- [ ] Confirm current FY2026 code file download location
- [ ] Verify GEMs file availability and format
- [ ] Check if CMS still publishes code table files separately from CDC

---

### 3.2 ICD-10-PCS (International Classification of Diseases, 10th Revision, Procedure Coding System)

- **Category**: Code System / Procedure (Inpatient)
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: XML, TXT (tabular list), PDF; ZIP archive
- **URL**: https://www.cms.gov/medicare/coding-billing/icd-10-codes/icd-10-pcs (NEEDS VERIFICATION)
- **Update Frequency**: Annual (effective October 1 each fiscal year)
- **Size Estimate**: ~78,000+ procedure codes; ~10-30 MB
- **Key Fields**: `ICD-10-PCS_Code` (7-character alphanumeric), `Description`, `Section`, `Body_System`, `Root_Operation`, `Body_Part`, `Approach`, `Device`, `Qualifier`
- **What It Contains**: The complete set of inpatient procedure codes used in the U.S. ICD-10-PCS has a 7-character structure where each character position has a defined meaning (section, body system, root operation, body part, approach, device, qualifier). Includes code tables organized by the first three characters, definitions of root operations, and coding guidelines.
- **What It Does NOT Contain**: Only used for inpatient hospital settings. Outpatient procedures use CPT/HCPCS. Does not include physician services. Not used internationally (PCS is a U.S.-only system, unlike ICD-10-CM which derives from WHO ICD-10).
- **Why It Matters for Project PUF**: Required for interpreting inpatient claims data. Procedure codes drive DRG assignment, which determines hospital payment. Essential for surgical volume analysis and hospital case-mix assessment.
- **Dependencies**: Upstream: CMS development (no WHO base unlike ICD-10-CM). Downstream: feeds MS-DRG grouper logic, inpatient claims analysis.
- **Regulatory Basis**: HIPAA (1996) mandated ICD-10-PCS adoption for inpatient procedures; same implementation timeline as ICD-10-CM.

#### Verification Needed
- [ ] Confirm current FY2026 PCS file download location
- [ ] Verify whether code tables are available in machine-readable format (XML/CSV) vs. PDF only
- [ ] Check for PCS-to-PCS year-over-year crosswalk availability

---

### 3.3 HCPCS Level I (CPT -- Current Procedural Terminology)

- **Category**: Code System / Procedure (Outpatient/Physician)
- **Publisher**: American Medical Association (AMA)
- **Access Level**: PROPRIETARY -- AMA copyright; requires license/purchase
- **Format**: Various (AMA sells digital files); CMS publishes limited CPT data within fee schedule files
- **URL**: https://www.ama-assn.org/practice-management/cpt (AMA); CMS includes CPT codes and short descriptions in MPFS and OPPS files
- **Update Frequency**: Annual (new edition each January, with mid-year Category III updates)
- **Size Estimate**: ~10,000+ codes (Category I, II, III); AMA file sizes vary
- **Key Fields**: `CPT_Code` (5-digit numeric), `Short_Description`, `Long_Description`, `Category` (I, II, III)
- **What It Contains**: The complete set of procedure codes for physician and outpatient services. CPT Category I covers standard medical/surgical/diagnostic procedures. Category II covers performance measurement. Category III covers emerging technology. CPT is the standard for physician billing, outpatient hospital billing, and ambulatory surgical center billing.
- **What It Does NOT Contain**: CPT descriptions beyond short descriptors are NOT freely available. The full CPT codebook requires AMA license. CMS publishes CPT codes in its fee schedules but with truncated descriptions due to licensing constraints.
- **Why It Matters for Project PUF**: CPT/HCPCS Level I codes appear in Part B Utilization, OPPS, ASC, and other outpatient datasets. However, the licensing restriction means Project PUF cannot freely distribute full CPT descriptions. Must use HCPCS Level II (free) and CMS-published short descriptions.
- **Dependencies**: Upstream: AMA CPT Editorial Panel. Downstream: used in MPFS, Part B claims, OPPS, ASC payment systems.
- **Regulatory Basis**: HIPAA mandated CPT as the standard code set for physician services. AMA holds copyright. CMS has a license to use CPT in its payment systems but short descriptions only in public files.

#### LICENSING WARNING
CPT is AMA-copyrighted. Project PUF CANNOT redistribute full CPT descriptions without a license. CMS-published short descriptions in fee schedule files are usable. Consider using HCPCS Level II codes (freely available) as the primary procedure code reference and CPT short descriptions from CMS files where available.

#### Verification Needed
- [ ] Verify current AMA licensing terms and costs
- [ ] Confirm that CMS fee schedule files still include CPT short descriptions
- [ ] Check if any open-source CPT description alternatives exist (unlikely)

---

### 3.4 HCPCS Level II (Healthcare Common Procedure Coding System, Level II)

- **Category**: Code System / Procedure / Supply
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV / fixed-width text; ZIP archive
- **URL**: https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system/hcpcs-level-ii-coding-procedures-supplies (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly (with annual major release January 1)
- **Size Estimate**: ~7,000-8,000 codes; ~5-10 MB
- **Key Fields**: `HCPCS_Code` (alpha + 4 digits, e.g., J0120), `Long_Description`, `Short_Description`, `Status_Code`, `Action_Code`, `Effective_Date`, `Termination_Date`, `Pricing_Indicator`, `Coverage_Code`
- **What It Contains**: Codes for products, supplies, and services not covered by CPT (Level I), including: durable medical equipment (DME), prosthetics and orthotics, ambulance services, injectable drugs (J-codes), temporary codes (G-codes, Q-codes), and other items. Unlike CPT, HCPCS Level II is maintained by CMS and is FREELY AVAILABLE with full descriptions.
- **What It Does NOT Contain**: Does not cover procedures that are in CPT (physician services, surgeries). Code descriptions are for billing classification, not clinical detail.
- **Why It Matters for Project PUF**: This is the freely available complement to proprietary CPT codes. HCPCS Level II codes appear extensively in DME data, Part B drug claims (J-codes), and outpatient data. G-codes are used by CMS for quality reporting and special payment rules.
- **Dependencies**: Upstream: CMS HCPCS workgroup. Downstream: used in DME fee schedule, ASP drug pricing, Part B claims, OPPS.
- **Regulatory Basis**: HIPAA mandated HCPCS as the standard code set alongside CPT. Social Security Act Section 1848(c)(5) authorizes CMS to establish coding systems.

#### Verification Needed
- [ ] Confirm current download URL and file format
- [ ] Verify whether quarterly updates are additive or full replacement
- [ ] Check if CMS provides a HCPCS-to-HCPCS year-over-year crosswalk

---

### 3.5 NDC (National Drug Codes) -- FDA NDC Directory

- **Category**: Code System / Drug
- **Publisher**: FDA (Food and Drug Administration)
- **Access Level**: Fully Public
- **Format**: CSV / text (delimited); also available via openFDA API
- **URL**: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory (NEEDS VERIFICATION); API at https://open.fda.gov/apis/drug/ndc/ (NEEDS VERIFICATION)
- **Update Frequency**: Updated continuously (real-time); bulk file refreshed daily to weekly
- **Size Estimate**: ~300,000+ active NDC records; product and package files total ~50-100 MB
- **Key Fields**: `NDC` (10-digit in 4-4-2, 5-3-2, or 5-4-1 format), `Proprietary_Name` (brand name), `Nonproprietary_Name` (generic name), `Dosage_Form`, `Route`, `Labeler_Name` (manufacturer/distributor), `Product_Type`, `Marketing_Category`, `DEA_Schedule`, `Package_Description`
- **What It Contains**: Two primary files -- Products (drug formulations) and Packages (specific package sizes/types). Each drug product is identified by a unique NDC consisting of labeler code, product code, and package code. Includes brand and generic names, dosage form, route of administration, active ingredients with strengths, manufacturer, marketing status, and DEA schedule for controlled substances.
- **What It Does NOT Contain**: No pricing data. No clinical efficacy information. No prescribing volume data. NDC format inconsistencies (10-digit vs. 11-digit, hyphenation) are a notorious data quality challenge.
- **Why It Matters for Project PUF**: NDC is the drug identifier used in Part D claims, Medicaid State Drug Utilization Data, hospital charge data, and ASP drug pricing files. It bridges drug identification across multiple datasets. Critical for drug cost and utilization analysis.
- **Dependencies**: Upstream: FDA drug approval process. Downstream: used in Part D claims, SDUD, ASP pricing, drug spending analyses. Crosswalks to RxNorm for clinical drug classification.
- **Regulatory Basis**: Federal Food, Drug, and Cosmetic Act; Drug Listing Act of 1972 (21 CFR Part 207).

#### Verification Needed
- [ ] Confirm current bulk download URL and format
- [ ] Verify NDC format standardization (10-digit vs. 11-digit issues)
- [ ] Check openFDA API rate limits and data completeness
- [ ] Confirm whether the NDC Directory includes all marketed drugs or only those actively listed

---

### 3.6 MS-DRG (Medicare Severity Diagnosis Related Groups) Definitions and Grouper Logic

- **Category**: Code System / Payment Classification (Inpatient)
- **Publisher**: CMS
- **Access Level**: Fully Public (definitions, weights, logic); grouper software is available from CMS and from NTIS
- **Format**: TXT / CSV (definitions, weights); software (ICD-10 MS-DRG Grouper); PDF (definitions manual)
- **URL**: https://www.cms.gov/medicare/payment/prospective-payment-systems/acute-inpatient-pps/ms-drg-classifications-and-software (NEEDS VERIFICATION)
- **Update Frequency**: Annual (effective October 1 each fiscal year, published with IPPS final rule)
- **Size Estimate**: ~750-800 MS-DRGs; definitions manual is ~2,500 pages; weight table is <1 MB
- **Key Fields**: `MS-DRG`, `Description`, `Relative_Weight`, `Geometric_Mean_LOS`, `Arithmetic_Mean_LOS`, `MDC` (Major Diagnostic Category), `Type` (Medical/Surgical/Other)
- **What It Contains**: Complete definitions for all MS-DRGs including: the diagnosis and procedure code combinations that map to each DRG, relative weights (which determine payment), mean and median length of stay statistics, Major Diagnostic Category assignments, and the grouper logic (decision trees) used to assign claims to DRGs. The grouper software itself is available for download.
- **What It Does NOT Contain**: Actual payment amounts (those depend on hospital-specific factors like wage index, DSH adjustment, IME adjustment). Does not include APR-DRGs (those are 3M proprietary).
- **Why It Matters for Project PUF**: MS-DRGs are the unit of analysis for all inpatient hospital payment analysis. The relative weights translate DRG codes in claims data into resource intensity measures. Essential for case-mix adjustment and hospital payment modeling.
- **Dependencies**: Upstream: ICD-10-CM and ICD-10-PCS code sets. Downstream: used in IPPS payment calculations, Inpatient Hospital PUF, Cost Report analysis.
- **Regulatory Basis**: Social Security Act Section 1886(d) -- Inpatient Prospective Payment System. Published annually in the Federal Register IPPS Final Rule.

#### Verification Needed
- [ ] Confirm current FY2026 MS-DRG version download location
- [ ] Verify grouper software availability and format (mainframe vs. PC)
- [ ] Check if CMS provides machine-readable DRG definition tables or only PDF manual

---

### 3.7 APR-DRG (All Patient Refined DRGs)

- **Category**: Code System / Payment Classification
- **Publisher**: 3M Health Information Systems
- **Access Level**: PROPRIETARY -- requires 3M license
- **Format**: Proprietary software and documentation
- **URL**: https://www.3m.com (3M HIS website) (NEEDS VERIFICATION)
- **Update Frequency**: Annual
- **Size Estimate**: ~1,500+ APR-DRG base categories with 4 severity and 4 mortality subclasses
- **Key Fields**: `APR-DRG`, `Severity_of_Illness`, `Risk_of_Mortality`, `Description`
- **What It Contains**: An alternative DRG system that classifies ALL patients (not just Medicare), with additional severity of illness and risk of mortality subclasses. Used by many state hospital reporting systems, Medicaid programs, and commercial payers.
- **What It Does NOT Contain**: Not publicly available. Cannot be redistributed without 3M license.
- **Why It Matters for Project PUF**: Important to document as a limitation. Many state-level hospital datasets use APR-DRGs. HCUP uses APR-DRGs. Project PUF cannot include APR-DRG logic without licensing.
- **Dependencies**: Upstream: ICD-10-CM/PCS codes. Downstream: used in state discharge data, HCUP, some Medicaid programs.
- **Regulatory Basis**: No federal mandate; adopted by individual states and payers by choice.

#### LICENSING WARNING
APR-DRGs are 3M proprietary. Project PUF CANNOT use APR-DRG definitions or grouper logic without a commercial license. Use MS-DRGs (free from CMS) as the primary inpatient classification system.

#### Verification Needed
- [ ] Confirm current 3M licensing terms and whether academic/research licenses exist
- [ ] Check if any states publish APR-DRG-classified data that is publicly available

---

### 3.8 APC (Ambulatory Payment Classifications)

- **Category**: Code System / Payment Classification (Outpatient)
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV / TXT; ZIP archive (part of OPPS files)
- **URL**: https://www.cms.gov/medicare/payment/prospective-payment-systems/hospital-outpatient/addendum-a-b-updates (NEEDS VERIFICATION)
- **Update Frequency**: Annual (effective January 1; published with OPPS final rule); quarterly updates
- **Size Estimate**: ~5,000+ status indicator / APC assignments; Addendum A and B files ~5-10 MB
- **Key Fields**: `HCPCS_Code`, `Short_Descriptor`, `Status_Indicator`, `APC`, `Relative_Weight`, `Payment_Rate`, `National_Unadjusted_Copayment`
- **What It Contains**: The mapping of HCPCS/CPT codes to Ambulatory Payment Classifications, which is how CMS pays hospital outpatient departments. Includes APC assignments, relative weights, payment rates, status indicators (which determine whether a service is paid separately, packaged, or unconditionally packaged), and copayment amounts.
- **What It Does NOT Contain**: Not used for physician services (those use MPFS/RVUs). Not used for non-hospital outpatient settings (ASCs have a separate payment system). Does not include hospital-specific adjustments (wage index, outlier payments).
- **Why It Matters for Project PUF**: APCs are the outpatient equivalent of DRGs. Understanding APC assignments is essential for analyzing outpatient hospital payment, procedure profitability, and the impact of OPPS policy changes.
- **Dependencies**: Upstream: HCPCS/CPT codes, OPPS final rule. Downstream: used in outpatient claims analysis, hospital financial modeling.
- **Regulatory Basis**: Social Security Act Section 1833(t) -- Outpatient Prospective Payment System. Published annually in the Federal Register OPPS Final Rule.

#### Verification Needed
- [ ] Confirm current CY2026 OPPS addendum file locations
- [ ] Verify whether Addendum A (APCs) and Addendum B (HCPCS-to-APC mapping) are both downloadable
- [ ] Check for machine-readable format (CSV vs. Excel vs. fixed-width)

---

### 3.9 NUCC Health Care Provider Taxonomy Codes

- **Category**: Code System / Provider Classification
- **Publisher**: NUCC (National Uniform Claim Committee), maintained by AMA secretariat
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://nucc.org/index.php/code-sets-mainmenu-41/provider-taxonomy-mainmenu-40 (NEEDS VERIFICATION)
- **Update Frequency**: Twice annually (April and July)
- **Size Estimate**: ~900+ taxonomy codes; <5 MB
- **Key Fields**: `Code` (10-character alphanumeric), `Grouping`, `Classification`, `Specialization`, `Definition`
- **What It Contains**: Hierarchical classification of healthcare providers by type and specialty. The taxonomy code has three levels: Grouping (broad category like "Allopathic & Osteopathic Physicians"), Classification (specialty like "Internal Medicine"), and Specialization (sub-specialty like "Cardiovascular Disease"). Each NPPES record can have up to 15 taxonomy codes.
- **What It Does NOT Contain**: Not a credentialing system. Does not validate that a provider is board-certified in their claimed specialty. Does not include CMS specialty codes (those are a separate, smaller classification).
- **Why It Matters for Project PUF**: Essential reference table for interpreting NPPES taxonomy codes. Enables granular specialty analysis beyond the broad CMS specialty categories used in utilization PUFs.
- **Dependencies**: Upstream: NUCC maintenance process. Downstream: maps to NPPES taxonomy code fields; used for provider specialty stratification across all analyses.
- **Regulatory Basis**: HIPAA mandated standard provider taxonomy codes; NUCC taxonomy adopted as the standard under 45 CFR 162.

#### Verification Needed
- [ ] Confirm current download URL and format
- [ ] Verify update frequency (twice annual or more frequent)
- [ ] Check if NUCC provides historical versions for longitudinal mapping

---

### 3.10 RxNorm (NLM)

- **Category**: Code System / Drug Terminology
- **Publisher**: NLM (National Library of Medicine)
- **Access Level**: Fully Public (UMLS license required for bulk download, but license is free)
- **Format**: RRF (Rich Release Format, pipe-delimited); also available via RxNorm API
- **URL**: https://www.nlm.nih.gov/research/umls/rxnorm/ (NEEDS VERIFICATION); API at https://rxnav.nlm.nih.gov/ (NEEDS VERIFICATION)
- **Update Frequency**: Weekly (full release monthly)
- **Size Estimate**: ~100,000+ concepts; full RxNorm files ~1-2 GB
- **Key Fields**: `RXCUI` (RxNorm Concept Unique Identifier), `Name`, `TTY` (term type: ingredient, brand, dose form, etc.), `Source` (originating vocabulary), NDC crosswalks
- **What It Contains**: Normalized drug naming system that provides standard names for clinical drugs and links to all drug vocabularies used in pharmacy management and drug interaction software. Maps between NDC, brand names, generic names, ingredients, dose forms, and strengths. The RxNorm API provides drug interaction checking and concept navigation.
- **What It Does NOT Contain**: No pricing data. No clinical efficacy or safety data beyond what's encoded in drug class relationships. Not a formulary system.
- **Why It Matters for Project PUF**: The Rosetta Stone for drug data. Bridges the NDC (FDA), drug names in Part D PUFs, and clinical drug classifications. Essential for normalizing drug names across datasets that use different naming conventions.
- **Dependencies**: Upstream: FDA NDC, First Databank, Micromedex, and other source vocabularies. Downstream: enables drug name normalization across Part D, SDUD, ASP pricing files.
- **Regulatory Basis**: NLM is authorized under 42 USC 286 to build and distribute biomedical vocabularies. RxNorm is designated as a federal standard for electronic prescribing under the Medicare Modernization Act (MMA) of 2003.

#### Verification Needed
- [ ] Confirm UMLS license is still free for bulk download
- [ ] Verify RxNorm API rate limits and availability
- [ ] Check current NDC-to-RxCUI crosswalk completeness

---

### 3.11 LOINC (Logical Observation Identifiers Names and Codes)

- **Category**: Code System / Lab & Clinical Observations
- **Publisher**: Regenstrief Institute
- **Access Level**: Fully Public (free license; requires registration and acceptance of terms)
- **Format**: CSV / ZIP archive
- **URL**: https://loinc.org/ (NEEDS VERIFICATION)
- **Update Frequency**: Semi-annual (February and August)
- **Size Estimate**: ~100,000+ observation codes; ~200-500 MB for complete download
- **Key Fields**: `LOINC_NUM`, `Component`, `Property`, `Time_Aspct`, `System`, `Scale_Typ`, `Method_Typ`, `Long_Common_Name`, `Short_Name`, `Class`
- **What It Contains**: Universal codes for identifying laboratory tests and clinical observations. Each LOINC code specifies the combination of: what is measured (component), the property measured (mass concentration, enzyme activity, etc.), the timing (point in time, 24-hour), the specimen type (blood, urine, etc.), the scale (quantitative, qualitative, ordinal), and the method. Also includes LOINC codes for clinical documents, survey instruments, and public health reporting.
- **What It Does NOT Contain**: No test results or patient data. No reference ranges. Not a test catalog (individual labs have their own test menus). Does not include proprietary lab panel definitions.
- **Why It Matters for Project PUF**: LOINC codes appear in clinical quality measures, EHR data, and public health reporting. Less directly relevant to claims-based analysis but critical if Project PUF expands to clinical data integration.
- **Dependencies**: Upstream: Regenstrief maintenance. Downstream: used in quality measures, EHR interoperability, public health reporting.
- **Regulatory Basis**: Meaningful Use (now Promoting Interoperability) regulations require LOINC for lab results. ONC Health IT Certification requires LOINC support.

#### Verification Needed
- [ ] Confirm registration and download process
- [ ] Verify current version and release schedule
- [ ] Check if LOINC-to-CPT crosswalk is available for lab procedure mapping

---

### 3.12 SNOMED CT (Systematized Nomenclature of Medicine -- Clinical Terms)

- **Category**: Code System / Clinical Terminology
- **Publisher**: NLM (U.S. distributor); SNOMED International (international maintainer)
- **Access Level**: Free in the U.S. (UMLS license required; license is free for U.S. users)
- **Format**: RF2 (Release Format 2, tab-delimited); also accessible via UMLS API
- **URL**: https://www.nlm.nih.gov/healthit/snomedct/ (NEEDS VERIFICATION)
- **Update Frequency**: Biannual international release (January and July); U.S. extension released separately
- **Size Estimate**: ~350,000+ active concepts; full release ~1-3 GB
- **Key Fields**: `SCTID` (SNOMED CT Identifier), `Fully_Specified_Name`, `Preferred_Term`, `Semantic_Tag`, `Hierarchy` (finding, procedure, body structure, etc.)
- **What It Contains**: The most comprehensive clinical terminology system, covering clinical findings, procedures, body structures, organisms, substances, pharmaceutical products, and more. SNOMED CT provides a concept-based ontology with formal logic definitions and hierarchical relationships. Used in EHRs for clinical documentation.
- **What It Does NOT Contain**: Not a billing code system. Not used directly in claims processing. Complex to implement and query compared to flat code lists.
- **Why It Matters for Project PUF**: Lower priority for claims-based analysis but critical for future EHR data integration. SNOMED CT-to-ICD-10-CM mappings exist and can bridge clinical and billing data. Important for quality measure logic which often references SNOMED concepts.
- **Dependencies**: Upstream: SNOMED International, NLM. Downstream: maps to ICD-10-CM, used in quality measures, EHR interoperability.
- **Regulatory Basis**: Designated as a standard terminology under Meaningful Use / Promoting Interoperability regulations. 45 CFR 170 (ONC Health IT Certification).

#### Verification Needed
- [ ] Confirm UMLS license covers SNOMED CT bulk download
- [ ] Verify U.S. SNOMED CT extension availability and content
- [ ] Check SNOMED-to-ICD-10-CM map availability and quality

---

### 3.13 CMS Place of Service Codes

- **Category**: Code System / Administrative
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: PDF / CSV (embedded in other files)
- **URL**: https://www.cms.gov/medicare/coding-billing/place-of-service-codes (NEEDS VERIFICATION)
- **Update Frequency**: Ad hoc (updated as new settings are recognized)
- **Size Estimate**: ~100 codes; <1 MB
- **Key Fields**: `POS_Code` (2-digit), `POS_Name`, `POS_Description`
- **What It Contains**: Two-digit codes identifying the setting where a healthcare service was delivered. Examples: 11 = Office, 21 = Inpatient Hospital, 22 = On Campus-Outpatient Hospital, 23 = Emergency Room-Hospital, 31 = Skilled Nursing Facility, 02 = Telehealth (added/expanded recently). Used on professional claims (CMS-1500).
- **What It Does NOT Contain**: Not a facility identifier (that's CCN). Does not indicate who provided the service, only where. Limited to Medicare-recognized settings.
- **Why It Matters for Project PUF**: Place of Service codes appear in Part B Utilization PUF and are essential for distinguishing facility vs. non-facility payment rates. Critical for telehealth utilization tracking.
- **Dependencies**: Upstream: CMS policy decisions. Downstream: used in Part B claims, MPFS payment calculations (facility vs. non-facility PE RVUs).
- **Regulatory Basis**: 42 CFR 424.32 -- claim form requirements. CMS-1500 form instructions.

#### Verification Needed
- [ ] Confirm download location (may be only PDF)
- [ ] Check if a machine-readable CSV version exists
- [ ] Verify telehealth POS code expansions since COVID-19

---

### 3.14 Revenue Codes (NUBC)

- **Category**: Code System / Institutional Billing
- **Publisher**: NUBC (National Uniform Billing Committee)
- **Access Level**: PROPRIETARY -- requires NUBC license/purchase
- **Format**: Published in the NUBC Official UB-04 Data Specifications Manual
- **URL**: https://www.nubc.org/ (NEEDS VERIFICATION)
- **Update Frequency**: Annual
- **Size Estimate**: ~600+ revenue codes
- **Key Fields**: `Revenue_Code` (4-digit), `Description`, `Category`
- **What It Contains**: Four-digit codes used on institutional claims (UB-04/837I) to identify specific accommodation, ancillary, and billing categories. Examples: 0120 = Room & Board Semi-Private, 0250 = Pharmacy, 0450 = Emergency Room, 0636 = Drugs Requiring Detailed Coding. Revenue codes appear on every institutional claim line.
- **What It Does NOT Contain**: Not freely available. The NUBC manual must be purchased. Does not describe specific services (those use HCPCS/CPT alongside the revenue code).
- **Why It Matters for Project PUF**: Revenue codes are present on all institutional claims. However, the proprietary nature limits what Project PUF can do with them. CMS cost reports and some public files reference revenue codes by number without full descriptions.
- **Dependencies**: Upstream: NUBC committee. Downstream: used on all UB-04 claims (hospital, SNF, HHA, hospice).
- **Regulatory Basis**: HIPAA mandated the UB-04 as the standard institutional claim form. Revenue codes are part of that standard.

#### LICENSING WARNING
Revenue code descriptions are NUBC proprietary. Project PUF can reference revenue code NUMBERS but cannot freely distribute the full description list. Consider building a limited reference with commonly used codes and generic descriptions.

#### Verification Needed
- [ ] Confirm NUBC licensing terms and cost
- [ ] Check if CMS publishes a partial revenue code list anywhere publicly
- [ ] Verify whether any open-source revenue code reference exists

---

### 3.15 Condition Codes, Occurrence Codes, Value Codes (UB-04)

- **Category**: Code System / Institutional Billing
- **Publisher**: NUBC
- **Access Level**: PROPRIETARY (part of NUBC UB-04 Data Specifications Manual)
- **Format**: Published in NUBC manual; CMS references some in the Medicare Claims Processing Manual
- **URL**: https://www.nubc.org/ (manual); CMS references at https://www.cms.gov/regulations-and-guidance/guidance/manuals/internet-only-manuals-ioms (NEEDS VERIFICATION)
- **Update Frequency**: Annual (NUBC manual); CMS references updated periodically
- **Size Estimate**: ~100 condition codes, ~50 occurrence codes, ~80 value codes; tiny reference tables
- **Key Fields**: `Code` (2-character), `Description`
- **What It Contains**: Condition codes describe conditions or events relating to the claim (e.g., 02 = condition is employment related, 07 = treatment of non-terminal condition for hospice patient). Occurrence codes identify significant dates (e.g., 11 = onset of symptoms, 17 = date occupational therapy plan established). Value codes carry monetary or quantitative information (e.g., 01 = most common semi-private room rate, 06 = Medicare blood deductible).
- **What It Does NOT Contain**: Full descriptions proprietary to NUBC. CMS's Medicare Claims Processing Manual documents the Medicare-relevant subset but may not be comprehensive.
- **Why It Matters for Project PUF**: These codes appear on institutional claims and in cost report data. The Medicare-relevant subsets are documented by CMS in manuals that are publicly available.
- **Dependencies**: Upstream: NUBC. Downstream: present on all UB-04 institutional claims.
- **Regulatory Basis**: HIPAA UB-04 standard.

#### Verification Needed
- [ ] Check which condition/occurrence/value codes CMS documents publicly in its manuals
- [ ] Verify whether Medicare Claims Processing Manual chapter 25 (Completing and Processing Form CMS-1450) is still the best public source

---

### 3.16 Type of Bill Codes (UB-04)

- **Category**: Code System / Institutional Billing
- **Publisher**: NUBC / CMS
- **Access Level**: Partially Public (CMS documents Medicare-relevant TOB codes; full list is NUBC proprietary)
- **Format**: Published in CMS Medicare Claims Processing Manual and NUBC manual
- **URL**: CMS manual chapters at https://www.cms.gov/regulations-and-guidance/guidance/manuals/ (NEEDS VERIFICATION)
- **Update Frequency**: Ad hoc
- **Size Estimate**: ~100+ Type of Bill combinations; tiny reference table
- **Key Fields**: `TOB` (4-digit: facility type + bill classification + frequency), `Description`
- **What It Contains**: Four-character code on institutional claims that identifies the type of facility (1st digit), type of care (2nd digit), bill classification (3rd digit), and frequency (4th digit). Examples: 011X = Hospital Inpatient, 013X = Hospital Outpatient, 021X = SNF Inpatient, 032X = Home Health. The 4th digit indicates claim frequency (1 = Admit through discharge, 7 = Replacement, etc.).
- **What It Does NOT Contain**: Full descriptions are NUBC proprietary. CMS publishes the Medicare-relevant subset.
- **Why It Matters for Project PUF**: TOB codes are the first field to examine on any institutional claim -- they tell you what kind of facility and what kind of care. Essential for filtering and routing claims data.
- **Dependencies**: Upstream: NUBC, CMS. Downstream: present on all institutional claims; determines which payment system applies.
- **Regulatory Basis**: HIPAA UB-04 standard; CMS Claims Processing Manual Chapter 25.

#### Verification Needed
- [ ] Confirm CMS manual chapter that documents TOB codes
- [ ] Check if CMS publishes a downloadable TOB reference table or only manual text

---

### 3.17 Modifier Codes (CPT/HCPCS)

- **Category**: Code System / Billing
- **Publisher**: AMA (CPT modifiers) / CMS (HCPCS Level II modifiers)
- **Access Level**: CPT modifiers are AMA proprietary; HCPCS Level II modifiers are Fully Public
- **Format**: Part of CPT codebook (proprietary) and HCPCS Level II files (public)
- **URL**: CMS HCPCS modifiers at https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system (NEEDS VERIFICATION)
- **Update Frequency**: Annual (with CPT and HCPCS updates)
- **Size Estimate**: ~100+ CPT modifiers; ~200+ HCPCS modifiers; tiny reference tables
- **Key Fields**: `Modifier` (2-character), `Description`
- **What It Contains**: Two-character codes appended to CPT/HCPCS codes to provide additional information about the service. CPT modifiers (e.g., -25 = significant, separately identifiable E/M service; -59 = distinct procedural service) modify physician services. HCPCS Level II modifiers (e.g., -LT = left side; -RT = right side; -GY = item statutorily excluded) provide additional billing context.
- **What It Does NOT Contain**: CPT modifier descriptions are AMA-copyrighted. HCPCS Level II modifier descriptions are freely available from CMS.
- **Why It Matters for Project PUF**: Modifiers affect payment and are critical for understanding billing patterns. The CMS-maintained modifiers (HCPCS Level II) are freely available and cover the most analytically important payment-affecting modifiers.
- **Dependencies**: Upstream: AMA (CPT modifiers), CMS (HCPCS modifiers). Downstream: present on all professional and outpatient claims.
- **Regulatory Basis**: HIPAA mandated CPT/HCPCS as standard code sets; modifiers are part of those standards.

#### Verification Needed
- [ ] Confirm HCPCS Level II modifier list download location
- [ ] Verify which payment-affecting modifiers CMS documents publicly

---

## 4. Fee Schedules & Payment Rules

---

### 4.1 Medicare Physician Fee Schedule (MPFS) -- Relative Value Files

- **Category**: Fee Schedule / Payment
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV / ZIP archive (multiple files: RVU file, GPCI file, anesthesia file, etc.)
- **URL**: https://www.cms.gov/medicare/payment/physician-fee-schedule (NEEDS VERIFICATION)
- **Update Frequency**: Annual (effective January 1; published with PFS final rule); quarterly updates for new/revised codes
- **Size Estimate**: ~15,000+ line items in RVU file (one per HCPCS code); multiple supplementary files; total ~50-100 MB
- **Key Fields**: `HCPCS`, `Mod` (modifier), `Description`, `Status_Code`, `Work_RVU`, `Non_Facility_PE_RVU`, `Facility_PE_RVU`, `MP_RVU` (malpractice), `Total_Non_Facility_RVU`, `Total_Facility_RVU`, `Conversion_Factor`, `Global_Surgery_Days`
- **What It Contains**: The complete Relative Value Unit (RVU) table for all physician and non-physician practitioner services. Each HCPCS code has three RVU components: Work (physician effort), Practice Expense (overhead, split into facility and non-facility), and Malpractice (liability insurance). Payment = (Work RVU x Work GPCI + PE RVU x PE GPCI + MP RVU x MP GPCI) x Conversion Factor. Also includes Geographic Practice Cost Indices (GPCIs) by Medicare locality, global surgery indicators, multiple procedure indicators, bilateral surgery indicators, and diagnostic imaging TC/26 indicators.
- **What It Does NOT Contain**: Does not include actual paid amounts (those vary by GPCI locality). Does not cover institutional services (hospitals, SNFs -- those have separate payment systems). Does not include private payer rates.
- **Why It Matters for Project PUF**: The MPFS is the foundation of physician payment in Medicare. Combined with Part B Utilization data, it enables calculation of expected payments, identification of high-value vs. low-value services, and analysis of geographic payment variation. The RVU structure is also used by many private payers.
- **Dependencies**: Upstream: CPT/HCPCS codes, AMA/Specialty Society RVS Update Committee (RUC). Downstream: determines Part B payments; essential for payment modeling, cost analysis, and price transparency.
- **Regulatory Basis**: Social Security Act Section 1848 -- Medicare payment for physicians' services. OBRA 1989 established the RBRVS-based fee schedule. Published annually in the Federal Register PFS Final Rule.

#### Verification Needed
- [ ] Confirm CY2026 RVU file download location
- [ ] Verify GPCI file format and Medicare locality definitions
- [ ] Check if CMS still provides the PPRRVU (Participating Physician Fee Schedule) file separately
- [ ] Confirm conversion factor for current year

---

### 4.2 Outpatient Prospective Payment System (OPPS) Rate Files

- **Category**: Fee Schedule / Payment (Outpatient Hospital)
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV / Excel / ZIP archive (Addendum A, B, D1, D2, E, etc.)
- **URL**: https://www.cms.gov/medicare/payment/prospective-payment-systems/hospital-outpatient (NEEDS VERIFICATION)
- **Update Frequency**: Annual (effective January 1; published with OPPS final rule); quarterly updates
- **Size Estimate**: Addendum A (APCs) ~200 rows; Addendum B (HCPCS-to-APC) ~5,000+ rows; total ~10-20 MB
- **Key Fields**: `APC`, `APC_Title`, `Relative_Weight`, `Payment_Rate`, `HCPCS_Code`, `Status_Indicator`, `Minimum_Unadjusted_Copayment`
- **What It Contains**: Complete payment rate files for the hospital outpatient PPS, including: Addendum A (APC groups with relative weights and payment rates), Addendum B (HCPCS codes with APC assignments and status indicators), Addendum D1 (pass-through drugs and biologicals), Addendum D2 (pass-through devices), Addendum E (new technology APCs), and the conversion factor. Status indicators determine how each code is paid (separately, packaged, unconditionally packaged, etc.).
- **What It Does NOT Contain**: Does not include hospital-specific payment adjustments (wage index, outlier payments, transitional corridor payments). Does not include physician professional fees.
- **Why It Matters for Project PUF**: Enables outpatient hospital payment modeling. When combined with outpatient charge data or claims, OPPS rates allow calculation of Medicare payment for each service. Essential for understanding hospital outpatient department pricing.
- **Dependencies**: Upstream: HCPCS/CPT codes, APC grouper logic. Downstream: used in outpatient claims payment, hospital financial analysis.
- **Regulatory Basis**: Social Security Act Section 1833(t) -- Outpatient PPS. Published annually in the Federal Register OPPS/ASC Final Rule.

#### Verification Needed
- [ ] Confirm CY2026 OPPS addendum file locations
- [ ] Verify all addendum types available (A through E)
- [ ] Check if quarterly update files are cumulative or incremental

---

### 4.3 Inpatient Prospective Payment System (IPPS) Rate Files -- MS-DRG Weights

- **Category**: Fee Schedule / Payment (Inpatient Hospital)
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV / Excel / ZIP archive (multiple tables from IPPS final rule)
- **URL**: https://www.cms.gov/medicare/payment/prospective-payment-systems/acute-inpatient-pps (NEEDS VERIFICATION)
- **Update Frequency**: Annual (effective October 1; published with IPPS final rule)
- **Size Estimate**: DRG weight table ~800 rows; Impact file ~3,500 hospitals; total supporting files ~50-100 MB
- **Key Fields**: `DRG`, `DRG_Description`, `Relative_Weight`, `Geometric_Mean_LOS`, `Arithmetic_Mean_LOS`, `Outlier_Threshold`; Impact file: `CCN`, `Provider_Name`, `Wage_Index`, `Case_Mix_Index`, `DSH_Percentage`, `IME_Resident_to_Bed_Ratio`, `Operating_Payment`, `Capital_Payment`
- **What It Contains**: MS-DRG relative weights (which determine the base payment for each DRG), the hospital wage index file (geographic labor cost adjustments), the Impact file (hospital-specific factors including DSH percentages, IME adjustments, case-mix indices, and estimated payments), the standardized amounts (base rates), and outlier thresholds. Together, these files fully specify how IPPS payments are calculated.
- **What It Does NOT Contain**: Actual claim-level payments (those require the full DRG grouper + all adjustments). Does not include Maryland hospitals (Maryland has a waiver from IPPS). Does not include Critical Access Hospitals (paid on cost basis, not DRG).
- **Why It Matters for Project PUF**: The IPPS is the largest Medicare payment system by dollar volume. DRG weights are essential for case-mix analysis. The Impact file provides hospital-level financial characteristics used across many analyses. Wage indices are used by multiple payment systems.
- **Dependencies**: Upstream: ICD-10 codes, MS-DRG grouper. Downstream: determines inpatient hospital payments; wage index used by OPPS, SNF PPS, HHA PPS, and other systems.
- **Regulatory Basis**: Social Security Act Section 1886(d) -- Inpatient PPS. Published annually in the Federal Register IPPS Final Rule.

#### Verification Needed
- [ ] Confirm FY2026 IPPS table download locations
- [ ] Verify Impact file format and field names
- [ ] Check if wage index file includes urban/rural reclassification details
- [ ] Confirm availability of new technology add-on payment tables

---

### 4.4 SNF PPS Rate Files

- **Category**: Fee Schedule / Payment (Skilled Nursing Facility)
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV / Excel / PDF
- **URL**: https://www.cms.gov/medicare/payment/prospective-payment-systems/skilled-nursing-facility-snf (NEEDS VERIFICATION)
- **Update Frequency**: Annual (effective October 1; published with SNF PPS final rule)
- **Size Estimate**: Rate tables ~50-100 rows (PDPM case-mix groups); <5 MB
- **Key Fields**: `PDPM_Component` (PT, OT, SLP, Nursing, Non-Case-Mix), `Case_Mix_Group`, `Case_Mix_Index`, `Per_Diem_Rate`
- **What It Contains**: Payment rates under the Patient-Driven Payment Model (PDPM), which replaced RUG-IV in FY 2020. PDPM classifies SNF stays into case-mix groups across five payment components (physical therapy, occupational therapy, speech-language pathology, nursing, and non-case-mix). Each component has its own case-mix classification and per diem rate. Also includes the SNF wage index and urban/rural base rates.
- **What It Does NOT Contain**: Does not include patient-level classification data. Does not include historical RUG-IV rates (those are archived separately). Does not cover non-Medicare SNF stays.
- **Why It Matters for Project PUF**: SNF PPS rate files, combined with SNF utilization and cost report data, enable analysis of post-acute care payment adequacy and facility profitability.
- **Dependencies**: Upstream: MDS assessment data (drives PDPM classification), SNF wage index (from IPPS). Downstream: used in SNF payment analysis, post-acute care cost studies.
- **Regulatory Basis**: Social Security Act Section 1888(e) -- SNF PPS. Balanced Budget Act of 1997. PDPM implemented by CMS-1679-F (FY 2019 final rule).

#### Verification Needed
- [ ] Confirm FY2026 PDPM rate table locations
- [ ] Verify whether RUG-IV historical rate tables are still available
- [ ] Check if variable per diem adjustment tables are published

---

### 4.5 HHA PPS Rate Files

- **Category**: Fee Schedule / Payment (Home Health Agency)
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV / Excel / PDF
- **URL**: https://www.cms.gov/medicare/payment/prospective-payment-systems/home-health (NEEDS VERIFICATION)
- **Update Frequency**: Annual (effective January 1; published with HH PPS final rule)
- **Size Estimate**: Rate tables ~200-400 rows (PDGM case-mix groups); <5 MB
- **Key Fields**: `PDGM_Payment_Group`, `Clinical_Grouping`, `Functional_Level`, `Comorbidity_Adjustment`, `Timing` (early vs. late), `LUPA_Threshold`, `Per_Period_Rate`
- **What It Contains**: Payment rates under the Patient-Driven Groupings Model (PDGM), which replaced the HH PPS case-mix system in CY 2020. PDGM classifies 30-day home health periods into payment groups based on admission source (institutional vs. community), timing (early vs. late), clinical grouping, functional level, and comorbidity adjustment. Includes LUPA (Low Utilization Payment Adjustment) thresholds and the home health wage index.
- **What It Does NOT Contain**: Does not include patient-level data. Does not include historical HH PPS (pre-PDGM) rate tables. Does not cover non-Medicare home health.
- **Why It Matters for Project PUF**: HHA rate files enable payment modeling for home health episodes. Combined with HHA utilization and cost report data, they support analysis of home health payment adequacy and utilization patterns.
- **Dependencies**: Upstream: OASIS assessment data (drives PDGM classification), HH wage index. Downstream: used in HHA payment analysis, post-acute care studies.
- **Regulatory Basis**: Social Security Act Section 1895 -- Home Health PPS. Balanced Budget Act of 1997. PDGM implemented by CMS-1689-FC (CY 2020 final rule).

#### Verification Needed
- [ ] Confirm CY2026 PDGM rate table locations
- [ ] Verify availability of historical HH PPS rate tables
- [ ] Check LUPA threshold file format

---

### 4.6 Hospice Payment Rates

- **Category**: Fee Schedule / Payment (Hospice)
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: PDF / Excel (rate tables published in Federal Register and CMS transmittals)
- **URL**: https://www.cms.gov/medicare/payment/hospice (NEEDS VERIFICATION)
- **Update Frequency**: Annual (effective October 1)
- **Size Estimate**: 4 levels of care x wage-index-adjusted rates; very small table
- **Key Fields**: `Level_of_Care` (Routine Home Care, Continuous Home Care, Inpatient Respite Care, General Inpatient Care), `Per_Diem_Rate`, `Wage_Index_Adjustment`
- **What It Contains**: Per diem payment rates for the four levels of hospice care, the hospice wage index, and the hospice cap amount (maximum per-beneficiary payment). Since FY 2016, routine home care has a two-tiered rate (higher rate for days 1-60, lower rate for days 61+) to address concerns about inappropriate long hospice stays.
- **What It Does NOT Contain**: Does not include patient-level data. Hospice payment is straightforward (per diem by level of care) compared to other PPS systems.
- **Why It Matters for Project PUF**: Hospice rate files enable payment modeling for hospice episodes. Combined with hospice utilization data, they support analysis of hospice length of stay, payment adequacy, and the impact of the two-tiered routine home care rate.
- **Dependencies**: Upstream: hospice wage index (separate from IPPS wage index in some years). Downstream: used in hospice payment and utilization analysis.
- **Regulatory Basis**: Social Security Act Section 1814(i) -- hospice care payments. Hospice cap provisions under Section 1814(a)(7).

#### Verification Needed
- [ ] Confirm FY2026 hospice rate table location and format
- [ ] Verify whether hospice wage index is published separately or uses IPPS wage index
- [ ] Check if Service Intensity Add-on (SIA) rates are still included

---

### 4.7 DMEPOS Fee Schedule

- **Category**: Fee Schedule / Payment (Durable Medical Equipment, Prosthetics, Orthotics, Supplies)
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV / ZIP archive
- **URL**: https://www.cms.gov/medicare/payment/durable-medical-equipment-prosthetics-orthotics-supplies-dmepos/dmepos-fee-schedule (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly
- **Size Estimate**: ~10,000+ HCPCS code/modifier/fee area combinations; ~20-50 MB
- **Key Fields**: `HCPCS_Code`, `Modifier`, `Fee_Schedule_Amount`, `State`, `Fee_Area` (statewide or specific), `Category` (Inexpensive/routinely purchased, Capped rental, Oxygen, etc.)
- **What It Contains**: Payment rates for all DMEPOS items by HCPCS code, modifier, and geographic area. Includes: fee schedule amounts (which may differ by state/locality), payment category (purchase, capped rental, oxygen, etc.), and whether the item is subject to competitive bidding. After the DMEPOS Competitive Bidding Program expanded and then ended, fee schedules now incorporate adjusted rates based on competitive bidding information.
- **What It Does NOT Contain**: Does not include actual claims data. Does not include supplier-specific negotiated rates. Competitive bidding rates in non-competitive areas are blended, not actual bid amounts.
- **Why It Matters for Project PUF**: Enables DME payment analysis when combined with DME Supplier utilization data. Critical for understanding equipment and supply costs in the Medicare program.
- **Dependencies**: Upstream: HCPCS Level II codes, competitive bidding results. Downstream: used in DME claims payment, DME supplier profitability analysis.
- **Regulatory Basis**: Social Security Act Section 1834(a) -- DME payment; Section 1847 -- Competitive Bidding Program. Medicare Improvements for Patients and Providers Act of 2008 (MIPPA).

#### Verification Needed
- [ ] Confirm current DMEPOS fee schedule download location
- [ ] Verify impact of competitive bidding program changes on fee schedule structure
- [ ] Check if rural and non-competitive bidding area rates are clearly distinguished

---

### 4.8 Clinical Laboratory Fee Schedule (CLFS)

- **Category**: Fee Schedule / Payment (Lab Services)
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV / Excel / ZIP archive
- **URL**: https://www.cms.gov/medicare/payment/clinical-laboratory-fee-schedule (NEEDS VERIFICATION)
- **Update Frequency**: Annual (effective January 1); quarterly updates
- **Size Estimate**: ~2,000-3,000 HCPCS codes; ~5-10 MB
- **Key Fields**: `HCPCS_Code`, `Short_Description`, `National_Limit_Amount`, `Reporting_Floor`, `Reporting_Ceiling`, `Personal_Lab_Service_Indicator`
- **What It Contains**: Medicare payment rates for clinical laboratory tests identified by HCPCS codes. Under PAMA (Protecting Access to Medicare Act of 2014), the CLFS was reformed starting CY 2018 to be based on private payer rates reported by laboratories. Includes the national limit amount, weighted median private payer rate, and personal lab service indicator.
- **What It Does NOT Contain**: Does not include individual lab claims data. Does not include the underlying private payer rate data reported by laboratories (that is confidential).
- **Why It Matters for Project PUF**: Lab tests are a significant component of physician services. The CLFS enables lab payment analysis and comparison between Medicare rates and private payer benchmarks (at aggregate level).
- **Dependencies**: Upstream: HCPCS codes, private payer rate reporting. Downstream: used in lab claims payment, lab industry analysis.
- **Regulatory Basis**: Social Security Act Section 1833(h) -- payment for clinical diagnostic lab tests. PAMA Section 216 reformed the CLFS methodology.

#### Verification Needed
- [ ] Confirm CY2026 CLFS download location
- [ ] Verify whether PAMA-based rates are now fully implemented or still in phase-in
- [ ] Check if crosswalk files between old and PAMA-based rates are available

---

### 4.9 ASP (Average Sales Price) Drug Pricing Files

- **Category**: Fee Schedule / Payment (Part B Drugs)
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV / Excel / ZIP archive
- **URL**: https://www.cms.gov/medicare/payment/part-b-drugs/average-sales-price (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly
- **Size Estimate**: ~800-1,000 HCPCS codes per quarter; <5 MB per quarterly file
- **Key Fields**: `HCPCS_Code`, `Short_Description`, `Dosage`, `Payment_Limit` (ASP + 6%), `ASP_per_Dosage_Unit`, `HCPCS_Code_Dosage`
- **What It Contains**: Medicare Part B drug payment limits based on Average Sales Price. Most Part B drugs (those administered in physician offices or hospital outpatient departments) are paid at ASP + 6%. Quarterly files include the HCPCS code, drug name, dosage description, and payment limit per billing unit. Also includes crosswalk files for new drug codes and not-otherwise-classified (NOC) drugs.
- **What It Does NOT Contain**: Does not include the underlying manufacturer-reported ASP data (confidential). Does not include Part D drug prices (those are negotiated by plans). Does not cover drugs paid under other methodologies (WAC-based, AWP-based).
- **Why It Matters for Project PUF**: Part B drug spending is a major and growing component of Medicare spending. ASP files enable drug cost analysis, identification of high-cost drugs, and tracking of price changes over time. Combined with Part B Utilization data, they enable drug spending projections.
- **Dependencies**: Upstream: manufacturer ASP data submissions. Downstream: used in Part B drug claims payment, drug spending analysis, 340B program analysis.
- **Regulatory Basis**: Social Security Act Section 1847A -- ASP payment methodology for Part B drugs. Medicare Modernization Act (MMA) of 2003 established ASP-based payment.

#### Verification Needed
- [ ] Confirm current quarterly ASP file download location
- [ ] Verify whether IRA (Inflation Reduction Act) rebate provisions affect public ASP file content
- [ ] Check if historical ASP files are archived and available

---

### 4.10 Medicare Advantage Rate Books (County Benchmarks)

- **Category**: Fee Schedule / Payment (Medicare Advantage)
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV / Excel
- **URL**: https://www.cms.gov/medicare/payment/medicare-advantage-rates-statistics (NEEDS VERIFICATION)
- **Update Frequency**: Annual (Advance Notice in February, Rate Announcement in April)
- **Size Estimate**: ~3,200 counties x rate components; ~10-20 MB
- **Key Fields**: `County_FIPS`, `State`, `County`, `FFS_Per_Capita_Cost` (county benchmark basis), `MA_Benchmark`, `Applicable_Percentage`, `Quality_Bonus_Percentage`, `Risk_Score_Factor`
- **What It Contains**: County-level Medicare Advantage payment benchmarks, which determine how much CMS pays MA plans per enrollee. Includes the FFS per-capita cost by county (the basis for benchmarks), the applicable percentage (quartile-based, ranging from 95% to 115% of FFS), quality bonus percentages (for plans with 4+ stars), and risk adjustment factors. Also includes the annual rate book that MA plans use for bidding.
- **What It Does NOT Contain**: Does not include individual plan bids (those are confidential until after contract year). Does not include MA encounter data (that is restricted access). Does not break down spending by service type at the county level.
- **Why It Matters for Project PUF**: MA benchmarks are essential for understanding the MA market and its relationship to FFS Medicare. Combined with MA enrollment data, they enable analysis of plan payment adequacy, geographic market attractiveness, and the FFS-MA payment differential.
- **Dependencies**: Upstream: county-level FFS spending data, CMS-HCC risk adjustment model. Downstream: used in MA plan payment, MA market analysis, benchmark adequacy studies.
- **Regulatory Basis**: Social Security Act Section 1853 -- MA payment methodology. ACA Section 3201 restructured benchmarks (quartile system).

#### Verification Needed
- [ ] Confirm current rate book download location
- [ ] Verify whether county-level FFS per-capita costs are published in the rate book or separately
- [ ] Check if risk adjustment model documentation is bundled with rate files

---

### 4.11 Wage Index Files

- **Category**: Fee Schedule / Payment (Geographic Adjustment)
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV / Excel (published as part of IPPS, OPPS, and other PPS final rules)
- **URL**: https://www.cms.gov/medicare/payment/prospective-payment-systems/acute-inpatient-pps/wage-index-files (NEEDS VERIFICATION)
- **Update Frequency**: Annual (IPPS: October 1; OPPS/PFS: January 1)
- **Size Estimate**: ~400 CBSA-based wage index areas; <5 MB
- **Key Fields**: `CBSA` (Core Based Statistical Area), `Wage_Index` (pre-reclassification), `Reclassified_Wage_Index`, `State`, `Urban_Rural`
- **What It Contains**: Geographic labor cost adjustment factors used across most Medicare payment systems. The IPPS wage index is the primary version -- it adjusts the labor-related share of hospital payments based on the area's hospital wage levels relative to the national average. Multiple wage index tables exist: pre-reclassification, post-reclassification (reflecting Section 508 and geographic reclassifications), pre-floor, post-floor (reflecting the rural floor), and outmigration adjustments. Separate wage indices exist for SNF PPS and HHA PPS, though they are derived from or closely related to the IPPS wage index.
- **What It Does NOT Contain**: Does not include the underlying hospital wage survey data (that comes from cost reports). Does not include wage indices for non-Medicare payment systems.
- **Why It Matters for Project PUF**: The wage index is the single most important geographic adjustment in Medicare payment. It affects every institutional payment system. Understanding wage index variation is essential for any cross-geographic payment analysis.
- **Dependencies**: Upstream: hospital cost report wage data (S-3 worksheet). Downstream: used in IPPS, OPPS, SNF PPS, HHA PPS, IRF PPS, LTCH PPS, and hospice payment calculations.
- **Regulatory Basis**: Social Security Act Section 1886(d)(3)(E) -- IPPS wage index. Published annually in the Federal Register IPPS Final Rule.

#### Verification Needed
- [ ] Confirm FY2026 wage index file locations for IPPS and other PPS systems
- [ ] Verify whether all wage index variants (pre/post reclassification, floor, outmigration) are available
- [ ] Check if CBSA definitions have been updated recently (OMB periodically revises CBSAs)

---

## 5. Geographic & Demographic Reference

---

### 5.1 State and County FIPS Codes

- **Category**: Geographic Reference
- **Publisher**: Census Bureau / NIST (National Institute of Standards and Technology)
- **Access Level**: Fully Public
- **Format**: CSV / TXT / PDF
- **URL**: https://www.census.gov/library/reference/code-lists/ansi.html (NEEDS VERIFICATION)
- **Update Frequency**: Updated with decennial census; periodic intercensal revisions
- **Size Estimate**: 50 states + territories; ~3,200 counties; <1 MB
- **Key Fields**: `State_FIPS` (2-digit), `County_FIPS` (3-digit, combined 5-digit with state), `State_Name`, `County_Name`, `FIPS_Class_Code`
- **What It Contains**: The Federal Information Processing Standards codes for all U.S. states, territories, counties, and county-equivalents. FIPS codes are the standard geographic identifiers used across federal data systems including CMS. Each county has a unique 5-digit code (2-digit state + 3-digit county).
- **What It Does NOT Contain**: Not a geographic boundary file (use Census TIGER/Line for that). Does not include sub-county geography. Does not account for county boundary changes over time without consulting historical FIPS files.
- **Why It Matters for Project PUF**: FIPS codes are the universal geographic join key across CMS datasets (Geographic Variation PUF, MA Enrollment, Cost Reports), Census data, and other federal datasets. Must-have reference table.
- **Dependencies**: Upstream: Census Bureau geography. Downstream: enables geographic joins across virtually all datasets.
- **Regulatory Basis**: FIPS publication 6-4 (counties), now administered under ANSI INCITS 31 standard.

#### Verification Needed
- [ ] Confirm current FIPS code list download location at Census
- [ ] Verify whether FIPS codes for recent county changes (e.g., Connecticut planning regions replacing counties) are reflected
- [ ] Check if Census provides historical FIPS change logs

---

### 5.2 ZIP Code to County Crosswalk (HUD)

- **Category**: Geographic Reference / Crosswalk
- **Publisher**: HUD (Department of Housing and Urban Development) Office of Policy Development and Research
- **Access Level**: Fully Public
- **Format**: CSV / Excel
- **URL**: https://www.huduser.gov/portal/datasets/usps_crosswalk.html (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly
- **Size Estimate**: ~43,000 ZIP codes; crosswalk file ~50,000+ rows (many-to-many); ~5-10 MB
- **Key Fields**: `ZIP`, `County_FIPS` (GEOID), `Residential_Ratio`, `Business_Ratio`, `Other_Ratio`, `Total_Ratio`
- **What It Contains**: Crosswalk between USPS ZIP codes and Census county FIPS codes. Since ZIP codes are mail delivery routes (not geographic areas) and do not align to county boundaries, the crosswalk provides allocation ratios indicating what proportion of each ZIP's addresses fall in each county. A ZIP that spans two counties will have two rows with different ratios.
- **What It Does NOT Contain**: Not a one-to-one mapping (many ZIPs span multiple counties). Does not include ZIP+4 level detail. Ratios are based on address counts, not population or land area.
- **Why It Matters for Project PUF**: Many CMS datasets (NPPES, Part B Utilization, Part D Prescribers) use ZIP codes while geographic analysis files use county FIPS codes. This crosswalk is essential for bridging the two. The ~5% of ZIPs that span multiple counties require ratio-based allocation or dominant-county assignment.
- **Dependencies**: Upstream: USPS ZIP code assignments, Census county geography. Downstream: enables ZIP-to-county conversion for all provider-level datasets.
- **Regulatory Basis**: No specific mandate; HUD produces this as a public service.

#### Verification Needed
- [ ] Confirm current HUD crosswalk URL and quarterly availability
- [ ] Verify whether the crosswalk covers all active USPS ZIP codes
- [ ] Check if Census ZCTA-to-county crosswalk is a better alternative for some uses

---

### 5.3 ZCTA (ZIP Code Tabulation Areas)

- **Category**: Geographic Reference
- **Publisher**: Census Bureau
- **Access Level**: Fully Public
- **Format**: Shapefile / CSV (relationship files); TIGER/Line geodata
- **URL**: https://www.census.gov/programs-surveys/geography/guidance/geo-areas/zctas.html (NEEDS VERIFICATION)
- **Update Frequency**: Decennial (major revision); annual American Community Survey data at ZCTA level
- **Size Estimate**: ~33,000 ZCTAs; relationship file <5 MB; TIGER shapefile ~100-500 MB
- **Key Fields**: `ZCTA5CE20` (5-digit ZCTA), `GEOID`, geographic boundaries (polygon geometry)
- **What It Contains**: Census-defined geographic areas that approximate ZIP code service areas using census blocks. Unlike ZIP codes (which are linear mail routes), ZCTAs are true polygons with defined boundaries. The Census Bureau publishes ZCTA boundary files and ZCTA-to-county/tract/CBSA relationship files. ACS demographic data is available at the ZCTA level.
- **What It Does NOT Contain**: Not the same as ZIP codes (there is no perfect 1:1 mapping). Some ZIP codes have no corresponding ZCTA (PO boxes, single large delivery points). Does not update between censuses.
- **Why It Matters for Project PUF**: ZCTAs provide the best available geographic approximation for ZIP code-based data. When precise geographic analysis is needed (mapping, spatial analysis, demographic overlay), ZCTAs provide polygon boundaries that ZIP codes lack.
- **Dependencies**: Upstream: Census Bureau geography, decennial census. Downstream: enables spatial analysis of ZIP-code-based healthcare data; links to ACS demographic data.
- **Regulatory Basis**: Census Bureau geographic program; no specific healthcare mandate.

#### Verification Needed
- [ ] Confirm 2020 Census ZCTA files are fully available
- [ ] Verify ZCTA-to-county relationship file location
- [ ] Check if ACS 5-year data at ZCTA level is the best source for demographic overlay

---

### 5.4 CBSA (Core Based Statistical Areas)

- **Category**: Geographic Reference
- **Publisher**: OMB (Office of Management and Budget) / Census Bureau
- **Access Level**: Fully Public
- **Format**: CSV / Excel
- **URL**: https://www.census.gov/geographies/reference-files/time-series/demo/metro-micro/delineation-files.html (NEEDS VERIFICATION)
- **Update Frequency**: Periodic (major revisions follow decennial census; interim updates as OMB directs)
- **Size Estimate**: ~930 CBSAs (metropolitan + micropolitan); ~1,900 counties (not all counties are in CBSAs); <1 MB
- **Key Fields**: `CBSA_Code` (5-digit), `CBSA_Title`, `Metropolitan_or_Micropolitan`, `CSA_Code`, `CSA_Title`, `State_FIPS`, `County_FIPS`, `Central_Outlying_County`
- **What It Contains**: OMB-defined metropolitan and micropolitan statistical areas, which group counties around core urban centers based on commuting patterns. Each CBSA contains at least one county with an urban core of 10,000+ (micropolitan) or 50,000+ (metropolitan) population, plus adjacent counties with strong commuting ties. The delineation file maps every county to its CBSA (if any).
- **What It Does NOT Contain**: Not all counties belong to a CBSA (rural counties outside any CBSA are not included). Does not provide sub-county detail. CBSA definitions change over time with OMB revisions, creating longitudinal challenges.
- **Why It Matters for Project PUF**: CBSAs are the geographic unit used for CMS wage indices and many other geographic adjustments. The IPPS wage index is CBSA-based. Understanding CBSA definitions is essential for interpreting geographic payment variation.
- **Dependencies**: Upstream: Census county definitions, OMB delineation decisions. Downstream: used in CMS wage index, IPPS geographic reclassification, and as an analytic unit for market analysis.
- **Regulatory Basis**: OMB Bulletin (most recently based on 2020 Census); CMS adopts CBSA definitions for payment system geographic adjustments per Section 1886(d)(3) of the Social Security Act.

#### Verification Needed
- [ ] Confirm latest CBSA delineation file based on 2020 Census
- [ ] Verify whether CMS has adopted the latest OMB CBSA revisions or uses an older vintage
- [ ] Check if CSA (Combined Statistical Area) data is included in the same file

---

### 5.5 HRR/HSA (Hospital Referral Regions / Hospital Service Areas) -- Dartmouth Atlas

- **Category**: Geographic Reference / Healthcare Market
- **Publisher**: Dartmouth Atlas Project (now at Dartmouth Institute for Health Policy & Clinical Practice)
- **Access Level**: Fully Public
- **Format**: CSV / Shapefile
- **URL**: https://data.dartmouthatlas.org/ (NEEDS VERIFICATION)
- **Update Frequency**: Static (last major revision ~2019); Dartmouth Atlas website may have periodic data updates
- **Size Estimate**: 306 HRRs; ~3,400 HSAs; crosswalk files <5 MB; boundary shapefiles ~50 MB
- **Key Fields**: `HRR_Number`, `HRR_Name`, `HSA_Number`, `HSA_Name`, `ZIP`, `State`
- **What It Contains**: Healthcare-specific geographic units defined by the Dartmouth Atlas Project based on Medicare patient referral patterns. HSAs (Hospital Service Areas) are groups of ZIP codes where the plurality of Medicare hospitalizations occur locally. HRRs (Hospital Referral Regions) are groups of HSAs where the plurality of major cardiovascular surgery and neurosurgery referrals occur. The ZIP-to-HRR/HSA crosswalk enables mapping any ZIP-coded data to these healthcare market areas.
- **What It Does NOT Contain**: Not official government geographies (they are research-derived). Definitions are based on older referral patterns and may not reflect current care delivery. Not updated regularly.
- **Why It Matters for Project PUF**: HRRs are the standard unit for healthcare geographic variation analysis. The Dartmouth Atlas's work on practice variation, spending variation, and supply-sensitive care is foundational to health policy. HRRs enable comparison to the extensive Dartmouth Atlas literature.
- **Dependencies**: Upstream: Medicare claims data (for defining referral patterns). Downstream: enables geographic variation analysis at the healthcare market level; links to Dartmouth Atlas research.
- **Regulatory Basis**: No regulatory mandate. Research-derived geography widely adopted in health services research and policy.

#### Verification Needed
- [ ] Confirm Dartmouth Atlas data download availability (project funding/hosting may have changed)
- [ ] Verify whether HRR/HSA definitions have been updated post-2020 Census
- [ ] Check if ZIP-to-HRR/HSA crosswalk is current

---

### 5.6 RUCA Codes (Rural-Urban Commuting Area Codes)

- **Category**: Geographic Reference / Rural Classification
- **Publisher**: USDA Economic Research Service (ERS) in collaboration with FORHP (Federal Office of Rural Health Policy)
- **Access Level**: Fully Public
- **Format**: CSV / Excel
- **URL**: https://www.ers.usda.gov/data-products/rural-urban-commuting-area-codes/ (NEEDS VERIFICATION)
- **Update Frequency**: Decennial (major revision with each census); may have intercensal updates
- **Size Estimate**: ~73,000 census tracts; ZIP-code approximation file also available; <10 MB
- **Key Fields**: `Census_Tract_FIPS`, `RUCA_Code` (primary code 1-10), `RUCA_Secondary_Code` (sub-code), `State_FIPS`, `County_FIPS`
- **What It Contains**: Classification of every U.S. census tract (and ZIP code, via approximation) into rural-urban categories based on population density, urbanization, and daily commuting patterns. RUCA codes range from 1 (metropolitan area core) to 10 (rural, not adjacent to any urban area). CMS and FORHP use RUCA codes to determine eligibility for rural health programs and payment adjustments.
- **What It Does NOT Contain**: Not a simple urban/rural binary -- the 10-level classification requires interpretation. ZIP-code approximation is imprecise for ZIPs spanning multiple tracts. Does not capture seasonal population fluctuations.
- **Why It Matters for Project PUF**: Rural-urban classification is essential for healthcare access analysis. CMS uses RUCA codes for certain payment adjustments and program eligibility. Any analysis of rural healthcare requires RUCA or similar classification.
- **Dependencies**: Upstream: Census tract definitions, ACS commuting data. Downstream: enables rural-urban stratification across all analyses; used by CMS for rural designation.
- **Regulatory Basis**: FORHP uses RUCA codes as part of its rural definition for grant programs. CMS references RUCA for some payment provisions.

#### Verification Needed
- [ ] Confirm 2020 Census-based RUCA codes are available
- [ ] Verify ZIP-code approximation file availability
- [ ] Check which RUCA threshold CMS uses for rural classification (varies by program)

---

### 5.7 CMS MAC (Medicare Administrative Contractor) Jurisdiction Maps

- **Category**: Geographic Reference / Administrative
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: PDF (maps); some tabular data
- **URL**: https://www.cms.gov/medicare/enrollment-renewal/providers-suppliers/medicare-administrative-contractors (NEEDS VERIFICATION)
- **Update Frequency**: Updated when MAC contracts change (infrequent)
- **Size Estimate**: ~12 A/B MAC jurisdictions; ~4 DME MAC jurisdictions; tiny reference
- **Key Fields**: `Jurisdiction`, `MAC_Name`, `States_Covered`, `Contract_Number`
- **What It Contains**: Maps and tables showing which Medicare Administrative Contractor processes claims for each geographic jurisdiction. A/B MACs handle Part A (institutional) and Part B (professional) claims by geographic region. DME MACs handle durable medical equipment claims in four jurisdictions. HH+H MACs handle home health and hospice claims.
- **What It Does NOT Contain**: No claims data. No performance data for MACs. No claims processing statistics in the jurisdiction files themselves.
- **Why It Matters for Project PUF**: MAC jurisdiction is relevant for understanding claims processing differences, local coverage determinations (LCDs), and administrative variation. Some coding and payment patterns vary by MAC.
- **Dependencies**: Upstream: CMS contracting process. Downstream: contextualizes geographic variation in claims patterns.
- **Regulatory Basis**: Social Security Act Section 1874A -- MAC requirements. Medicare Modernization Act of 2003 created the MAC structure.

#### Verification Needed
- [ ] Confirm current MAC jurisdiction assignments
- [ ] Verify whether tabular state-to-MAC mappings are available or only PDF maps
- [ ] Check if LCD (Local Coverage Determination) data is linked to MAC jurisdictions in a downloadable format

---

### 5.8 Census Population Estimates

- **Category**: Geographic / Demographic Reference
- **Publisher**: Census Bureau
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://www.census.gov/programs-surveys/popest.html (NEEDS VERIFICATION)
- **Update Frequency**: Annual (July 1 estimates released each December/March)
- **Size Estimate**: ~3,200 counties x multiple demographic breakdowns; ~10-50 MB per vintage
- **Key Fields**: `State_FIPS`, `County_FIPS`, `Year`, `Total_Population`, `Age_Group`, `Sex`, `Race_Hispanic_Origin`
- **What It Contains**: Annual population estimates by county, with breakdowns by single year of age, sex, race, and Hispanic origin. Vintage estimates are revised each year. Also includes state-level and national estimates. The Population Estimates Program bridges decennial census years, providing intercensal population data.
- **What It Does NOT Contain**: Not actual counts between censuses (estimates with margins of error). Does not include health insurance coverage (use ACS for that). Sub-county estimates are available only for places and MCDs, not census tracts.
- **Why It Matters for Project PUF**: Population denominators are essential for per-capita calculations. Any analysis of Medicare spending or utilization per capita requires population estimates. The 65+ population by county is the primary denominator for Medicare analyses.
- **Dependencies**: Upstream: decennial census, vital statistics, migration data. Downstream: denominators for all per-capita analyses; age 65+ population enables Medicare penetration calculations.
- **Regulatory Basis**: Census Bureau's mandate under Title 13, U.S. Code.

#### Verification Needed
- [ ] Confirm current vintage population estimates download location
- [ ] Verify whether single-year-of-age data is available at county level
- [ ] Check if 2020 Census-based estimates have superseded the 2010-based intercensal series

---

### 5.9 Area Deprivation Index (ADI)

- **Category**: Geographic / Socioeconomic Reference
- **Publisher**: Health Resources and Services Administration (HRSA) / University of Wisconsin
- **Access Level**: Fully Public (requires free registration for UW version)
- **Format**: CSV
- **URL**: https://www.neighborhoodatlas.medicine.wisc.edu/ (NEEDS VERIFICATION)
- **Update Frequency**: Periodic (updated with new ACS releases, approximately annually)
- **Size Estimate**: ~73,000 census block groups; ~10-20 MB
- **Key Fields**: `FIPS` (block group), `ADI_National_Rank` (percentile 1-100), `ADI_State_Rank` (decile 1-10)
- **What It Contains**: A composite index of socioeconomic disadvantage at the census block group level (the smallest geography), incorporating income, education, employment, and housing quality indicators from the American Community Survey. The national rank places each block group on a 1-100 percentile scale (100 = most disadvantaged). The state rank provides a within-state decile.
- **What It Does NOT Contain**: Not a health outcome index. Does not directly measure healthcare access or utilization. Block group level may be too granular for some analyses (requires crosswalking to ZIP or county).
- **Why It Matters for Project PUF**: Socioeconomic context is critical for understanding health disparities. ADI enables stratification of any geographic analysis by deprivation level. CMS has begun using ADI in payment models (e.g., ACO REACH model uses ADI for benchmark adjustments).
- **Dependencies**: Upstream: ACS data, Census block group geography. Downstream: enables health equity analysis across all datasets; used by CMS in emerging payment models.
- **Regulatory Basis**: No specific mandate for ADI itself. CMS's adoption in payment models gives it increasing regulatory relevance.

#### Verification Needed
- [ ] Confirm current ADI version and download process (registration required)
- [ ] Verify whether HRSA has its own ADI version or relies on UW Neighborhood Atlas
- [ ] Check which ACS year the current ADI version is based on

---

### 5.10 Social Vulnerability Index (SVI)

- **Category**: Geographic / Socioeconomic Reference
- **Publisher**: CDC/ATSDR (Agency for Toxic Substances and Disease Registry)
- **Access Level**: Fully Public
- **Format**: CSV / Shapefile
- **URL**: https://www.atsdr.cdc.gov/placeandhealth/svi/ (NEEDS VERIFICATION)
- **Update Frequency**: Biennial (every 2 years, corresponding to ACS releases)
- **Size Estimate**: ~73,000 census tracts; ~20-50 MB (CSV); shapefiles larger
- **Key Fields**: `FIPS` (census tract), `RPL_THEMES` (overall vulnerability percentile), `RPL_THEME1` (Socioeconomic Status), `RPL_THEME2` (Household Characteristics), `RPL_THEME3` (Racial & Ethnic Minority Status), `RPL_THEME4` (Housing Type & Transportation)
- **What It Contains**: A composite index ranking every census tract on four themes of social vulnerability: socioeconomic status, household characteristics (age, disability, single parent), racial/ethnic minority status, and housing type/transportation. Each tract receives a percentile ranking (0-1) on each theme and overall. Originally designed for emergency preparedness but widely adopted for health equity analysis.
- **What It Does NOT Contain**: Not a health outcome measure. Does not include health-specific indicators (use CDC PLACES for that). Census tract level may need crosswalking for ZIP-based healthcare data.
- **Why It Matters for Project PUF**: Complements ADI with a different vulnerability framework. SVI's four-theme structure enables more nuanced equity analysis. CDC's PLACES project (health estimates at census tract level) uses the same geography, enabling linking.
- **Dependencies**: Upstream: ACS data, Census tract geography. Downstream: enables health equity stratification; links to CDC PLACES and other tract-level health data.
- **Regulatory Basis**: CDC/ATSDR mission under CERCLA (Superfund) and related environmental health authorities. Increasingly referenced in CMS health equity initiatives.

#### Verification Needed
- [ ] Confirm current SVI version (2020-based)
- [ ] Verify download format options (CSV, shapefile, geodatabase)
- [ ] Check if CDC has updated SVI methodology for 2020 Census tracts

---

## 6. Claims & Utilization (Raw/Granular)

> **Access Level Note**: Many of the most valuable claims datasets are NOT public use files. This section documents the full spectrum from fully public to research-only, clearly labeling access requirements. Understanding what exists -- even if restricted -- is essential for planning the platform's analytical ceiling.

---

### 6.1 Medicare FFS Claims -- Standard Analytic Files (SAF) and Limited Data Sets (LDS)

- **Category**: Claims / Utilization
- **Publisher**: CMS (via ResDAC -- Research Data Assistance Center)
- **Access Level**: LDS (Data Use Agreement required); some identifiable versions require full DUA + IRB
- **Format**: SAS / CSV (fixed-width historical); claim-level records
- **URL**: https://resdac.org/cms-data/files (NEEDS VERIFICATION)
- **Update Frequency**: Annual (typically 18-24 month lag)
- **Size Estimate**: Billions of claim lines per year; Inpatient SAF ~15-20 million claims/year; Part B SAF ~1+ billion claim lines/year; each file type is hundreds of GB
- **Key Fields**: `BENE_ID` (encrypted), `CLM_ID`, `NCH_CLM_TYPE_CD`, `Provider`, `CLM_FROM_DT`, `CLM_THRU_DT`, `ICD_DGNS_CD_1` through `_25`, `ICD_PRCDR_CD_1` through `_25`, `HCPCS_CD`, `CLM_PMT_AMT`, `CLM_TOT_CHRG_AMT`
- **What It Contains**: Complete claim-level Medicare FFS data across all claim types: Inpatient (IP), Outpatient (OP), Skilled Nursing Facility (SNF), Home Health (HH), Hospice, Carrier (Part B physician), and Durable Medical Equipment (DME). Each claim includes diagnoses, procedures, charges, payments, dates of service, provider identifiers, and beneficiary identifiers (encrypted in LDS versions). This is the gold standard for Medicare utilization research.
- **What It Does NOT Contain**: No Medicare Advantage encounter data (that is separate). No drug claims (Part D is separate). LDS versions have encrypted beneficiary IDs (no direct identification). No clinical data beyond what is coded on claims.
- **Why It Matters for Project PUF**: These are the source data from which most CMS PUFs are derived. While Project PUF cannot distribute SAF/LDS data, understanding their structure informs the platform's analytical design. Users may access SAF data through ResDAC and use Project PUF's reference tables (code systems, fee schedules, provider registries) to enrich their analyses.
- **Dependencies**: Upstream: Medicare claims processing by MACs. Downstream: source data for virtually all CMS PUFs, quality measures, and research datasets.
- **Regulatory Basis**: Privacy Act of 1974; HIPAA Privacy Rule; CMS data governance policies. Access governed by ResDAC DUA process.

#### Verification Needed
- [ ] Confirm current ResDAC data request process and timelines
- [ ] Verify whether CMS has expanded any SAF data access (e.g., synthetic claims data for testing)
- [ ] Check if CMS Synthetic Public Use Files (SynPUFs) are still available as a SAF proxy

---

### 6.2 CMS Virtual Research Data Center (VRDC)

- **Category**: Claims / Research Infrastructure
- **Publisher**: CMS
- **Access Level**: Research Only (DUA + approved project required; access via remote desktop)
- **Format**: SAS datasets accessible within the VRDC environment; no data extraction permitted
- **URL**: https://resdac.org/cms-virtual-research-data-center-vrdc (NEEDS VERIFICATION)
- **Update Frequency**: Continuously updated; most recent data available within 6-12 months
- **Size Estimate**: Complete Medicare/Medicaid claims universe; petabytes of data
- **Key Fields**: All fields from SAF/LDS files plus additional identifiable variables
- **What It Contains**: CMS's secure research environment providing access to the full universe of Medicare and Medicaid claims, enrollment, and assessment data. Includes 100% Medicare FFS claims, MA encounter data, Part D drug event data, Medicaid T-MSIS data, MDS/OASIS/IRF-PAI assessment data, and more. Researchers access data through a virtual desktop; no data leaves the environment (only statistical output after disclosure review).
- **What It Does NOT Contain**: Data cannot be extracted or downloaded. Output must pass disclosure review. No real-time access (batch processing environment).
- **Why It Matters for Project PUF**: The VRDC represents the analytical ceiling -- it contains everything. While Project PUF cannot replicate VRDC data, understanding what is available there helps define what questions the platform can and cannot answer with public data alone. VRDC researchers are a key user persona for Project PUF's reference tools.
- **Dependencies**: Upstream: all CMS claims processing systems. Downstream: source for CMS-published research, quality measures, and aggregate PUFs.
- **Regulatory Basis**: CMS data governance policies; Privacy Act; HIPAA.

#### Verification Needed
- [ ] Confirm current VRDC access costs and timeline
- [ ] Verify whether CMS has expanded VRDC access (cloud-based options)
- [ ] Check if VRDC now includes additional data sources (e.g., COVID-19 data)

---

### 6.3 Medicare Current Beneficiary Survey (MCBS)

- **Category**: Survey / Claims-Linked
- **Publisher**: CMS (conducted by NORC at the University of Chicago)
- **Access Level**: Public Use File available (limited variables); full file requires DUA
- **Format**: SAS / CSV; PUF is downloadable; full data requires ResDAC
- **URL**: https://www.cms.gov/data-research/research/medicare-current-beneficiary-survey (NEEDS VERIFICATION)
- **Update Frequency**: Annual
- **Size Estimate**: ~15,000 beneficiaries surveyed per year; PUF ~10,000-12,000 respondents; ~50-100 MB
- **Key Fields**: PUF version: `BASEID` (survey ID), demographic variables, self-reported health status, insurance coverage, access to care measures, satisfaction measures, expenditure categories
- **What It Contains**: A nationally representative survey of the Medicare population linked to Medicare claims data. The MCBS PUF includes survey responses on health status, functional limitations, access to care, satisfaction, supplemental insurance, and out-of-pocket spending. The Survey File includes respondent demographics and survey responses. The Cost Supplement links survey data to actual Medicare claims to produce total healthcare expenditure estimates (including non-Medicare spending).
- **What It Does NOT Contain**: PUF version has limited geographic detail (no state identifiers for small states). PUF excludes some sensitive variables. Claims linkage variables are not in the PUF. Small sample size limits sub-group analysis.
- **Why It Matters for Project PUF**: MCBS is the only data source that combines beneficiary-reported information (access, satisfaction, health status) with actual claims-based utilization and spending. The PUF provides a beneficiary perspective that claims data alone cannot offer.
- **Dependencies**: Upstream: Medicare enrollment files (sampling frame), Medicare claims (linkage). Downstream: enables beneficiary-level analysis of access, spending burden, and health status.
- **Regulatory Basis**: CMS research authority under the Social Security Act. Survey funded and directed by the CMS Office of Enterprise Data and Analytics (OEDA).

#### Verification Needed
- [ ] Confirm MCBS PUF download location and current data year
- [ ] Verify PUF variable list and geographic identifiers available
- [ ] Check if MCBS COVID supplement data is in the PUF

---

### 6.4 Medicaid State Drug Utilization Data (SDUD)

- **Category**: Claims / Utilization (Drug)
- **Publisher**: CMS (Medicaid)
- **Access Level**: Fully Public
- **Format**: CSV; also available via Medicaid.gov API
- **URL**: https://data.medicaid.gov/datasets?theme=State+Drug+Utilization (NEEDS VERIFICATION); also at https://www.medicaid.gov/medicaid/prescription-drugs/state-drug-utilization-data/index.html (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly (with lag)
- **Size Estimate**: ~50-60 million rows per year (state x drug x quarter); multi-year archive; ~2-5 GB per year
- **Key Fields**: `State_Code`, `NDC` (11-digit), `Labeler_Name`, `Product_Name`, `Year`, `Quarter`, `Utilization_Type` (FFSU = Fee-for-Service, MCOU = Managed Care Organization), `Number_of_Prescriptions`, `Total_Amount_Reimbursed`, `Medicaid_Amount_Reimbursed`, `Units_Reimbursed`, `Suppression_Used`
- **What It Contains**: State-level drug utilization data from the Medicaid Drug Rebate Program. Each record shows the number of prescriptions, units dispensed, and Medicaid reimbursement amount for a specific drug (by NDC) in a specific state and quarter. Data is split by utilization type (FFS vs. managed care). This is the most granular publicly available Medicaid prescription drug dataset.
- **What It Does NOT Contain**: No patient-level data. No prescriber identifiers. No diagnosis information (cannot determine what condition the drug was prescribed for). MCO data quality varies by state. No rebate amounts (those are confidential).
- **Why It Matters for Project PUF**: The primary publicly available Medicaid drug utilization dataset. Enables analysis of state-by-state drug utilization patterns, Medicaid drug spending trends, and generic vs. brand utilization. When combined with NDC directory and drug pricing data, enables deep pharmaceutical policy analysis.
- **Dependencies**: Upstream: state Medicaid agency claims data, Medicaid Drug Rebate Program. Downstream: enables Medicaid drug spending analysis, state comparison studies.
- **Regulatory Basis**: Social Security Act Section 1927 -- Medicaid Drug Rebate Program. States are required to report utilization data to CMS as a condition of rebate participation.

#### Verification Needed
- [ ] Confirm current download location on data.medicaid.gov
- [ ] Verify data latency (how far behind is the most recent quarter)
- [ ] Check if managed care data completeness has improved
- [ ] Verify whether 340B-carved-out claims are identifiable in SDUD

---

### 6.5 Medicare Provider Charge Data (Inpatient DRG / Outpatient APC)

- **Category**: Claims / Utilization / Cost
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://data.cms.gov/provider-summary-by-type-of-service/ (NEEDS VERIFICATION)
- **Update Frequency**: Annual (18-24 month lag)
- **Size Estimate**: Inpatient: ~200,000-300,000 rows (hospital x DRG); Outpatient: ~500,000-1,000,000 rows (hospital x APC); ~50-200 MB each
- **Key Fields**: `CCN`, `Provider_Name`, `Provider_Address`, `DRG_Definition` or `APC`, `Total_Discharges` or `Total_Services`, `Average_Covered_Charges`, `Average_Total_Payments`, `Average_Medicare_Payments`
- **What It Contains**: Hospital-level aggregate data showing charges, payments, and volume for each DRG (inpatient) or APC (outpatient). For each hospital-DRG or hospital-APC combination, shows the number of discharges/services, average charges (what the hospital bills), average total payments (what Medicare actually pays including beneficiary responsibility), and average Medicare payments (Medicare's share only). This data was first released in 2013 as part of CMS's price transparency initiative.
- **What It Does NOT Contain**: No patient-level data. No individual claim records. Subject to CMS suppression rules (minimum 11 discharges). Does not include physician professional fees. Only covers Medicare FFS.
- **Why It Matters for Project PUF**: Uniquely bridges charges (what hospitals bill) and payments (what Medicare pays), enabling charge-to-payment ratio analysis and geographic pricing variation studies. Previously cataloged as a summary PUF but included here because it provides granular hospital-by-service pricing data.
- **Dependencies**: Upstream: Medicare FFS claims data. Downstream: enables hospital pricing analysis, charge variation studies, provider-level cost comparisons.
- **Regulatory Basis**: ACA Section 10332 -- transparency of Medicare and Medicaid data. CMS authority to publish aggregate claims data.

#### Verification Needed
- [ ] Confirm current download location and most recent data year
- [ ] Verify whether outpatient APC charge data is still published separately
- [ ] Check if CMS has added new charge data files (e.g., physician-level charges)

---

### 6.6 CMS Cost Reports (Hospital, SNF, HHA, Hospice, FQHC, RHC)

- **Category**: Financial / Cost
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV (from HCRIS -- Healthcare Cost Report Information System); some historical data in fixed-width
- **URL**: https://www.cms.gov/data-research/statistics-trends-and-reports/cost-reports (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly (HCRIS extracts); individual cost reports filed annually by each provider
- **Size Estimate**: Hospital cost reports (CMS-2552-10): ~6,500 hospitals x ~500 worksheets with thousands of fields; HCRIS extract is several GB. SNF, HHA, Hospice, FQHC, RHC: similar structure, smaller provider counts.
- **Key Fields**: `CCN`, `Provider_Name`, `Fiscal_Year_Begin_Date`, `Fiscal_Year_End_Date`, `Report_Status` (As Submitted, Settled, Reopened); data fields span: total costs, cost-to-charge ratios, departmental costs, revenue, patient days, FTEs, bed counts, payer mix, charity care, bad debt, capital costs, GME costs, DSH statistics, wage data, Medicare utilization statistics
- **What It Contains**: Detailed financial and operational data from every Medicare-certified institutional provider. Cost reports are the most comprehensive public source of hospital financial data. The hospital cost report (Form CMS-2552-10) has hundreds of worksheets covering: total facility costs, departmental cost allocation, cost-to-charge ratios by department, inpatient and outpatient revenue, patient days and discharges by payer, FTE counts by staff category, bed counts, case mix, wage data (used for wage index), GME (graduate medical education) data, DSH (disproportionate share hospital) data, uncompensated care, capital costs, and much more. Similar cost reports exist for SNFs (CMS-2540), HHAs (CMS-1728), Hospices (CMS-1984), FQHCs, and RHCs.
- **What It Does NOT Contain**: Not claims data. Cost reports are self-reported and subject to audit. Settled (final audited) reports differ from as-submitted reports. The HCRIS database extracts specific fields; accessing the full cost report for a single provider requires the individual report file.
- **Why It Matters for Project PUF**: Cost reports are irreplaceable for facility financial analysis. They are the ONLY public source of detailed hospital cost data, departmental profitability, payer mix, staffing levels, and capital structure. Combined with utilization PUFs and quality data, they enable the holy trinity of healthcare analysis: cost-quality-utilization.
- **Dependencies**: Upstream: provider financial operations. Downstream: feeds CMS wage index calculations, DSH percentages, IME adjustments, hospital margin calculations.
- **Regulatory Basis**: 42 CFR 413.20 -- Medicare providers must submit annual cost reports. Social Security Act Sections 1815 and 1886 -- cost reporting requirements.

#### Verification Needed
- [ ] Confirm HCRIS download location and current extract date
- [ ] Verify availability of all cost report types (2552, 2540, 1728, 1984, FQHC, RHC)
- [ ] Check if CMS provides cost report documentation (record layout, worksheet descriptions)
- [ ] Verify whether HCRIS includes both as-submitted and settled reports

---

### 6.7 Part D Drug Event (PDE) Data

- **Category**: Claims / Drug
- **Publisher**: CMS (via ResDAC)
- **Access Level**: Research Only (DUA required; available through ResDAC/VRDC)
- **Format**: SAS / fixed-width
- **URL**: https://resdac.org/cms-data/files/pde (NEEDS VERIFICATION)
- **Update Frequency**: Annual
- **Size Estimate**: ~1.5 billion+ drug events per year; hundreds of GB
- **Key Fields**: `BENE_ID` (encrypted), `SRVC_DT`, `PRDSRVID` (NDC), `DAYS_SUPLY_NUM`, `QTY_DSPNSD_NUM`, `PTNT_PAY_AMT`, `OTHR_TROOP_AMT`, `LICS_AMT`, `PLRO_AMT`, `CVRD_D_PLAN_PD_AMT`, `NCVRD_PLAN_PD_AMT`, `TOT_RX_CST_AMT`, `PHRMCY_SRVC_TYPE_CD`
- **What It Contains**: Claim-level Part D prescription drug event records for all Medicare Part D beneficiaries. Each record represents a single prescription fill and includes the drug (by NDC), quantity, days supply, total cost, and the breakdown of who paid (beneficiary, plan, low-income subsidy, catastrophic coverage, other third-party). This is the most detailed Medicare drug spending dataset.
- **What It Does NOT Contain**: No diagnosis codes (cannot determine what the drug was prescribed for from PDE alone). Not publicly available. Requires DUA through ResDAC.
- **Why It Matters for Project PUF**: PDE data underlies the Part D Prescriber PUF. While not directly accessible for Project PUF, understanding PDE structure informs interpretation of the public Part D data and identifies analytical gaps.
- **Dependencies**: Upstream: Part D plan claims processing. Downstream: source for Part D PUFs, Drug Spending Dashboard, and Medicare drug spending analyses.
- **Regulatory Basis**: Social Security Act Section 1860D-15 -- Part D payment provisions requiring PDE data submission. MMA of 2003.

#### Verification Needed
- [ ] Confirm PDE access path through ResDAC
- [ ] Verify whether any PDE-derived public data products exist beyond the prescriber PUF
- [ ] Check if CMS Synthetic PDE data is available for testing

---

### 6.8 T-MSIS (Transformed Medicaid Statistical Information System)

- **Category**: Claims / Enrollment (Medicaid)
- **Publisher**: CMS (Medicaid)
- **Access Level**: Research Only (DUA required; T-MSIS Analytic Files available through ResDAC/VRDC)
- **Format**: SAS / structured files within VRDC environment
- **URL**: https://resdac.org/cms-data/files/tmsis (NEEDS VERIFICATION); also https://www.medicaid.gov/medicaid/data-and-systems/macbis/tmsis/index.html (NEEDS VERIFICATION)
- **Update Frequency**: Monthly submission by states; Analytic Files updated quarterly to annually
- **Size Estimate**: ~90 million Medicaid/CHIP enrollees; billions of claims per year; terabytes
- **Key Fields**: `BENE_ID` (Medicaid), `State_Code`, `Eligibility_Group`, `Managed_Care_Plan`, `Claim_Type` (IP, OT, Rx, LT), `Diagnosis_Codes`, `Procedure_Codes`, `Payment_Amount`
- **What It Contains**: The successor to the legacy MSIS, T-MSIS is the comprehensive Medicaid/CHIP claims and enrollment data system. Contains person-level enrollment data, inpatient claims, other therapy (outpatient/physician) claims, pharmacy claims, and long-term care claims for all Medicaid and CHIP beneficiaries in all states. The T-MSIS Analytic Files (TAF) are research-ready versions cleaned by CMS.
- **What It Does NOT Contain**: Not publicly available. State data quality varies significantly. Early T-MSIS years had substantial data quality issues. Does not include uncompensated care or services not covered by Medicaid.
- **Why It Matters for Project PUF**: T-MSIS is the Medicaid equivalent of Medicare SAF data. While restricted, it is the source for Medicaid-focused analyses and for understanding dual-eligible (Medicare-Medicaid) beneficiaries. Public Medicaid data products (SDUD, enrollment files) are derived from T-MSIS.
- **Dependencies**: Upstream: state Medicaid Management Information Systems (MMIS). Downstream: source for public Medicaid data products, Medicaid quality measures, dual-eligible analyses.
- **Regulatory Basis**: Social Security Act Section 1902(a)(6) -- state Medicaid reporting requirements. 42 CFR 431.300-431.306 -- Medicaid statistical reporting.

#### Verification Needed
- [ ] Confirm T-MSIS Analytic Files access path through ResDAC
- [ ] Verify current data quality assessments by state (DQ Atlas)
- [ ] Check which T-MSIS years are now considered research-quality

---

### 6.9 HCUP (Healthcare Cost and Utilization Project) -- AHRQ

- **Category**: Claims / Utilization (Multi-payer)
- **Publisher**: AHRQ (Agency for Healthcare Research and Quality)
- **Access Level**: Requires licensing agreement and fees; NOT freely public
- **Format**: SAS / ASCII; HCUPnet (online query tool) is free
- **URL**: https://www.hcup-us.ahrq.gov/ (NEEDS VERIFICATION); HCUPnet at https://hcupnet.ahrq.gov/ (NEEDS VERIFICATION)
- **Update Frequency**: Annual (with 18-24 month lag)
- **Size Estimate**: NIS (Nationwide Inpatient Sample): ~7 million discharges/year (20% stratified sample); SID (State Inpatient Databases): varies by state, 30+ states; NEDS, SASD, SEDD similarly
- **Key Fields**: `HCUP_Record_ID`, `DRG`, `DX1`-`DX40` (ICD-10-CM), `PR1`-`PR25` (ICD-10-PCS/CPT), `TOTCHG`, `LOS`, `AGE`, `RACE`, `PAY1` (expected payer), `ZIPINC_QRTL` (income quartile), `HOSP_BEDSIZE`, `HOSP_LOCTEACH`
- **What It Contains**: Multi-payer hospital discharge data from state partners. The Nationwide Inpatient Sample (NIS) is a 20% stratified sample of all U.S. hospital discharges (all payers, not just Medicare). State-level databases (SID, SEDD, SASD) contain all discharges/visits for participating states. HCUP data includes diagnosis codes, procedure codes, charges, length of stay, patient demographics, hospital characteristics, and expected payer. This is the only multi-payer hospital data available at the national level.
- **What It Does NOT Contain**: Not free (licensing fees apply). Not all states participate. Patient identifiers are removed. No physician-level data. APR-DRGs in HCUP require 3M license awareness.
- **Why It Matters for Project PUF**: HCUP is the only national multi-payer hospital data source. While licensing costs limit direct integration into Project PUF, HCUPnet (the free online query tool) provides aggregated statistics that can complement Medicare-only analyses.
- **Dependencies**: Upstream: state hospital discharge data systems, state data organizations. Downstream: widely used in health services research; NIS is the most-cited hospital discharge database.
- **Regulatory Basis**: AHRQ's statutory mission under the Healthcare Research and Quality Act of 1999 (42 USC 299). State participation is voluntary.

#### LICENSING WARNING
HCUP data requires a Data Use Agreement with AHRQ and associated fees. Individual-record data cannot be freely redistributed. HCUPnet (the online query tool) is free and can provide aggregate statistics.

#### Verification Needed
- [ ] Confirm current HCUP licensing terms and costs
- [ ] Verify which states participate in each HCUP database
- [ ] Check if HCUPnet API access exists for programmatic queries
- [ ] Verify whether HCUP has transitioned from APR-DRGs to a different severity adjustment

---

## 7. Enrollment & Beneficiary Data

---

### 7.1 Medicare Beneficiary Summary File (MBSF)

- **Category**: Enrollment / Beneficiary
- **Publisher**: CMS (via ResDAC)
- **Access Level**: LDS (Data Use Agreement required); Research Only for identifiable version
- **Format**: SAS / fixed-width
- **URL**: https://resdac.org/cms-data/files/mbsf-base (NEEDS VERIFICATION)
- **Update Frequency**: Annual
- **Size Estimate**: ~60-65 million Medicare beneficiaries per year; ~10-20 GB
- **Key Fields**: `BENE_ID` (encrypted), `STATE_CODE`, `COUNTY_CODE`, `ZIP_CODE`, `AGE_AT_END_REF_YR`, `SEX_IDENT_CD`, `RACE_CD`, `ENTLMT_RSN_ORIG` (original entitlement reason), `MDCR_STATUS_CODE_*` (monthly HI/SMI/HMO status), `DUAL_STUS_CD_*` (monthly dual-eligible status), Chronic Condition flags (27+ conditions)
- **What It Contains**: Annual summary of every Medicare beneficiary's enrollment status, demographics, and chronic conditions. The Base segment includes demographics, geographic identifiers (state, county, ZIP), monthly entitlement status (Part A, Part B, Part C, Part D), HMO indicator, dual-eligible status, and original reason for entitlement (age, disability, ESRD). The Chronic Conditions segment flags 27+ chronic conditions based on claims-based algorithms. The Cost & Utilization segment summarizes annual utilization and payments by claim type.
- **What It Does NOT Contain**: Not publicly available (requires DUA). LDS version has encrypted beneficiary IDs. No individual claims data (summary-level only). Geographic identifiers limited in LDS version.
- **Why It Matters for Project PUF**: The MBSF is the denominator file for all Medicare analyses. It defines the population at risk. While not directly available for Project PUF, public aggregate data products (Geographic Variation PUF, Chronic Conditions dashboard) are derived from MBSF data.
- **Dependencies**: Upstream: CMS enrollment systems, Medicare claims (for chronic conditions). Downstream: denominator for all per-capita analyses; source for aggregate enrollment and chronic condition statistics.
- **Regulatory Basis**: Social Security Act Title XVIII -- Medicare program administration. CMS data governance policies.

#### Verification Needed
- [ ] Confirm ResDAC access path and timeline
- [ ] Verify whether any MBSF-derived public aggregates are available beyond existing PUFs
- [ ] Check if CMS Chronic Conditions Data Warehouse public statistics are current

---

### 7.2 Medicare Advantage Enrollment Files (Monthly)

- **Category**: Enrollment
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-advantagepart-d-contract-and-enrollment-data (NEEDS VERIFICATION)
- **Update Frequency**: Monthly
- **Size Estimate**: ~50,000+ rows per month (contract x plan x county); annual files ~500K+ rows; ~50-200 MB per year
- **Key Fields**: `Contract_Number`, `Plan_ID`, `State`, `County`, `FIPS_State_County_Code`, `Enrollment`
- **What It Contains**: Monthly enrollment counts by Medicare Advantage contract, plan, and county. Enables tracking of MA enrollment trends, plan market share, and county-level MA penetration rates. Also includes separate files for Special Needs Plans (SNPs), Employer Group Waiver Plans (EGWPs), and Part D enrollment.
- **What It Does NOT Contain**: No beneficiary-level data. No clinical data. No plan financial data (bids, rebates). Enrollment counts only -- no utilization or spending.
- **Why It Matters for Project PUF**: Previously cataloged in the initial 12-source inventory. Included here for completeness. MA enrollment is essential context for all FFS utilization analysis, as MA enrollment now exceeds 50% of Medicare beneficiaries in many markets.
- **Dependencies**: Upstream: CMS MA enrollment systems. Downstream: enables MA market analysis, FFS denominator adjustment, plan competition studies.
- **Regulatory Basis**: Social Security Act Section 1851 -- MA enrollment provisions.

#### Verification Needed
- [ ] Confirm monthly enrollment file download location
- [ ] Verify whether SNP and EGWP breakdowns are in separate files
- [ ] Check most recent available month

---

### 7.3 Part D Enrollment Files

- **Category**: Enrollment
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-advantagepart-d-contract-and-enrollment-data/part-d-contract-and-enrollment-data (NEEDS VERIFICATION)
- **Update Frequency**: Monthly
- **Size Estimate**: ~50,000+ rows per month (contract x plan x state/county); ~50-200 MB per year
- **Key Fields**: `Contract_Number`, `Plan_ID`, `State`, `County`, `FIPS_State_County_Code`, `Enrollment`, `Plan_Type` (PDP, MA-PD)
- **What It Contains**: Monthly enrollment counts for Medicare Part D prescription drug plans, both standalone PDPs and Medicare Advantage-Prescription Drug plans (MA-PDs). Shows enrollment by contract, plan, and geography. Enables tracking of Part D plan market share and enrollment trends.
- **What It Does NOT Contain**: No prescription drug utilization or spending data. No plan formulary information. No premium or cost-sharing data in enrollment files.
- **Why It Matters for Project PUF**: Part D enrollment context is essential for interpreting Part D Prescriber PUF data. Understanding plan market dynamics (PDP vs. MA-PD) informs drug policy analysis.
- **Dependencies**: Upstream: CMS Part D enrollment systems. Downstream: denominators for Part D utilization analysis; plan market studies.
- **Regulatory Basis**: Social Security Act Section 1860D -- Medicare Part D provisions. MMA of 2003.

#### Verification Needed
- [ ] Confirm Part D enrollment file download location
- [ ] Verify whether PDP and MA-PD enrollment are in the same or separate files
- [ ] Check if Low-Income Subsidy (LIS) enrollment counts are available publicly

---

### 7.4 Medicaid Enrollment Data

- **Category**: Enrollment (Medicaid)
- **Publisher**: CMS (Medicaid.gov)
- **Access Level**: Fully Public
- **Format**: CSV / PDF
- **URL**: https://data.medicaid.gov/datasets?theme=Enrollment (NEEDS VERIFICATION); also https://www.medicaid.gov/medicaid/program-information/medicaid-and-chip-enrollment-data/index.html (NEEDS VERIFICATION)
- **Update Frequency**: Monthly (Medicaid.gov reports); annual (detailed breakdowns)
- **Size Estimate**: 50 states + DC + territories; ~5,000-10,000 rows for detailed breakdowns; <50 MB
- **Key Fields**: `State`, `Year`, `Month`, `Total_Medicaid_Enrollment`, `CHIP_Enrollment`, `Medicaid_Expansion_Enrollment`, `Eligibility_Group`
- **What It Contains**: State-level Medicaid and CHIP enrollment counts, with breakdowns by eligibility group (children, adults, aged, blind/disabled, expansion adults), managed care vs. FFS, and monthly enrollment trends. The Performance Indicator project provides more detailed enrollment statistics.
- **What It Does NOT Contain**: No beneficiary-level data. No claims or spending data. Limited demographic breakdowns. State reporting lag and quality varies.
- **Why It Matters for Project PUF**: Medicaid enrollment is the primary denominator for Medicaid analyses. Understanding Medicaid enrollment by state and eligibility group provides context for SDUD data and Medicaid spending analyses.
- **Dependencies**: Upstream: state Medicaid enrollment systems, T-MSIS. Downstream: denominators for Medicaid analyses, Medicaid expansion impact studies.
- **Regulatory Basis**: Social Security Act Title XIX -- Medicaid; ACA Section 2001 (Medicaid expansion).

#### Verification Needed
- [ ] Confirm current Medicaid.gov enrollment data download locations
- [ ] Verify latency of monthly enrollment reports
- [ ] Check if eligibility group breakdowns are available for all states

---

### 7.5 CHIP Enrollment Data

- **Category**: Enrollment (CHIP)
- **Publisher**: CMS (Medicaid.gov)
- **Access Level**: Fully Public
- **Format**: CSV / PDF
- **URL**: https://www.medicaid.gov/medicaid/program-information/medicaid-and-chip-enrollment-data/index.html (NEEDS VERIFICATION)
- **Update Frequency**: Monthly to annual
- **Size Estimate**: 50 states + DC + territories; <5,000 rows; <10 MB
- **Key Fields**: `State`, `Year`, `Month`, `CHIP_Enrollment`, `Separate_CHIP`, `Medicaid_Expansion_CHIP`
- **What It Contains**: State-level enrollment in the Children's Health Insurance Program, including breakdowns by separate CHIP programs and Medicaid-expansion CHIP. CHIP covers children in families with incomes too high for Medicaid but too low for affordable private coverage.
- **What It Does NOT Contain**: No beneficiary-level data. No utilization or spending data. Limited demographic detail.
- **Why It Matters for Project PUF**: Completes the public insurance enrollment picture (Medicare + Medicaid + CHIP). Important for pediatric health policy analysis.
- **Dependencies**: Upstream: state CHIP enrollment data, T-MSIS. Downstream: completes public insurance coverage analysis.
- **Regulatory Basis**: Social Security Act Title XXI -- CHIP. Balanced Budget Act of 1997. Various reauthorizations (CHIPRA 2009, ACA, HEALTHY KIDS Act).

#### Verification Needed
- [ ] Confirm CHIP enrollment data availability and format
- [ ] Check if CHIP enrollment is combined with Medicaid enrollment reporting or separate

---

### 7.6 Medicare-Medicaid Dual-Eligible Data

- **Category**: Enrollment / Cross-Program
- **Publisher**: CMS (Medicare-Medicaid Coordination Office)
- **Access Level**: Partially Public (aggregate data public; individual-level requires DUA)
- **Format**: CSV / PDF (aggregate reports); SAS (individual-level through ResDAC)
- **URL**: https://www.cms.gov/medicare-medicaid-coordination/medicare-and-medicaid-coordination/medicare-medicaid-coordination-office/analytics (NEEDS VERIFICATION)
- **Update Frequency**: Annual
- **Size Estimate**: ~12 million dual-eligible beneficiaries; aggregate reports <10 MB; individual files through ResDAC
- **Key Fields**: Aggregate: `State`, `Dual_Status_Category` (full-benefit, partial-benefit, QMB, SLMB, QI, QDWI), `Enrollment_Count`, `Per_Capita_Spending`
- **What It Contains**: Aggregate statistics on Medicare-Medicaid dual-eligible beneficiaries, including enrollment counts by state and dual status category, spending breakdowns (Medicare FFS, Medicare MA, Medicaid), utilization patterns, and demographic profiles. The Medicare-Medicaid Coordination Office publishes data briefs and analytic reports. Individual-level dual-eligible data is available through ResDAC as part of the MBSF.
- **What It Does NOT Contain**: Individual-level data is not publicly available. State-level Medicaid spending for duals is incomplete in aggregate files due to state reporting variation. No integrated Medicare+Medicaid claims at the public level.
- **Why It Matters for Project PUF**: Dual-eligible beneficiaries account for ~20% of Medicare beneficiaries but ~35% of Medicare spending. Understanding this population is critical for any comprehensive Medicare spending analysis.
- **Dependencies**: Upstream: Medicare enrollment (MBSF), Medicaid enrollment (T-MSIS). Downstream: enables dual-eligible population analysis; contextualizes Medicare spending analyses.
- **Regulatory Basis**: ACA Section 2602 -- established the Medicare-Medicaid Coordination Office. Social Security Act Sections 1902(a)(10) and 1905(p) -- dual-eligible provisions.

#### Verification Needed
- [ ] Confirm current dual-eligible data product availability
- [ ] Verify whether state-level dual-eligible dashboards/datasets exist on data.cms.gov
- [ ] Check if the Medicare-Medicaid Linked Enrollee Analytic Data Source (MMLEADS) is available publicly

---

### 7.7 Medicare Entitlement/Eligibility Reference Data

- **Category**: Enrollment / Reference
- **Publisher**: CMS
- **Access Level**: Aggregate statistics Fully Public; individual data via ResDAC
- **Format**: Various (CMS Data Compendium, Medicare & Medicaid Statistical Supplement)
- **URL**: https://www.cms.gov/data-research/statistics-trends-and-reports/cms-statistics-reference-booklet (NEEDS VERIFICATION); also https://data.cms.gov/summary-statistics-on-beneficiary-enrollment/ (NEEDS VERIFICATION)
- **Update Frequency**: Annual
- **Size Estimate**: Aggregate tables; <10 MB
- **Key Fields**: `Year`, `Total_Medicare_Enrollment`, `Part_A_Only`, `Part_A_and_B`, `Part_C_Enrollment`, `Part_D_Enrollment`, `Original_Reason_for_Entitlement` (age, disability, ESRD), `State`
- **What It Contains**: Aggregate Medicare enrollment and entitlement statistics, including total enrollment by Part (A, B, C, D), original reason for entitlement (age 65+, disability, ESRD), age distribution, sex distribution, and state-level breakdowns. The CMS Statistics Reference Booklet and Medicare & Medicaid Statistical Supplement provide comprehensive historical statistics.
- **What It Does NOT Contain**: No individual beneficiary data. No claims or spending data in enrollment reference files.
- **Why It Matters for Project PUF**: Provides the big-picture Medicare enrollment context. Essential for understanding the denominator before analyzing utilization or spending data.
- **Dependencies**: Upstream: CMS enrollment systems. Downstream: provides context and denominators for all Medicare analyses.
- **Regulatory Basis**: Social Security Act Title XVIII -- Medicare eligibility provisions (Sections 226, 226A).

#### Verification Needed
- [ ] Confirm CMS Statistics Reference Booklet availability and current edition
- [ ] Verify data.cms.gov enrollment summary datasets
- [ ] Check if Medicare Trustees Report statistical appendices are available in downloadable format

---

## 8. Quality & Outcomes

---

### 8.1 CMS Quality Measure Specifications

- **Category**: Quality / Reference
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: PDF (measure specifications); Excel (code value sets); ZIP archives
- **URL**: https://www.cms.gov/medicare/quality/measures (NEEDS VERIFICATION); eCQM specifications at https://ecqi.healthit.gov/ (NEEDS VERIFICATION)
- **Update Frequency**: Annual (with payment rule updates)
- **Size Estimate**: Hundreds of measure specifications; code value sets vary; total ~100-500 MB
- **Key Fields**: `Measure_ID`, `Measure_Name`, `Measure_Type` (outcome, process, structural, patient experience), `Data_Source`, `NQF_Number`, `Value_Set_OID`, `Code_System` (ICD-10-CM, CPT, SNOMED, etc.)
- **What It Contains**: Complete specifications for all CMS quality measures across programs: Hospital IQR/VBP, Hospital OQR, MIPS, ACO Quality, SNF QRP, HHA QRP, Hospice QRP, ESRD QIP, and more. Each measure specification defines the numerator, denominator, exclusions, and the code value sets used to identify qualifying patients and events. eCQM (electronic Clinical Quality Measure) specifications use CQL (Clinical Quality Language) and are fully computable.
- **What It Does NOT Contain**: Specifications only -- no actual performance data (that is in Care Compare and other reporting files). Implementing measures from specifications requires claims or clinical data.
- **Why It Matters for Project PUF**: Quality measure specifications define how quality scores in Care Compare and other public reporting programs are calculated. Understanding the specifications is essential for interpreting quality data and for identifying which code systems and diagnoses drive quality measures.
- **Dependencies**: Upstream: NQF endorsement process, CMS rulemaking. Downstream: defines quality measures reported in Care Compare, MIPS, VBP, and other quality programs.
- **Regulatory Basis**: Social Security Act Sections 1886(b)(3)(B) (hospital VBP), 1848(q) (MIPS), and various other sections establishing quality reporting programs.

#### Verification Needed
- [ ] Confirm current measure specification download locations by program
- [ ] Verify eCQI resource center availability
- [ ] Check if code value sets are available in machine-readable format (VSAC -- Value Set Authority Center)

---

### 8.2 Hospital Readmission Rates (HRRP Data)

- **Category**: Quality / Outcomes
- **Publisher**: CMS (Care Compare)
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://data.cms.gov/provider-data/dataset/9n3s-kdb3 (NEEDS VERIFICATION)
- **Update Frequency**: Annual (updated with Care Compare refresh)
- **Size Estimate**: ~4,000-5,000 hospitals x ~6 conditions; ~50,000-100,000 rows; <50 MB
- **Key Fields**: `Facility_ID` (CCN), `Facility_Name`, `Measure_ID` (e.g., READM_30_AMI, READM_30_HF, READM_30_PN, READM_30_COPD, READM_30_HIP_KNEE, READM_30_CABG), `Score`, `Compared_to_National`, `Denominator`, `Lower_Estimate`, `Upper_Estimate`
- **What It Contains**: Hospital-level 30-day risk-standardized readmission rates for specific conditions: acute myocardial infarction (AMI), heart failure (HF), pneumonia, COPD, hip/knee replacement, and CABG surgery. Also includes the Hospital-Wide Readmission measure (all-cause). Rates are risk-adjusted for patient characteristics. Each hospital receives a point estimate, confidence interval, and comparison to the national rate (better/same/worse).
- **What It Does NOT Contain**: No patient-level data. No readmission detail (which diagnoses triggered the readmission). Risk adjustment methodology is complex; the published rate is a single number that obscures significant methodological choices.
- **Why It Matters for Project PUF**: Readmission rates directly affect hospital payment through the Hospital Readmissions Reduction Program (HRRP). These measures are high-profile policy tools. Combined with hospital financial data, they enable analysis of the HRRP's financial impact.
- **Dependencies**: Upstream: Medicare FFS claims data. Downstream: feeds HRRP payment adjustments, Care Compare reporting, hospital VBP program.
- **Regulatory Basis**: ACA Section 3025 -- Hospital Readmissions Reduction Program. Social Security Act Section 1886(q).

#### Verification Needed
- [ ] Confirm current readmission data download location
- [ ] Verify which conditions/measures are currently included (list has expanded over time)
- [ ] Check if excess readmission ratio (ERR) data is published separately for HRRP penalty calculations

---

### 8.3 Hospital-Acquired Condition (HAC) Reduction Program Data

- **Category**: Quality / Outcomes
- **Publisher**: CMS (Care Compare)
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://data.cms.gov/provider-data/ (hospital section) (NEEDS VERIFICATION)
- **Update Frequency**: Annual
- **Size Estimate**: ~3,000-4,000 hospitals; <10 MB
- **Key Fields**: `Facility_ID` (CCN), `Total_HAC_Score`, `Domain_1_Score` (Patient Safety Indicator composite), `Domain_2_Score` (CDC NHSN measures), `Payment_Reduction` (Yes/No)
- **What It Contains**: Hospital-level scores under the HAC Reduction Program, which penalizes the worst-performing quartile of hospitals on healthcare-acquired conditions. The Total HAC Score combines two domains: Patient Safety and Adverse Events Composite (AHRQ PSI 90) and healthcare-associated infections (from CDC NHSN: CLABSI, CAUTI, SSI, MRSA, C. diff). Hospitals in the worst-performing 25% receive a 1% payment reduction on all Medicare discharges.
- **What It Does NOT Contain**: No individual HAC event counts. No patient-level infection data. Does not show which specific infections drove the score.
- **Why It Matters for Project PUF**: HAC penalties directly affect hospital revenue. Combined with hospital financial data, enables analysis of safety net hospital penalty burden (a significant health equity issue, as safety net hospitals disproportionately receive HAC penalties).
- **Dependencies**: Upstream: Medicare claims (PSI 90), CDC NHSN infection surveillance data. Downstream: affects hospital payment, Care Compare reporting.
- **Regulatory Basis**: ACA Section 3008 -- HAC Reduction Program. Social Security Act Section 1886(p).

#### Verification Needed
- [ ] Confirm current HAC data download location
- [ ] Verify which measures are currently in each domain
- [ ] Check if CMS publishes individual measure scores or only domain/total scores

---

### 8.4 Patient Safety Indicator (PSI) Data

- **Category**: Quality / Outcomes
- **Publisher**: AHRQ (specifications) / CMS (hospital-level results via Care Compare)
- **Access Level**: Fully Public (hospital-level results); AHRQ PSI software free
- **Format**: CSV (CMS results); SAS (AHRQ software)
- **URL**: https://qualityindicators.ahrq.gov/measures/psi_resources (AHRQ) (NEEDS VERIFICATION); CMS results via Care Compare
- **Update Frequency**: Annual (AHRQ updates PSI specifications); CMS results updated with Care Compare
- **Size Estimate**: ~4,000-5,000 hospitals for PSI 90 composite; <10 MB
- **Key Fields**: `Facility_ID`, `PSI_Measure` (PSI 90 composite or individual PSIs), `Observed_Rate`, `Expected_Rate`, `Risk_Adjusted_Rate`
- **What It Contains**: Patient Safety Indicators are claims-based measures of potentially avoidable complications and adverse events during hospitalization. PSI 90 is a composite of multiple individual PSIs (pressure ulcers, iatrogenic pneumothorax, post-op hemorrhage, etc.). AHRQ publishes the complete PSI specification software. CMS publishes hospital-level PSI 90 results as part of Care Compare and the HAC Reduction Program.
- **What It Does NOT Contain**: No individual adverse event counts at the public hospital level. PSI specifications rely on ICD-10 coding, which may miss events not coded and may flag false positives.
- **Why It Matters for Project PUF**: PSIs are the primary claims-based patient safety measures. PSI 90 directly affects hospital payment through the HAC Reduction Program and Hospital VBP Program. AHRQ's PSI software can be applied to any ICD-10-coded claims data.
- **Dependencies**: Upstream: ICD-10-CM/PCS coded claims. Downstream: feeds HAC Reduction Program, VBP Program, Care Compare.
- **Regulatory Basis**: AHRQ mandate under 42 USC 299 (quality measures development). CMS adoption in HAC and VBP programs per ACA.

#### Verification Needed
- [ ] Confirm AHRQ PSI software download availability
- [ ] Verify which individual PSIs are included in PSI 90 (the composition changes periodically)
- [ ] Check if AHRQ publishes hospital-level PSI data independently of CMS

---

### 8.5 Nursing Home Five-Star Quality Rating Data Files

- **Category**: Quality / Outcomes
- **Publisher**: CMS (Nursing Home Compare / Care Compare)
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://data.cms.gov/provider-data/topics/nursing-homes (NEEDS VERIFICATION)
- **Update Frequency**: Monthly (star ratings recalculated monthly)
- **Size Estimate**: ~15,000 facilities; multiple files totaling ~100-300 MB
- **Key Fields**: `Federal_Provider_Number` (CCN), `Overall_Rating` (1-5 stars), `Health_Inspection_Rating`, `Staffing_Rating`, `Quality_Measure_Rating`, individual quality measure scores, health inspection deficiency details, staffing hours
- **What It Contains**: Complete Five-Star Quality Rating System data for all Medicare/Medicaid-certified nursing homes. The overall rating combines three domain ratings: health inspections (based on survey deficiencies, complaints, and complaint investigations), staffing (based on PBJ-reported nurse staffing levels), and quality measures (based on MDS-reported clinical outcomes). Individual files provide detailed deficiency data, staffing levels by category, and quality measure performance.
- **What It Does NOT Contain**: No resident-level data. The star rating methodology involves complex percentile-based scoring that is not transparent in the data files themselves. Staffing data may undercount contract/agency staff.
- **Why It Matters for Project PUF**: The Five-Star system is the primary public-facing nursing home quality tool. It directly affects consumer choice and regulatory scrutiny. Combined with cost report and staffing data, enables deep analysis of what drives quality in long-term care.
- **Dependencies**: Upstream: CASPER survey data, PBJ staffing data, MDS quality measure data. Downstream: CMS Nursing Home Compare, state regulatory actions, consumer information.
- **Regulatory Basis**: ACA Section 6103 -- required CMS to implement a five-star quality rating system for nursing homes. OBRA '87 nursing home reform provisions.

#### Verification Needed
- [ ] Confirm current Five-Star data file download location
- [ ] Verify whether the star rating calculation methodology is documented in a publicly available technical guide
- [ ] Check if abuse/neglect citation data is included in the deficiency files

---

### 8.6 CAHPS Survey Data (Consumer Assessment of Healthcare Providers and Systems)

- **Category**: Quality / Patient Experience
- **Publisher**: CMS / AHRQ
- **Access Level**: Fully Public (facility-level aggregated results); individual survey responses are not public
- **Format**: CSV (via Care Compare)
- **URL**: https://data.cms.gov/provider-data/ (various provider types) (NEEDS VERIFICATION); AHRQ CAHPS at https://www.ahrq.gov/cahps/ (NEEDS VERIFICATION)
- **Update Frequency**: Annual to biannual (varies by survey)
- **Size Estimate**: Hospital HCAHPS: ~4,000 hospitals; Home Health HHCAHPS: ~9,000 agencies; CAHPS Hospice: ~4,000 hospices; <50 MB total
- **Key Fields**: `Facility_ID` (CCN), `Measure_ID`, `Patient_Survey_Star_Rating`, `HCAHPS_Answer_Percent`, `Survey_Response_Rate`, `Number_of_Completed_Surveys`
- **What It Contains**: Standardized patient experience survey results aggregated to the facility level. HCAHPS (Hospital CAHPS) covers communication, responsiveness, hospital environment, discharge information, and overall rating. HHCAHPS covers home health patient experience. CAHPS Hospice covers hospice care experience. Results are reported as percentages giving each response level (Always/Usually/Sometimes/Never) and summary star ratings.
- **What It Does NOT Contain**: No individual survey responses. Survey is limited to a sample of patients. Non-response bias is a known concern (sicker patients less likely to respond). Does not cover outpatient or physician office visits in the same way.
- **Why It Matters for Project PUF**: Patient experience is a key quality domain. HCAHPS scores affect hospital payment through the VBP Program. Combining patient experience with clinical quality and cost data creates a comprehensive provider quality profile.
- **Dependencies**: Upstream: CAHPS survey administration (contracted survey vendors). Downstream: feeds VBP payment adjustments, Care Compare star ratings, consumer information.
- **Regulatory Basis**: Social Security Act Section 1886(b)(3)(B)(viii) -- HCAHPS required for IQR program. ACA Section 3001 -- HCAHPS in VBP Program. CAHPS Hospice Survey mandated by ACA.

#### Verification Needed
- [ ] Confirm HCAHPS data download location within Care Compare
- [ ] Verify availability of HHCAHPS and CAHPS Hospice data in downloadable format
- [ ] Check if CAHPS for ACOs, MA plans, or other settings are publicly available

---

### 8.7 Dialysis Facility Compare Data

- **Category**: Quality / Outcomes
- **Publisher**: CMS (Dialysis Facility Compare / Care Compare)
- **Access Level**: Fully Public
- **Format**: CSV
- **URL**: https://data.cms.gov/provider-data/topics/dialysis-facilities (NEEDS VERIFICATION)
- **Update Frequency**: Quarterly
- **Size Estimate**: ~7,500 facilities; multiple quality measure files; <100 MB total
- **Key Fields**: `CCN`, `Facility_Name`, `Five_Star_Rating`, `Kt/V_Dialysis_Adequacy`, `Hypercalcemia_Rate`, `Patient_Survival`, `Patient_Hospitalization`, `Transfusion_Rate`, `Fistula_Rate`, `SWR` (Standardized Mortality Ratio), `SHR` (Standardized Hospitalization Ratio)
- **What It Contains**: Clinical quality measures for all Medicare-certified ESRD dialysis facilities. Includes dialysis adequacy (Kt/V), anemia management (transfusion rate), vascular access (fistula rate), infection rates (bloodstream infections), mineral metabolism (hypercalcemia), patient survival (standardized mortality ratio), hospitalization (standardized hospitalization ratio), and patient experience (ICH-CAHPS survey results). Five-star quality rating composite.
- **What It Does NOT Contain**: No patient-level data. No financial data. Does not distinguish home vs. in-center patient outcomes clearly. Does not capture non-Medicare dialysis patients.
- **Why It Matters for Project PUF**: Dialysis is a highly regulated, data-rich domain with direct payment-quality linkage through the ESRD Quality Incentive Program (QIP). The market concentration (DaVita/Fresenius) makes quality-competition analysis particularly interesting.
- **Dependencies**: Upstream: CROWNWeb clinical data, CDC NHSN infection data, ICH-CAHPS survey. Downstream: feeds ESRD QIP payment adjustments, Care Compare, consumer information.
- **Regulatory Basis**: Social Security Act Section 1881(h) -- ESRD QIP. Medicare Improvements for Patients and Providers Act (MIPPA) of 2008.

#### Verification Needed
- [ ] Confirm current Dialysis Facility Compare data structure
- [ ] Verify which quality measures are currently included (CMS updates the measure set periodically)
- [ ] Check if ESRD QIP Total Performance Score data is included in public files

---

## 9. Open Data Portals

> These are not individual datasets but comprehensive portals hosting hundreds of datasets each. They serve as discovery mechanisms for datasets not individually cataloged above.

---

### 9.1 data.cms.gov

- **Category**: Open Data Portal
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: CSV / JSON / API (Socrata-based platform)
- **URL**: https://data.cms.gov/ (NEEDS VERIFICATION)
- **Update Frequency**: Varies by dataset (real-time to annual)
- **Size Estimate**: 200+ datasets across provider data, spending, enrollment, quality, and more
- **Key Fields**: Varies by dataset
- **What It Contains**: CMS's primary open data platform. Hosts downloadable datasets and APIs for: provider characteristics, quality of care, spending, utilization, enrollment, Medicare-Medicaid coordination, and more. The platform uses the Socrata data platform, which provides built-in API access, filtering, and visualization for all hosted datasets. Major dataset categories include: Provider Data (Care Compare), Summary Statistics, Medicare Claims Data Aggregates, and Provider Enrollment data.
- **What It Does NOT Contain**: Does not host individual-level claims or enrollment data (those require ResDAC). Some datasets are snapshots while the source data is updated more frequently.
- **Why It Matters for Project PUF**: The primary discovery portal for CMS public data. Many datasets cataloged individually in this inventory are hosted on data.cms.gov. The Socrata API provides programmatic access that can feed Project PUF's acquisition pipelines.
- **Dependencies**: Upstream: CMS data systems. Downstream: distributes the majority of CMS public data products.
- **Regulatory Basis**: Open Government Directive (2009), DATA Act (2014), OPEN Government Data Act (2018) -- requiring federal agencies to publish data in open, machine-readable formats.

#### Verification Needed
- [ ] Confirm data.cms.gov is still active and Socrata-based
- [ ] Catalog the full list of available datasets (200+)
- [ ] Verify API access terms and rate limits
- [ ] Check if any datasets have migrated away from data.cms.gov

---

### 9.2 data.medicaid.gov

- **Category**: Open Data Portal
- **Publisher**: CMS (Medicaid)
- **Access Level**: Fully Public
- **Format**: CSV / JSON / API (Socrata-based)
- **URL**: https://data.medicaid.gov/ (NEEDS VERIFICATION)
- **Update Frequency**: Varies by dataset
- **Size Estimate**: 50+ datasets covering enrollment, spending, drug utilization, managed care, and more
- **Key Fields**: Varies by dataset
- **What It Contains**: Medicaid-specific open data portal. Hosts the State Drug Utilization Data (SDUD), Medicaid enrollment statistics, Medicaid managed care enrollment, state plan amendments, Medicaid drug rebate data (aggregate), CHIP enrollment, Medicaid spending by state, and quality measures. Also provides API access through the Socrata platform.
- **What It Does NOT Contain**: No individual-level Medicaid claims or enrollment data. T-MSIS data is not available through this portal. State-level data quality varies.
- **Why It Matters for Project PUF**: The primary portal for public Medicaid data. SDUD (cataloged above) is hosted here. The Socrata API enables programmatic access for pipeline integration.
- **Dependencies**: Upstream: state Medicaid agency data, T-MSIS. Downstream: distributes public Medicaid data products.
- **Regulatory Basis**: Same open data mandates as data.cms.gov.

#### Verification Needed
- [ ] Confirm data.medicaid.gov is active
- [ ] Catalog available datasets
- [ ] Verify API access

---

### 9.3 HealthData.gov

- **Category**: Open Data Portal
- **Publisher**: HHS (Department of Health and Human Services)
- **Access Level**: Fully Public
- **Format**: Various (CSV, JSON, API, links to source agency portals)
- **URL**: https://healthdata.gov/ (NEEDS VERIFICATION)
- **Update Frequency**: Varies (acts as an aggregator/catalog)
- **Size Estimate**: 3,000+ dataset listings (many are links to datasets on other portals)
- **Key Fields**: Varies by dataset
- **What It Contains**: HHS-wide health data catalog aggregating datasets from CMS, CDC, FDA, HRSA, SAMHSA, AHRQ, NIH, and other HHS agencies. Acts as a meta-portal -- many listings link to datasets hosted on agency-specific portals (data.cms.gov, data.cdc.gov, etc.). Also hosts some unique datasets, particularly COVID-19 data and cross-agency datasets. Uses the DKAN open data platform.
- **What It Does NOT Contain**: Many listings are catalog entries (metadata) that link to external sources rather than hosting data directly. Discovery can be challenging due to inconsistent metadata quality.
- **Why It Matters for Project PUF**: Useful as a discovery tool for datasets across all HHS agencies. May surface datasets not found on individual agency portals. The COVID-19 data hosted here was particularly valuable.
- **Dependencies**: Upstream: all HHS agency data systems. Downstream: discovery layer for cross-agency datasets.
- **Regulatory Basis**: Open Government Directive; OPEN Government Data Act.

#### Verification Needed
- [ ] Confirm healthdata.gov is still active and maintained
- [ ] Check if the portal has been restructured or merged with other data.gov sites
- [ ] Verify whether COVID-19 data remains available

---

### 9.4 data.hrsa.gov

- **Category**: Open Data Portal
- **Publisher**: HRSA (Health Resources and Services Administration)
- **Access Level**: Fully Public
- **Format**: CSV / JSON / API
- **URL**: https://data.hrsa.gov/ (NEEDS VERIFICATION)
- **Update Frequency**: Varies by dataset
- **Size Estimate**: 50+ datasets covering health center data, workforce, shortage areas, and more
- **Key Fields**: Varies by dataset
- **What It Contains**: HRSA open data portal hosting datasets on: Federally Qualified Health Centers (FQHCs) and other safety net providers (UDS -- Uniform Data System), Health Professional Shortage Areas (HPSAs), Medically Underserved Areas/Populations (MUA/P), National Health Service Corps, Area Health Resources Files, Ryan White HIV/AIDS Program data, Maternal and Child Health data, and organ transplantation data (OPTN/SRTR). The Area Health Resources File (AHRF) is particularly valuable -- it's a county-level database of healthcare resources and socioeconomic indicators.
- **What It Does NOT Contain**: No individual patient or provider claims data. FQHC data is aggregate (UDS reporting), not claim-level.
- **Why It Matters for Project PUF**: HRSA data complements CMS data by focusing on healthcare access, workforce, and safety net providers. HPSAs and MUA/P designations affect CMS payment (HPSA bonuses). The AHRF is an excellent county-level reference file.
- **Dependencies**: Upstream: HRSA program data, state primary care offices. Downstream: HPSA data affects Medicare physician payment bonuses; AHRF provides demographic context.
- **Regulatory Basis**: Public Health Service Act Section 332 (HPSAs), Section 330 (FQHCs). OPEN Government Data Act.

#### Verification Needed
- [ ] Confirm data.hrsa.gov is active
- [ ] Verify AHRF availability and current version
- [ ] Check HPSA data download format and update frequency

---

### 9.5 CDC WONDER

- **Category**: Open Data Portal / Public Health
- **Publisher**: CDC (Centers for Disease Control and Prevention)
- **Access Level**: Fully Public (some restricted data requires agreement to terms)
- **Format**: Web-based query system; results downloadable as tab-delimited text
- **URL**: https://wonder.cdc.gov/ (NEEDS VERIFICATION)
- **Update Frequency**: Varies by database (vital statistics: annual; some near-real-time)
- **Size Estimate**: Dozens of databases; vital statistics alone cover billions of records (but accessed via aggregated queries, not bulk download)
- **Key Fields**: Varies by database; vital statistics: `County`, `Year`, `Age_Group`, `Cause_of_Death` (ICD-10), `Deaths`, `Population`, `Crude_Rate`, `Age_Adjusted_Rate`
- **What It Contains**: CDC's online query system for public health data. Major databases include: mortality data (underlying cause of death, multiple cause of death, by county/state/national, 1968-present), natality data (births, by county/state), population estimates, vaccine adverse events (VAERS), tuberculosis, STD surveillance, environmental health data, and more. Users construct queries through a web interface and download results. The mortality data (based on death certificates, coded with ICD-10) is particularly valuable for healthcare outcomes analysis.
- **What It Does NOT Contain**: Not a bulk download system (queries are interactive). Results are aggregated -- no individual-level records accessible through WONDER. Suppression rules apply to small cell counts. Cannot download the full underlying microdata through WONDER (some microdata available through NCHS/ResDAC).
- **Why It Matters for Project PUF**: Mortality data from CDC WONDER provides the ultimate outcomes measure -- death rates by cause, geography, age, race, and time. When combined with CMS utilization and spending data, enables mortality-spending correlation analysis. Population data from WONDER can serve as denominators.
- **Dependencies**: Upstream: vital statistics from state registrars, NCHS. Downstream: enables mortality analysis, population health trending, and outcomes research.
- **Regulatory Basis**: Public Health Service Act. CDC's mandate for disease surveillance and vital statistics.

#### Verification Needed
- [ ] Confirm CDC WONDER is still available and active
- [ ] Verify whether bulk data download is possible or only interactive queries
- [ ] Check if API access to WONDER data exists
- [ ] Confirm most recent mortality data year available

---

### 9.6 FDA Open Data (openFDA)

- **Category**: Open Data Portal
- **Publisher**: FDA (Food and Drug Administration)
- **Access Level**: Fully Public
- **Format**: JSON API; bulk download in JSON/CSV
- **URL**: https://open.fda.gov/ (NEEDS VERIFICATION)
- **Update Frequency**: Varies (NDC Directory: weekly; adverse events: quarterly; approvals: as they occur)
- **Size Estimate**: Millions of records across multiple databases
- **Key Fields**: Varies by endpoint; drug endpoints include `brand_name`, `generic_name`, `ndc`, `application_number`, `manufacturer_name`, `route`, `dosage_form`
- **What It Contains**: FDA's open data platform providing API access to: drug adverse event reports (FAERS), drug product labeling, drug NDC directory, device adverse events (MAUDE), device recalls, food enforcement reports, and drug approval data (Drugs@FDA). The drug endpoints are particularly relevant -- FAERS data enables pharmacovigilance analysis, and Drugs@FDA provides approval history for every FDA-approved drug.
- **What It Does NOT Contain**: No prescription volume or utilization data (that is CMS territory). Adverse event reports are voluntary and do not establish causation. Device data does not include device utilization.
- **Why It Matters for Project PUF**: The NDC Directory (cataloged separately above) is the primary touchpoint. FAERS data could enrich drug safety analysis alongside Part D utilization data. Drugs@FDA provides the regulatory approval context for drugs in the CMS system.
- **Dependencies**: Upstream: FDA regulatory processes, voluntary adverse event reporting. Downstream: NDC data enables drug identification across CMS datasets; FAERS enables drug safety overlay.
- **Regulatory Basis**: Federal Food, Drug, and Cosmetic Act. OPEN Government Data Act.

#### Verification Needed
- [ ] Confirm openFDA API is active and rate limits
- [ ] Verify bulk download availability for key endpoints
- [ ] Check if openFDA has added new endpoints since last review

---

## 10. Regulatory & Administrative Reference

> These are not traditional datasets but are essential reference materials that define the rules governing all other data in this inventory.

---

### 10.1 Medicare Conditions of Participation (CoPs) and Conditions for Coverage (CfCs)

- **Category**: Regulatory Reference
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: HTML / PDF (Code of Federal Regulations)
- **URL**: https://www.ecfr.gov/ (electronic CFR); CMS interpretive guidelines at https://www.cms.gov/regulations-and-guidance/guidance/manuals/ (NEEDS VERIFICATION)
- **Update Frequency**: Updated via Federal Register rulemaking (ad hoc)
- **Size Estimate**: 42 CFR Parts 482-486 (hospitals, SNFs, HHAs, etc.); hundreds of pages
- **Key Fields**: N/A (regulatory text, not structured data)
- **What It Contains**: The federal regulations that define the minimum standards institutional providers must meet to participate in Medicare and Medicaid. CoPs/CfCs cover: governance, patient rights, quality assessment, infection control, medical staff, nursing services, pharmaceutical services, laboratory services, physical environment, and more. CMS publishes Interpretive Guidelines (State Operations Manual, Appendix A through PP) that explain how surveyors evaluate compliance.
- **What It Does NOT Contain**: Not structured data. Interpretive guidelines are not legally binding. Does not include state licensure requirements (which may be more stringent).
- **Why It Matters for Project PUF**: CoPs define what it means to be a Medicare-certified provider. Survey deficiencies (in CASPER/Care Compare data) reference specific CoP standards. Understanding CoPs is essential for interpreting quality and compliance data.
- **Dependencies**: Upstream: Congressional legislation, CMS rulemaking. Downstream: defines the standards against which all providers are surveyed; drives CASPER deficiency data.
- **Regulatory Basis**: Social Security Act Sections 1861, 1864, 1865, 1866.

#### Verification Needed
- [ ] Confirm eCFR URL for current 42 CFR Parts 482-486
- [ ] Verify State Operations Manual Appendices are still publicly available on CMS website
- [ ] Check if CMS has updated CoPs recently (e.g., for emergency preparedness, infection control post-COVID)

---

### 10.2 Federal Register Final Rules (IPPS, OPPS, PFS Annual Updates)

- **Category**: Regulatory Reference
- **Publisher**: CMS (published in Federal Register via Office of the Federal Register)
- **Access Level**: Fully Public
- **Format**: HTML / PDF (Federal Register); supplementary data files in CSV/Excel
- **URL**: https://www.federalregister.gov/ (rules); supplementary files at respective CMS payment system pages (NEEDS VERIFICATION)
- **Update Frequency**: Annual (each payment system has its own rulemaking cycle: IPPS = August, OPPS = November, PFS = November)
- **Size Estimate**: Each annual final rule is 1,000-3,000 pages; supplementary data files vary
- **Key Fields**: N/A (regulatory text with embedded data tables)
- **What It Contains**: The annual final rules that set Medicare payment rates, quality measure requirements, and policy changes for each payment system. The IPPS final rule (August each year) sets DRG weights, wage indices, DSH and IME percentages, new technology add-on payments, and quality program updates. The OPPS/ASC final rule (November) sets APC rates, status indicators, and outpatient quality measures. The PFS final rule (November) sets RVUs, conversion factor, MIPS policies, and telehealth service lists. These rules are the authoritative source for understanding WHY payment data looks the way it does.
- **What It Does NOT Contain**: Not structured data (though supplementary files are). Proposed rules (earlier in the year) may differ from final rules. Requires deep domain knowledge to interpret.
- **Why It Matters for Project PUF**: Every fee schedule and payment rate in Categories 4 is a direct product of these annual rules. Understanding the rules is essential for interpreting payment data, especially when analyzing year-over-year changes.
- **Dependencies**: Upstream: Congressional legislation, CMS policy analysis. Downstream: produces all fee schedules, payment rates, and quality program requirements.
- **Regulatory Basis**: Administrative Procedure Act (5 USC 553) -- notice-and-comment rulemaking. Social Security Act provisions for each payment system.

#### Verification Needed
- [ ] Confirm Federal Register search and download accessibility
- [ ] Verify that CMS posts supplementary data files concurrently with final rules
- [ ] Check if CMS provides summary/fact sheet documents alongside the full final rules

---

### 10.3 CMS Transmittals

- **Category**: Regulatory / Administrative Reference
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: HTML / PDF
- **URL**: https://www.cms.gov/regulations-and-guidance/guidance/transmittals (NEEDS VERIFICATION)
- **Update Frequency**: Continuous (as CMS issues operational guidance)
- **Size Estimate**: Thousands of transmittals over the program's history; individual transmittals vary from 1-100+ pages
- **Key Fields**: `Transmittal_Number`, `Date`, `Subject`, `CR_Number` (Change Request), `Implementation_Date`, `Affected_Manual_Chapters`
- **What It Contains**: Official CMS instructions to Medicare Administrative Contractors (MACs) and other CMS partners that implement policy changes. Transmittals update the Internet-Only Manuals (IOMs), communicate new coding instructions, implement payment policy changes, and convey operational directives. Each transmittal is linked to a Change Request (CR) number and specifies the implementation date and affected manual sections.
- **What It Does NOT Contain**: Not structured data. Not searchable as a unified database (though CMS provides a searchable transmittal index). Individual transmittals may reference other transmittals, creating complex chains.
- **Why It Matters for Project PUF**: Transmittals explain the operational implementation of policy changes. When a coding change, coverage decision, or payment rule change takes effect, the transmittal provides the implementation detail. Essential for understanding data anomalies and mid-year policy changes.
- **Dependencies**: Upstream: Federal Register rules, National Coverage Determinations, CMS policy decisions. Downstream: directs MAC claims processing behavior; explains changes in claims data patterns.
- **Regulatory Basis**: Social Security Act Section 1874A (MAC program management).

#### Verification Needed
- [ ] Confirm transmittal search/index availability on CMS website
- [ ] Verify whether transmittals are archived historically
- [ ] Check if CMS provides a transmittal API or structured index

---

### 10.4 Medicare Claims Processing Manual (IOM 100-04)

- **Category**: Regulatory / Administrative Reference
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: HTML / PDF (individual chapters)
- **URL**: https://www.cms.gov/regulations-and-guidance/guidance/manuals/internet-only-manuals-ioms-items/cms018912 (NEEDS VERIFICATION)
- **Update Frequency**: Continuous (updated via transmittals)
- **Size Estimate**: 40+ chapters; thousands of pages total
- **Key Fields**: N/A (reference text with structured chapter/section numbering)
- **What It Contains**: The comprehensive manual governing how Medicare claims are processed. Each chapter covers a specific topic: Chapter 1 (General Billing), Chapter 4 (Part B Physician/NPP Billing), Chapter 12 (Physician/NPP Services), Chapter 14 (Ambulatory Surgical Centers), Chapter 17 (Drugs and Biologicals), Chapter 23 (Fee Schedule Administration), Chapter 25 (Completing and Processing Form CMS-1450/UB-04), Chapter 26 (Completing and Processing Form CMS-1500), and many more. This manual defines the operational rules that produce the claims data in all CMS datasets.
- **What It Does NOT Contain**: Not structured data. Does not replace the CFR (regulations) -- the manual implements the regulations operationally. May not always be current (transmittal updates sometimes lag).
- **Why It Matters for Project PUF**: The Claims Processing Manual is the operations manual for Medicare claims. Understanding how claims are billed, coded, and processed is essential for interpreting claims-derived data. Code systems, billing rules, and payment policies documented here explain patterns in the data.
- **Dependencies**: Upstream: CFR regulations, Federal Register rules, CMS transmittals. Downstream: governs how all Medicare claims are produced; understanding the manual is prerequisite for understanding the data.
- **Regulatory Basis**: Social Security Act Title XVIII. Published under CMS authority to administer the Medicare program.

#### Verification Needed
- [ ] Confirm IOM 100-04 chapter index availability
- [ ] Verify whether individual chapters are downloadable as PDF
- [ ] Check if CMS provides a consolidated, searchable version

---

### 10.5 Medicare Benefit Policy Manual (IOM 100-02)

- **Category**: Regulatory / Administrative Reference
- **Publisher**: CMS
- **Access Level**: Fully Public
- **Format**: HTML / PDF (individual chapters)
- **URL**: https://www.cms.gov/regulations-and-guidance/guidance/manuals/internet-only-manuals-ioms-items/cms012673 (NEEDS VERIFICATION)
- **Update Frequency**: Continuous (updated via transmittals)
- **Size Estimate**: 15+ chapters; thousands of pages total
- **Key Fields**: N/A (reference text)
- **What It Contains**: Defines what services and items Medicare covers, under what conditions, and with what limitations. Chapter 1 covers inpatient hospital services, Chapter 6 covers hospital services covered under Part B, Chapter 7 covers home health services, Chapter 9 covers hospice, Chapter 11 covers end-stage renal disease, Chapter 15 covers covered medical and other health services, and Chapter 16 covers general exclusions from coverage. This manual answers the fundamental question "Is this covered by Medicare?"
- **What It Does NOT Contain**: Not structured data. Does not address payment amounts (that is in the Claims Processing Manual and fee schedules). Coverage policy may differ from actual coverage decisions (NCDs and LCDs can be more specific).
- **Why It Matters for Project PUF**: Coverage policy determines what appears in claims data. If a service is not covered, it will not appear in Medicare claims (or will appear with specific denial codes). Understanding coverage policy is essential for interpreting utilization patterns and identifying coverage-driven data gaps.
- **Dependencies**: Upstream: Social Security Act, Federal Register rules, NCDs. Downstream: defines what services generate Medicare claims; explains what is and is not in the data.
- **Regulatory Basis**: Social Security Act Title XVIII, specifically Sections 1812-1813 (Part A benefits) and 1832-1833 (Part B benefits).

#### Verification Needed
- [ ] Confirm IOM 100-02 chapter index availability
- [ ] Verify whether chapters are downloadable as PDF
- [ ] Check if recent coverage expansions (e.g., telehealth, obesity treatments) are reflected

---
---

## Priority Ranking

All 67 sources cataloged above, ranked by three dimensions:

### Scoring Criteria

- **Priority (1-5)**: How foundational is this? Does other work depend on it being loaded first?
- **Impact (1-5)**: How much analytical value does it unlock once integrated?
- **Value (1-5)**: How unique/irreplaceable is this data? Is there any substitute?

### Composite Score = Priority + Impact + Value (max 15)

| Rank | Source | Category | Access | Priority | Impact | Value | Score | Rationale |
|------|--------|----------|--------|----------|--------|-------|-------|-----------|
| 1 | NPPES (NPI Registry) | Provider Identity | Public | 5 | 5 | 5 | 15 | Universal provider identity hub. Every NPI-keyed dataset depends on it. No substitute. Must load first. |
| 2 | ICD-10-CM (Diagnosis Codes) | Code System | Public | 5 | 5 | 5 | 15 | Every claims dataset uses diagnosis codes. Without this lookup table, diagnosis data is meaningless. No substitute. |
| 3 | HCPCS Level II | Code System | Public | 5 | 5 | 5 | 15 | Freely available procedure/supply code system. Covers DME, drugs, supplies. Essential for every non-inpatient claims analysis. |
| 4 | State/County FIPS Codes | Geographic Ref | Public | 5 | 5 | 5 | 15 | Universal geographic join key. Every geographic analysis depends on it. Trivial to load, impossible to skip. |
| 5 | MS-DRG Definitions & Weights | Code System / Payment | Public | 5 | 5 | 5 | 15 | Defines inpatient hospital payment unit. Without DRG weights, inpatient data lacks resource intensity context. |
| 6 | Provider of Services (POS) File | Facility Identity | Public | 5 | 5 | 4 | 14 | Institutional provider identity hub (CCN). All facility-level datasets join to it. Nearly irreplaceable. |
| 7 | Medicare Physician Fee Schedule (MPFS/RVU) | Fee Schedule | Public | 5 | 5 | 4 | 14 | Foundation of physician payment. Enables payment modeling for all Part B services. RVU structure used industry-wide. |
| 8 | NUCC Provider Taxonomy Codes | Code System | Public | 5 | 4 | 5 | 14 | Only source for interpreting NPPES taxonomy codes. Must load alongside NPPES. |
| 9 | CMS Cost Reports (Hospital) | Financial | Public | 4 | 5 | 5 | 14 | Only public source of detailed hospital financial data. Irreplaceable for cost analysis, wage index, margin calculations. |
| 10 | ZIP-to-County Crosswalk (HUD) | Geographic Ref | Public | 5 | 4 | 4 | 13 | Bridges ZIP-coded provider data to county-based geographic analysis. Essential crosswalk, few alternatives. |
| 11 | NDC Directory (FDA) | Code System / Drug | Public | 4 | 5 | 4 | 13 | Universal drug identifier. Links Part D, SDUD, ASP data. NDC format issues make this challenging but irreplaceable. |
| 12 | ICD-10-PCS (Procedure Codes) | Code System | Public | 4 | 4 | 5 | 13 | Only system for inpatient procedure coding. Required for DRG grouper logic and surgical analysis. |
| 13 | IPPS Rate Files (DRG Weights, Wage Index) | Fee Schedule | Public | 4 | 5 | 4 | 13 | Largest Medicare payment system. Impact file has hospital-specific characteristics used across analyses. |
| 14 | Wage Index Files | Fee Schedule / Geo | Public | 4 | 5 | 4 | 13 | Affects every institutional payment system. Essential for geographic payment analysis. |
| 15 | PECOS (Provider Enrollment) | Provider Identity | Partially Public | 4 | 4 | 4 | 12 | Filters NPPES to Medicare-participating providers. Reassignment data reveals group practice structure. |
| 16 | Medicaid State Drug Utilization Data (SDUD) | Claims / Drug | Public | 3 | 5 | 4 | 12 | Most granular publicly available Medicaid data. State x drug x quarter. High policy relevance (drug pricing). |
| 17 | OPPS Rate Files (APC Rates) | Fee Schedule | Public | 4 | 4 | 4 | 12 | Outpatient hospital payment rates. Second-largest institutional payment system. |
| 18 | CMS Place of Service Codes | Code System | Public | 4 | 3 | 5 | 12 | Small but essential reference table. Determines facility vs. non-facility payment. Critical for telehealth tracking. |
| 19 | RxNorm (NLM) | Code System / Drug | Free (registration) | 3 | 4 | 5 | 12 | The drug name normalizer. Bridges NDC, brand, generic across datasets. Irreplaceable for drug data integration. |
| 20 | APC (Ambulatory Payment Classifications) | Code System / Payment | Public | 4 | 4 | 4 | 12 | Outpatient equivalent of DRGs. Required for understanding outpatient hospital payment and services. |
| 21 | ASP Drug Pricing Files | Fee Schedule / Drug | Public | 3 | 5 | 4 | 12 | Part B drug payment rates. Quarterly price tracking. Highly relevant for drug pricing policy analysis. |
| 22 | CBSA Definitions | Geographic Ref | Public | 4 | 4 | 4 | 12 | Wage index geographic unit. Required for geographic payment analysis. |
| 23 | CMS Cost Reports (SNF, HHA, Hospice) | Financial | Public | 3 | 5 | 4 | 12 | Only public source of post-acute facility financial data. Essential for PAC cost analysis. |
| 24 | Medicare Advantage Rate Books | Fee Schedule / MA | Public | 3 | 5 | 4 | 12 | County-level MA benchmarks. Essential for MA market analysis and FFS-MA payment comparison. |
| 25 | Census Population Estimates | Demographic Ref | Public | 4 | 4 | 3 | 11 | Population denominators for per-capita calculations. Census-only source but alternatives exist (ACS). |
| 26 | RUCA Codes | Geographic Ref | Public | 3 | 4 | 4 | 11 | Standard rural-urban classification. Required for rural healthcare analysis. Used by CMS. |
| 27 | Medicare Provider Charge Data | Claims / Cost | Public | 3 | 4 | 4 | 11 | Unique charge-vs-payment data. Enables hospital pricing variation analysis. |
| 28 | Hospital General Information | Facility | Public | 3 | 4 | 3 | 10 | Clean hospital reference file with type, ownership, star rating. Easy to load, immediate value. |
| 29 | Five-Star Nursing Home Data | Quality | Public | 3 | 4 | 3 | 10 | Comprehensive nursing home quality data. High policy relevance. |
| 30 | Hospital Readmission Rates (HRRP) | Quality | Public | 3 | 4 | 3 | 10 | High-profile quality measure with direct payment impact. |
| 31 | Nursing Home Staffing (PBJ) | Facility / Staffing | Public | 3 | 4 | 3 | 10 | Unique daily staffing data. Links directly to quality outcomes. |
| 32 | CAHPS Survey Data | Quality | Public | 3 | 3 | 4 | 10 | Unique patient experience perspective. No substitute. Affects VBP payment. |
| 33 | SNF PPS Rate Files (PDPM) | Fee Schedule | Public | 3 | 3 | 4 | 10 | SNF payment rates. Required for post-acute care payment analysis. |
| 34 | CLFS (Clinical Lab Fee Schedule) | Fee Schedule | Public | 3 | 3 | 4 | 10 | Lab test payment rates. Useful for lab industry and Part B analysis. |
| 35 | DMEPOS Fee Schedule | Fee Schedule | Public | 3 | 3 | 4 | 10 | DME payment rates. Required for DME cost analysis. |
| 36 | MA Enrollment Files (Monthly) | Enrollment | Public | 3 | 4 | 3 | 10 | MA market dynamics. Essential context for FFS data interpretation. (Previously cataloged.) |
| 37 | Dialysis Facility Data | Facility / Quality | Public | 3 | 3 | 4 | 10 | ESRD-focused quality data in a highly concentrated market. Policy-relevant. |
| 38 | Ordering & Referring File | Provider Identity | Public | 3 | 3 | 4 | 10 | Compliance/referral validation file. Useful for DME/lab referral analysis. |
| 39 | HRR/HSA (Dartmouth Atlas) | Geographic Ref | Public | 3 | 4 | 3 | 10 | Standard healthcare market geography. Bridges to Dartmouth Atlas literature. |
| 40 | data.cms.gov (full portal) | Data Portal | Public | 3 | 4 | 3 | 10 | Discovery and API access for 200+ CMS datasets. Pipeline integration opportunity. |
| 41 | HHA PPS Rate Files (PDGM) | Fee Schedule | Public | 3 | 3 | 3 | 9 | Home health payment rates. Required for HHA payment analysis. |
| 42 | Hospice Payment Rates | Fee Schedule | Public | 3 | 3 | 3 | 9 | Hospice per diem rates. Simple structure, specialized domain. |
| 43 | HHA Provider Data | Facility | Public | 3 | 3 | 3 | 9 | Home health agency quality data. Complements HHA utilization. |
| 44 | Hospice Provider Data | Facility | Public | 3 | 3 | 3 | 9 | Hospice quality data. Complements hospice utilization. |
| 45 | SNF Provider Data | Facility | Public | 3 | 3 | 3 | 9 | SNF quality/facility data. Complements SNF utilization and Five-Star data. |
| 46 | Opt-Out Affidavits | Provider Identity | Public | 2 | 3 | 4 | 9 | Small but unique -- identifies providers who left Medicare. Analytically interesting. |
| 47 | Area Deprivation Index (ADI) | Socioeconomic Ref | Free (registration) | 2 | 4 | 3 | 9 | Block-group-level deprivation index. Increasingly used by CMS for equity. |
| 48 | Social Vulnerability Index (SVI) | Socioeconomic Ref | Public | 2 | 4 | 3 | 9 | Census-tract vulnerability measure. Complements ADI for equity analysis. |
| 49 | ZCTA Files (Census) | Geographic Ref | Public | 3 | 3 | 3 | 9 | ZIP-code polygon boundaries. Required for spatial analysis and mapping. |
| 50 | HAC Reduction Program Data | Quality | Public | 2 | 3 | 3 | 8 | Safety/infection quality measure with payment impact. Smaller scope than readmissions. |
| 51 | PSI Data (AHRQ/CMS) | Quality | Public | 2 | 3 | 3 | 8 | Claims-based safety measures. Feeds HAC program. Specifications freely available. |
| 52 | Dialysis Facility Compare Data | Quality | Public | 2 | 3 | 3 | 8 | Detailed ESRD quality measures. Specialized domain. |
| 53 | CMS Quality Measure Specifications | Quality / Reference | Public | 2 | 3 | 3 | 8 | Measure specs define how quality scores are calculated. Reference material. |
| 54 | Medicare-Medicaid Dual-Eligible Data | Enrollment | Partially Public | 2 | 3 | 3 | 8 | Important population but public data is limited to aggregates. |
| 55 | Deactivated NPI Report | Provider Identity | Public | 2 | 2 | 4 | 8 | Data quality filter. Small, specialized use. |
| 56 | MCBS (PUF version) | Survey | Public | 2 | 3 | 3 | 8 | Unique beneficiary perspective. Small sample limits utility. |
| 57 | data.medicaid.gov (full portal) | Data Portal | Public | 2 | 3 | 3 | 8 | Medicaid data discovery. SDUD is the primary asset. |
| 58 | Medicaid Enrollment Data | Enrollment | Public | 2 | 3 | 3 | 8 | State-level Medicaid denominators. Limited detail but essential for Medicaid context. |
| 59 | Part D Enrollment Files | Enrollment | Public | 2 | 3 | 3 | 8 | Part D plan market data. Specialized. |
| 60 | Federal Register Final Rules | Regulatory Ref | Public | 2 | 3 | 2 | 7 | Essential reference for policy context but not structured data. |
| 61 | LOINC | Code System | Free (registration) | 2 | 2 | 3 | 7 | Lab code system. Lower priority for claims-based analysis. Future EHR integration. |
| 62 | SNOMED CT | Code System | Free (UMLS) | 2 | 2 | 3 | 7 | Clinical terminology. Lower priority for claims. Future EHR integration. |
| 63 | CMS Transmittals | Regulatory Ref | Public | 1 | 3 | 2 | 6 | Operational guidance. Unstructured. Contextual reference. |
| 64 | Claims Processing Manual | Regulatory Ref | Public | 1 | 3 | 2 | 6 | Operations manual. Unstructured. Contextual reference. |
| 65 | Benefit Policy Manual | Regulatory Ref | Public | 1 | 3 | 2 | 6 | Coverage policy manual. Unstructured. Contextual reference. |
| 66 | CoPs/CfCs | Regulatory Ref | Public | 1 | 2 | 2 | 5 | Regulatory standards. Unstructured. Background reference. |
| 67 | MAC Jurisdiction Maps | Geographic Ref | Public | 1 | 2 | 2 | 5 | Small administrative reference. Rarely needed for analysis. |

> **Not ranked (proprietary/restricted -- cannot be integrated into Project PUF without licensing):**
> - CPT (HCPCS Level I) -- AMA copyright. Use CMS-published short descriptions from fee schedule files.
> - APR-DRG -- 3M proprietary. Use MS-DRGs instead.
> - Revenue Codes -- NUBC proprietary. Reference by number only.
> - Condition/Occurrence/Value Codes -- NUBC proprietary. Use CMS manual excerpts.
> - Type of Bill Codes -- Partially public via CMS manuals.
> - HCPCS Modifier Codes (CPT subset) -- AMA copyright on CPT modifiers; HCPCS Level II modifiers are free.
> - HCUP -- AHRQ licensing required. Use HCUPnet for aggregate queries.
> - Medicare SAF/LDS Claims -- ResDAC DUA required. Not distributable.
> - VRDC -- Research access only. Not distributable.
> - Part D Drug Event Data -- ResDAC DUA required.
> - T-MSIS -- Research access only.
> - MBSF -- ResDAC DUA required.

---

### Tier 1 (Score 13-15): Must Have for MVP

These are non-negotiable foundational sources. They are the reference tables and code systems that everything else depends on. All are fully public and freely downloadable.

| Source | Score | Load Order Rationale |
|--------|-------|---------------------|
| NPPES (NPI Registry) | 15 | Load first. Provider identity hub. |
| ICD-10-CM | 15 | Load with code systems. Diagnosis lookup. |
| HCPCS Level II | 15 | Load with code systems. Procedure/supply lookup. |
| State/County FIPS | 15 | Load with geographic references. Trivial size. |
| MS-DRG Definitions & Weights | 15 | Load with code systems. Inpatient classification. |
| Provider of Services (POS) | 14 | Load second. Facility identity hub. |
| MPFS / RVU Files | 14 | Load with fee schedules. Physician payment foundation. |
| NUCC Taxonomy | 14 | Load alongside NPPES. Specialty reference. |
| CMS Cost Reports (Hospital) | 14 | Load early. Only source of hospital financial data. |
| ZIP-to-County Crosswalk | 13 | Load with geographic references. Essential bridge. |
| NDC Directory | 13 | Load with code systems. Drug identifier bridge. |
| ICD-10-PCS | 13 | Load with code systems. Inpatient procedures. |
| IPPS Rate Files | 13 | Load with fee schedules. Hospital payment rates. |
| Wage Index Files | 13 | Load with fee schedules. Geographic payment adjustment. |

**Total Tier 1: 14 sources.** These should be the first pipeline targets.

---

### Tier 2 (Score 10-12): High Value, Second Wave

These unlock significant analytical capability and should be the immediate follow-on after Tier 1.

| Source | Score | Rationale |
|--------|-------|-----------|
| PECOS | 12 | Medicare provider filtering and group practice data. |
| SDUD (Medicaid Drug Utilization) | 12 | Most granular public Medicaid data. Drug policy goldmine. |
| OPPS Rate Files | 12 | Outpatient hospital payment. Second-largest institutional PPS. |
| Place of Service Codes | 12 | Tiny reference table with outsized impact. |
| RxNorm | 12 | Drug name normalization engine. |
| APC Definitions | 12 | Outpatient classification system. |
| ASP Drug Pricing | 12 | Part B drug prices. Quarterly tracking. |
| CBSA Definitions | 12 | Wage index geography. |
| CMS Cost Reports (SNF/HHA/Hospice) | 12 | Post-acute facility financials. |
| MA Rate Books | 12 | MA benchmark analysis. |
| Census Population Estimates | 11 | Per-capita denominators. |
| RUCA Codes | 11 | Rural-urban classification. |
| Provider Charge Data | 11 | Charge-vs-payment analysis. |
| Hospital General Info | 10 | Clean hospital reference. |
| Five-Star Nursing Home | 10 | Nursing home quality. |
| Readmission Rates | 10 | HRRP quality-payment data. |
| PBJ Staffing | 10 | Nursing home staffing data. |
| CAHPS Data | 10 | Patient experience. |
| SNF PPS Rates | 10 | SNF payment rates. |
| CLFS | 10 | Lab fee schedule. |
| DMEPOS Fee Schedule | 10 | DME payment rates. |
| MA Enrollment (Monthly) | 10 | MA market dynamics. |
| Dialysis Facility Data | 10 | ESRD quality data. |
| Ordering/Referring File | 10 | Referral validation. |
| HRR/HSA (Dartmouth) | 10 | Healthcare market geography. |
| data.cms.gov Portal | 10 | API pipeline integration. |

**Total Tier 2: 26 sources.**

---

### Tier 3 (Score 7-9): Important but Can Wait

These are valuable but serve more specialized analytical purposes.

| Source | Score | Rationale |
|--------|-------|-----------|
| HHA PPS Rates | 9 | HHA payment analysis. |
| Hospice Rates | 9 | Hospice payment analysis. |
| HHA Provider Data | 9 | HHA quality overlay. |
| Hospice Provider Data | 9 | Hospice quality overlay. |
| SNF Provider Data | 9 | SNF quality overlay. |
| Opt-Out Affidavits | 9 | Provider universe refinement. |
| ADI | 9 | Health equity stratification. |
| SVI | 9 | Health equity stratification. |
| ZCTA Files | 9 | Spatial analysis support. |
| HAC Data | 8 | Safety measure with payment impact. |
| PSI Data | 8 | Safety measures. |
| Dialysis Compare | 8 | ESRD quality detail. |
| Quality Measure Specs | 8 | Reference for quality interpretation. |
| Dual-Eligible Data | 8 | Important population, limited public data. |
| Deactivated NPI Report | 8 | Data quality filter. |
| MCBS PUF | 8 | Beneficiary survey perspective. |
| data.medicaid.gov Portal | 8 | Medicaid data discovery. |
| Medicaid Enrollment | 8 | Medicaid denominators. |
| Part D Enrollment | 8 | Part D market data. |
| Federal Register Rules | 7 | Policy context reference. |
| LOINC | 7 | Lab codes. Future use. |
| SNOMED CT | 7 | Clinical terminology. Future use. |

**Total Tier 3: 22 sources.**

---

### Tier 4 (Score 4-6): Nice to Have

Reference materials and administrative data. Low urgency but useful for completeness.

| Source | Score | Rationale |
|--------|-------|-----------|
| CMS Transmittals | 6 | Operational guidance. Unstructured. |
| Claims Processing Manual | 6 | Operations reference. |
| Benefit Policy Manual | 6 | Coverage reference. |
| CoPs/CfCs | 5 | Regulatory standards text. |
| MAC Jurisdiction Maps | 5 | Administrative geography. |

**Total Tier 4: 5 sources.**

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| **Total sources cataloged** | 67 |
| **Fully Public** | 45 |
| **Free with registration** | 5 |
| **Partially Public** | 4 |
| **Proprietary/Licensed** | 7 |
| **Research Only (DUA/VRDC)** | 6 |
| **Tier 1 (MVP must-have)** | 14 |
| **Tier 2 (second wave)** | 26 |
| **Tier 3 (can wait)** | 22 |
| **Tier 4 (nice to have)** | 5 |

---

## Global Verification Checklist

> All URLs, file sizes, update frequencies, and field names in this inventory are based on domain knowledge as of the knowledge cutoff. Before pipeline development begins for any source, the following must be verified with live web access:

- [ ] All download URLs must be confirmed active
- [ ] File formats must be verified (CMS occasionally changes from CSV to Excel or vice versa)
- [ ] Column/field names must be confirmed against actual downloaded files
- [ ] File sizes must be measured from actual downloads
- [ ] Update frequencies must be confirmed against actual release calendars
- [ ] API endpoints and rate limits must be tested
- [ ] Licensing terms must be reviewed for any source requiring registration or agreement
- [ ] Any new datasets published since this inventory was created must be identified

---

> **Domain Scholar** | Inventory complete: 67 sources across 10 categories | Status: CATALOGED
> Next step: Verify URLs and schemas with live web access, then proceed to Pipeline Architect for acquisition pipeline design starting with Tier 1 sources.
