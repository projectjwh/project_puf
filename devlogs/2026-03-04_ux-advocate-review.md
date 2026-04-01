# UX Advocate Review: MVP Frontend Data Contracts

> **Agent**: UX Advocate | **Date**: 2026-03-04 | **Status**: NEEDS UPSTREAM WORK
> **Scope**: 5 MVP pages — National Dashboard, Provider Lookup, Geographic Explorer, Specialty Comparison, Opioid Prescribing Monitor
> **Tech Stack**: Next.js + ECharts + Tailwind + TanStack Table + FastAPI (Arch Advisor approved)
> **Data Layer**: 17 mart/ref tables across Provider and Geographic domains (Schema Smith approved)

---

## Table of Contents

1. [Page: National Dashboard](#page-national-dashboard)
2. [Page: Provider Lookup](#page-provider-lookup)
3. [Page: Geographic Explorer](#page-geographic-explorer)
4. [Page: Specialty Comparison](#page-specialty-comparison)
5. [Page: Opioid Prescribing Monitor](#page-opioid-prescribing-monitor)
6. [Shared UI Components](#shared-ui-components)
7. [Shared Data Requirements](#shared-data-requirements)
8. [Upstream Requirements Summary](#upstream-requirements-summary)
9. [Overall Verdict](#overall-verdict)

---

# Page: National Dashboard

**Route**: `/`

## User Story

As a **healthcare researcher or policy analyst**,
I want to see key national Medicare metrics at a glance — total providers, total spending, top specialties, and a geographic spending heatmap,
so that I can quickly orient myself to the scale and shape of the Medicare landscape before drilling into specifics.

## Data Contract

| Query | Input Parameters | Expected Response | Max Latency | Mart Table |
|-------|-----------------|-------------------|-------------|------------|
| National headline metrics | `data_year` (default: latest) | `{ total_providers, total_services, total_payment, total_drug_cost, total_beneficiaries, ma_penetration_rate, avg_hcc_risk_score }` | <500ms | `mart_geographic__spending_variation` (national row) + pre-aggregated from `mart_provider__by_specialty` |
| Top 10 specialties by spending | `data_year`, `sort_by` (payment or provider_count) | Array of `{ specialty, provider_count, total_payment, total_services, avg_payment_per_service }` | <500ms | `mart_provider__by_specialty` |
| Spending by service category | `data_year` | `{ ip_per_capita, physician_per_capita, partd_per_capita, op_per_capita, pac_per_capita, hh_per_capita, hospice_per_capita, dme_per_capita }` | <500ms | `mart_geographic__spending_variation` (national row) |
| State spending heatmap | `data_year` | Array of `{ state_fips, state_name, standardized_per_capita, spending_index_vs_national, ffs_beneficiary_count }` — all 50 states + DC + territories | <500ms | `mart_geographic__spending_variation` (state-level rows) |
| Year-over-year national spending trend | None | Array of `{ data_year, standardized_per_capita, ip_per_capita, physician_per_capita, partd_per_capita }` for all available years | <1s | `mart_geographic__spending_variation` (national row, all years) |
| Provider count by entity type | `data_year` | `{ individual_count, organization_count, active_count, inactive_count }` | <500ms | Pre-aggregated from `ref_providers` |

## Filter Dimensions

| Filter | Source Table | Cardinality | UI Element |
|--------|------------|-------------|------------|
| Year | All marts (`data_year`) | ~10 (2013-2022) | Dropdown (single-select, default: latest) |

## Visualization Spec

| Chart | Type | X-axis | Y-axis | Data Source | Interaction |
|-------|------|--------|--------|------------|-------------|
| Headline KPI cards | Stat cards (4-6) | -- | -- | National headline metrics query | None; static with YOY delta badge |
| Spending by service category | Stacked horizontal bar | Service category | Per-capita spending ($) | Spending by category query | Hover tooltip with percentage of total |
| Top specialties | Horizontal bar chart | Total Medicare payment ($) | Specialty name (sorted) | Top 10 specialties query | Click to navigate to `/specialties?type=X` |
| State spending heatmap | US choropleth map | -- | -- | State spending heatmap query | Hover shows state name + spending index; click navigates to `/geography?state=XX` |
| National spending trend | Multi-line chart | Data year | Per-capita spending ($) | YOY trend query | Hover tooltip; toggle lines by category |

## Performance Budget

| Metric | Target |
|--------|--------|
| Initial load (all above-the-fold queries) | <3s |
| Year filter change | <500ms |
| Chart render (all 5 charts) | <1s total |
| Largest Contentful Paint | <2.5s |
| Cumulative Layout Shift | <0.1 |

## Accessibility

- Tabular alternative for all charts: every chart has a "View as table" toggle rendering the same data in a TanStack Table
- Colorblind-safe palette: Viridis for choropleth, categorical palette from ColorBrewer (8-class Set2) for bar/line charts
- Keyboard navigation: Tab through KPI cards, Enter to expand chart tables, arrow keys to navigate within charts
- Screen reader: KPI cards have `aria-label` with full metric description and value
- URL-driven state: `/?year=2022` — all filter states encoded in URL query params
- Reduced motion: Disable chart animations when `prefers-reduced-motion` is set

## Upstream Requirements

| Requirement | Assigned To | Priority |
|------------|-------------|----------|
| Pre-aggregated national headline KPI endpoint (total provider count from `ref_providers`, not re-counted per request) | Pipeline Architect / API layer | HIGH |
| National row in `mart_geographic__spending_variation` must always exist for every `data_year` | Schema Smith | HIGH |
| `mart_provider__by_specialty` needs a `rank_by_payment` or pre-sorted index on `total_medicare_payment_amount DESC` for efficient Top-N | Schema Smith | MEDIUM |

---

# Page: Provider Lookup

**Route**: `/providers` (search) and `/providers/:npi` (detail)

## User Story

As a **healthcare researcher, journalist, or general public user**,
I want to search for a specific provider by NPI, name, or specialty and view their complete practice profile — what they bill, what they prescribe, and how they compare to peers,
so that I can understand an individual provider's practice patterns in a Medicare context.

## Data Contract

### Search Endpoint

| Query | Input Parameters | Expected Response | Max Latency | Mart Table |
|-------|-----------------|-------------------|-------------|------------|
| Provider search | `q` (search string), `entity_type` (optional: Individual/Organization), `state` (optional), `specialty` (optional), `page`, `page_size` (default 25) | Paginated array of `{ npi, provider_display_name, provider_credential, primary_taxonomy_code, rendering_provider_type, practice_state_code, practice_city_name, is_active_flag }` + `total_count` | <1s | `ref_providers` (full-text search on `provider_display_name`, exact match on `npi`) |
| Provider autocomplete | `q` (min 3 chars) | Array of top 10 `{ npi, provider_display_name, practice_state_code, rendering_provider_type }` | <300ms | `ref_providers` (prefix search) |

### Detail Endpoint

| Query | Input Parameters | Expected Response | Max Latency | Mart Table |
|-------|-----------------|-------------------|-------------|------------|
| Provider identity | `npi` | `{ npi, entity_type_name, provider_display_name, provider_first_name, provider_last_name, provider_credential, provider_gender_code, primary_taxonomy_code, taxonomy_count, practice_city_name, practice_state_code, practice_zip5, enumeration_date, is_active_flag, years_since_enumeration }` | <500ms | `ref_providers` |
| Provider taxonomies | `npi` | Array of `{ taxonomy_code, is_primary_taxonomy_flag, taxonomy_slot_number }` | <500ms | `ref_provider_taxonomies` |
| Provider Part B profile | `npi`, `data_year` (default: latest) | `{ rendering_npi, data_year, rendering_provider_type, total_beneficiary_count, total_service_count, total_medicare_payment_amount, total_medicare_standardized_amount, total_submitted_charge_amount, distinct_hcpcs_code_count, facility_service_rate, drug_service_rate, avg_payment_per_service_amount, avg_services_per_beneficiary_count }` | <500ms | `mart_provider__practice_profile` |
| Provider Part D profile | `npi`, `data_year` (default: latest) | `{ prescriber_npi, data_year, total_claim_count, total_drug_cost_amount, distinct_drug_count, opioid_claim_count, opioid_claim_rate, antibiotic_claim_rate, avg_cost_per_claim_amount }` | <500ms | `mart_provider__prescribing_summary` |
| Provider practice profile (combined) | `npi`, `data_year` (default: latest) | Full `mart_provider__practice_profile` row including Part D columns | <500ms | `mart_provider__practice_profile` (cross-source) |
| Provider year-over-year trend | `npi` | Array of `{ data_year, total_service_count, total_medicare_payment_amount, total_beneficiary_count, partd_total_claim_count, partd_total_drug_cost_amount, partd_opioid_claim_rate }` for all available years | <1s | `mart_provider__practice_profile` (all years for this NPI) |
| Provider peer comparison | `npi`, `data_year` | `{ provider_values: {...}, specialty_avg: {...}, national_avg: {...} }` where each contains `total_service_count, total_payment, avg_payment_per_service, opioid_claim_rate` | <1s | `mart_provider__practice_profile` + `mart_provider__by_specialty` |
| Provider top HCPCS codes | `npi`, `data_year` (default: latest), `limit` (default 10) | Array of `{ hcpcs_code, hcpcs_description, service_count, beneficiary_count, avg_medicare_payment_amount, total_medicare_payment_amount }` sorted by `service_count DESC` | <1s | `int_provider_services` (filtered to single NPI) |
| Provider top drugs | `npi`, `data_year` (default: latest), `limit` (default 10) | Array of `{ drug_generic_name, drug_brand_name, total_claim_count, total_drug_cost_amount, total_beneficiary_count, is_opioid_drug_flag }` sorted by `total_claim_count DESC` | <1s | `int_provider_prescriptions` (filtered to single NPI) |

## Filter Dimensions

### Search Page

| Filter | Source Table | Cardinality | UI Element |
|--------|------------|-------------|------------|
| Search query | `ref_providers` (`provider_display_name`, `npi`) | Free text | Search input with autocomplete |
| Entity type | `ref_providers` (`entity_type_name`) | 2 (Individual, Organization) | Toggle buttons |
| State | `ref_providers` (`practice_state_code`) | 56 | Searchable dropdown |
| Specialty | `mart_provider__by_specialty` (`rendering_provider_type`) | ~100-200 | Searchable dropdown |

### Detail Page

| Filter | Source Table | Cardinality | UI Element |
|--------|------------|-------------|------------|
| Year | `mart_provider__practice_profile` (`data_year`) | ~10 (only years with data for this NPI) | Dropdown (single-select) |

## Visualization Spec

### Detail Page

| Chart | Type | X-axis | Y-axis | Data Source | Interaction |
|-------|------|--------|--------|------------|-------------|
| Provider identity card | Info card | -- | -- | Provider identity query | Static display |
| Part B / Part D summary cards | Stat cards (6-8) | -- | -- | Combined practice profile query | Peer comparison badges (above/below specialty avg) |
| Year-over-year trend | Multi-line chart | Data year | Spending / services / beneficiaries (switchable) | YOY trend query | Toggle metric; hover tooltip |
| Peer comparison radar/bar | Grouped bar chart | Metric name | Normalized value (percentile or ratio to specialty avg) | Peer comparison query | Hover tooltip with raw values |
| Top HCPCS codes | Horizontal bar chart | Service count | HCPCS code + description (top 10) | Top HCPCS query | Click to filter; hover shows payment |
| Top drugs prescribed | Horizontal bar chart | Claim count | Drug name (top 10) | Top drugs query | Opioid drugs highlighted in distinct color; hover shows cost |

## Performance Budget

| Metric | Target |
|--------|--------|
| Search results (first page) | <1s |
| Autocomplete response | <300ms |
| Provider detail page (all queries) | <2s total (parallel fetch) |
| Year filter change on detail page | <500ms |
| Chart render (detail page) | <1s |

## Accessibility

- Tabular alternative for all charts
- Colorblind-safe palette: opioid drugs highlighted using pattern fill (diagonal stripes) in addition to color
- Keyboard navigation: Tab through search results, Enter to open detail, Escape to close
- Screen reader: Provider identity card reads full name, NPI, specialty, location
- URL-driven state: `/providers?q=smith&state=CA&type=Individual&page=2` for search; `/providers/1234567890?year=2022` for detail
- Search input has `role="combobox"` with `aria-autocomplete="list"` for autocomplete

## Upstream Requirements

| Requirement | Assigned To | Priority |
|------------|-------------|----------|
| Full-text search index on `ref_providers.provider_display_name` (PostgreSQL `gin_trgm_ops` or equivalent) | Schema Smith | HIGH |
| Prefix/trigram search capability for autocomplete (<300ms on 8M rows) | Schema Smith / Pipeline Architect | HIGH |
| `int_provider_services` must be queryable by single NPI + year with reasonable latency (index on `rendering_npi, data_year`) | Schema Smith | HIGH |
| `int_provider_prescriptions` must be queryable by single NPI + year with reasonable latency (index on `prescriber_npi, data_year`) | Schema Smith | HIGH |
| Peer comparison requires specialty-level averages to be returned alongside individual provider data — API must join `mart_provider__practice_profile` with `mart_provider__by_specialty` on `rendering_provider_type` | API layer | MEDIUM |
| NUCC taxonomy code descriptions needed for display on provider detail page — requires a `ref_taxonomy_codes` reference table mapping taxonomy codes to human-readable classification/specialization names | Schema Smith | HIGH |

---

# Page: Geographic Explorer

**Route**: `/geography`

## User Story

As a **policy analyst or healthcare researcher**,
I want to explore Medicare spending, utilization, and beneficiary demographics across states (and eventually counties) using an interactive map and comparison table,
so that I can identify geographic variation in healthcare delivery and spending — a core driver of Medicare policy reform.

## Data Contract

| Query | Input Parameters | Expected Response | Max Latency | Mart Table |
|-------|-----------------|-------------------|-------------|------------|
| State choropleth data | `data_year`, `metric` (one of: `standardized_per_capita`, `spending_index`, `ma_penetration_rate`, `er_visits_per_1000`, `ip_stays_per_1000`, `readmission_rate`, `avg_hcc_risk_score`, `partd_opioid_claim_rate`) | Array of `{ state_fips, state_name, metric_value, national_value, ratio_to_national }` for all states | <500ms | `mart_geographic__spending_variation` (state rows) |
| State comparison table | `data_year`, `sort_by`, `sort_dir`, `page`, `page_size` | Paginated array of all `mart_geographic__by_state` columns for state rows | <500ms | `mart_geographic__by_state` |
| State detail | `state_fips`, `data_year` | Full `mart_geographic__by_state` row + `mart_geographic__spending_variation` row for this state | <500ms | `mart_geographic__by_state` + `mart_geographic__spending_variation` |
| State trend | `state_fips` | Array of `{ data_year, standardized_per_capita, spending_index, ma_penetration_rate, partb_total_payment, partd_total_drug_cost, partd_opioid_claim_rate }` for all years | <1s | `mart_geographic__spending_variation` + `mart_geographic__by_state` (all years for this state) |
| Multi-state comparison | `state_fips[]` (up to 5), `data_year` | Array of full `mart_geographic__by_state` rows for selected states | <500ms | `mart_geographic__by_state` |
| Spending category breakdown | `state_fips`, `data_year` | `{ ip_per_capita, physician_per_capita, op_per_capita, pac_per_capita, hh_per_capita, hospice_per_capita, dme_per_capita, partd_per_capita }` for this state + national values | <500ms | `mart_geographic__spending_variation` |
| National benchmarks (for comparison line) | `data_year` | National row from `mart_geographic__spending_variation` | <500ms | `mart_geographic__spending_variation` (national row) |

## Filter Dimensions

| Filter | Source Table | Cardinality | UI Element |
|--------|------------|-------------|------------|
| Year | `mart_geographic__spending_variation` (`data_year`) | ~10-15 (2007-2022) | Dropdown (single-select) |
| Metric for map | -- | ~8 (see metric list above) | Dropdown or button group |
| State (for multi-state comparison) | `ref_geographies` | 56 | Searchable multi-select dropdown (max 5) |

## Visualization Spec

| Chart | Type | X-axis | Y-axis | Data Source | Interaction |
|-------|------|--------|--------|------------|-------------|
| US choropleth map | Choropleth (US state boundaries) | -- | -- | State choropleth query | Hover shows state name + metric value + rank; click selects state for detail panel |
| State comparison table | Sortable data table | -- | -- | State comparison table query | Sort by any column; click row to select state; column highlighting for selected metric |
| State detail panel (sidebar/drawer) | Info panel with mini-charts | -- | -- | State detail query | Opens on state click from map or table |
| State trend line chart | Multi-line chart | Data year | Selected metric | State trend query | Hover tooltip; compare to national benchmark line (dashed) |
| Multi-state comparison | Grouped bar chart | State name | Selected metric | Multi-state comparison query | Hover tooltip; national avg reference line |
| Spending category breakdown | Stacked bar chart | Service category | Per-capita spending ($) | Spending category query | Side-by-side: selected state vs. national |

## Performance Budget

| Metric | Target |
|--------|--------|
| Initial load (map + table) | <3s |
| Metric switch on map | <500ms (client-side re-render; data already loaded) |
| Year filter change | <500ms |
| State click (detail panel) | <500ms |
| Multi-state comparison render | <1s |

## Accessibility

- Tabular alternative for choropleth: the state comparison table IS the tabular alternative — always visible alongside the map
- Colorblind-safe palette: Viridis (sequential) for choropleth; diverging palette (blue-white-red via Cividis) when showing index vs. national
- Keyboard navigation: Tab to map region, arrow keys between states, Enter to select; full keyboard support for table sort/filter
- Screen reader: Map regions have `aria-label` with state name and metric value; table is properly marked up with `<th scope>`
- URL-driven state: `/geography?year=2022&metric=spending_index&selected=CA,TX,NY`
- Mobile adaptation: Map becomes a ranked bar chart (top 10 states) with "show all" expanding to full table; comparison table uses horizontal scroll with sticky first column (state name)

## Upstream Requirements

| Requirement | Assigned To | Priority |
|------------|-------------|----------|
| GeoJSON or TopoJSON file for US state boundaries (linked by `state_fips`) | Pipeline Architect (static asset) | HIGH |
| `mart_geographic__spending_variation` must include national row as benchmark for every metric and year | Schema Smith | HIGH (already designed, confirming) |
| County-level choropleth deferred to post-MVP (requires county TopoJSON + ZIP-to-county crosswalk) | -- | DEFERRED |
| `spending_index_vs_national` column confirmed available in `mart_geographic__spending_variation` | Schema Smith | HIGH (already designed) |

---

# Page: Specialty Comparison

**Route**: `/specialties`

## User Story

As a **healthcare researcher or policy analyst**,
I want to compare Medicare spending, utilization, and practice patterns across medical specialties,
so that I can understand which specialties drive Medicare spending, how practice intensity varies, and how specialties differ in coding breadth and drug prescribing patterns.

## Data Contract

| Query | Input Parameters | Expected Response | Max Latency | Mart Table |
|-------|-----------------|-------------------|-------------|------------|
| All specialties summary | `data_year`, `sort_by`, `sort_dir` | Array of all `mart_provider__by_specialty` rows for the given year (estimated ~100-200 rows) | <500ms | `mart_provider__by_specialty` |
| Specialty detail | `rendering_provider_type`, `data_year` | Full `mart_provider__by_specialty` row for this specialty + year | <500ms | `mart_provider__by_specialty` |
| Specialty trend | `rendering_provider_type` | Array of `{ data_year, provider_count, total_medicare_payment_amount, total_service_count, avg_payment_per_service_amount, avg_services_per_provider_count, avg_beneficiaries_per_provider_count, drug_service_rate }` for all years | <1s | `mart_provider__by_specialty` (all years) |
| Specialty comparison | `rendering_provider_type[]` (up to 5), `data_year` | Array of full `mart_provider__by_specialty` rows for selected specialties | <500ms | `mart_provider__by_specialty` |
| Specialty prescribing profile | `rendering_provider_type`, `data_year` | Aggregated prescribing metrics: `{ total_claim_count, total_drug_cost, avg_opioid_claim_rate, avg_antibiotic_claim_rate, avg_distinct_drug_count }` — aggregated from providers of this specialty | <1s | `mart_provider__prescribing_summary` aggregated by `prescriber_type` |
| Top providers in specialty | `rendering_provider_type`, `data_year`, `sort_by`, `limit` (default 20) | Array of `{ npi, provider_display_name, practice_state_code, total_service_count, total_medicare_payment_amount, total_beneficiary_count }` | <1s | `mart_provider__practice_profile` filtered by `rendering_provider_type` |

## Filter Dimensions

| Filter | Source Table | Cardinality | UI Element |
|--------|------------|-------------|------------|
| Year | `mart_provider__by_specialty` (`data_year`) | ~10 | Dropdown (single-select) |
| Specialty (multi-select for comparison) | `mart_provider__by_specialty` (`rendering_provider_type`) | ~100-200 | Searchable multi-select dropdown (max 5) |
| Sort metric | -- | ~8 (payment, services, providers, avg_payment, avg_services, avg_beneficiaries, hcpcs_breadth, drug_rate) | Dropdown |

## Visualization Spec

| Chart | Type | X-axis | Y-axis | Data Source | Interaction |
|-------|------|--------|--------|------------|-------------|
| Specialty ranking table | Sortable data table | -- | -- | All specialties query | Sort by any column; click row to select specialty; sparkline column for YOY trend |
| Specialty bubble chart | Scatter/bubble | Avg services per provider | Avg payment per service | All specialties query | Bubble size = provider count; hover shows specialty name + all metrics; click selects |
| Specialty comparison grouped bar | Grouped bar chart | Metric name | Value | Specialty comparison query | Side-by-side bars for each selected specialty |
| Specialty trend line | Multi-line chart | Data year | Selected metric (toggle) | Specialty trend query | One line per selected specialty; hover tooltip |
| Top providers in specialty | Data table | -- | -- | Top providers query | Click NPI to navigate to `/providers/:npi` |
| Prescribing profile summary | Stat cards + horizontal bar | -- | -- | Specialty prescribing query | Static display; opioid rate highlighted if above national avg |

## Performance Budget

| Metric | Target |
|--------|--------|
| Initial load (table + bubble chart) | <2s |
| Year filter change | <500ms |
| Specialty selection for comparison | <500ms |
| Trend chart load | <1s |
| Top providers table load | <1s |

## Accessibility

- Tabular alternative: the specialty ranking table IS the primary view; bubble chart has "View as table" toggle
- Colorblind-safe palette: Categorical palette (ColorBrewer Set2) for multi-specialty comparison; bubbles use size + label, not color alone
- Keyboard navigation: Tab through table rows, Enter to select specialty for detail; arrow keys within comparison chart
- Screen reader: Table has sortable column headers with `aria-sort`; bubble chart has `aria-label` per bubble
- URL-driven state: `/specialties?year=2022&selected=Internal+Medicine,Cardiology&sort=total_medicare_payment_amount&dir=desc`
- Mobile adaptation: Bubble chart hidden on mobile; table uses card layout with expandable rows

## Upstream Requirements

| Requirement | Assigned To | Priority |
|------------|-------------|----------|
| Specialty-level prescribing aggregation: `mart_provider__by_specialty` currently only has Part B columns. Need a companion `mart_specialty__prescribing_summary` or add prescribing columns (opioid_claim_rate, antibiotic_claim_rate, avg_drug_cost) to `mart_provider__by_specialty` by joining through `mart_provider__prescribing_summary` on `prescriber_type` | Schema Smith | HIGH |
| Specialty names need a canonical mapping — CMS `rendering_provider_type` may have inconsistencies across years (e.g., "Internal Medicine" vs "INTERNAL MEDICINE"). Need normalization in int layer or a `ref_specialties` lookup | Schema Smith | MEDIUM |
| Sparkline data in the table requires all years' data loaded per specialty — confirm `mart_provider__by_specialty` is small enough (~200 specialties x 10 years = 2,000 rows) to load entirely client-side | API layer | LOW |

---

# Page: Opioid Prescribing Monitor

**Route**: `/opioids`

## User Story

As a **policy analyst, public health researcher, or journalist**,
I want to monitor opioid prescribing patterns across providers, specialties, and geographies,
so that I can identify high-prescribing outliers, track trends over time, and understand the geographic distribution of opioid prescribing — critical for monitoring the ongoing opioid crisis response.

## Data Contract

| Query | Input Parameters | Expected Response | Max Latency | Mart Table |
|-------|-----------------|-------------------|-------------|------------|
| National opioid headline metrics | `data_year` | `{ total_opioid_claims, total_opioid_cost, total_prescribers_with_opioids, pct_prescribers_with_opioids, avg_opioid_claim_rate, long_acting_opioid_claims }` | <500ms | Pre-aggregated from `mart_provider__prescribing_summary` |
| Opioid trend (national) | None | Array of `{ data_year, total_opioid_claims, total_opioid_cost, avg_opioid_claim_rate, pct_prescribers_with_opioids }` for all years | <1s | Pre-aggregated from `mart_provider__prescribing_summary` (all years) |
| State opioid map | `data_year` | Array of `{ state_fips, state_name, opioid_claim_rate, opioid_claim_count, prescriber_count }` for all states | <500ms | `mart_geographic__by_state` (has `partd_opioid_claim_rate`) |
| Specialty opioid ranking | `data_year`, `sort_by`, `limit` (default 20) | Array of `{ specialty, prescriber_count, opioid_claim_rate, opioid_claim_count, opioid_cost, long_acting_opioid_claim_count }` | <1s | Aggregated from `mart_provider__prescribing_summary` grouped by `prescriber_type` |
| High-prescribing providers | `data_year`, `state` (optional), `specialty` (optional), `min_opioid_claim_rate` (optional, default 0.10), `sort_by`, `page`, `page_size` | Paginated array of `{ npi, provider_display_name, prescriber_type, state_code, total_claim_count, opioid_claim_count, opioid_claim_rate, opioid_cost, long_acting_opioid_claim_count }` | <1s | `mart_provider__prescribing_summary` filtered + joined to `ref_providers` |
| Provider opioid detail | `npi` | Array of `{ data_year, opioid_claim_count, opioid_claim_rate, opioid_drug_cost, long_acting_opioid_claim_count, total_claim_count }` for all years | <1s | `mart_provider__prescribing_summary` (all years for this NPI) |
| State vs. national opioid comparison | `state_fips`, `data_year` | `{ state_opioid_rate, national_opioid_rate, state_rank, total_states }` | <500ms | `mart_geographic__by_state` |
| Opioid distribution histogram | `data_year`, `state` (optional) | Histogram bins: array of `{ bin_floor, bin_ceiling, provider_count }` for opioid_claim_rate distribution (e.g., 0-5%, 5-10%, ..., 90-100%) | <2s | `mart_provider__prescribing_summary` (requires bucketing query) |

## Filter Dimensions

| Filter | Source Table | Cardinality | UI Element |
|--------|------------|-------------|------------|
| Year | `mart_provider__prescribing_summary` (`data_year`) | ~10 | Dropdown (single-select) |
| State | `ref_geographies` (`state_fips`) | 56 | Searchable dropdown |
| Specialty | `mart_provider__prescribing_summary` (`prescriber_type`) | ~100-200 | Searchable dropdown |
| Minimum opioid claim rate | -- | Continuous (0-100%) | Slider with numeric input |

## Visualization Spec

| Chart | Type | X-axis | Y-axis | Data Source | Interaction |
|-------|------|--------|--------|------------|-------------|
| Headline opioid KPI cards | Stat cards (4-5) | -- | -- | National opioid headline query | YOY delta badge; trend sparkline |
| National opioid trend | Line chart | Data year | Opioid claims / rate / cost (toggle) | Opioid trend query | Hover tooltip; toggleable metric |
| State opioid choropleth | Choropleth (US state) | -- | -- | State opioid map query | Hover shows state rate + rank; click filters provider table to that state |
| Specialty opioid bar chart | Horizontal bar chart | Opioid claim rate (%) | Specialty name (sorted) | Specialty opioid ranking query | Click navigates to `/specialties?type=X`; hover shows claim count + cost |
| High-prescribing provider table | Sortable data table | -- | -- | High-prescribing providers query | Sort by any column; click NPI navigates to `/providers/:npi`; opioid rate column has color-coded cell background (low/medium/high) |
| Opioid rate distribution | Histogram | Opioid claim rate (%) bins | Provider count | Distribution histogram query | Hover shows exact count; click bin to filter provider table |
| Provider opioid trend (modal/drawer) | Line chart | Data year | Opioid claims / rate | Provider opioid detail query | Opens on click from provider table |

## Performance Budget

| Metric | Target |
|--------|--------|
| Initial load (KPIs + map + trend chart) | <3s |
| Year filter change | <500ms |
| State/specialty filter on provider table | <1s |
| Provider table pagination | <500ms |
| Distribution histogram | <2s |
| Provider detail modal | <1s |

## Accessibility

- Tabular alternative for all charts
- Colorblind-safe palette: Sequential red palette (Reds from ColorBrewer) for opioid choropleth — intensity conveys severity. Pattern fills added for high-rate thresholds
- Keyboard navigation: Full table keyboard support; slider accessible via arrow keys
- Screen reader: KPI cards with full metric context; provider table rows include opioid rate category ("high", "moderate", "low") in aria-label
- URL-driven state: `/opioids?year=2022&state=WV&specialty=Family+Practice&min_rate=0.15&sort=opioid_claim_rate&dir=desc&page=1`
- Sensitive data disclaimer: Banner stating data reflects prescribing patterns and does not imply inappropriate prescribing; individual clinical context is not available
- Mobile adaptation: Choropleth replaced with ranked state bar chart (top 10 by opioid rate); provider table uses card layout

## Upstream Requirements

| Requirement | Assigned To | Priority |
|------------|-------------|----------|
| Pre-aggregated national opioid headline metrics endpoint — requires SUM/COUNT across all rows of `mart_provider__prescribing_summary` per year (1.1M rows per year). This MUST be materialized as a summary table or cached, not computed on-the-fly | Schema Smith / Pipeline Architect | HIGH |
| `long_acting_opioid_claim_count` needs to be added to `mart_provider__prescribing_summary` — currently only `opioid_claim_count` is aggregated; the long-acting opioid flag exists in `int_provider_prescriptions` but is not carried to the prescribing summary mart | Schema Smith | HIGH |
| Specialty-level opioid aggregation: need `mart_specialty__opioid_summary` or add to the specialty prescribing model requested in Specialty Comparison page | Schema Smith | HIGH |
| Histogram bucketing: either pre-computed in a mart table or supported as a server-side query. At ~1.1M rows/year, bucketing `opioid_claim_rate` into 20 bins is feasible in DuckDB but may need caching for <2s latency | Pipeline Architect / API layer | MEDIUM |
| Provider opioid table requires index on `mart_provider__prescribing_summary` for `(data_year, prescriber_state_code, prescriber_type, opioid_claim_rate)` to support filtered+sorted queries | Schema Smith | MEDIUM |

---

# Shared UI Components

## Navigation / Sidebar Structure

```
[Logo: Project PUF]
-----------------------------
Dashboard          /
Provider Lookup    /providers
Geographic Explorer /geography
Specialty Comparison /specialties
Opioid Monitor     /opioids
-----------------------------
[Data Year Selector]  (global, sticky)
[About / Data Sources] /about
```

- **Desktop**: Collapsible left sidebar (default expanded). Active page highlighted. Global year selector at bottom of sidebar.
- **Mobile**: Bottom tab bar with 5 icons (Dashboard, Providers, Geography, Specialties, Opioids). Year selector in a sticky top bar.
- The global year selector sets the default `data_year` for all pages. Individual pages can override. Changing the global year updates the URL `?year=` param on the current page.

## Common Filter Bar Component

- Sticky below the page header (desktop) or in a collapsible filter drawer (mobile)
- Composed of:
  - **Dropdown** (single-select): Year, sort metric, sort direction
  - **Searchable dropdown** (single-select): State, specialty
  - **Searchable multi-select dropdown** (up to 5): States for comparison, specialties for comparison
  - **Slider** (continuous): Minimum opioid rate
  - **Toggle buttons**: Entity type (Individual/Organization)
  - **Search input with autocomplete**: Provider name/NPI
- All filter values synchronized to URL query params
- "Reset filters" button clears all to defaults
- Filter state changes trigger data re-fetch with debounce (300ms for text inputs, immediate for dropdowns)

## Data Table Component (TanStack Table)

Standard configuration applied across all tables:

| Feature | Configuration |
|---------|--------------|
| Library | TanStack Table v8 (headless) |
| Sorting | Client-side for <1,000 rows; server-side for larger datasets |
| Pagination | Server-side with configurable page size (10, 25, 50, 100) |
| Column visibility | User-toggleable; default set per page |
| Column resize | Enabled |
| Row click | Navigates to detail page or opens detail panel |
| Sticky header | Always on |
| Sticky first column | On horizontal scroll (for wide tables) |
| Number formatting | `Intl.NumberFormat` with appropriate precision: integers for counts, 2 decimals for currency, 1-2 decimals for rates/percentages |
| Currency formatting | USD with $ prefix, comma thousands separator |
| Percentage formatting | Multiply by 100 if stored as decimal; display with % suffix |
| Null/suppressed display | "N/A" or suppression indicator icon with tooltip explaining CMS <11 suppression rule |
| Export | CSV and JSON download for current view (filtered + sorted) |
| Empty state | "No results match your filters" with suggestion to broaden filters |
| Loading state | Skeleton rows matching column count |

## Chart Wrapper Component (ECharts)

Standard configuration applied across all charts:

| Feature | Configuration |
|---------|--------------|
| Library | Apache ECharts v5 |
| Theme | Custom theme aligned with Tailwind design tokens |
| Responsive | `useResizeObserver` — charts resize on container change |
| Tooltip | Always enabled; formatted with same number/currency formatting as tables |
| Legend | Positioned top-right for line/bar charts; hidden for single-series |
| Colors | Categorical: ColorBrewer Set2 (8-class). Sequential: Viridis. Diverging: Cividis. Opioid: Reds. All palettes colorblind-safe |
| Grid lines | Light gray, horizontal only for bar charts; both for scatter |
| Animation | 300ms ease-out; disabled when `prefers-reduced-motion` |
| View as table toggle | Every chart instance includes a "View as table" button that swaps to TanStack Table rendering of the same data |
| Loading state | Skeleton chart placeholder matching approximate dimensions |
| Error state | "Failed to load chart data" with retry button |
| No data state | "No data available for selected filters" |
| Download | PNG export via ECharts `getDataURL()` |
| Choropleth maps | US state GeoJSON registered as ECharts map; state boundaries styled with 1px white stroke |

## Export Component

- **CSV export**: Downloads the current filtered/sorted table data as CSV. Filename includes page name + filters + timestamp (e.g., `providers_CA_2022_20260304.csv`).
- **JSON export**: Same data as JSON array.
- **Chart PNG export**: Downloads the current chart as PNG via ECharts.
- **Shareable link**: "Copy link" button copies the current URL (with all filter state) to clipboard.

---

# Shared Data Requirements

## Reference Data Loaded on App Init

These datasets are small enough to load once on application initialization and cache in memory:

| Data | Source Table | Estimated Size | Cache Strategy |
|------|-------------|----------------|----------------|
| Available data years | Distinct `data_year` from all marts | <1 KB | App init; refresh on deploy |
| State list (FIPS + name) | `ref_geographies` (state-level rows) | ~56 rows, <5 KB | App init; static |
| Specialty list | Distinct `rendering_provider_type` from `mart_provider__by_specialty` | ~200 rows, <10 KB | App init; refresh weekly |
| US state GeoJSON | Static file | ~500 KB (TopoJSON) | App init; static asset via CDN |

## Caching Strategy

| Data Type | Cache Location | TTL | Invalidation |
|-----------|---------------|-----|-------------|
| Reference data (states, specialties, years) | Client-side (React state / context) | Session lifetime | On app init |
| National dashboard metrics | Server-side (FastAPI response cache, e.g., `cachetools` or Redis) | 24 hours | On data refresh (dbt run) |
| Geographic data (all states for a year) | Server-side + client-side (TanStack Query) | 24 hours server / 5 min client stale time | On data refresh |
| Specialty data (all specialties for a year) | Server-side + client-side | 24 hours server / 5 min client stale time | On data refresh |
| Provider search results | Client-side only (TanStack Query) | 5 min stale time | Not cached server-side (too variable) |
| Provider detail | Client-side (TanStack Query) | 5 min stale time | Not cached server-side |
| Opioid aggregations | Server-side | 24 hours | On data refresh |

## API Pagination Conventions

All paginated endpoints follow a consistent contract:

```json
{
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_count": 1234,
    "total_pages": 50,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {
    "data_year": 2022,
    "state": "CA"
  },
  "sort": {
    "field": "total_medicare_payment_amount",
    "direction": "desc"
  }
}
```

- Default `page_size`: 25
- Maximum `page_size`: 100
- Page numbering starts at 1
- `total_count` is always returned for client-side pagination controls
- Non-paginated endpoints (small datasets like specialties, states) return flat arrays

## API Route Structure

```
/api/v1/
  dashboard/
    GET /metrics?year=2022                          → National headline KPIs
    GET /spending-trend                              → National YOY trend
    GET /spending-categories?year=2022               → Spending by service category
  providers/
    GET /search?q=smith&state=CA&page=1              → Provider search
    GET /autocomplete?q=smi                          → Provider autocomplete
    GET /:npi                                        → Provider identity
    GET /:npi/profile?year=2022                      → Combined practice profile
    GET /:npi/trend                                  → Provider YOY trend
    GET /:npi/services?year=2022&limit=10            → Top HCPCS codes
    GET /:npi/drugs?year=2022&limit=10               → Top drugs
    GET /:npi/peers?year=2022                        → Peer comparison
  geography/
    GET /map?year=2022&metric=spending_index          → State choropleth data
    GET /states?year=2022&sort=standardized_per_capita → State comparison table
    GET /states/:state_fips?year=2022                 → State detail
    GET /states/:state_fips/trend                     → State trend
    GET /compare?states=CA,TX,NY&year=2022            → Multi-state comparison
  specialties/
    GET /?year=2022&sort=total_medicare_payment_amount → All specialties
    GET /:specialty?year=2022                          → Specialty detail
    GET /:specialty/trend                              → Specialty trend
    GET /:specialty/prescribing?year=2022              → Specialty prescribing profile
    GET /:specialty/providers?year=2022&limit=20       → Top providers in specialty
    GET /compare?types=Internal+Medicine,Cardiology&year=2022 → Comparison
  opioids/
    GET /metrics?year=2022                             → National opioid KPIs
    GET /trend                                         → National opioid trend
    GET /map?year=2022                                 → State opioid map
    GET /by-specialty?year=2022                         → Specialty opioid ranking
    GET /providers?year=2022&state=WV&min_rate=0.10     → High-prescribing providers
    GET /providers/:npi/trend                           → Provider opioid detail
    GET /distribution?year=2022&state=WV                → Opioid rate histogram
```

---

# Upstream Requirements Summary

Consolidated list of ALL requirements sent back to Schema Smith and Pipeline Architect.

## Schema Smith Requirements

| # | Requirement | Source Page | Priority | Rationale |
|---|------------|------------|----------|-----------|
| S1 | Add full-text search index (`gin_trgm_ops` or similar) on `ref_providers.provider_display_name` | Provider Lookup | **HIGH** | Autocomplete and search on 8M rows requires trigram index; without it, LIKE queries will timeout |
| S2 | Add indexes on `int_provider_services` for `(rendering_npi, data_year)` | Provider Lookup | **HIGH** | Provider detail page queries individual NPI's services; without index, full table scan on ~10M rows |
| S3 | Add indexes on `int_provider_prescriptions` for `(prescriber_npi, data_year)` | Provider Lookup | **HIGH** | Same as S2 for Part D data (~25M rows) |
| S4 | Create `ref_taxonomy_codes` reference table mapping NUCC taxonomy codes to human-readable classification and specialization names | Provider Lookup | **HIGH** | Provider detail page needs to display taxonomy descriptions, not raw codes. Source: NUCC taxonomy CSV (publicly available) |
| S5 | Add `long_acting_opioid_claim_count` to `mart_provider__prescribing_summary` | Opioid Monitor | **HIGH** | Long-acting opioid distinction is critical for policy analysis; the flag exists in `int_provider_prescriptions` but is not aggregated to the mart |
| S6 | Create `mart_specialty__prescribing_summary` (or add prescribing columns to `mart_provider__by_specialty`) — specialty-level aggregation of Part D prescribing including opioid_claim_rate, antibiotic_claim_rate, avg_drug_cost, avg_distinct_drug_count | Specialty Comparison + Opioid Monitor | **HIGH** | Both pages need specialty-level prescribing metrics; currently `mart_provider__by_specialty` only has Part B columns |
| S7 | Normalize specialty names: ensure `rendering_provider_type` / `prescriber_type` values are consistent across Part B and Part D data and across years. Consider a `ref_specialties` lookup table | Specialty Comparison | **MEDIUM** | Inconsistent specialty names (case, abbreviation) will cause incorrect grouping and confusing UI |
| S8 | Add composite index on `mart_provider__prescribing_summary` for `(data_year, prescriber_state_code, prescriber_type, opioid_claim_rate)` | Opioid Monitor | **MEDIUM** | High-prescribing provider table needs filtered + sorted queries on this combination |
| S9 | Add `rank_by_payment` or ensure efficient Top-N query support on `mart_provider__by_specialty` (`total_medicare_payment_amount DESC`) | National Dashboard | **MEDIUM** | Top 10 specialties query on dashboard |
| S10 | Confirm national row always exists in `mart_geographic__spending_variation` for every `data_year` | National Dashboard + Geographic Explorer | **HIGH** | Multiple pages depend on the national row as a benchmark; if missing, all relative comparisons fail |

## Pipeline Architect Requirements

| # | Requirement | Source Page | Priority | Rationale |
|---|------------|------------|----------|-----------|
| P1 | Pre-aggregated national headline KPI endpoint: total provider count, total services, total payment — materialized view or summary table refreshed on each dbt run | National Dashboard | **HIGH** | Cannot SUM across all `mart_provider__practice_profile` rows (~1.2M/year) on every dashboard load and meet <500ms target |
| P2 | Pre-aggregated national opioid headline metrics: materialized view or summary table with total opioid claims, total opioid cost, prescriber count with opioids, avg opioid rate | Opioid Monitor | **HIGH** | Same as P1 — aggregation over ~1.1M rows must be pre-computed |
| P3 | US state GeoJSON/TopoJSON static asset: state boundaries linked by `state_fips`. Deploy as static asset served via CDN | Geographic Explorer + Opioid Monitor | **HIGH** | Choropleth maps require geometry data; must be available at app init |
| P4 | Server-side response caching (Redis or in-memory TTL cache) for aggregate endpoints (dashboard, opioid KPIs, geographic, specialty) with 24-hour TTL, invalidated on data refresh | All pages | **HIGH** | Aggregate queries on large marts need caching to meet latency targets |
| P5 | Histogram bucketing query for opioid rate distribution — either pre-computed summary table or optimized DuckDB query with caching | Opioid Monitor | **MEDIUM** | Bucketing ~1.1M rows into 20 bins; feasible in DuckDB but needs caching for consistent <2s |

## API Layer Requirements

| # | Requirement | Source Page | Priority | Rationale |
|---|------------|------------|----------|-----------|
| A1 | Consistent pagination contract (see [API Pagination Conventions](#api-pagination-conventions)) | All pages | **HIGH** | Frontend pagination components depend on consistent response shape |
| A2 | Provider search endpoint must support: exact NPI match, prefix name match, trigram fuzzy match, with filters (state, specialty, entity_type) | Provider Lookup | **HIGH** | Core user flow; search must feel fast and accurate |
| A3 | Peer comparison endpoint must join `mart_provider__practice_profile` with `mart_provider__by_specialty` server-side and return both provider values and specialty averages | Provider Lookup | **MEDIUM** | Client should not need two separate requests to render the comparison |
| A4 | All endpoints must accept `data_year` parameter with default to latest available year | All pages | **HIGH** | Consistent API convention |

---

# Overall Verdict: NEEDS UPSTREAM WORK

## Blocking Items (must be resolved before frontend development begins)

1. **S1** — Full-text search index on `ref_providers`. Without this, the Provider Lookup page is non-functional. The entire provider search experience depends on sub-second queries against 8M rows.

2. **S4** — `ref_taxonomy_codes` reference table. Provider detail pages need to display taxonomy descriptions. Without this, we show raw NUCC codes which are meaningless to users.

3. **S5 + S6** — Long-acting opioid aggregation and specialty prescribing summary. The Opioid Monitor and Specialty Comparison pages both depend on prescribing data aggregated at the specialty level. The current Schema Smith design aggregates Part D only at the individual provider level (`mart_provider__prescribing_summary`), not at the specialty level. This is a structural gap.

4. **P1 + P2** — Pre-aggregated headline KPI tables. The National Dashboard and Opioid Monitor both need national-level aggregations that cannot be computed on-the-fly within latency budgets. These should be materialized views or summary tables refreshed on each dbt run.

5. **P3** — US state GeoJSON. Two pages depend on choropleth maps. This is a static asset but must be sourced, processed, and deployed.

6. **S10** — National benchmark row confirmation. Multiple pages use the national row in `mart_geographic__spending_variation` as a comparison baseline. If this row is missing for any data year, relative metrics (spending index, above/below national) break.

## Non-Blocking Items (can be resolved in parallel with frontend development)

- S2, S3 (indexes on int tables) — performance optimization, not structural
- S7 (specialty name normalization) — data quality improvement
- S8, S9 (additional indexes) — performance optimization
- P4 (server-side caching) — infrastructure setup, not data model
- P5 (histogram bucketing) — implementation detail
- A1-A4 (API conventions) — API layer design, not data model

## Readiness Assessment

| Page | Status | Blocking On |
|------|--------|------------|
| National Dashboard | NEEDS UPSTREAM WORK | P1 (headline KPIs), S10 (national row confirmation) |
| Provider Lookup | NEEDS UPSTREAM WORK | S1 (search index), S4 (taxonomy reference), S2+S3 (int table indexes) |
| Geographic Explorer | READY (with P3 caveat) | P3 (GeoJSON asset) |
| Specialty Comparison | NEEDS UPSTREAM WORK | S6 (specialty prescribing mart) |
| Opioid Prescribing Monitor | NEEDS UPSTREAM WORK | S5 (long-acting opioid), S6 (specialty prescribing), P2 (opioid KPIs) |

## Recommended Resolution Order

1. **Schema Smith sprint** (resolves S1, S2, S3, S4, S5, S6, S10): Add indexes, create `ref_taxonomy_codes`, add `long_acting_opioid_claim_count` to prescribing summary, create specialty prescribing mart, confirm national row invariant. Estimated effort: 1-2 days.
2. **Pipeline Architect sprint** (resolves P1, P2, P3): Create materialized summary tables for national KPIs, source and deploy US state TopoJSON. Estimated effort: 1 day.
3. **API layer design** (resolves A1-A4): Define FastAPI route handlers, pagination, caching. Can begin in parallel with Schema Smith sprint. Estimated effort: 2-3 days.
4. **Frontend development** begins after upstream items resolved.

---

*Generated by UX Advocate subagent. All data contracts are derived from the Schema Smith APPROVED models dated 2026-03-03. Upstream requirements have been identified and assigned. Frontend development should not begin until HIGH-priority blocking items are resolved.*
