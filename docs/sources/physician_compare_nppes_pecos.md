# Data Source: Physician Compare / Provider Enrollment (NPPES/PECOS)

## Overview
- **Publisher**: CMS (Physician Compare, PECOS); National Plan and Provider Enumeration System (NPPES) is maintained by CMS but enumeration is through a separate system
- **Program**: Cross-program (all Medicare); NPPES covers all HIPAA-covered entities
- **URL**:
  - NPPES NPI Registry: https://npiregistry.cms.hhs.gov/ and bulk download at https://download.cms.gov/nppes/NPI_Files.html (NEEDS VERIFICATION)
  - Physician Compare (now part of Care Compare Provider Data): https://data.cms.gov/provider-data/dataset/mj5m-pzi6 (NEEDS VERIFICATION)
  - PECOS: Data available through Provider Enrollment data on data.cms.gov (NEEDS VERIFICATION)
- **Update Frequency**: NPPES — monthly bulk download, weekly incremental updates; Physician Compare — quarterly; PECOS data — periodically
- **Current Coverage**: NPPES — all currently and previously enumerated NPIs (since 2005); Physician Compare — varies by data element; PECOS — current enrollment status
- **Access Level**: Public Use File (all three)
- **File Format**: NPPES — CSV (large single file + monthly deactivation files); Physician Compare — CSV; PECOS — CSV/API
- **Approximate Size**: NPPES full file — ~8 million NPI records, ~8–10 GB uncompressed; Physician Compare — ~2 million rows, ~500 MB; PECOS — varies

## Purpose & Policy Context

These three datasets serve related but distinct purposes in the provider identity and enrollment ecosystem:

**NPPES** was mandated by the Health Insurance Portability and Accountability Act of 1996 (HIPAA), which required the adoption of a standard unique health identifier for healthcare providers. The National Provider Identifier (NPI) system went live on May 23, 2007, replacing dozens of legacy identifiers (UPIN, Medicare provider number, etc.). Every HIPAA-covered provider — individual or organizational — must have an NPI. The NPPES registry is the authoritative source for NPI-to-provider mapping and is the backbone of provider identity across the entire U.S. healthcare system.

**PECOS** (Provider Enrollment, Chain, and Ownership System) is CMS's internal system for managing Medicare provider enrollment. A provider must be enrolled in PECOS to bill Medicare. PECOS data includes enrollment status, specialty, practice location, group practice affiliations, and reassignment relationships (which individual NPIs bill through which organizational NPIs). Publicly available PECOS data provides enrollment-level details not found in NPPES.

**Physician Compare** was mandated by ACA Section 10331, which required CMS to develop a website with information on physicians and other eligible professionals participating in Medicare. It was originally a consumer-facing comparison tool, but its downloadable data became valuable for research. In 2020, CMS folded Physician Compare into the unified Care Compare platform, though the underlying data files remain available. Physician Compare adds quality performance data (MIPS scores) and group practice affiliations to the basic enrollment information.

Together, these three datasets form the provider identity layer for Project PUF. Every NPI-bearing record in Part B, Part D, Inpatient, DME, and other CMS datasets can be enriched by joining to NPPES/PECOS/Physician Compare. Key legislation: HIPAA 1996 (NPI mandate), ACA 2010 Section 10331 (Physician Compare), MACRA 2015 (MIPS quality reporting feeds into Physician Compare), the Medicare Improvements for Patients and Providers Act of 2008 (MIPPA, provider enrollment requirements).

## Contents

### NPPES NPI Registry
| Column Group | Description | Key Fields |
|---|---|---|
| NPI | Unique identifier | `NPI` (10-digit) |
| Entity Type | Individual vs Organization | `Entity_Type_Code` (1=Individual, 2=Organization) |
| Provider Name | Name fields | `Provider_Last_Name`, `Provider_First_Name`, `Provider_Organization_Name`, `Provider_Credential_Text` |
| Practice Address | Primary practice location | `Provider_First_Line_Business_Practice_Location_Address`, `Provider_Business_Practice_Location_Address_City_Name`, `Provider_Business_Practice_Location_Address_State_Name`, `Provider_Business_Practice_Location_Address_Postal_Code` |
| Mailing Address | Mailing location | Parallel `_Mailing_` address fields |
| Taxonomy | Provider specialty classification | `Healthcare_Provider_Taxonomy_Code_1` through `_15`, `Healthcare_Provider_Primary_Taxonomy_Switch_1` through `_15` |
| Other Identifiers | Legacy IDs | `Other_Provider_Identifier_1` through `_50`, with associated `Other_Provider_Identifier_Type_Code_*` and `Other_Provider_Identifier_State_*` |
| Enumeration | Administrative dates | `Provider_Enumeration_Date`, `Last_Update_Date`, `NPI_Deactivation_Reason_Code`, `NPI_Deactivation_Date`, `NPI_Reactivation_Date` |
| Authorized Official | Organization contact | `Authorized_Official_*` fields (for organizational NPIs) |

### Physician Compare
| Column Group | Description | Key Fields |
|---|---|---|
| Provider Identity | NPI and name | `NPI`, `Last_Name`, `First_Name`, `Credential` |
| Specialty | Medicare specialty | `Primary_Specialty`, `Secondary_Specialty_*` |
| Practice Location | Practice details | `Organization_legal_name`, `Group_Practice_PAC_ID`, `Line_1_Street_Address`, `City`, `State`, `Zip` |
| Enrollment | Medicare status | `Professional_accepts_Medicare_Assignment`, `PAC_ID` (Provider Associate Control ID) |
| Quality | MIPS performance | `MIPS_Score` (in MIPS-specific files), quality measure performance data |
| Affiliations | Hospital/group affiliations | `Hospital_affiliation_CCN_*`, `Group_Practice_PAC_ID` |

### PECOS (Public Enrollment Data)
| Column Group | Description | Key Fields |
|---|---|---|
| Provider Identity | NPI and enrollment | `NPI`, `PECOS_Associate_Control_ID` (PAC ID) |
| Enrollment Status | Medicare participation | Enrollment type, specialty, accepting new patients |
| Reassignments | Billing relationships | Which individual NPIs have reassigned billing rights to which organizational NPIs |
| Practice Location | Enrolled practice sites | Multiple practice location records per NPI |

## Key Identifiers

| Identifier | Type | Links To |
|---|---|---|
| `NPI` | National Provider Identifier (10-digit) | ALL provider-level CMS datasets (Part B, Part D, Inpatient, DME, HHA, Hospice, SNF) |
| `Entity_Type_Code` | 1=Individual, 2=Organization | Disambiguates individual practitioners from facilities/groups |
| `Healthcare_Provider_Taxonomy_Code` | NUCC taxonomy code (10-character) | Provider specialty/type classification; maps to NUCC taxonomy |
| `PAC_ID` (Physician Compare/PECOS) | Provider Associate Control ID | Links providers to group practices within PECOS |
| `Group_Practice_PAC_ID` | PAC ID for the group | Links individual providers to their group practice |
| `Hospital_affiliation_CCN` | CMS Certification Number | Links physicians to affiliated hospitals in Care Compare |
| `Provider_Business_Practice_Location_Address_Postal_Code` | ZIP+4 or ZIP5 | Geographic analyses, crosswalks |

## Relationships

| Related Source | Join Key | Relationship Type |
|---|---|---|
| Medicare Part B Utilization | `NPI` = `Rndrng_NPI` | Direct — provider identity enrichment |
| Medicare Part D Prescribers | `NPI` = `Prscrbr_NPI` | Direct — provider identity enrichment |
| Medicare Inpatient Hospitals | Organizational NPI or CCN crosswalk | Contextual — hospital identity |
| Hospital Compare / Care Compare | `Hospital_affiliation_CCN` = `Facility_ID` | Direct — physician-hospital affiliation |
| Open Payments (Sunshine Act) | `NPI` = `Covered_Recipient_NPI` | Direct — industry payment linkage |
| DME Suppliers | `NPI` = referring/supplier NPI | Direct — provider identity enrichment |
| HHA Utilization | `NPI` = referring/attending NPI | Direct — referral pattern analysis |
| Medicare Geographic Variation | State FIPS from address | Contextual — geographic context |
| NUCC Taxonomy | `Healthcare_Provider_Taxonomy_Code` = taxonomy code | Direct — maps to human-readable specialty descriptions |

## Data Quality Notes

- **NPPES is not Medicare-specific**: NPPES contains ALL enumerated providers, including those who never bill Medicare. Filtering to Medicare-participating providers requires joining to PECOS or using Physician Compare.
- **Address quality**: NPPES addresses are self-reported and may be stale. The practice location address is generally more useful than the mailing address for geographic analysis. Many providers have multiple practice locations in NPPES (up to 50 taxonomy/address slots).
- **Taxonomy code complexity**: A single NPI can have up to 15 taxonomy codes. The primary taxonomy switch indicates the provider's self-reported primary specialty, but this does not always align with Medicare's specialty classification.
- **Deactivated NPIs**: NPPES includes deactivated NPIs. For current provider analyses, filter on `NPI_Deactivation_Date` being null.
- **PECOS reassignments**: Understanding reassignment relationships is essential for studying group practice dynamics. An individual physician (Type 1 NPI) typically reassigns billing rights to an organization (Type 2 NPI). This is how group practices work in Medicare.
- **Physician Compare retirement**: With the transition to Care Compare, the Physician Compare download files may be restructured or renamed. The underlying data elements should persist.
- **MIPS scores**: Quality performance data through MIPS is added to Physician Compare/Care Compare data with a lag. Not all providers have MIPS scores (exemptions exist for low-volume providers).
- **No historical snapshots**: NPPES is a "current state" file. It does not maintain historical versions. If a provider changes their address or specialty, the old data is overwritten. For longitudinal analysis, maintain your own snapshots.

## Use Cases

1. **Provider identity resolution**: Use NPI as the universal join key across all CMS provider-level datasets. Enrich provider records with name, specialty, address, and credentials.
2. **Group practice analysis**: Map individual physicians to group practices using PAC IDs and reassignment data. Analyze group-level utilization and spending patterns.
3. **Network adequacy**: Identify providers by specialty and geographic area for network adequacy assessments.
4. **Specialty classification**: Use taxonomy codes for granular specialty analysis beyond the CMS specialty categories in utilization files.
5. **Provider migration tracking**: With periodic NPPES snapshots, track providers who change practice locations over time.
6. **Quality-cost integration**: Link MIPS scores to Part B and Part D utilization data to study whether quality incentives affect practice patterns.

## Regulatory Notes

- **HIPAA mandate**: NPI enumeration is a legal requirement under HIPAA for all covered healthcare providers. The public availability of NPI data is inherent to the system's design as a standard identifier.
- **Privacy considerations**: NPPES contains business contact information for individual providers (practice address, phone). This is intentionally public. No patient/beneficiary data is included.
- **Terms of use**: NPPES data is freely available for download. CMS has terms of use prohibiting commercial resale of the raw data without value-added processing. Physician Compare data follows standard CMS PUF terms.
- **Data freshness**: NPPES is a living database. Monthly downloads capture a snapshot. For compliance-sensitive applications (e.g., claims processing), use the most recent data.
- **Citation**: "Centers for Medicare & Medicaid Services. National Plan and Provider Enumeration System (NPPES) NPI Registry." / "Centers for Medicare & Medicaid Services. Physician Compare/Care Compare Provider Data."

## Verification Needed

- [ ] Confirm NPPES bulk download URL is still active at download.cms.gov
- [ ] Verify whether Physician Compare data files still exist as separate downloads or have been fully merged into Care Compare
- [ ] Check current PECOS public data availability and format
- [ ] Confirm whether MIPS score data is now integrated into Care Compare provider data downloads
- [ ] Verify the NPPES file structure (column names may have changed)
- [ ] Check if CMS has added new data elements to NPPES (e.g., digital contact information, certification data)
- [ ] Confirm whether the NPPES API (NPI Registry API) is still available and its rate limits
- [ ] Verify whether PAC ID is still the primary group practice linkage key
- [ ] Check if PECOS reassignment data is publicly downloadable or API-only
