# Insight Engine Review: MVP Launch Analysis Plan

> **Agent**: Insight Engine | **Date**: 2026-03-04 | **Status**: PUBLISH
> **Scope**: 8-10 initial analyses using only MVP Tier 1 data (NPPES, Part B, Part D, Geographic Variation)
> **Purpose**: Launch content — blog posts, interactive visualizations, and trend monitors to demonstrate platform capabilities and attract healthcare researchers and policy analysts

---

## Table of Contents

1. [Replication Study 1: Geographic Variation in Medicare Spending](#replication-1-geographic-variation-in-medicare-spending)
2. [Replication Study 2: Opioid Prescribing in Medicare Part D](#replication-2-opioid-prescribing-in-medicare-part-d)
3. [Replication Study 3: Medicare Physician Spending Concentration](#replication-3-medicare-physician-spending-concentration)
4. [Replication Study 4: Generic Drug Utilization Rates](#replication-4-generic-drug-utilization-rates)
5. [Original Analysis 1: The Dual Practice Profile — Linking Procedure Billing to Prescribing Behavior](#original-1-the-dual-practice-profile)
6. [Original Analysis 2: Telehealth Adoption Trajectory by Specialty and Geography](#original-2-telehealth-adoption-trajectory)
7. [Original Analysis 3: Provider Workforce Dynamics — NPI Enumeration, Deactivation, and Specialty Distribution](#original-3-provider-workforce-dynamics)
8. [Original Analysis 4: State-Level Spending Decomposition — Price vs. Utilization vs. Mix](#original-4-state-level-spending-decomposition)
9. [Trend Monitor 1: Per-Capita Medicare Standardized Spending by State](#trend-monitor-1-per-capita-spending)
10. [Trend Monitor 2: Opioid Prescribing Rate Among Medicare Part D Providers](#trend-monitor-2-opioid-prescribing-rate)
11. [Recommended Launch Sequence](#recommended-launch-sequence)
12. [Data Gaps Identified](#data-gaps-identified)
13. [Upstream Requirements](#upstream-requirements)
14. [Overall Verdict](#overall-verdict)

---

## Replication 1: Geographic Variation in Medicare Spending

### Source Publication
- **Organization**: CMS / Dartmouth Atlas / MedPAC
- **Title**: "Geographic Variation in Medicare Spending" — CMS publishes a data highlight accompanying each Geographic Variation PUF release, showing state-level per-capita spending maps and identifying high/low-spending regions. MedPAC's annual March Report to Congress includes a chapter on regional variation in Medicare spending. The Dartmouth Atlas has published similar maps since the 1990s.
- **Approximate date**: CMS data highlight released annually with PUF (most recent ~2024 for 2022 data); MedPAC March 2024 Report Chapter 12 (NEEDS VERIFICATION)
- **Key finding**: "Per-capita Medicare spending varies by more than 50% across Hospital Referral Regions, with Miami, McAllen TX, and parts of Louisiana consistently among the highest-spending areas, while areas like Grand Junction CO, Rochester MN, and Portland OR rank among the lowest." MedPAC consistently documents a 1.5x-2x ratio between the 90th and 10th percentile states in standardized per-capita spending.

### Data Requirements

| Dataset | Years Needed | Available in MVP? | Mart Table |
|---------|-------------|-------------------|------------|
| Geographic Variation | 2018-2022 (5 years) | Yes | `mart_geographic__spending_variation` |
| Geographic Variation (county) | 2022 (latest year) | Yes | `mart_geographic__spending_variation` |
| NPPES (provider counts by state) | Current | Yes | `ref_providers` |

### Methodology
- **Original method (as understood)**: CMS calculates age-sex-race standardized per-capita spending by state and county, using both actual and price-standardized amounts. MedPAC uses price-standardized spending to isolate utilization differences. The Dartmouth Atlas uses HRR-level aggregations.
- **Our replication approach**: Use `mart_geographic__spending_variation` at state and county levels. Map `total_medicare_standardized_per_capita_amount` and `total_medicare_actual_per_capita_amount` across states. Calculate `spending_index_vs_national` (ratio to national average). Decompose into service categories (inpatient, physician, Part D, post-acute, etc.) to show what drives variation.
- **Key differences**: We cannot replicate HRR-level analysis (Geographic Variation PUF provides national/state/county, not HRR). Our analysis uses CMS's standardized amounts rather than running our own risk adjustment. We work with FFS beneficiaries only; cannot account for MA enrollment differences without Tier 2 data, though we can include `ma_penetration_rate` as context.

### Expected Output
- **Key metrics to reproduce**:
  - Range of state-level per-capita standardized spending (expected: ~$8,000-$13,000+ depending on year)
  - Coefficient of variation across states
  - Ratio of highest to lowest state (expected: ~1.4-1.6x)
  - Service category decomposition showing which service types drive variation
  - County-level spending distribution (histogram + map)
- **Visualizations to produce**:
  - Choropleth map: State-level standardized per-capita spending (red-blue diverging from national average)
  - Choropleth map: County-level spending for latest year (with suppression caveats)
  - Stacked bar chart: Service category breakdown (IP, physician, Part D, PAC, etc.) for top 10 and bottom 10 states
  - Scatter plot: Spending index vs. HCC risk score by state — testing whether high spending is explained by health status
  - Time series: Top 5 and bottom 5 states over 2018-2022
- **Blog post angle**: "The Medicare Spending Map: Where Does Your State Rank?" — an accessible overview showing that Medicare spending varies dramatically by geography, what service categories drive the differences, and how much is explained by population health versus practice patterns. Positions Project PUF as a tool for exploring these patterns interactively.

### Feasibility: HIGH
All data is directly available in the Geographic Variation PUF. State-level analysis requires no crosswalks or complex joins. County-level analysis is also directly supported. The only limitation is the inability to do HRR-level analysis.

### Priority: 1

---

## Replication 2: Opioid Prescribing in Medicare Part D

### Source Publication
- **Organization**: CMS / Office of Inspector General (OIG)
- **Title**: CMS publishes an annual "Medicare Part D Opioid Prescribing Mapping Tool" and data highlights on opioid prescribing trends. The OIG has published multiple reports including "Opioid Use in Medicare Part D" (OEI-02-18-00220, ~2020). CMS's "Opioid Prescribing Rates in Medicare Part D" data snapshot is published annually with the Part D PUF.
- **Approximate date**: CMS data snapshot updated annually (~2024 for 2022 data); OIG report ~2020 (NEEDS VERIFICATION)
- **Key finding**: "Opioid prescribing in Medicare Part D has declined significantly since 2013, with the number of opioid claims falling approximately 45-50% by 2022. However, geographic variation remains substantial, with states in the Southeast and Appalachia maintaining rates 2-3x the national average. A small fraction of providers (~1-2%) account for a disproportionate share of opioid prescribing."

### Data Requirements

| Dataset | Years Needed | Available in MVP? | Mart Table |
|---------|-------------|-------------------|------------|
| Part D Prescribers | 2017-2022 (opioid flags available ~2017+) | Yes | `mart_provider__prescribing_summary` |
| Part D Prescribers (drug-level) | 2017-2022 | Yes | `int_provider_prescriptions` |
| Geographic Variation | 2017-2022 | Yes | `mart_geographic__by_state` |
| NPPES | Current | Yes | `ref_providers` |

### Methodology
- **Original method (as understood)**: CMS uses the `Opioid_Drug_Flag` in the Part D PUF to identify opioid claims. They calculate the opioid prescribing rate as (opioid claims / total claims) per provider, then aggregate geographically. The OIG report identified "questionable" prescribers using volume thresholds and peer comparisons.
- **Our replication approach**: Use `mart_provider__prescribing_summary` which already has `opioid_claim_count`, `opioid_claim_rate`, and `opioid_beneficiary_count` pre-aggregated per prescriber per year. Aggregate to state level via `prescriber_state_code`. Use `mart_geographic__by_state` which includes `partd_opioid_claim_rate` at the state level. For provider-level analysis, identify top percentiles of opioid prescribers by `opioid_claim_rate` (among providers with >50 total claims to avoid small-sample noise). Track trends 2017-2022.
- **Key differences**: Our analysis uses CMS's `Opioid_Drug_Flag` directly — we do not independently classify drugs. Earlier years (pre-2017) may lack opioid flags, limiting our trend window. We cannot distinguish between appropriate and inappropriate opioid prescribing without clinical context (diagnoses, pain assessments) that is not in the PUF.

### Expected Output
- **Key metrics to reproduce**:
  - National opioid prescribing rate (claims) trend, 2017-2022
  - Total opioid claims and beneficiaries by year
  - State-level opioid prescribing rate map
  - Distribution of provider-level opioid rates (expect highly right-skewed)
  - Concentration: share of opioid claims from top 1%, 5%, 10% of prescribers
  - Long-acting opioid share of total opioid claims (using `is_long_acting_opioid_drug_flag`)
- **Visualizations to produce**:
  - Time series: National opioid claim count and opioid rate, 2017-2022
  - Choropleth map: State-level opioid prescribing rate, latest year
  - Small multiples: State-level opioid rate trends (sparklines for all 50 states)
  - Histogram: Provider-level opioid claim rate distribution
  - Lorenz curve / concentration chart: Share of total opioid claims by prescriber percentile
  - Specialty bar chart: Opioid prescribing rate by CMS specialty (`prescriber_type`)
- **Blog post angle**: "Tracking the Opioid Prescription Decline: Progress, Pockets, and Providers" — shows the national progress in reducing opioid prescribing, but highlights persistent geographic hotspots and the concentration of prescribing among a small number of providers. Positions Project PUF as a monitoring tool for this ongoing public health concern.

### Feasibility: HIGH
Opioid flags are embedded in the Part D PUF (from ~2017). The `mart_provider__prescribing_summary` already aggregates opioid metrics per provider. State-level aggregation is straightforward. The only limitation is the data year window for opioid flags.

### Priority: 2

---

## Replication 3: Medicare Physician Spending Concentration

### Source Publication
- **Organization**: CMS / Academic researchers
- **Title**: CMS published a data highlight with the original 2014 Part B PUF release showing spending concentration among physicians. Multiple academic papers have studied this, notably Welch et al. and analyses from the Brookings Institution. CMS's own fact sheet showed that "roughly 1% of providers accounted for approximately 14% of total Medicare Part B payments." The Wall Street Journal and ProPublica published interactive tools based on the Part B PUF data highlighting high-billing providers.
- **Approximate date**: CMS data highlight ~2014; ongoing academic literature. ProPublica "Dollars for Docs" and related projects ~2014-2018 (NEEDS VERIFICATION)
- **Key finding**: "Medicare Part B spending is highly concentrated: a small percentage of providers account for a disproportionate share of total payments. The top 10% of providers by total Medicare payment account for approximately 65-70% of all Part B spending. Specialty significantly determines billing volume — ophthalmologists, oncologists, and cardiologists consistently rank among the highest-billing specialties."

### Data Requirements

| Dataset | Years Needed | Available in MVP? | Mart Table |
|---------|-------------|-------------------|------------|
| Part B Utilization | 2020-2022 (2-3 years) | Yes | `mart_provider__practice_profile` |
| Part B by Specialty | 2020-2022 | Yes | `mart_provider__by_specialty` |
| NPPES | Current | Yes | `ref_providers` |

### Methodology
- **Original method (as understood)**: Rank all providers by total Medicare payment, then calculate cumulative share. Identify top specialties by total payments and per-provider averages. CMS and journalists have published lists of highest-paid individual providers.
- **Our replication approach**: Use `mart_provider__practice_profile` to rank providers by `total_medicare_payment_amount`. Calculate percentile distributions and cumulative concentration curves. Use `mart_provider__by_specialty` to compare specialties by `total_medicare_payment_amount`, `avg_payment_per_service_amount`, and `provider_count`. Filter to individual providers (`is_individual_flag = TRUE` from `ref_providers`) to avoid double-counting with organizational NPIs.
- **Key differences**: We replicate at the provider-NPI level using aggregated payments per year. We cannot verify individual provider identities beyond what is in the PUF (name, NPI, specialty). We must caveat that these are Part B payments only, not total income. We filter out organizational NPIs to avoid conflation.

### Expected Output
- **Key metrics to reproduce**:
  - Gini coefficient of Part B payment distribution among providers
  - Share of total spending from top 1%, 5%, 10%, 25% of providers
  - Mean and median total payment per provider by specialty
  - Top 20 specialties ranked by total Medicare payment, with provider counts
  - Average payment per service by specialty (reveals high-intensity vs. high-volume specialties)
- **Visualizations to produce**:
  - Lorenz curve: Cumulative share of Part B spending by provider percentile
  - Treemap: Total Part B spending by specialty (area = total spend, color = per-provider average)
  - Box plot: Distribution of provider-level total payment by specialty (top 15 specialties)
  - Bar chart: Top 20 specialties by total Medicare payment, with provider count overlay
  - Scatter plot: Per-provider average payment vs. provider count by specialty (bubble size = total spending)
- **Blog post angle**: "Who Gets the Medicare Dollar? Provider Spending Concentration in Part B" — reveals the dramatic concentration of Medicare spending among a small number of providers and certain specialties. Contextualizes why certain specialties dominate (procedure intensity, beneficiary volume) and what this means for payment reform efforts.

### Feasibility: HIGH
All required data is in `mart_provider__practice_profile` and `mart_provider__by_specialty`. No cross-source joins needed. Provider-level rankings and aggregations are straightforward. The filter for individual vs. organizational NPIs is available in `ref_providers`.

### Priority: 3

---

## Replication 4: Generic Drug Utilization Rates

### Source Publication
- **Organization**: CMS / KFF (Kaiser Family Foundation) / ASPE (HHS Office of the Assistant Secretary for Planning and Evaluation)
- **Title**: CMS publishes generic utilization metrics in Part D dashboards. KFF publishes "Medicare Part D in 20XX" fact sheets that include generic dispensing rates. ASPE has published issue briefs on generic drug savings in Medicare. CMS's "Medicare Part D — An In-Depth Review" annual report tracks generic utilization rates.
- **Approximate date**: KFF fact sheets published annually; ASPE briefs periodically; CMS dashboards updated annually (NEEDS VERIFICATION)
- **Key finding**: "Generic drugs account for approximately 90% of all Medicare Part D prescriptions filled but only about 20-25% of total drug spending. Generic utilization rates vary by specialty and geography, with some provider types lagging in generic adoption. Brand-name drugs, while only ~10% of prescriptions, drive the majority of Part D cost growth."

### Data Requirements

| Dataset | Years Needed | Available in MVP? | Mart Table |
|---------|-------------|-------------------|------------|
| Part D Prescribers (drug-level) | 2018-2022 | Yes | `int_provider_prescriptions` |
| Part D Prescribers (provider-level) | 2018-2022 | Yes | `mart_provider__prescribing_summary` |
| NPPES | Current | Yes | `ref_providers` |

### Methodology
- **Original method (as understood)**: CMS and KFF calculate generic dispensing rate (GDR) as the percentage of total claims or 30-day fills that are for generic drugs. The Part D PUF does not have a direct brand/generic flag, but the presence of both `Brnd_Name` and `Gnrc_Name` allows inference — when `Brnd_Name` matches or closely resembles `Gnrc_Name`, the drug is likely generic. Alternatively, certain brand names are well-known branded products.
- **Our replication approach**: Use `int_provider_prescriptions` at the drug level. Classify drugs as brand vs. generic using a heuristic: if `drug_brand_name` equals `drug_generic_name` (after normalization), classify as generic. This is an imperfect heuristic — some brands share names with generics and vice versa. Aggregate at the provider level and state level. Calculate generic claim rate, generic fill rate, and generic cost share. Compare across specialties and geographies.
- **Key differences**: Without an authoritative brand/generic flag or NDC-level data, our classification relies on name-matching heuristics. This introduces classification noise. CMS has access to complete claims data with NDC codes for precise classification. Our analysis will caveat this limitation clearly. We should build a drug name normalization/classification reference table to improve accuracy over time.

### Expected Output
- **Key metrics to reproduce**:
  - National generic dispensing rate by year (expected: ~88-92% of claims)
  - Generic cost share by year (expected: ~20-25% of total drug cost)
  - Average cost per claim: generic vs. brand (expected 5-10x difference)
  - State-level generic utilization rate variation
  - Specialty-level generic utilization rates (e.g., family medicine vs. oncology)
  - Year-over-year trend in generic rate (slow upward trend expected)
- **Visualizations to produce**:
  - Dual-axis bar chart: Generic share of claims vs. generic share of spending, by year
  - Choropleth map: State-level generic dispensing rate
  - Horizontal bar chart: Generic dispensing rate by prescriber specialty (top 20 specialties)
  - Scatter plot: Provider-level generic rate vs. total drug cost (providers with low generic rates and high costs are interesting outliers)
  - Time series: National generic claim rate and cost share, 2018-2022
- **Blog post angle**: "The Generic Gap: Where Brand-Name Drug Spending Persists in Medicare" — highlights the paradox that generics dominate prescription counts but brand-name drugs dominate costs. Identifies specialties and geographies where generic adoption lags and estimates the potential savings from increased generic utilization.

### Feasibility: MEDIUM
The main challenge is the absence of a definitive brand/generic flag in the Part D PUF. The name-matching heuristic will produce reasonable but imperfect results. A future `ref_drugs` normalization table would improve accuracy significantly. Despite this, the broad patterns (generic claim share >> generic cost share) will be robust to classification noise.

### Priority: 5

---

## Original 1: The Dual Practice Profile — Linking Procedure Billing to Prescribing Behavior

### Research Question
How do physician procedure billing patterns (Part B) correlate with prescribing behavior (Part D) across specialties, and can combined profiles identify distinct practice styles?

### Relevance
- **Why this matters**: Part B and Part D data are typically analyzed in isolation. CMS publishes them as separate files and most analyses treat them independently. Linking them via NPI creates a more complete picture of provider practice behavior — what procedures they perform AND what drugs they prescribe. This cross-source capability is a key differentiator for Project PUF.
- **Target audience**: Health services researchers, medical practice consultants, health plan network analysts, policy analysts studying practice variation.

### Data Sources

| Dataset | Years | Grain | Key Measures |
|---------|-------|-------|-------------|
| Part B Utilization | 2022 (latest) | Provider-service | `total_medicare_payment_amount`, `service_count`, `beneficiary_count` per NPI |
| Part D Prescribers | 2022 (latest) | Provider-drug | `total_drug_cost_amount`, `total_claim_count`, `opioid_claim_rate` per NPI |
| NPPES | Current | Provider identity | `primary_taxonomy_code`, `practice_state_code`, specialty |

### Methodology
- **Approach**: Descriptive + comparative + outlier detection
- **Key variables**:
  - From Part B (`mart_provider__practice_profile`): `total_medicare_payment_amount`, `total_service_count`, `distinct_hcpcs_code_count`, `facility_service_rate`, `drug_service_rate`
  - From Part D (`mart_provider__prescribing_summary`): `total_drug_cost_amount`, `distinct_drug_count`, `opioid_claim_rate`, `antibiotic_claim_rate`, `avg_cost_per_claim_amount`
  - Combined: `total_medicare_spend_amount` (Part B + Part D), `has_partb_activity_flag`, `has_partd_activity_flag`
- **Filters/exclusions**: Individual providers only (`is_individual_flag = TRUE`). Providers with both Part B and Part D activity (`has_partb_activity_flag AND has_partd_activity_flag`). Minimum volume threshold: >= 50 Part B services AND >= 50 Part D claims (to filter out low-activity providers affected by suppression artifacts).

### Expected Findings (hypotheses)
1. **Specialty clusters emerge**: Primary care specialties (Family Medicine, Internal Medicine) will show moderate Part B billing with high prescribing volume. Procedural specialties (Orthopedics, Cardiology) will show high Part B billing with lower prescribing relative to procedures. Medical specialties (Psychiatry, Rheumatology) will show moderate both.
2. **Opioid prescribing correlates with surgical procedure volume**: Specialties that perform pain-associated procedures (Orthopedics, Pain Management) will show higher opioid prescribing rates, but the correlation at the individual provider level within specialties will be weaker than expected.
3. **Drug cost intensity varies dramatically by specialty**: Oncology providers will have the highest average drug cost per claim (Part B drug infusions + Part D oral oncolytics). Primary care will have the lowest.
4. **"Part B only" and "Part D only" providers**: A meaningful fraction of providers (~15-25%) will appear in only one dataset, reflecting scope-of-practice differences (e.g., surgeons who don't prescribe Part D drugs; NPs/PAs who prescribe but don't bill many Part B procedures).

### Visualization Spec

| Chart | Type | Data | Interaction |
|-------|------|------|-------------|
| Specialty Practice Map | Scatter plot | X = avg Part B payment per provider, Y = avg Part D cost per provider, colored by specialty group | Hover: specialty name, provider count, key metrics |
| Provider Universe Venn | Proportional Venn diagram | Providers with Part B only, Part D only, and both | Click to filter dashboard |
| Dual Profile Card | Multi-metric card | For a selected specialty: side-by-side Part B and Part D summary stats | Specialty dropdown selector |
| Opioid-Procedure Correlation | Scatter with marginal histograms | X = facility service rate, Y = opioid claim rate, per provider within a selected specialty | Specialty filter, trend line toggle |
| Code Diversity vs. Drug Diversity | Scatter plot | X = distinct HCPCS codes, Y = distinct drugs prescribed, per provider | Color by specialty |

### Blog Post Angle
"Two Sides of the Stethoscope: What Medicare Part B and Part D Together Reveal About Physician Practice" — this analysis demonstrates the unique value of cross-source data linking. By combining procedure billing and prescribing data for the same providers, we reveal practice style differences that are invisible when examining either dataset alone. The piece would walk through 3-4 specialty profiles (e.g., comparing a typical internist, cardiologist, and orthopedic surgeon) and show how combined data creates a richer picture of practice behavior.

### Feasibility: HIGH
The `mart_provider__practice_profile` cross-source mart is specifically designed for this analysis, joining Part B and Part D on NPI. All required columns are modeled. The analysis is descriptive and requires no external data beyond the four MVP sources.

### Priority: 2

---

## Original 2: Telehealth Adoption Trajectory by Specialty and Geography

### Research Question
How did telehealth utilization in Medicare Part B change from pre-pandemic baseline (2019) through the pandemic (2020-2021) and into the post-pandemic period (2022+), and which specialties and states sustained the highest telehealth adoption rates?

### Relevance
- **Why this matters**: The COVID-19 public health emergency triggered unprecedented expansion of Medicare telehealth coverage. CMS temporarily waived geographic and originating site restrictions, and Congress extended many flexibilities. Whether telehealth utilization has "stuck" or reverted toward pre-pandemic levels is a major policy question — the Consolidated Appropriations Act of 2023 and subsequent legislation extended telehealth flexibilities, but their permanence depends in part on utilization evidence. This analysis contributes directly to that evidence base.
- **Target audience**: Telehealth policy advocates and critics, CMS policymakers, congressional staff, health systems evaluating virtual care investment, state medical boards.

### Data Sources

| Dataset | Years | Grain | Key Measures |
|---------|-------|-------|-------------|
| Part B Utilization | 2019-2022 (4 years) | Provider-service | Telehealth HCPCS codes, `service_count`, `beneficiary_count`, `total_medicare_payment_amount` |
| NPPES | Current | Provider identity | Specialty, geography |
| Geographic Variation | 2019-2022 | State/county benchmarks | Context for population-level denominators |

### Methodology
- **Approach**: Trend analysis + comparative
- **Key variables**:
  - Telehealth identification: HCPCS modifier approach — CMS uses Place of Service code '02' (Telehealth) and specific modifier codes. In the Part B PUF, we identify telehealth via: (a) HCPCS codes that are telehealth-specific (e.g., 99441-99443 for telephone E/M, G2010, G2012 for virtual check-ins, G2250-G2252 for virtual check-ins post-2020), and (b) broader E/M codes (99201-99215) where the `Place_Of_Srvc` may indicate telehealth.
  - **Important limitation**: The Part B PUF's `Place_Of_Srvc` field distinguishes 'F' (Facility) from 'O' (Office/non-facility) but does NOT specifically flag telehealth. Telehealth identification relies entirely on HCPCS code-based identification, which captures telehealth-specific codes but misses traditional E/M codes delivered via telehealth with only a modifier change.
- **Filters/exclusions**: Individual providers only. Analysis limited to HCPCS codes identifiable as telehealth. Behavioral health and primary care specialties are expected to show the strongest telehealth signal.

### Expected Findings (hypotheses)
1. **Massive spike in 2020**: Telehealth-specific HCPCS code volume increased by 50-100x from 2019 baseline.
2. **Partial reversion in 2021-2022**: Volume declined from 2020 peak but remains dramatically above 2019 baseline (likely 5-20x baseline).
3. **Specialty concentration**: Psychiatry, clinical psychology, and primary care specialties (Internal Medicine, Family Medicine) account for the majority of sustained telehealth utilization. Procedural specialties show minimal telehealth.
4. **Geographic variation**: Urban areas and states with pre-existing telehealth infrastructure (e.g., CA, NY) show higher sustained adoption. Rural areas show a spike but potentially lower sustained rates (contradicting the initial promise that telehealth would bridge rural access gaps).

### Visualization Spec

| Chart | Type | Data | Interaction |
|-------|------|------|-------------|
| Telehealth Volume Timeline | Area chart (stacked) | Total telehealth services by quarter/year, stacked by top specialties | Hover: exact counts; toggle between absolute and per-1000-beneficiary rates |
| Specialty Adoption Rates | Slope chart | Telehealth share of total services for top 15 specialties, 2019 vs. 2022 | Highlight specialty on hover |
| State Telehealth Map | Choropleth | State-level telehealth services per 1,000 FFS beneficiaries, latest year | Year slider for animation |
| Pre/Post Comparison | Dumbbell chart | Before (2019) and after (2022) telehealth claim volume by specialty | Sorted by absolute change or percent change |
| Top Telehealth Codes | Horizontal bar | Top 20 HCPCS codes by telehealth claim volume, 2022 | Tooltip with code description |

### Blog Post Angle
"Medicare Telehealth After the Emergency: Who's Still Dialing In?" — tracks the telehealth explosion and its aftermath using Part B billing data. Shows which specialties and regions turned a temporary emergency expansion into a permanent practice change, and where telehealth may be reverting to pre-pandemic norms. Relevant to ongoing Congressional debates about making telehealth flexibilities permanent.

### Feasibility: MEDIUM
The analysis is feasible but requires careful HCPCS code identification. The Part B PUF does not have a direct telehealth flag — we must maintain a curated list of telehealth-specific HCPCS codes and accept that we will undercount telehealth (traditional E/M codes delivered via telehealth with only a modifier, not a different HCPCS code, will be missed). The `ref_hcpcs_codes` table will need to be augmented with a telehealth classification flag. Despite this limitation, the telehealth-specific codes alone capture a meaningful signal.

### Priority: 4

---

## Original 3: Provider Workforce Dynamics — NPI Enumeration, Deactivation, and Specialty Distribution

### Research Question
What does the NPPES provider registry reveal about the healthcare workforce — how many providers are entering and exiting Medicare, what is the specialty and geographic distribution, and how has it changed over time?

### Relevance
- **Why this matters**: Healthcare workforce shortages are a top policy concern. AAMC projects a physician shortage of 37,800-124,000 by 2034. The NPPES registry, while not a perfect workforce measure (it includes all HIPAA-covered providers, not just Medicare participants), provides a uniquely comprehensive view of provider enumeration. By analyzing enumeration dates, deactivation dates, and taxonomy codes, we can track the inflow and outflow of providers over time by specialty and geography — a proxy for workforce dynamics.
- **Target audience**: Health workforce researchers, state medical boards, residency program directors, rural health policy analysts, congressional staff working on workforce legislation.

### Data Sources

| Dataset | Years | Grain | Key Measures |
|---------|-------|-------|-------------|
| NPPES | Current (covers enumeration dates from 2005-present) | Provider identity | `enumeration_date`, `deactivation_date`, `reactivation_date`, `primary_taxonomy_code`, `practice_state_code` |
| Geographic Variation | Latest year | State-level | `ffs_beneficiary_count` for provider-to-population ratios |

### Methodology
- **Approach**: Descriptive + trend
- **Key variables**:
  - From `ref_providers`: `enumeration_date` (proxy for workforce entry year), `deactivation_date` (proxy for exit), `primary_taxonomy_code` (specialty), `practice_state_code` (geography), `entity_type_code` (individual vs. organization), `is_active_flag`
  - From `ref_provider_taxonomies`: Full taxonomy distribution per provider
  - From `ref_geographies`: State-level beneficiary counts for provider-to-population ratios
- **Filters/exclusions**: Focus on Type 1 (individual) NPIs for workforce analysis. Exclude organizational NPIs. Acknowledge that NPPES includes all HIPAA-covered providers (not Medicare-specific) — some NPIs may never bill Medicare.
- **Enumeration cohorts**: Group providers by enumeration year (2005-2024). Calculate annual net change (new enumerations minus deactivations).
- **Taxonomy analysis**: Map NUCC taxonomy codes to human-readable specialty groups. Calculate specialty distribution among active NPIs.

### Expected Findings (hypotheses)
1. **Steady enumeration growth**: Approximately 300,000-400,000 new NPIs enumerated per year, with growth accelerating for NPs and PAs.
2. **NP/PA growth outpacing physicians**: The fastest-growing taxonomy groups will be Nurse Practitioners and Physician Assistants, reflecting scope-of-practice expansions.
3. **Geographic maldistribution persists**: Provider-to-beneficiary ratios will vary 2-3x between highest and lowest density states. Rural states will show lower provider density.
4. **Deactivation patterns**: Annual deactivations run at approximately 5-8% of the active NPI pool. Spikes may correspond to CMS revalidation cycles.

### Visualization Spec

| Chart | Type | Data | Interaction |
|-------|------|------|-------------|
| NPI Enumeration Trend | Area chart | New NPIs enumerated per year, 2005-present, stacked by major provider type (MD/DO, NP, PA, Other) | Hover for counts; toggle individual vs. organizational |
| Workforce Balance | Waterfall chart | Annual: starting active NPIs + new enumerations - deactivations = ending active NPIs | Year selector |
| Provider Density Map | Choropleth | Active individual NPIs per 1,000 Medicare FFS beneficiaries, by state | Toggle to show specific specialty groups |
| Specialty Distribution | Sunburst chart | Hierarchical: major specialty group > specific taxonomy > state distribution | Click to drill down |
| Growth Rate Ranking | Horizontal bar | Year-over-year percentage growth in active NPIs by specialty group, latest year | Sort toggle |

### Blog Post Angle
"8 Million NPIs: What the Provider Registry Tells Us About America's Healthcare Workforce" — uses the NPPES database as a lens on workforce dynamics. Highlights the rapid growth of NPs and PAs, persistent geographic maldistribution, and provides state-level provider density scorecards. Relevant to every state legislature debating scope-of-practice laws and to federal workforce planning.

### Feasibility: HIGH
All data is available in `ref_providers` and `ref_provider_taxonomies`. The NPPES file contains enumeration and deactivation dates that directly support longitudinal analysis. The main caveat is that NPPES includes non-Medicare providers — this should be clearly disclosed. For a more Medicare-specific view, we could filter to NPIs that appear in the Part B or Part D files, but this reduces the workforce scope.

### Priority: 3

---

## Original 4: State-Level Spending Decomposition — Price vs. Utilization vs. Mix

### Research Question
For each state, how much of the difference between that state's Medicare spending and the national average is attributable to price differences, utilization differences, and service mix differences?

### Relevance
- **Why this matters**: The geographic variation debate often conflates price and utilization. A state might have high Medicare spending because its providers charge more (price), because its beneficiaries use more services (utilization), or because it has a different mix of expensive vs. inexpensive services (mix). CMS's standardized spending removes price, but does not separately isolate utilization vs. mix. This decomposition is analytically novel and directly relevant to policy: payment reform targets price, while delivery reform targets utilization. Understanding the decomposition guides which intervention is appropriate.
- **Target audience**: Health economists, CMS/CMMI staff designing payment models, state-level policymakers, MedPAC commissioners and staff.

### Data Sources

| Dataset | Years | Grain | Key Measures |
|---------|-------|-------|-------------|
| Part B Utilization | 2022 | Provider-service-state | `service_count`, `avg_medicare_payment_amount`, `avg_medicare_standardized_amount` per HCPCS per provider |
| Geographic Variation | 2022 | State-level | `total_medicare_actual_per_capita_amount`, `total_medicare_standardized_per_capita_amount`, `ffs_beneficiary_count` |
| NPPES | Current | Provider identity | `practice_state_code` |

### Methodology
- **Approach**: Decomposition analysis (Blinder-Oaxaca style conceptual framework, simplified)
- **Key variables**:
  - **Price effect**: Difference between actual per-capita spending and standardized per-capita spending at the state level. Available directly from Geographic Variation: `total_medicare_actual_per_capita_amount - total_medicare_standardized_per_capita_amount` isolates the impact of geographic price adjustments (wage index, practice cost index, etc.).
  - **Utilization effect**: From Part B data aggregated to the state level, compare services-per-beneficiary for each state to the national average. Weighted by national average payment per service to hold price and mix constant.
  - **Mix effect**: The residual after removing price and utilization effects. Reflects differences in the composition of services (e.g., more imaging vs. more E/M) valued at national prices.
- **Filters/exclusions**: Part B individual providers only. State-level aggregation. HCPCS codes with sufficient volume for stable estimates.

### Expected Findings (hypotheses)
1. **Price explains 30-50% of interstate spending variation**: Geographic payment adjustments (wage index, GPCIs) create substantial price differences between states.
2. **Utilization explains 30-40%**: After removing price, states still vary substantially in how many services per beneficiary are provided.
3. **Mix explains 10-20%**: The composition of services (high-cost procedures vs. office visits) accounts for a smaller but meaningful share.
4. **State profiles cluster**: High-cost states like FL and TX show different decomposition profiles (FL: high utilization; TX: mixed). Low-cost states like MN and OR show low utilization.

### Visualization Spec

| Chart | Type | Data | Interaction |
|-------|------|------|-------------|
| Decomposition Waterfall | Waterfall chart per state | National avg -> + Price effect -> + Utilization effect -> + Mix effect -> = State actual spending | State selector dropdown |
| State Rankings by Component | Diverging bar chart | For each state, three bars showing deviation from national average for price, utilization, and mix | Sort by any component |
| Decomposition Map | Choropleth (3-panel) | Three maps side by side: price deviation, utilization deviation, mix deviation | Synchronized hover across panels |
| Scatter: Price vs. Utilization | Scatter plot | X = price effect (deviation from national), Y = utilization effect, per state, bubble size = total spending | Quadrant annotations (high-price/high-util, etc.) |

### Blog Post Angle
"Why Medicare Costs More in Some States: Untangling Price, Utilization, and Service Mix" — provides a novel decomposition that goes beyond the standard geographic variation analysis. Shows policymakers that high-spending states are not all high-spending for the same reasons, and therefore require different interventions. A state with high prices needs payment reform; a state with high utilization needs delivery reform.

### Feasibility: MEDIUM
The price effect is directly calculable from Geographic Variation (actual vs. standardized spending). The utilization and mix decomposition requires aggregating Part B data to the state level, calculating services-per-beneficiary by HCPCS code, and comparing to national averages. This is computationally involved but uses only MVP data. The main complexity is ensuring the decomposition is methodologically sound and that residuals are handled properly.

### Priority: 6

---

## Trend Monitor 1: Per-Capita Medicare Standardized Spending by State

### Definition
- **What**: Total Medicare standardized per-capita payment amount for FFS beneficiaries, calculated by state, reported annually. This is the single most important benchmark for tracking geographic variation in Medicare spending over time.
- **Source**: `mart_geographic__spending_variation.total_medicare_standardized_per_capita_amount` at `geographic_level = 'State'`
- **Grain**: State-level, annual. 50 states + DC + territories.

### Policy Relevance
Standardized per-capita spending is the North Star metric for geographic variation in Medicare. It removes price differences to isolate utilization and intensity variation. Tracking this metric over time reveals whether the spending gap between high- and low-spending states is widening or narrowing. This matters for:

- **ACO and value-based care evaluation**: Are ACOs in high-spending areas bending the cost curve?
- **Payment reform**: Congress periodically considers geographic payment adjustments. The spending trend data informs these debates.
- **MedPAC recommendations**: MedPAC's annual March Report includes updated geographic variation analysis. This monitor allows Project PUF users to track the same metrics.
- **State-level health policy**: State health departments and legislatures use this data to benchmark their state's Medicare cost trajectory.

### Dashboard Widget
- **Chart type**: Small multiples — one sparkline per state showing 5-year trend, arranged geographically (as a tile map) or ranked by latest-year spending level. Accompanied by a headline summary showing the national average, the state range (min-max), and the coefficient of variation.
- **Timeframe**: 5 most recent data years (e.g., 2018-2022)
- **Alert threshold**: Flag any state where year-over-year change in standardized per-capita spending exceeds +/- 5%. Also flag if the coefficient of variation across states increases by more than 10% year-over-year (indicating growing disparity).
- **Drill-down**: Click on a state to see service-category breakdown (inpatient, physician, Part D, etc.) and county-level within-state variation.
- **Update cadence**: Annually when new Geographic Variation PUF is released.

### Priority: 1

---

## Trend Monitor 2: Opioid Prescribing Rate Among Medicare Part D Providers

### Definition
- **What**: National and state-level opioid prescribing rate, defined as (total opioid claims / total Part D claims) * 100, aggregated across all Part D prescribers, reported annually.
- **Source**: `mart_geographic__by_state.partd_opioid_claim_rate` at the state level. National rate calculated from `mart_provider__prescribing_summary` aggregated across all providers.
- **Grain**: National (one number per year) and state-level (one number per state per year). Optionally, specialty-level (one number per CMS specialty per year).

### Policy Relevance
The opioid crisis remains one of the defining public health challenges of this era. Medicare Part D prescribing data is a critical monitoring tool because:

- **Policy enforcement tracking**: CMS has implemented multiple opioid prescribing safety measures including the Part D Overutilization Monitoring System (OMS), prior authorization for high-dose opioids, and lock-in programs. This monitor tracks whether these policies are reflected in aggregate prescribing trends.
- **SUPPORT Act compliance**: The Substance Use-Disorder Prevention that Promotes Opioid Recovery and Treatment (SUPPORT) for Patients and Communities Act of 2018 included provisions specifically targeting Medicare Part D opioid prescribing. Tracking the rate monitors compliance.
- **Geographic hotspot identification**: Persistently high-rate states may need targeted interventions. New hotspots emerging should trigger alerts.
- **Long-acting opioid tracking**: The `is_long_acting_opioid_drug_flag` enables separate tracking of long-acting opioids, which carry higher abuse potential.

### Dashboard Widget
- **Chart type**: Dual panel — (1) national time series line chart showing opioid claim rate over 5 years with shaded confidence band, (2) state tile map showing latest-year opioid rate with color gradient (green to red).
- **Timeframe**: 5 most recent data years with opioid flags (e.g., 2017-2022)
- **Alert threshold**: Flag any state where the opioid prescribing rate increases year-over-year (since the national trend is downward, any reversal is noteworthy). Flag the national rate if it fails to decline by at least 1 percentage point per year. Flag states where the rate exceeds 2x the national average.
- **Supplementary metric**: Long-acting opioid share of total opioid claims (track separately).
- **Update cadence**: Annually when new Part D PUF is released.

### Priority: 2

---

## Recommended Launch Sequence

Analyses should be published in an order that maximizes impact, builds credibility through replication first, and progressively demonstrates cross-source capabilities.

| Sequence | Analysis | Type | Rationale |
|----------|----------|------|-----------|
| **1** | Geographic Variation in Medicare Spending | Replication | Establishes credibility by reproducing the most well-known CMS data story. Provides the "map" that draws readers in. Relatively simple analysis that validates data pipeline integrity. |
| **2** | Opioid Prescribing in Medicare Part D | Replication | High public interest topic. Demonstrates Part D data pipeline. Opioids consistently generate media and policy attention. |
| **3** | Trend Monitor: Per-Capita Spending by State | Trend Monitor | Launches simultaneously with Analysis 1 as the dashboard companion. Shows the platform provides ongoing monitoring, not just static reports. |
| **4** | Trend Monitor: Opioid Prescribing Rate | Trend Monitor | Launches simultaneously with Analysis 2 as the dashboard companion. |
| **5** | Medicare Physician Spending Concentration | Replication | Well-known finding. Demonstrates provider-level Part B analysis. Sets up audience interest in "who are these providers?" — teeing up the cross-source analysis next. |
| **6** | The Dual Practice Profile | Original | **The showcase analysis.** Demonstrates cross-source NPI linkage (Part B + Part D), which is the platform's core differentiator. Published after the audience understands the individual datasets from analyses 1-5. |
| **7** | Provider Workforce Dynamics | Original | Uses NPPES in a novel way. Broader audience appeal beyond Medicare policy (workforce is relevant to every healthcare stakeholder). Generates state-level scorecards that drive social sharing. |
| **8** | Generic Drug Utilization Rates | Replication | Drug pricing is politically charged and drives ongoing media coverage. Demonstrates Part D drug-level analysis capability. |
| **9** | State-Level Spending Decomposition | Original | The most analytically sophisticated piece. Published last because it requires the audience to understand geographic variation (Analysis 1), Part B data (Analysis 5), and the difference between price and utilization. This is the "expert-level" content that attracts researchers and MedPAC-type audiences. |
| **10** | Telehealth Adoption Trajectory | Original | Published when the HCPCS classification work is complete. This analysis requires the most preprocessing (building a telehealth HCPCS code list). High policy relevance justifies the effort, but other analyses can launch while this is being refined. |

---

## Data Gaps Identified

| Gap | Impact | Affected Analyses | Severity |
|-----|--------|-------------------|----------|
| **No brand/generic drug flag in Part D PUF** | Cannot definitively classify brand vs. generic drugs. Requires name-matching heuristic. | Replication 4 (Generic Utilization) | MEDIUM — heuristic will approximate but not match CMS precision |
| **No telehealth flag in Part B PUF** | Cannot identify all telehealth encounters; only telehealth-specific HCPCS codes are identifiable. Traditional E/M codes delivered via telehealth are missed. | Original 2 (Telehealth) | MEDIUM — analysis will undercount telehealth but capture the trend |
| **No NUCC taxonomy description lookup table** | `ref_provider_taxonomies` stores taxonomy codes but not human-readable specialty names. Need a crosswalk from NUCC taxonomy code to specialty description. | Original 3 (Workforce Dynamics) | LOW — NUCC publishes the crosswalk; need to ingest it as a reference table |
| **No ZIP-to-county crosswalk** | Part B and Part D provider data uses ZIP codes; Geographic Variation uses FIPS county codes. Cannot do county-level provider aggregation without the crosswalk. | All analyses requiring sub-state provider aggregation | MEDIUM — state-level joins work fine; county-level requires HUD crosswalk |
| **No `ref_drugs` normalization table** | Part D drug names are free-text with variant spellings. Cannot reliably aggregate by drug molecule without normalization. | Replication 4, any drug-specific analysis | MEDIUM — deferred to future sprint per Schema Smith |
| **Chronic condition prevalence columns not yet in staging** | Geographic Variation PUF includes ~20 chronic condition prevalence fields (`Benes_FFS_Pct_*`) that are documented but deferred from MVP staging schema. | Enriches geographic analyses with disease burden context | LOW for launch analyses — these are contextual, not primary |
| **Historical NPPES snapshots not available** | NPPES is a "current state" file. We have no historical snapshots. Provider addresses, taxonomies, and active status reflect only current data. | Original 3 (Workforce Dynamics) — longitudinal address changes are not trackable | LOW for launch — enumeration/deactivation dates still enable entry/exit analysis |
| **MA enrollment data not in MVP** | Cannot precisely quantify MA penetration at the county level to contextualize FFS-only analyses. | Geographic Variation mart includes `ma_penetration_rate` from Geo Variation PUF, which mitigates this partially | LOW — Geo Variation already provides MA counts; full MA enrollment is Tier 2 |

---

## Upstream Requirements

| Requirement | Agent | Priority | Description |
|------------|-------|----------|-------------|
| Build `ref_telehealth_hcpcs_codes` reference table | **Schema Smith** | HIGH | Curated list of HCPCS codes classified as telehealth-specific. Required for Original 2 (Telehealth). Should include code, description, first-year-available, and telehealth subcategory (e.g., telephone E/M, virtual check-in, audio-only). |
| Build `ref_nucc_taxonomy` reference table | **Schema Smith** | HIGH | Crosswalk from NUCC taxonomy code to specialty description, classification, and specialty group. Required for Original 3 (Workforce) and useful for all provider analyses. NUCC publishes this as a CSV. |
| Build brand/generic drug classification heuristic | **Schema Smith** | MEDIUM | Logic (dbt model or seed) that classifies Part D drug records as brand vs. generic based on `drug_brand_name` / `drug_generic_name` matching. Required for Replication 4 (Generic Utilization). |
| Ingest HUD ZIP-to-county crosswalk | **Pipeline Architect** | MEDIUM | Required to aggregate Part B/Part D provider data to the county level for geographic analyses. HUD publishes quarterly updates. |
| Add chronic condition prevalence columns to `stg_cms__geographic_variation` | **Schema Smith** | LOW | ~20 additional columns (`Benes_FFS_Pct_*`) already in the source data but deferred from MVP staging. Enriches geographic analyses with disease burden context. |
| Design interactive visualization framework | **UX Advocate** | HIGH | All 10 analyses produce visualizations. Need to decide on charting library (D3.js, Plotly, Observable, etc.), map rendering (Mapbox, Leaflet), and interaction patterns (filters, drill-downs, tooltips) before building the first visualization. |
| Design blog post template and publishing workflow | **UX Advocate** | MEDIUM | Analyses produce blog posts. Need a content management approach — static site generator, template design, metadata schema for cross-linking analyses to data sources. |
| Build opioid trend monitoring pipeline | **Pipeline Architect** | LOW | For Trend Monitor 2 to function as an automated monitor, need a pipeline that detects when new Part D data is released, triggers ingestion, and updates the dashboard. Not required for initial manual analysis. |

---

## Overall Verdict: PUBLISH

**Rationale**: All 10 analyses are feasible with MVP Tier 1 data. Four replication studies validate data accuracy by reproducing known findings. Four original analyses demonstrate cross-source capabilities that distinguish Project PUF from existing CMS data tools. Two trend monitors establish the platform as an ongoing monitoring resource rather than a one-time report.

**Key strengths of the plan**:
- Every analysis uses only MVP Tier 1 data (NPPES, Part B, Part D, Geographic Variation)
- Replication studies target well-documented, verifiable findings from CMS, MedPAC, and KFF
- Original analyses exploit cross-source NPI joins that CMS does not publish
- Analyses span the full range of complexity, from simple choropleth maps to decomposition analyses
- Each analysis has a clear blog post narrative and visualization specification
- The launch sequence builds credibility (replication first) before showcasing innovation (cross-source originals)

**Key risks**:
- Data vintage: Analyses assume 2018-2022 data availability, which needs verification (latest Part B/Part D may be 2022 or 2023)
- Telehealth analysis depends on HCPCS code curation that is not yet done
- Generic drug classification is approximate without NDC-level data
- All analyses cover FFS Medicare only — as MA exceeds 50%, this is increasingly unrepresentative (must caveat consistently)

**Verification items to resolve before execution**:
- [ ] Confirm latest available data year for Part B, Part D, and Geographic Variation PUFs
- [ ] Verify that opioid flags are available in Part D data from 2017 onward
- [ ] Locate and verify CMS data highlights, MedPAC chapters, and KFF publications cited in replication studies
- [ ] Confirm NUCC taxonomy crosswalk CSV is freely available for download
- [ ] Confirm HUD ZIP-to-county crosswalk availability and format
- [ ] Identify specific telehealth HCPCS codes for the curated reference table
