# 9. Frontend Architecture

[← Back to Index](index.md) | [← API](08-api.md)

---

## Technology

- **Framework**: Next.js 13+ with App Router (`"use client"` directives)
- **Language**: TypeScript
- **Styling**: Tailwind CSS (slate/blue palette)
- **State**: React hooks (useState, useEffect) — no global state library
- **Data Fetching**: Client-side fetch with 5-minute revalidation cache

---

## Component Dependency Tree

```d2
direction: down

pages: Pages {
  style.fill: "#f3e8ff"
  dashboard: "/dashboard" {style.fill: "#e9d5ff"}
  providers: "/providers" {style.fill: "#e9d5ff"}
  geographic: "/geographic" {style.fill: "#e9d5ff"}
  specialties: "/specialties" {style.fill: "#e9d5ff"}
  opioid: "/opioid" {style.fill: "#e9d5ff"}
  hospitals: "/hospitals" {style.fill: "#e9d5ff"}
  drugs: "/drugs" {style.fill: "#e9d5ff"}
  postacute: "/postacute" {style.fill: "#e9d5ff"}
}

components: "Shared Components" {
  style.fill: "#dcfce7"
  sidebar: Sidebar {style.fill: "#bbf7d0"}
  datatable: "DataTable<T>" {style.fill: "#bbf7d0"}
  kpicard: KpiCard {style.fill: "#bbf7d0"}
  filterbar: FilterBar {style.fill: "#bbf7d0"}
}

pages.dashboard -> components.kpicard
pages.dashboard -> components.datatable
pages.providers -> components.datatable
pages.providers -> components.filterbar
pages.geographic -> components.kpicard
pages.geographic -> components.datatable
pages.hospitals -> components.datatable
pages.hospitals -> components.filterbar
pages.hospitals -> components.kpicard
```

Full diagram: [`diagrams/frontend-pages.d2`](diagrams/frontend-pages.d2)

---

## Page Inventory

Source: `frontend/app/`

| Path | Page Component | API Consumed | Key Features |
|------|---------------|-------------|-------------|
| `/` | `Home` | — | Redirect to `/dashboard` |
| `/dashboard` | `DashboardPage` | `GET /national/kpis` | National KPI cards with YOY trends (payments, drug spending, per-capita, providers, opioid) |
| `/providers` | `ProvidersPage` | `GET /providers/`, `GET /providers/{npi}` | NPI search, name search, state filter, full provider profile with Part B/D data |
| `/geographic` | `GeographicPage` | `GET /geographic/spending`, `GET /geographic/states` | State spending variation, per-capita costs, MA participation, year filter |
| `/specialties` | `SpecialtiesPage` | `GET /specialties/`, `GET /specialties/{s}` | Specialty comparison table with expandable detail view |
| `/opioid` | `OpioidPage` | `GET /opioid/by-state`, `GET /opioid/top-prescribers` | State prescriber rates, claim share, top prescribers dual table |
| `/hospitals` | `HospitalComparisonPage` | `GET /hospitals/financial` | Financial metrics (revenue, margin, occupancy, beds, CMS rating), year/state filters |
| `/drugs` | `DrugSpendingPage` | `GET /drugs/medicaid-utilization`, `GET /drugs/price-trends` | Two-tab: Medicaid utilization by state, ASP pricing by HCPCS with quarterly history |
| `/postacute` | `PostAcutePage` | `GET /postacute/snf`, `GET /postacute/hha`, `GET /postacute/hospice` | SNF/HHA/Hospice quality tabs with ratings, staffing, penalties |

---

## Reusable Components

Source: `frontend/components/`

| Component | File | Props | Behavior |
|-----------|------|-------|----------|
| `Sidebar` | `sidebar.tsx` | — | Navigation with 8 routes, active link highlighting, version badge |
| `DataTable<T>` | `data-table.tsx` | `columns`, `data`, `pageSize?`, `onRowClick?` | Generic sortable table with client-side pagination (25 rows default) |
| `KpiCard` | `kpi-card.tsx` | `label`, `value`, `change?`, `changeLabel?`, `icon?` | Metric card with up/down change indicator (red increase, green decrease) |
| `FilterBar` | `filter-bar.tsx` | `filters`, `values`, `onChange` | Horizontal filter strip with dropdown selects and search inputs |

---

## Utility Modules

Source: `frontend/lib/`

### `api.ts`

API client functions with TypeScript interfaces mirroring API schemas:

- `getNationalKPIs()`, `searchProviders()`, `getProvider()`, `getSpendingVariation()`, `getStates()`
- `getOpioidByState()`, `getTopOpioidPrescribers()`, `getSpecialties()`, `getSpecialtyDetail()`
- Hospital, drug, and post-acute functions

### `format.ts`

Formatting utilities (all return "N/A" for null):

| Function | Output Example |
|----------|---------------|
| `formatCurrency()` | `$1,000` |
| `formatNumber()` | `1,000,000` (locale thousands) |
| `formatPercent()` | `25.5%` |
| `formatCompact()` | `$1.2B` / `$3.5M` |

---

**Next:** [Testing →](10-testing.md)
