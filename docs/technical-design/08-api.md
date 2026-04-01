# 8. API Design

[← Back to Index](index.md) | [← Cross-Source Joins](07-cross-source-joins.md)

---

## Architecture

Source: `api/main.py`

- **Framework**: FastAPI 0.115+
- **Server**: Uvicorn with standard extras
- **CORS**: Allows `http://localhost:3000` and `http://127.0.0.1:3000`
- **Lifecycle**: Lazy connection initialization on first use, graceful shutdown via `close_all()`
- **Versioning**: All routes under `/api/v1/` prefix (except `/health`)

---

## API Route Tree

```d2
direction: right

root: "/api/v1" {
  style.fill: "#f0f9ff"
  style.stroke: "#0284c7"

  health: "/health" {style.fill: "#bbf7d0"}
  providers: "/providers (3)" {style.fill: "#dbeafe"}
  geographic: "/geographic (3)" {style.fill: "#dcfce7"}
  national: "/national (2)" {style.fill: "#dcfce7"}
  opioid: "/opioid (3)" {style.fill: "#fecaca"}
  specialties: "/specialties (2)" {style.fill: "#e0e7ff"}
  catalog: "/catalog (2)" {style.fill: "#fef3c7"}
  hospitals: "/hospitals (5)" {style.fill: "#fed7aa"}
  drugs: "/drugs (3)" {style.fill: "#e9d5ff"}
  postacute: "/postacute (4)" {style.fill: "#ccfbf1"}
}
```

Full diagram: [`diagrams/api-route-tree.d2`](diagrams/api-route-tree.d2)

---

## Dual-Engine Query Routing

Source: `api/services/database.py`

```d2
shape: sequence_diagram

frontend: Frontend
api: FastAPI
router: Router
postgres: PostgreSQL
duckdb: DuckDB

frontend -> api: "GET /providers/1234567890"
api -> router: "engine='pg'"
router -> postgres: "SELECT ... WHERE npi = ?"
postgres -> router: "1 row (<10ms)"
router -> api: "dict"
api -> frontend: "200 OK JSON"

frontend -> api: "GET /geographic/spending?year=2022"
api -> router: "engine='duckdb'"
router -> duckdb: "SELECT ... FROM read_parquet()"
duckdb -> router: "50 rows"
router -> api: "list[dict]"
api -> frontend: "200 OK JSON"
```

Full diagram: [`diagrams/dual-engine-sequence.d2`](diagrams/dual-engine-sequence.d2)

```python
# PostgreSQL — singleton SQLAlchemy engine with connection pooling
get_pg_engine()              # pool_size=5, max_overflow=10, pool_pre_ping=True
query_pg(sql, params)        # → list[dict]
query_pg_df(sql, params)     # → pd.DataFrame

# DuckDB — in-memory, auto-registers Parquet directories as views
get_duckdb_conn()            # Scans data/processed/mart/ for *.parquet
query_duckdb(sql)            # → list[dict]
query_duckdb_df(sql)         # → pd.DataFrame
```

---

## Complete Endpoint Inventory (28 Endpoints)

### Health

| Route | Method | Description | Engine |
|-------|--------|-------------|--------|
| `/health` | GET | Application health with DB connectivity flags | PostgreSQL |

### Providers (`/api/v1/providers`)

| Route | Method | Description | Engine | Response Schema |
|-------|--------|-------------|--------|----------------|
| `/` | GET | Search providers (state, specialty, name, entity_type filters; pagination) | PostgreSQL | `ProviderSearchResponse` |
| `/{npi}` | GET | Single provider by 10-digit NPI | PostgreSQL | `ProviderProfile` |
| `/by-specialty/{specialty}` | GET | Top providers by specialty (optional state filter) | PostgreSQL | `list[ProviderSummary]` |

### Geographic (`/api/v1/geographic`)

| Route | Method | Description | Engine | Response Schema |
|-------|--------|-------------|--------|----------------|
| `/spending` | GET | State spending variation by year (optional region filter) | PostgreSQL | `list[StateSpending]` |
| `/states` | GET | Lightweight state summaries for maps/dropdowns | PostgreSQL | `list[StateSummary]` |
| `/states/{state_fips}` | GET | Single state spending trend across all years | PostgreSQL | `list[StateSpending]` |

### National (`/api/v1/national`)

| Route | Method | Description | Engine | Response Schema |
|-------|--------|-------------|--------|----------------|
| `/kpis` | GET | All years KPI summary, sorted by year desc | PostgreSQL | `list[NationalKPI]` |
| `/kpis/{data_year}` | GET | Single year KPI summary | PostgreSQL | `NationalKPI` |

### Opioid (`/api/v1/opioid`)

| Route | Method | Description | Engine | Response Schema |
|-------|--------|-------------|--------|----------------|
| `/by-state` | GET | State-level opioid metrics by year | PostgreSQL | `list[OpioidByState]` |
| `/top-prescribers` | GET | Top opioid prescribers (year, state, limit filters) | PostgreSQL | `list[OpioidTopPrescriber]` |
| `/by-state/{state_fips}` | GET | Single state opioid trend across all years | PostgreSQL | `list[OpioidByState]` |

### Specialties (`/api/v1/specialties`)

| Route | Method | Description | Engine | Response Schema |
|-------|--------|-------------|--------|----------------|
| `/` | GET | All specialties with aggregate metrics (min_providers filter) | PostgreSQL | `list[SpecialtySummary]` |
| `/{specialty}` | GET | Detailed metrics for a specific specialty | PostgreSQL | `SpecialtyDetail` |

### Catalog (`/api/v1/catalog`)

| Route | Method | Description | Engine | Response Schema |
|-------|--------|-------------|--------|----------------|
| `/sources` | GET | All data sources with publication/load metadata | PostgreSQL | `list[CatalogSource]` |
| `/freshness` | GET | Data freshness status for all sources | PostgreSQL | `list[dict]` |

### Hospitals (`/api/v1/hospitals`)

| Route | Method | Description | Engine | Response Schema |
|-------|--------|-------------|--------|----------------|
| `/financial` | GET | Financial profiles (year, state, limit filters) | PostgreSQL | `list[HospitalFinancialProfile]` |
| `/financial/{ccn}` | GET | Single hospital by CCN and year | PostgreSQL | `HospitalFinancialProfile` |
| `/performance` | GET | Discharge performance with DRG mix (year, state, limit) | PostgreSQL | `list[HospitalPerformance]` |
| `/readmissions` | GET | Readmission data with penalty risk (year, state, penalty_risk_only) | PostgreSQL | `list[HospitalReadmission]` |
| `/charges` | GET | Charge variation by DRG (year, ccn, drg_code, limit) | PostgreSQL | `list[HospitalChargeVariation]` |

### Drugs (`/api/v1/drugs`)

| Route | Method | Description | Engine | Response Schema |
|-------|--------|-------------|--------|----------------|
| `/medicaid-utilization` | GET | State-level Medicaid utilization (year, state filters) | PostgreSQL | `list[MedicaidDrugUtilization]` |
| `/price-trends` | GET | ASP price trends (hcpcs_code, year, limit filters) | PostgreSQL | `list[DrugPriceTrend]` |
| `/price-trends/{hcpcs_code}` | GET | Price trend for single drug across quarters/years | PostgreSQL | `list[DrugPriceTrend]` |

### Post-Acute Care (`/api/v1/postacute`)

| Route | Method | Description | Engine | Response Schema |
|-------|--------|-------------|--------|----------------|
| `/snf` | GET | SNF quality ratings (state, min_rating, limit filters) | PostgreSQL | `list[SNFQuality]` |
| `/snf/{ccn}` | GET | Single SNF details by CCN | PostgreSQL | `SNFQuality` |
| `/hha` | GET | Home Health Agency quality (year, state, limit) | PostgreSQL | `list[HHAQuality]` |
| `/hospice` | GET | Hospice quality (year, state, limit) | PostgreSQL | `list[HospiceQuality]` |

---

## Pydantic Schema Modules

Source: `api/schemas/`

| Module | Models Defined |
|--------|---------------|
| `common.py` | `HealthResponse`, `CatalogSource`, `ErrorResponse`, `PaginationParams` |
| `providers.py` | `ProviderProfile`, `ProviderSummary`, `ProviderSearchResponse` |
| `geographic.py` | `StateSpending`, `StateSummary` |
| `national.py` | `NationalKPI` |
| `opioid.py` | `OpioidByState`, `OpioidTopPrescriber` |
| `hospitals.py` | `HospitalFinancialProfile`, `HospitalPerformance`, `HospitalReadmission`, `HospitalChargeVariation` |
| `drugs.py` | `MedicaidDrugUtilization`, `DrugPriceTrend` |
| `postacute.py` | `SNFQuality`, `HHAQuality`, `HospiceQuality` |
| `specialties.py` | `SpecialtySummary`, `SpecialtyDetail` |

---

**Next:** [Frontend →](09-frontend.md)
