# Data Source: DME Suppliers — by Referring Provider and by Supplier

## Overview
- **Publisher**: Centers for Medicare & Medicaid Services (CMS)
- **Program**: Medicare Part B (DMEPOS — Durable Medical Equipment, Prosthetics, Orthotics, and Supplies)
- **URL**: https://data.cms.gov/provider-summary-by-type-of-service/medicare-durable-medical-equipment-devices-supplies/ (NEEDS VERIFICATION)
- **Update Frequency**: Annual (typically released 1.5–2 years after the service year)
- **Current Coverage**: 2013–2022 (latest year NEEDS VERIFICATION)
- **Access Level**: Public Use File
- **File Format**: CSV download; CMS Data API
- **Approximate Size**: By Referring Provider — ~500,000–700,000 rows per year (~200–400 MB); By Supplier — ~300,000–500,000 rows per year (~150–300 MB)

## Purpose & Policy Context

The Medicare DMEPOS PUF was released as part of the ACA-driven transparency initiative, alongside the physician and hospital-level datasets. Durable medical equipment (DME) — wheelchairs, oxygen equipment, hospital beds, prosthetic devices, diabetic supplies, and similar items — is covered under Medicare Part B when prescribed by a physician and supplied by a Medicare-enrolled DME supplier. The data is published in two complementary views: one organized by the referring/ordering provider (the physician who prescribed the equipment) and one by the supplier (the company that furnished it).

The DME sector has historically been one of the highest-fraud areas in Medicare. The Medicare Modernization Act of 2003 established a competitive bidding program for DMEPOS to control costs. The ACA further strengthened program integrity requirements. CMS's Office of Inspector General (OIG) and the Department of Justice have pursued numerous fraud cases involving DME suppliers billing for items never delivered, billing for more expensive items than ordered (upcoding), and operating sham supplier operations. Making this data public serves both transparency and program integrity goals.

In the transparency ecosystem, the DME data provides a view of a distinct supply chain: unlike physician services (where the provider and biller are often the same), DME involves a referring provider (the physician who orders), a supplier (the company that furnishes), and sometimes an intermediary. The two PUF views allow analysis from either direction. The referring provider view can reveal physicians whose DME ordering patterns are outliers; the supplier view can reveal suppliers with unusual billing patterns. Key legislation: ACA 2010 (transparency, competitive bidding expansion), MMA 2003 (competitive bidding creation), the 21st Century Cures Act 2016 (DMEPOS provisions), HIPAA and the Medicare, Medicaid, and SCHIP Benefits Improvement and Protection Act of 2000 (BIPA, supplier standards).

## Contents

### By Referring Provider
| Column Group | Description | Key Fields |
|---|---|---|
| Referring Provider Identity | Ordering physician | `Rfrg_NPI`, `Rfrg_Prvdr_Last_Org_Name`, `Rfrg_Prvdr_First_Name`, `Rfrg_Prvdr_Crdntls` |
| Referring Provider Location | Physician geography | `Rfrg_Prvdr_St1`, `Rfrg_Prvdr_City`, `Rfrg_Prvdr_State_Abrvtn`, `Rfrg_Prvdr_State_FIPS`, `Rfrg_Prvdr_Zip5` |
| Referring Provider Type | Specialty | `Rfrg_Prvdr_Type`, `Rfrg_Prvdr_Gndr` |
| HCPCS | Product/service code | `HCPCS_Cd`, `HCPCS_Desc` |
| Utilization | Volume | `Tot_Suplr_Benes`, `Tot_Suplr_Clms`, `Tot_Suplr_Srvcs` |
| Payment | Dollar amounts | `Avg_Suplr_Sbmtd_Chrg`, `Avg_Suplr_Mdcr_Alowd_Amt`, `Avg_Suplr_Mdcr_Pymt_Amt`, `Avg_Suplr_Mdcr_Stdzd_Amt` |

### By Supplier
| Column Group | Description | Key Fields |
|---|---|---|
| Supplier Identity | Furnishing company | `Suplr_NPI`, `Suplr_Prvdr_Last_Org_Name`, `Suplr_Prvdr_First_Name` |
| Supplier Location | Supplier geography | `Suplr_Prvdr_St1`, `Suplr_Prvdr_City`, `Suplr_Prvdr_State_Abrvtn`, `Suplr_Prvdr_State_FIPS`, `Suplr_Prvdr_Zip5` |
| Supplier Type | Entity type | `Suplr_Prvdr_Type`, `Suplr_Prvdr_Ent_Cd` |
| HCPCS | Product/service code | `HCPCS_Cd`, `HCPCS_Desc` |
| Utilization | Volume | `Tot_Suplr_Benes`, `Tot_Suplr_Clms`, `Tot_Suplr_Srvcs` |
| Payment | Dollar amounts | `Avg_Suplr_Sbmtd_Chrg`, `Avg_Suplr_Mdcr_Alowd_Amt`, `Avg_Suplr_Mdcr_Pymt_Amt`, `Avg_Suplr_Mdcr_Stdzd_Amt` |

## Key Identifiers

| Identifier | Type | Links To |
|---|---|---|
| `Rfrg_NPI` | National Provider Identifier (referring physician) | Part B Utilization, NPPES, Physician Compare, Part D Prescribers |
| `Suplr_NPI` | National Provider Identifier (supplier) | NPPES, Supplier enrollment data |
| `HCPCS_Cd` | HCPCS Level II code (alphanumeric, typically starting with A, E, K, L) | DMEPOS fee schedule, HCPCS reference tables |
| `Rfrg_Prvdr_State_FIPS` / `Suplr_Prvdr_State_FIPS` | FIPS State Code | Geographic datasets |

## Relationships

| Related Source | Join Key | Relationship Type |
|---|---|---|
| Medicare Part B Utilization | `Rfrg_NPI` = `Rndrng_NPI` | Direct — referring physician's procedure/service billing |
| NPPES | `Rfrg_NPI` or `Suplr_NPI` = `NPI` | Direct — provider/supplier identity enrichment |
| Medicare Part D Prescribers | `Rfrg_NPI` = `Prscrbr_NPI` | Direct — same physician's prescribing patterns |
| Open Payments | `Rfrg_NPI` = `Covered_Recipient_NPI` | Direct — industry payments to referring physicians |
| Medicare Geographic Variation | State/County FIPS | Contextual — population-level spending context |
| DMEPOS Fee Schedule | `HCPCS_Cd` | Direct — maps codes to fee schedule amounts, competitive bidding areas |
| Physician Compare / PECOS | `Rfrg_NPI` = `NPI` | Direct — physician enrollment and specialty |

## Data Quality Notes

- **Suppression**: Rows with fewer than 11 beneficiaries for a given provider-HCPCS combination are suppressed.
- **Two separate files**: The "by Referring Provider" and "by Supplier" files are separate datasets with different grains. They cannot be directly joined to each other at the individual claim level (the PUF does not contain a referring-to-supplier linkage). Analysis of the referring-supplier relationship requires working with both files independently.
- **HCPCS Level II codes**: DME uses Level II HCPCS codes (alphanumeric), distinct from the Level I CPT codes in Part B physician data. The code structure is: A=Transportation/Miscellaneous, E=Durable Medical Equipment, K=Temporary codes, L=Orthotics/Prosthetics.
- **Competitive bidding impact**: The DMEPOS Competitive Bidding Program (CBP) changed payment rates in designated areas. Payment amounts in CBP areas may be significantly lower than in non-CBP areas for the same HCPCS code. This complicates cross-area comparisons.
- **Rental vs. purchase**: Some DME items (e.g., oxygen equipment, wheelchairs) can be rented or purchased. The data does not clearly distinguish rental payments from purchase payments in all cases.
- **Excludes**: Medicare Advantage beneficiaries (DME claims processed outside FFS), items not covered by Medicare Part B DMEPOS benefit.
- **Fraud sensitivity**: DME data should be interpreted with awareness that this sector has high fraud rates. Outlier patterns may indicate fraud rather than legitimate practice variation.
- **Supplier turnover**: DME suppliers have higher enrollment/disenrollment rates than physician providers. A supplier NPI appearing in one year may not appear in the next.

## Use Cases

1. **Fraud detection**: Identify referring physicians or suppliers with statistically anomalous ordering/billing patterns (e.g., unusually high DME referral volumes, concentration in high-cost items).
2. **Competitive bidding evaluation**: Analyze the impact of the DMEPOS Competitive Bidding Program on prices, supplier participation, and beneficiary access.
3. **Physician referral analysis**: Profile referring physicians by their DME ordering patterns — what types of equipment they order, at what volume, for how many beneficiaries.
4. **DME market analysis**: Map supplier concentration by geography and product category.
5. **Cost variation**: Compare payment amounts for the same HCPCS codes across regions, controlling for competitive bidding status.

## Regulatory Notes

- **Privacy protections**: Standard CMS cell suppression (11-beneficiary minimum). No patient-level data.
- **Terms of use**: Standard CMS PUF terms. No DUA required.
- **Supplier enrollment standards**: DME suppliers must meet CMS supplier standards (28 conditions) and maintain surety bonds. The data reflects only Medicare-enrolled suppliers.
- **Competitive Bidding Program**: The CBP, authorized by MMA Section 302, sets payment rates through competitive bidding in designated areas. Understanding which areas are subject to competitive bidding is essential for interpreting payment data.
- **Prior authorization**: CMS has implemented prior authorization for certain DME items (e.g., power wheelchairs, PMDs). This may affect utilization patterns in the data.
- **Citation**: "Centers for Medicare & Medicaid Services. Medicare DMEPOS Suppliers — by Referring Provider [or by Supplier], [YEAR]."

## Verification Needed

- [ ] Confirm current URL on data.cms.gov
- [ ] Verify most recent data year available
- [ ] Check whether CMS has added a linked referring-to-supplier view
- [ ] Verify current competitive bidding areas and their impact on data interpretation
- [ ] Check if column naming conventions match current Part B conventions
- [ ] Confirm whether prior authorization indicators are included in the data
- [ ] Verify suppression thresholds
- [ ] Check if CMS has expanded the dataset to include additional HCPCS categories
