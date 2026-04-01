# Data Source: Medicare Advantage / Part C Enrollment

## Overview
- **Publisher**: Centers for Medicare & Medicaid Services (CMS)
- **Program**: Medicare Part C (Medicare Advantage)
- **URL**: https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-advantagepart-d-contract-and-enrollment-data (NEEDS VERIFICATION); also monthly enrollment files at https://www.cms.gov/research-statistics-data-and-systems/statistics-trends-and-reports/mcradvpartdenroldata (NEEDS VERIFICATION)
- **Update Frequency**: Monthly enrollment snapshots; annual summary reports
- **Current Coverage**: Monthly data back to 2006 or earlier; annual reports back to ~1999 (latest year NEEDS VERIFICATION)
- **Access Level**: Public Use File
- **File Format**: CSV download (multiple file types: contract-level, plan-level, county-level, state-level)
- **Approximate Size**: Monthly enrollment by county — ~50,000+ rows per month (county-contract-plan grain); contract/plan summary files are smaller; total archive is several GB across all years

## Purpose & Policy Context

Medicare Advantage (MA, also called Medicare Part C) is the private-plan alternative to traditional Fee-for-Service (FFS) Medicare. Under MA, private insurers contract with CMS to provide all Part A and Part B benefits (and usually Part D drug coverage) to enrolled beneficiaries, receiving a per-capita payment from CMS. The MA program traces its origins to the Medicare+Choice program established by the Balanced Budget Act of 1997, which itself built on earlier Medicare managed care options. The MMA of 2003 rebranded the program as "Medicare Advantage" and significantly increased payment rates to attract plan participation.

The MA enrollment data answers critical structural questions about the Medicare program: how many beneficiaries are in MA vs. FFS, how has enrollment shifted over time, which plans and insurers dominate which markets, and how does MA penetration vary geographically? As of 2024, more than 50% of Medicare beneficiaries are enrolled in MA plans — this is a fundamental transformation of Medicare that makes understanding MA enrollment data essential for any comprehensive Medicare analysis.

In the transparency landscape, MA enrollment data provides the essential denominator for understanding the FFS data universe. All of the provider-level PUFs (Part B, Part D, Inpatient, etc.) cover only FFS beneficiaries (with limited exceptions). As MA enrollment grows, FFS data becomes less representative of the total Medicare population. Understanding MA penetration by county is critical for interpreting FFS utilization rates — areas with high MA penetration have a smaller, potentially sicker FFS population (or healthier, depending on favorable selection dynamics). Key legislation: BBA 1997 (Medicare+Choice), MMA 2003 (Medicare Advantage creation, Part D establishment), ACA 2010 (MA payment reductions, quality bonus program), the 21st Century Cures Act 2016, the Bipartisan Budget Act of 2018 (MA provisions).

## Contents

### Monthly Enrollment by Contract/Plan/County
| Column Group | Description | Key Fields |
|---|---|---|
| Contract Identity | MA plan contract | `Contract_Number` (H-number for MA, R-number for MA-PD, S-number for standalone PDP), `Plan_ID`, `Organization_Name`, `Plan_Name` |
| Contract Type | Plan classification | `Contract_Type` (Local CCP, PFFS, MSA, Regional PPO, etc.), `Plan_Type`, `Offers_Part_D` |
| Geography | Enrollment location | `State`, `County`, `FIPS_State_County_Code` |
| Enrollment | Beneficiary counts | `Enrollment` (total enrollees in that contract-plan-county), various enrollment breakdowns |

### Monthly Enrollment by State/County (Aggregated)
| Column Group | Description | Key Fields |
|---|---|---|
| Geography | Area | `State`, `County`, `FIPS_State_County_Code` |
| MA Enrollment | Total MA | `MA_Enrollment`, `MA_Penetration_Rate` |
| FFS Enrollment | Total FFS | `Original_Medicare_Enrollment` / `FFS_Enrollment` |
| Total Medicare | All beneficiaries | `Total_Medicare_Enrollment` |

### Contract-Level Summary
| Column Group | Description | Key Fields |
|---|---|---|
| Contract Identity | Contract details | `Contract_Number`, `Organization_Name`, `Organization_Type`, `Plan_Type` |
| Performance | Quality ratings | `Overall_Star_Rating`, `Part_C_Star_Rating`, `Part_D_Star_Rating` |
| Enrollment | Aggregate enrollment | `Total_Enrollment`, `Enrollment_by_Plan` |

## Key Identifiers

| Identifier | Type | Links To |
|---|---|---|
| `Contract_Number` | CMS Contract ID (letter + 4 digits, e.g., H1234) | MA Star Ratings, MA plan-level data, bid/payment data |
| `Plan_ID` | Plan identifier within contract (3 digits, e.g., 001) | Plan-specific enrollment and benefit data |
| `FIPS_State_County_Code` | 5-digit FIPS county code | Geographic Variation data, Census/ACS, all county-level health data |
| `Organization_Name` | Parent organization name | Corporate-level analysis (text matching required) |

## Relationships

| Related Source | Join Key | Relationship Type |
|---|---|---|
| Medicare Geographic Variation | `FIPS_State_County_Code` = `County_FIPS` | Direct — MA penetration is a critical contextual variable for FFS utilization data |
| Medicare Part B Utilization | County FIPS crosswalk | Contextual — MA penetration affects FFS population composition |
| Medicare Part D Prescribers | County FIPS crosswalk | Contextual — MA-PD enrollment reduces standalone PDP market |
| Medicare Inpatient Hospitals | County FIPS crosswalk | Contextual — MA penetration affects FFS hospitalization rates |
| MA Star Ratings | `Contract_Number` | Direct — plan quality ratings linked to enrollment |
| MA Plan Finder / Benefits Data | `Contract_Number` + `Plan_ID` | Direct — plan benefits, premiums, cost-sharing |
| MA Payment / Bid Data | `Contract_Number` | Direct — CMS payment benchmarks and plan bids |
| Census / ACS Data | `FIPS_State_County_Code` | Contextual — demographic context for enrollment patterns |
| Hospital Compare / Care Compare | Indirect (MA plans contract with hospitals) | Contextual — hospital networks serving MA populations |

## Data Quality Notes

- **Enrollment timing**: Monthly enrollment snapshots capture point-in-time enrollment (typically first of the month). Beneficiaries can change plans during the Annual Election Period (October 15 – December 7), Open Enrollment Period (January 1 – March 31), and via Special Enrollment Periods. Month-to-month volatility is normal.
- **Contract number complexity**: Contract numbers encode plan type (H = MA-only, R = MA-PD, S = standalone PDP, E = employer-sponsored). Understanding the letter prefix is essential for filtering.
- **Plan turnover**: Plans enter and exit markets annually. A contract number may exist in one year but not the next if a plan exits a county. Longitudinal analysis must handle plan discontinuation.
- **SNP identification**: Special Needs Plans (D-SNPs, C-SNPs, I-SNPs) serve specific populations (dual-eligible, chronic conditions, institutional). They are included in MA enrollment but may need to be analyzed separately.
- **Penetration rate calculation**: MA penetration rate = MA enrollment / total Medicare enrollment in a geography. This is the single most important contextual variable for interpreting all FFS Medicare data.
- **Employer group plans**: Some MA enrollment is through employer-sponsored group plans (EGWP). These may be reported differently and can skew county-level enrollment counts if a large employer is headquartered in a small county.
- **No claims data**: This is enrollment data, not utilization or claims data. CMS does not publish MA claims/encounter data in PUF form. The absence of MA claims in public data is one of the most significant gaps in Medicare transparency.
- **Star ratings lag**: Star ratings used for quality bonus payments are based on prior-year performance. The enrollment file's star ratings may not align with the enrollment period's payment year.
- **PACE programs**: Programs of All-Inclusive Care for the Elderly (PACE) are included in MA enrollment counts but serve a very different population (frail elderly eligible for nursing home care). They are a small but distinct segment.

## Use Cases

1. **MA market analysis**: Map plan availability, enrollment, and market share by county, insurer, and plan type.
2. **FFS population adjustment**: Use MA penetration rates to adjust denominators when analyzing FFS utilization data — higher MA penetration means the FFS population may not represent the general Medicare population.
3. **Enrollment trend analysis**: Track the shift from FFS to MA over time at national, state, and county levels.
4. **Competition analysis**: Measure market concentration (HHI) in MA markets by county or metropolitan area.
5. **Star rating impact**: Study how quality ratings affect enrollment growth — do higher-rated plans gain market share?
6. **Dual-eligible analysis**: Track D-SNP enrollment to understand managed care penetration in the dual-eligible population.
7. **Rural access**: Analyze MA plan availability and enrollment in rural vs. urban counties to assess access equity.

## Regulatory Notes

- **MA payment structure**: CMS sets county-level benchmarks based on FFS spending. Plans bid against these benchmarks. If a plan bids below the benchmark, it keeps a portion of the savings (the "rebate") to fund supplemental benefits. Understanding benchmarks and bids is essential context for enrollment analysis.
- **Quality Bonus Program**: Plans rated 4 stars or higher receive bonus payments (5% increase to the benchmark in most counties, 10% in qualifying counties under a now-extended double bonus provision). This creates strong incentives around star ratings.
- **Network adequacy**: MA plans must meet CMS network adequacy requirements (maximum time and distance to providers). Network adequacy affects where plans can be offered.
- **Privacy protections**: Enrollment data is aggregated to the contract-plan-county level. No individual beneficiary data is included.
- **Terms of use**: Standard CMS PUF terms. No DUA required. CMS makes enrollment data freely available.
- **Citation**: "Centers for Medicare & Medicaid Services. Medicare Advantage/Part D Contract and Enrollment Data, [YEAR/MONTH]."

## Verification Needed

- [ ] Confirm current URL(s) for enrollment data downloads (CMS has multiple pages for different file types)
- [ ] Verify most recent monthly enrollment file available
- [ ] Check whether CMS has added new data elements (e.g., race/ethnicity breakdowns, SNP type indicators)
- [ ] Confirm whether encounter data is now available in any PUF form (CMS has discussed this)
- [ ] Verify whether MA Star Ratings are now published as a separate downloadable file or integrated
- [ ] Check the current MA penetration rate nationally (was ~51% in 2024)
- [ ] Verify FIPS code format in current files (some older files used separate state/county fields)
- [ ] Confirm whether PACE enrollment is separately identifiable
- [ ] Check if CMS has published MA utilization data (encounter-based PUFs) as planned
- [ ] Verify whether the Inflation Reduction Act's Part D changes affect MA-PD enrollment data
