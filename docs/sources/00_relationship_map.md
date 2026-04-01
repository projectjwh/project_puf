# CMS Public Use File (PUF) — Source Relationship Map

> **Domain Scholar Output** | Created: 2026-03-03 | Status: CATALOGED (12 sources)
> All URLs, latest data years, and schema details flagged for live verification before pipeline development.

---

## Master Source Catalog

| # | Source | Short Name | Primary Key(s) | Grain | Program | Approx Rows/Year |
|---|--------|-----------|----------------|-------|---------|-------------------|
| 1 | Medicare Provider Utilization & Payment: Physician/Other Practitioners | **Part B Utilization** | `Rndrng_NPI` + `HCPCS_Cd` + `Place_Of_Srvc` | Provider-Service-PlaceOfService | Part B | ~10M |
| 2 | Medicare Inpatient Hospitals — by Provider and Service | **Inpatient Hospitals** | `Rndrng_Prvdr_CCN` + `DRG_Cd` | Hospital-DRG | Part A | ~200K–300K |
| 3 | Medicare Part D Prescribers — by Provider and Drug | **Part D Prescribers** | `Prscrbr_NPI` + `Brnd_Name` + `Gnrc_Name` | Provider-Drug | Part D | ~25M |
| 4 | Hospital Compare / Care Compare | **Care Compare** | `Facility_ID` (CCN) + `Measure_ID` | Hospital-Measure | Cross-program | ~50K–200K (varies) |
| 5 | Medicare Geographic Variation | **Geo Variation** | `BENE_GEO_LVL` + `State_FIPS` + `County_FIPS` | National/State/County | Parts A, B, D | ~3,250 |
| 6 | Medicare Spending Per Beneficiary | **MSPB** | `Facility_ID` (CCN) | Hospital | Parts A, B | ~4,500 |
| 7 | Physician Compare / NPPES / PECOS | **Provider Registry** | `NPI` (universal) | Provider | Cross-program | ~8M (NPPES total) |
| 8 | DME Suppliers | **DME** | `Rfrg_NPI` or `Suplr_NPI` + `HCPCS_Cd` | Provider-HCPCS | Part B (DMEPOS) | ~500K–700K |
| 9 | Home Health Agency Utilization | **HHA** | `Rndrng_Prvdr_CCN` | Agency | Part A | ~10K–12K |
| 10 | Hospice Utilization | **Hospice** | `Rndrng_Prvdr_CCN` | Agency | Part A | ~5K–6K |
| 11 | Skilled Nursing Facility Utilization | **SNF** | `Rndrng_Prvdr_CCN` | Facility | Part A | ~15K–16K |
| 12 | Medicare Advantage / Part C Enrollment | **MA Enrollment** | `Contract_Number` + `Plan_ID` + `FIPS_State_County_Code` | Contract-Plan-County | Part C | ~50K+/month |

---

## Key Identifier Crosswalk

The CMS data ecosystem uses a small number of universal identifiers that enable cross-source joins. Understanding which identifiers each source carries is the foundation of the data model.

| Identifier | Full Name | Format | Sources That Carry It |
|---|---|---|---|
| **NPI** | National Provider Identifier | 10-digit numeric | Part B, Part D, DME (both views), Provider Registry (NPPES), Physician Compare, PECOS |
| **CCN** | CMS Certification Number | 6-digit (state prefix + facility type) | Inpatient Hospitals, Care Compare, MSPB, HHA, Hospice, SNF, Provider of Services |
| **HCPCS** | Healthcare Common Procedure Coding System | 5-character (Level I: numeric CPT; Level II: alpha + numeric) | Part B, DME |
| **DRG** | Medicare Severity Diagnosis Related Group | 3-digit numeric | Inpatient Hospitals |
| **State FIPS** | Federal Information Processing Standard state code | 2-digit numeric | Part B, Part D, DME, HHA, Hospice, SNF, Geo Variation, MA Enrollment |
| **County FIPS** | FIPS county code | 5-digit numeric (state + county) | Geo Variation, MA Enrollment |
| **Contract Number** | CMS MA/PD contract identifier | Letter + 4 digits (e.g., H1234) | MA Enrollment, MA Star Ratings |
| **Drug Name** | Brand/Generic name pair | Free text | Part D Prescribers |
| **Measure ID** | CMS quality measure identifier | Alphanumeric (e.g., MORT_30_AMI) | Care Compare, MSPB |
| **PAC ID** | Provider Associate Control ID | Numeric | Physician Compare, PECOS |

---

## Join Relationships

### Direct Joins (Shared Key, Same Entity)

These are reliable, key-based joins where the same identifier appears in both datasets and refers to the same entity.

| Source A | Source B | Join Key | Join Description |
|----------|----------|----------|------------------|
| Part B Utilization | Part D Prescribers | `Rndrng_NPI` = `Prscrbr_NPI` | Same provider — links procedure billing to prescribing behavior |
| Part B Utilization | Provider Registry (NPPES) | `Rndrng_NPI` = `NPI` | Provider identity enrichment (name, taxonomy, address) |
| Part B Utilization | DME (by Referring) | `Rndrng_NPI` = `Rfrg_NPI` | Same physician — links procedure billing to DME ordering |
| Part D Prescribers | Provider Registry (NPPES) | `Prscrbr_NPI` = `NPI` | Provider identity enrichment |
| Part D Prescribers | DME (by Referring) | `Prscrbr_NPI` = `Rfrg_NPI` | Same physician — links prescribing to DME ordering |
| DME (by Supplier) | Provider Registry (NPPES) | `Suplr_NPI` = `NPI` | Supplier identity enrichment |
| Inpatient Hospitals | Care Compare | `Rndrng_Prvdr_CCN` = `Facility_ID` | Same hospital — links cost/utilization to quality metrics |
| Inpatient Hospitals | MSPB | `Rndrng_Prvdr_CCN` = `Facility_ID` | Same hospital — links DRG payments to episode spending |
| Care Compare | MSPB | `Facility_ID` = `Facility_ID` | MSPB is one of the Care Compare measures |
| HHA | Care Compare (Home Health) | `Rndrng_Prvdr_CCN` = Home Health CCN | Same agency — utilization linked to quality measures |
| Hospice | Care Compare (Hospice) | `Rndrng_Prvdr_CCN` = Hospice CCN | Same agency — utilization linked to quality measures |
| SNF | Care Compare (Nursing Homes) | `Rndrng_Prvdr_CCN` = `Federal_Provider_Number` | Same facility — utilization linked to star ratings |
| Geo Variation | MA Enrollment | `County_FIPS` = `FIPS_State_County_Code` | Same geography — FFS spending context + MA penetration |

### Contextual Joins (Shared Geography, Different Grain)

These joins link sources through geographic identifiers but at different levels of aggregation. They provide population-level context for provider-level or facility-level data.

| Source A | Source B | Join Key | Join Description |
|----------|----------|----------|------------------|
| Part B Utilization | Geo Variation | `Rndrng_Prvdr_State_FIPS` = `State_FIPS` | Population context for provider billing patterns |
| Part D Prescribers | Geo Variation | `Prscrbr_State_FIPS` = `State_FIPS` | Population context for prescribing patterns |
| Inpatient Hospitals | Geo Variation | `Rndrng_Prvdr_State_FIPS` = `State_FIPS` | Population context for hospital utilization |
| Part B Utilization | MA Enrollment | Provider ZIP/State to County FIPS crosswalk | MA penetration context for FFS provider data |
| HHA | Geo Variation | `Rndrng_Prvdr_State_FIPS` = `State_FIPS` | Population home health spending context |
| Hospice | Geo Variation | `Rndrng_Prvdr_State_FIPS` = `State_FIPS` | Population hospice spending context |
| SNF | Geo Variation | `Rndrng_Prvdr_State_FIPS` = `State_FIPS` | Population post-acute spending context |

### Hierarchical / Aggregation Relationships

These describe how sources relate through care pathways and aggregation hierarchies, not through direct key joins.

| Upstream Source | Downstream Source | Relationship | Description |
|----------------|-------------------|--------------|-------------|
| Inpatient Hospitals | SNF | **Care Pathway** | SNF stays typically follow qualifying hospital stays. Hospital discharge feeds SNF admission. |
| Inpatient Hospitals | HHA | **Care Pathway** | Home health episodes often begin after hospital discharge as an alternative to institutional PAC. |
| Inpatient Hospitals | Hospice | **Care Pathway** | Hospice election may follow a terminal hospitalization. |
| SNF | HHA | **Care Pathway** | Home health may follow SNF discharge for continued rehabilitation. |
| Part B Utilization | DME (by Referring) | **Referral** | Physicians who bill Part B services also order DME for patients. The same NPI appears in both. |
| Part B Utilization | Part D Prescribers | **Practice Profile** | Same physician's procedure and prescribing patterns form a complete practice profile. |
| Provider Registry (NPPES) | ALL provider-level sources | **Identity Hub** | NPPES is the master provider identity source. All NPI-bearing datasets join to it. |
| Care Compare | Inpatient, HHA, Hospice, SNF | **Quality Overlay** | Quality measures for each provider type overlay the utilization data. |
| Geo Variation | ALL sources | **Population Denominator** | Geographic variation provides population-level context for all provider and facility data. |
| MA Enrollment | ALL FFS sources | **Coverage Context** | MA penetration rates are essential context for interpreting all FFS utilization data. |
| MSPB | Inpatient, SNF, HHA, Hospice | **Episode Aggregation** | MSPB aggregates costs across the care episode, drawing from inpatient, PAC, and physician costs. |

---

## Data Flow Diagram (Text Representation)

```
                         PROVIDER IDENTITY LAYER
                    ┌──────────────────────────────────┐
                    │   NPPES / PECOS / Phys Compare    │
                    │         (NPI = Hub Key)           │
                    └──────────┬───────────────────────┘
                               │ NPI
           ┌───────────────────┼───────────────────────┐
           │                   │                       │
    ┌──────▼──────┐    ┌──────▼──────┐    ┌───────────▼──────┐
    │  Part B     │    │  Part D     │    │  DME Suppliers   │
    │  Utilization│    │  Prescribers│    │  (Referring &    │
    │  (NPI+HCPCS)│    │  (NPI+Drug) │    │   Supplier)      │
    └──────┬──────┘    └──────┬──────┘    └───────────┬──────┘
           │                   │                       │
           └───────────────────┼───────────────────────┘
                               │ State/County FIPS
                    ┌──────────▼───────────────────────┐
                    │  Geographic Variation             │
                    │  (National / State / County)      │
                    └──────────┬───────────────────────┘
                               │ County FIPS
                    ┌──────────▼───────────────────────┐
                    │  MA Enrollment                    │
                    │  (Contract + Plan + County)       │
                    └──────────────────────────────────┘

                        INSTITUTIONAL LAYER
                    ┌──────────────────────────────────┐
                    │  Care Compare / Hospital Compare  │
                    │  (CCN = Hub Key for facilities)   │
                    └──────────┬───────────────────────┘
                               │ CCN (Facility_ID)
           ┌───────────────────┼───────────────────────┐
           │                   │                       │
    ┌──────▼──────┐    ┌──────▼──────┐    ┌───────────▼──────┐
    │  Inpatient  │    │    MSPB     │    │  Post-Acute:     │
    │  Hospitals  │    │  (Episode   │    │  SNF, HHA,       │
    │  (CCN+DRG)  │    │   Spending) │    │  Hospice         │
    └─────────────┘    └─────────────┘    └──────────────────┘
```

---

## MVP Priority Ranking

Based on data richness, join potential, policy relevance, and implementation complexity, the recommended order for initial ingestion is:

### Tier 1 — Ingest First (MVP Core)

| Priority | Source | Rationale |
|----------|--------|-----------|
| **1** | **Provider Registry (NPPES)** | Universal identity hub. Every provider-level join depends on NPI. Must be loaded first as the reference dimension. Relatively simple schema, single large file. |
| **2** | **Part B Utilization** | Highest-value provider-level dataset. Largest row count, richest analysis surface. Covers all physician/practitioner services. Links to every other provider-level dataset via NPI. |
| **3** | **Part D Prescribers** | Natural complement to Part B — same NPI key, different service domain. Together they form a comprehensive provider practice profile. High policy relevance (opioids, drug pricing). |
| **4** | **Geographic Variation** | Essential denominator and context dataset. Small file size, high value. Provides population-level benchmarks needed to interpret all provider-level data. |

### Tier 2 — Ingest Second (Institutional + Market Context)

| Priority | Source | Rationale |
|----------|--------|-----------|
| **5** | **Inpatient Hospitals** | Opens the institutional (CCN-based) data domain. Enables hospital cost-quality analysis when combined with Care Compare. |
| **6** | **Care Compare** | Quality overlay for hospitals and all institutional providers. Complex multi-file structure but essential for value analysis. |
| **7** | **MA Enrollment** | Critical context for interpreting all FFS data. As MA exceeds 50% of Medicare, failing to account for MA penetration leads to biased FFS analysis. |

### Tier 3 — Ingest Third (Domain Expansion)

| Priority | Source | Rationale |
|----------|--------|-----------|
| **8** | **MSPB** | Small file, high analytic value. Episode-based spending bridges inpatient and post-acute domains. |
| **9** | **SNF Utilization** | Largest post-acute care spending category. Pairs well with Inpatient Hospitals for care pathway analysis. |
| **10** | **HHA Utilization** | Post-acute complement to SNF. Important for studying alternatives to institutional PAC. |
| **11** | **Hospice Utilization** | Unique end-of-life care domain. Smaller dataset, specialized analysis surface. |
| **12** | **DME Suppliers** | Specialized supply chain analysis. Important for fraud detection but less central to core Medicare spending analysis. |

### MVP Justification

The Tier 1 sources (NPPES, Part B, Part D, Geographic Variation) are recommended as the MVP for the following reasons:

1. **Maximum join connectivity**: NPI links Part B, Part D, and NPPES directly. Geographic FIPS codes link all three to Geographic Variation. Four sources, fully connected.
2. **Provider-centric analysis from day one**: The MVP enables complete physician profiling — what procedures they bill, what drugs they prescribe, where they practice, how their area compares to national benchmarks.
3. **Manageable data volume**: Geographic Variation is tiny (<100 MB). NPPES is large but is a reference dimension (load once). Part B and Part D are the largest files (~10M and ~25M rows) but are well-structured tabular data amenable to standard ETL.
4. **Immediate analytic value**: Opioid prescribing, geographic variation, provider outlier detection, specialty benchmarking — all are possible with just these four sources.
5. **Foundation for expansion**: Once NPI (provider) and FIPS (geography) are established as join dimensions, adding institutional sources (CCN-based) is incremental.

---

## Cross-Cutting Considerations

### Universal Join Challenges

| Challenge | Description | Mitigation |
|-----------|-------------|------------|
| **NPI-to-CCN crosswalk** | Provider-level (NPI) and facility-level (CCN) datasets use different identifiers. No single PUF provides a clean crosswalk. | Use NPPES (organizational NPIs) + PECOS (enrollment data) + Physician Compare (hospital affiliation CCNs) to build the crosswalk. |
| **ZIP-to-County mapping** | Provider-level data uses ZIP codes; geographic data uses FIPS county codes. ZIP codes do not align perfectly to counties. | Use HUD ZIP-to-County crosswalk or Census ZCTA-to-county relationship file. Accept that ~5% of ZIPs span multiple counties. |
| **Drug name normalization** | Part D uses free-text brand/generic names, not standardized NDC codes. | Build a drug name normalization table mapping variants to canonical names. Consider linking to FDA NDC directory or RxNorm. |
| **Year-over-year schema drift** | Column names, suppression thresholds, and field definitions change across years. | Maintain a schema registry documenting column mappings per source per year. Build ETL transformations per schema version. |
| **FFS-only bias** | All utilization PUFs cover only FFS Medicare. As MA grows past 50%, FFS data is increasingly unrepresentative. | Always include MA enrollment penetration as a contextual variable. Caveat all population-level findings with FFS-only disclaimer. |

### Suppression and Small Cell Handling

All CMS PUFs suppress records with fewer than 11 beneficiaries/discharges/claims. This creates systematic data gaps:

- **Rural providers**: Lower volume means more suppression
- **Rare conditions/procedures**: Uncommon DRGs or HCPCS codes are disproportionately suppressed
- **Specialty providers**: Narrow-specialty providers who see few Medicare patients per service code
- **Implication for analysis**: Suppression means aggregated totals from PUF data will systematically undercount compared to CMS's own national totals. The gap is larger for fine-grained analyses.

### Temporal Alignment

| Source | Typical Lag | Release Calendar |
|--------|-------------|------------------|
| Part B Utilization | 18–24 months | Annual, usually spring/summer |
| Part D Prescribers | 18–24 months | Annual, usually spring/summer |
| Inpatient Hospitals | 18–24 months | Annual |
| Care Compare | 3–6 months (quarterly) | Quarterly |
| Geographic Variation | 18–24 months | Annual |
| MSPB | 12–18 months (part of Care Compare) | Annual within Care Compare |
| NPPES | Real-time to 1 month | Monthly bulk, weekly incremental |
| MA Enrollment | 1–3 months | Monthly |
| SNF, HHA, Hospice, DME | 18–24 months | Annual |

---

## File Inventory

| Source Entry File | Path |
|---|---|
| Medicare Part B Utilization | `docs/sources/medicare_provider_utilization_partb.md` |
| Medicare Inpatient Hospitals | `docs/sources/medicare_inpatient_hospitals.md` |
| Medicare Part D Prescribers | `docs/sources/medicare_partd_prescribers.md` |
| Hospital Compare / Care Compare | `docs/sources/hospital_care_compare.md` |
| Medicare Geographic Variation | `docs/sources/medicare_geographic_variation.md` |
| Medicare Spending Per Beneficiary | `docs/sources/medicare_spending_per_beneficiary.md` |
| Physician Compare / NPPES / PECOS | `docs/sources/physician_compare_nppes_pecos.md` |
| DME Suppliers | `docs/sources/dme_suppliers.md` |
| Home Health Agency Utilization | `docs/sources/home_health_agency_utilization.md` |
| Hospice Utilization | `docs/sources/hospice_utilization.md` |
| Skilled Nursing Facility Utilization | `docs/sources/skilled_nursing_facility_utilization.md` |
| Medicare Advantage / Part C Enrollment | `docs/sources/medicare_advantage_partc_enrollment.md` |
