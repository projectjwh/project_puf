# 7. Cross-Source Join Matrix

[← Back to Index](index.md) | [← Data Models](06-data-models.md)

---

## How Independent Government Files Become a Unified Platform

The power of Project PUF comes from joining 48 independently published government data files into a unified analytical dataset. No single CMS file tells you "here is a provider's full practice profile with geographic context, prescribing patterns, and opioid metrics." That requires joining NPPES (provider identity), NUCC Taxonomy (specialty descriptions), FIPS (state names), Part B (service volumes), and Part D (prescribing patterns) — five independent datasets from three different publishers.

The intermediate and mart dbt models perform these joins systematically, producing analytical tables that would take researchers weeks to construct manually.

---

## Join Graph

```d2
direction: right

nppes: NPPES {shape: circle; style.fill: "#bfdbfe"}
taxonomy: Taxonomy {shape: circle; style.fill: "#bfdbfe"}
fips: FIPS {shape: circle; style.fill: "#bbf7d0"}
partb: Part B {shape: circle; style.fill: "#93c5fd"}
partd: Part D {shape: circle; style.fill: "#93c5fd"}
geovar: GeoVar {shape: circle; style.fill: "#86efac"}
inpatient: Inpatient {shape: circle; style.fill: "#fdba74"}
msdrg: MS-DRG {shape: circle; style.fill: "#fcd34d"}
cost_reports: Cost Reports {shape: circle; style.fill: "#fdba74"}
pos: POS Facilities {shape: circle; style.fill: "#fdba74"}
five_star: Five-Star {shape: circle; style.fill: "#5eead4"}
pbj: PBJ Staffing {shape: circle; style.fill: "#5eead4"}
sdud: SDUD {shape: circle; style.fill: "#c4b5fd"}
ndc: NDC {shape: circle; style.fill: "#c4b5fd"}
asp: ASP Pricing {shape: circle; style.fill: "#c4b5fd"}
hcpcs: HCPCS {shape: circle; style.fill: "#fcd34d"}
readm: Readmissions {shape: circle; style.fill: "#fdba74"}
hosp_gen: Hospital General {shape: circle; style.fill: "#fdba74"}
ma_enroll: MA Enrollment {shape: circle; style.fill: "#fcd34d"}
charges: Charges {shape: circle; style.fill: "#fdba74"}

int_prov: int_providers {shape: diamond; style.fill: "#e0e7ff"}
int_geo: int_geographic_benchmarks {shape: diamond; style.fill: "#e0e7ff"}
int_disch: int_hospital_discharges {shape: diamond; style.fill: "#e0e7ff"}
int_fin: int_hospital_financials {shape: diamond; style.fill: "#e0e7ff"}
int_nq: int_nursing_home_quality {shape: diamond; style.fill: "#e0e7ff"}
int_drug: int_drug_utilization {shape: diamond; style.fill: "#e0e7ff"}
int_price: int_drug_pricing {shape: diamond; style.fill: "#e0e7ff"}
int_readm: int_hospital_readmissions {shape: diamond; style.fill: "#e0e7ff"}
int_ma: int_ma_market {shape: diamond; style.fill: "#e0e7ff"}

nppes -> int_prov: NPI
taxonomy -> int_prov: taxonomy_code
fips -> int_prov: state_fips
geovar -> int_geo: state_fips
fips -> int_geo: state_fips
inpatient -> int_disch: "ccn, drg"
msdrg -> int_disch: drg_code
charges -> int_disch: "ccn, drg"
cost_reports -> int_fin: ccn
pos -> int_fin: ccn
five_star -> int_nq: ccn
pbj -> int_nq: ccn
sdud -> int_drug: ndc_code
ndc -> int_drug: ndc_code
asp -> int_price: hcpcs_code
hcpcs -> int_price: hcpcs_code
readm -> int_readm: ccn
hosp_gen -> int_readm: ccn
ma_enroll -> int_ma: county_fips
fips -> int_ma: county_fips
```

Full diagram: [`diagrams/cross-source-joins.d2`](diagrams/cross-source-joins.d2)

---

## Join Matrix

| Source A | Source B | Join Key | Model Produced | Analytical Value |
|----------|----------|----------|---------------|-----------------|
| NPPES | NUCC Taxonomy | `taxonomy_code` | `int_providers` | Provider identity enriched with specialty descriptions |
| NPPES | FIPS | `state_fips` | `int_providers` | Geographic context (state names, census region) |
| Part B (utilization) | NPPES | `rendering_npi` | `mart_provider__practice_profile` | Provider practice profile with service volumes |
| Part D (prescribers) | NPPES | `prescriber_npi` | `mart_provider__practice_profile` | Prescribing patterns joined to provider identity |
| Geographic Variation | FIPS States | `state_fips` | `int_geographic_benchmarks` | State spending with names and regions |
| Inpatient | MS-DRG | `drg_code` | `int_hospital_discharges` | Case mix index from DRG weights |
| Cost Reports | POS Facilities | `ccn` | `int_hospital_financials` | Financial metrics with facility characteristics |
| Five-Star | PBJ Staffing | `ccn` | `int_nursing_home_quality` | Quality ratings + actual staffing data |
| SDUD | NDC Directory | `ndc_code` | `int_drug_utilization_medicaid` | Drug utilization with product descriptions |
| ASP Pricing | HCPCS | `hcpcs_code` | `int_drug_pricing` | Price trends linked to procedure descriptions |
| Readmissions | Hospital General | `ccn` | `mart_hospital__readmissions` | Readmission rates with hospital characteristics |
| MA Enrollment | FIPS | `county_fips` | `int_ma_market` | Medicare Advantage penetration by county |

---

**Next:** [API →](08-api.md)
