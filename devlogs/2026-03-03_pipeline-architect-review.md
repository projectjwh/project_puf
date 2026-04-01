# Pipeline Architect Review: MVP Tier 1 Data Sources
Date: 2026-03-03
Agent: Pipeline Architect
Status: Initial Lifecycle Review (Wave 1)

> **Scope**: 7-stage lifecycle plans for the 4 MVP Tier 1 data sources (NPPES, Part B Utilization,
> Part D Prescribers, Geographic Variation). Each lifecycle plan is shaped by the source's specific
> characteristics — volume, update frequency, schema complexity, and downstream use cases.
>
> **Tech Stack Reference** (Arch Advisor approved):
> - Orchestration: Prefect 3.x (self-hosted)
> - Validation: Pydantic v2 + Pandera
> - Transformation: dbt-core (deferred to Wave 2; raw SQL via DuckDB for Wave 1)
> - OLTP: PostgreSQL 16+
> - OLAP: DuckDB (embedded)
> - Storage: Local filesystem with S3-like paths
> - File format: Parquet (via PyArrow)
> - API: FastAPI
> - Logging: structlog (JSON)

---

# 1. Data Lifecycle Review: NPPES (National Plan and Provider Enumeration System)
Date: 2026-03-03

## Source Profile

| Attribute | Value |
|-----------|-------|
| Source name | NPPES NPI Registry |
| Publisher | CMS (National Plan and Provider Enumeration System) |
| URL/Endpoint | https://download.cms.gov/nppes/NPI_Files.html (NEEDS VERIFICATION) |
| Format | CSV (single large file, zipped; monthly deactivation files; weekly incremental updates) |
| Update frequency | Monthly full replacement + weekly incremental updates |
| Estimated volume | ~8M rows, ~8-10 GB uncompressed (full file) |
| Schema stability | Stable core fields; up to 330+ columns due to repeating groups (15 taxonomy slots, 50 other identifier slots) |
| Primary key | `NPI` (10-digit National Provider Identifier) |
| Role in MVP | **Provider identity hub** — every NPI-bearing record in Part B, Part D, and other CMS datasets joins here |

## Lifecycle Plan

### 1. Discovery & Cataloging

- **Catalog entry**: Complete — `docs/sources/physician_compare_nppes_pecos.md`
- **Missing metadata**:
  - [ ] Confirm bulk download URL is still active at `download.cms.gov/nppes/NPI_Files.html`
  - [ ] Verify exact file structure (ZIP contains one large CSV + a README/header file)
  - [ ] Confirm whether column names have changed since last documentation
  - [ ] Check if weekly incremental files follow the same schema as the full file
  - [ ] Verify whether NPPES API (NPI Registry API) is still available and its rate limits
- **Action**: Before first pipeline run, execute a manual discovery script that downloads the file listing page via HTTP HEAD requests, captures file sizes and last-modified dates, and stores this metadata in `catalog_sources` table in Postgres.

### 2. Acquisition

- **Method**: HTTP download from `download.cms.gov`
  - Full file: Single large ZIP (~2-3 GB compressed) containing one CSV
  - Deactivation file: Small monthly CSV of deactivated NPIs
  - Weekly incremental: Small CSV of new/updated NPIs
- **Schedule**:
  - Full file monthly: `0 2 8 * *` (8th of every month at 2:00 AM — CMS typically publishes early in the month)
  - Weekly incremental: `0 3 * * 1` (every Monday at 3:00 AM)
  - Deactivation file: downloaded alongside the monthly full file
- **Landing zone**: `data/raw/nppes/{YYYY-MM-DD}/`
  - Full file: `data/raw/nppes/{YYYY-MM-DD}/npi_full.csv.zip`
  - Incremental: `data/raw/nppes/{YYYY-MM-DD}/npi_weekly_increment.csv.zip`
  - Deactivation: `data/raw/nppes/{YYYY-MM-DD}/npi_deactivation.csv.zip`
- **Incremental strategy**:
  - MVP: **Full replacement** each month. The full file IS the current state — NPPES is not versioned.
  - Weekly incremental files are downloaded and stored but NOT processed in MVP. They exist for future use when near-real-time provider data matters.
  - Rationale: Full replacement is simpler, idempotent, and avoids merge complexity. The full file is manageable at ~8-10 GB.
- **Failure handling**:
  - Retry with exponential backoff: 3 retries at 5min, 15min, 45min intervals
  - On 3rd failure: log ERROR, send alert (structured log entry with `severity=CRITICAL`, `pipeline=nppes_acquisition`)
  - Stale data fallback: previous month's data remains active in all downstream tables until new data loads successfully
- **Checksum/hash verification**:
  - CMS does not publish checksums for NPPES files (NEEDS VERIFICATION)
  - Compute SHA-256 of downloaded ZIP and store in `catalog_sources` metadata for change detection
  - On re-download, compare hash — skip processing if unchanged
- **Size validation**:
  - ZIP file expected range: 1.5 GB - 4.0 GB (BLOCK if outside range)
  - Uncompressed CSV expected range: 6.0 GB - 12.0 GB (BLOCK if outside range)
  - Row count expected range: 7,000,000 - 10,000,000 (WARN if outside range)

**Prefect flow sketch**:
```python
@flow(name="nppes-acquisition", retries=3, retry_delay_seconds=[300, 900, 2700])
def acquire_nppes(run_date: date = None):
    run_date = run_date or date.today()
    landing_path = f"data/raw/nppes/{run_date.isoformat()}/"

    url = discover_nppes_url()          # Task: resolve current download URL
    zip_path = download_file(url, landing_path)  # Task: HTTP GET with streaming
    validate_file_size(zip_path, min_gb=1.5, max_gb=4.0)  # Task: BLOCK check
    sha256 = compute_hash(zip_path)     # Task: SHA-256
    is_new = check_hash_changed(sha256, source="nppes")  # Task: compare to last

    if not is_new:
        log.info("nppes_unchanged", sha256=sha256)
        return  # Skip processing — idempotent exit

    csv_path = extract_zip(zip_path, landing_path)  # Task: unzip
    validate_row_count(csv_path, min_rows=7_000_000, max_rows=10_000_000)
    store_acquisition_metadata(source="nppes", run_date=run_date, sha256=sha256, rows=count)
```

### 3. Validation & Quality

**Boundary**: Applied after extraction, before any transformation.

**BLOCK rules** (stop the pipeline):
| Rule | Check | Rationale |
|------|-------|-----------|
| Column count | Exactly matches expected schema (330+ columns) | Schema drift detection — column addition/removal means CMS changed the file |
| `NPI` not null | `NPI` column has zero nulls | NPI is the universal join key; nulls are corrupt data |
| `NPI` format | All values match `^\d{10}$` | Invalid NPIs would cascade to every downstream join |
| `NPI` uniqueness | Zero duplicate NPIs (after filtering to latest record if dupes exist) | NPPES full file should have one row per NPI |
| `Entity_Type_Code` values | All values in {1, 2} | Only Individual (1) and Organization (2) are valid |
| File row count | Within 7M-10M range | Catches truncated downloads or wrong file |

**WARN rules** (alert but continue):
| Rule | Check | Rationale |
|------|-------|-----------|
| `Provider_Enumeration_Date` range | All dates between 2005-01-01 and today | NPI system started in 2005; future dates are suspect |
| `Healthcare_Provider_Taxonomy_Code_1` null rate | < 5% null | Most NPIs should have at least one taxonomy code |
| Address completeness | `Provider_Business_Practice_Location_Address_State_Name` null rate < 2% | Most providers should have a practice state |
| Deactivation rate | < 30% of total NPIs have `NPI_Deactivation_Date` set | Sanity check — system has ~25% deactivated historically |
| Row count delta | Within +/- 5% of previous month's count | Large swings may indicate data issue |

**Baseline**: Established from first successful load. Stored in `catalog_quality` table in Postgres with run_date, source, metric_name, metric_value.

**Pandera schema** (Wave 2 formalization):
```python
class NPPESSchema(pa.DataFrameModel):
    NPI: Series[str] = pa.Field(str_matches=r"^\d{10}$", nullable=False, unique=True)
    Entity_Type_Code: Series[str] = pa.Field(isin=["1", "2"], nullable=False)
    Provider_Enumeration_Date: Series[str] = pa.Field(nullable=True)
    # ... additional fields
```

### 4. Processing & Transformation

- **Transform type**: Python (DuckDB SQL) — Wave 1; dbt models in Wave 2
- **Idempotent**: Yes — full replacement each run. Processing overwrites `processed/nppes/` entirely.
- **Key transformations**:

| Transform | Input | Output | Description |
|-----------|-------|--------|-------------|
| Column pruning | 330+ columns | ~40 core columns | Drop repeating groups beyond taxonomy_1-3 and other_identifier_1-3 for MVP. Full columns kept in raw. |
| Type casting | All strings (CSV) | Typed columns | `NPI` → VARCHAR(10), `Entity_Type_Code` → SMALLINT, dates → DATE, ZIP → VARCHAR(9) |
| Deactivation filter | Full file | Active providers view | Create both `nppes_all` (full) and `nppes_active` (where `NPI_Deactivation_Date` IS NULL) |
| Primary taxonomy extract | 15 taxonomy columns + 15 switch columns | Single `primary_taxonomy_code` | Find the taxonomy slot where `Healthcare_Provider_Primary_Taxonomy_Switch` = 'Y' |
| Address standardization | Raw address fields | Normalized practice address | Trim whitespace, uppercase state abbreviation, extract ZIP5 from ZIP+4 |
| State FIPS derivation | `Provider_Business_Practice_Location_Address_State_Name` | `provider_state_fips` (2-digit) | Lookup table mapping state name → FIPS code (for geographic joins) |
| Snapshot metadata | None | `snapshot_date` column | Add the download date as a column so every row carries its temporal context |

- **Lineage**: `raw/nppes/{date}/npi_full.csv` → `processed/nppes/nppes_all.parquet` + `processed/nppes/nppes_active.parquet`
- **Output**:
  - `data/processed/nppes/nppes_all.parquet` — all NPIs, typed and pruned
  - `data/processed/nppes/nppes_active.parquet` — active NPIs only (deactivation_date IS NULL)
  - Both files are single Parquet files (at ~8M rows, a single file is manageable and simplifies DuckDB queries)

**DuckDB processing sketch**:
```sql
-- Run via DuckDB Python binding
COPY (
    SELECT
        NPI,
        CAST(Entity_Type_Code AS SMALLINT) AS entity_type_code,
        Provider_Organization_Name AS org_name,
        Provider_Last_Name AS last_name,
        Provider_First_Name AS first_name,
        Provider_Credential_Text AS credential,
        Provider_Business_Practice_Location_Address_City_Name AS practice_city,
        Provider_Business_Practice_Location_Address_State_Name AS practice_state,
        LEFT(Provider_Business_Practice_Location_Address_Postal_Code, 5) AS practice_zip5,
        -- Primary taxonomy extraction
        CASE
            WHEN Healthcare_Provider_Primary_Taxonomy_Switch_1 = 'Y' THEN Healthcare_Provider_Taxonomy_Code_1
            WHEN Healthcare_Provider_Primary_Taxonomy_Switch_2 = 'Y' THEN Healthcare_Provider_Taxonomy_Code_2
            WHEN Healthcare_Provider_Primary_Taxonomy_Switch_3 = 'Y' THEN Healthcare_Provider_Taxonomy_Code_3
            ELSE Healthcare_Provider_Taxonomy_Code_1  -- fallback to first
        END AS primary_taxonomy_code,
        Healthcare_Provider_Taxonomy_Code_1 AS taxonomy_code_1,
        Healthcare_Provider_Taxonomy_Code_2 AS taxonomy_code_2,
        Healthcare_Provider_Taxonomy_Code_3 AS taxonomy_code_3,
        TRY_CAST(Provider_Enumeration_Date AS DATE) AS enumeration_date,
        TRY_CAST(Last_Update_Date AS DATE) AS last_update_date,
        TRY_CAST(NPI_Deactivation_Date AS DATE) AS deactivation_date,
        NPI_Deactivation_Reason_Code AS deactivation_reason,
        TRY_CAST(NPI_Reactivation_Date AS DATE) AS reactivation_date,
        Authorized_Official_Last_Name AS auth_official_last_name,
        Authorized_Official_First_Name AS auth_official_first_name,
        '{run_date}' AS snapshot_date
    FROM read_csv_auto('data/raw/nppes/{date}/npi_full.csv',
                        all_varchar=true,
                        header=true,
                        sample_size=10000)
) TO 'data/processed/nppes/nppes_all.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
```

### 5. Storage & Organization

- **Hot tier (PostgreSQL)**:
  - `staging.nppes_current` — current active providers (~6M rows), loaded for API serving and joins
  - Columns: npi, entity_type_code, org_name, last_name, first_name, credential, practice_city, practice_state, practice_zip5, primary_taxonomy_code, enumeration_date, snapshot_date
  - Updated via TRUNCATE + COPY (full replacement, idempotent)
- **Warm tier (Parquet in lake)**:
  - `data/processed/nppes/nppes_all.parquet` — full file, all NPIs
  - `data/processed/nppes/nppes_active.parquet` — active NPIs only
  - Queried directly by DuckDB for analytical workloads
- **Partition keys**: None needed — single file per snapshot. Historical snapshots stored as `data/archive/nppes/{YYYY-MM-DD}/nppes_all.parquet`.
- **Indexes (PostgreSQL)**:
  - `idx_nppes_npi` — PRIMARY KEY on `npi` (B-tree, unique)
  - `idx_nppes_state` — B-tree on `practice_state` (for geographic filtering)
  - `idx_nppes_zip5` — B-tree on `practice_zip5` (for ZIP-based lookups)
  - `idx_nppes_entity_type` — B-tree on `entity_type_code` (for individual vs. org filtering)
  - `idx_nppes_taxonomy` — B-tree on `primary_taxonomy_code` (for specialty filtering)

### 6. Serving & Access

- **API endpoints** (FastAPI):
  | Endpoint | Method | Description | Source |
  |----------|--------|-------------|--------|
  | `/api/v1/providers/{npi}` | GET | Single provider lookup by NPI | PostgreSQL |
  | `/api/v1/providers` | GET | Search providers (paginated, filterable by state, specialty, entity_type) | PostgreSQL |
  | `/api/v1/providers/stats` | GET | Aggregate stats (count by state, by entity type, by specialty) | DuckDB on Parquet |
  | `/api/v1/providers/{npi}/profile` | GET | Full provider profile with Part B + Part D data joined | DuckDB (cross-source) |

- **Pre-aggregations** (computed during processing, stored as Parquet):
  - Provider count by state: `data/mart/nppes/providers_by_state.parquet`
  - Provider count by specialty (top 50 taxonomies): `data/mart/nppes/providers_by_specialty.parquet`
  - Provider count by entity type by state: `data/mart/nppes/providers_by_type_state.parquet`
  - New provider enumeration rate by month (historical trend): `data/mart/nppes/enumeration_trend.parquet`

- **Cache strategy**:
  - MVP: No caching. DuckDB + Parquet is fast enough for single-user queries.
  - Wave 2: Valkey cache for `/api/v1/providers/{npi}` with 24-hour TTL (provider data changes monthly at most).

### 7. Retention & Archival

- **Raw**: Keep all monthly snapshots indefinitely. NPPES is a "current state" file with no historical versions from CMS. Our snapshots ARE the longitudinal record. Path: `data/raw/nppes/{YYYY-MM-DD}/` — each month's download preserved.
- **Processed**: Keep current + last 2 monthly versions in `data/processed/nppes/`. Move older versions to `data/archive/nppes/{YYYY-MM-DD}/`.
- **Archive**: `data/archive/nppes/{YYYY-MM-DD}/nppes_all.parquet` — every historical snapshot. This enables longitudinal provider migration analysis (a key use case from Domain Scholar).
- **Estimated storage**: ~2 GB/month (compressed Parquet) = ~24 GB/year for raw+processed+archive. Acceptable for local filesystem.
- **Cleanup policy**: No deletion. Public data, disk is cheap, and historical snapshots have unique analytical value.

## Gaps Identified

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| CMS download URL unverified | HIGH | Must verify `download.cms.gov/nppes/NPI_Files.html` is still the correct URL before building the acquisition pipeline. Run a manual HTTP request first. |
| No CMS-published checksums | MEDIUM | Implement our own SHA-256 tracking. Accept that we cannot verify file integrity against a CMS reference hash. |
| Weekly incremental processing deferred | LOW | MVP uses monthly full replacement. Weekly increments downloaded but not merged. Acceptable for MVP; provider data is not time-critical at weekly granularity. |
| Taxonomy code normalization not included | MEDIUM | NUCC taxonomy code → human-readable specialty description mapping is needed for the UI. Requires a separate NUCC taxonomy reference table (available from NUCC.org). Add as a separate mini-pipeline. |
| State FIPS derivation requires lookup table | LOW | Need a state name → state FIPS code mapping table. Standard reference data; include in seed data. |
| Physician Compare / PECOS data not in MVP scope | LOW | The Domain Scholar entry covers NPPES + Physician Compare + PECOS. For MVP, only NPPES is ingested. Physician Compare and PECOS are deferred to Tier 2 (adds MIPS scores and group practice affiliations). |

## Verdict: HAS GAPS (1 HIGH — URL verification blocks pipeline development)

---

# 2. Data Lifecycle Review: Medicare Part B Utilization (Physician and Other Practitioners)
Date: 2026-03-03

## Source Profile

| Attribute | Value |
|-----------|-------|
| Source name | Medicare Provider Utilization and Payment Data: Physician and Other Practitioners |
| Publisher | CMS |
| URL/Endpoint | https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/ (NEEDS VERIFICATION) |
| Format | CSV download; also available via CMS Data API (JSON/CSV endpoints) |
| Update frequency | Annual (typically released 18-24 months after the service year) |
| Estimated volume | ~10M rows per year; ~2-4 GB per annual file uncompressed |
| Schema stability | Evolving — column naming changed around 2017-2018 from verbose to abbreviated `Rndrng_Prvdr_*` convention |
| Primary key | `Rndrng_NPI` + `HCPCS_Cd` + `Place_Of_Srvc` (composite) |
| Role in MVP | **Core utilization dataset** — what services each provider bills, how much Medicare pays |

## Lifecycle Plan

### 1. Discovery & Cataloging

- **Catalog entry**: Complete — `docs/sources/medicare_provider_utilization_partb.md`
- **Missing metadata**:
  - [ ] Confirm current URL — CMS has migrated data portals multiple times (restructured ~2022-2023)
  - [ ] Verify most recent data year available (likely 2022 or 2023 as of early 2026)
  - [ ] Check whether column naming convention has changed again post-2022
  - [ ] Confirm whether CMS Data API endpoints are still active and their rate limits
  - [ ] Check if CMS has added new fields (e.g., MIPS score linkage, telehealth indicators)
  - [ ] Verify file size for most recent data year
  - [ ] Confirm suppression threshold is still 11 beneficiaries
- **Action**: Download the data dictionary / methodology PDF from CMS (usually published alongside the data). Parse column definitions and store in `catalog_columns` table.

### 2. Acquisition

- **Method**: HTTP download from `data.cms.gov`
  - Each annual file is a separate download (2013, 2014, ..., latest year)
  - MVP scope: Start with most recent 3 years (e.g., 2020, 2021, 2022) to enable year-over-year trending while keeping volume manageable
  - CMS Data API is available but has rate limits and pagination; direct CSV download is preferred for bulk acquisition
- **Schedule**:
  - Initial load: One-time download of 3 years: `manual trigger` via Prefect
  - Annual refresh: `0 2 15 6 *` (June 15 at 2:00 AM — CMS typically releases new annual data in spring/summer; check and adjust)
  - Monitoring: `0 6 1 3,4,5,6,7 *` (1st of March through July at 6:00 AM — check CMS for new data release announcements)
- **Landing zone**: `data/raw/partb/{YYYY}/` (organized by data year, not download date)
  - Example: `data/raw/partb/2022/medicare_physician_other_practitioners_2022.csv`
- **Incremental strategy**: **Full replacement per year.** Each annual file is complete for that year. No incremental updates within a year. New years are additive.
- **Failure handling**:
  - Retry with exponential backoff: 3 retries at 5min, 15min, 45min
  - On 3rd failure: log ERROR, alert. Annual data is not time-critical — retry manually.
  - CMS Data API fallback: if direct download fails, try the API endpoint (slower but more reliable)
- **Checksum/hash verification**:
  - Compute SHA-256 of downloaded file
  - CMS does not publish checksums (NEEDS VERIFICATION)
  - Store hash in metadata to detect re-releases (CMS occasionally re-publishes corrected files)
- **Size validation**:
  - Per-year CSV expected range: 1.0 GB - 5.0 GB (BLOCK if outside)
  - Row count expected range: 8,000,000 - 13,000,000 per year (WARN if outside)

**Prefect flow sketch**:
```python
@flow(name="partb-acquisition")
def acquire_partb(data_years: list[int] = None):
    data_years = data_years or [2020, 2021, 2022]  # MVP default

    for year in data_years:
        landing_path = f"data/raw/partb/{year}/"
        url = discover_partb_url(year)       # Task: resolve download URL for year
        csv_path = download_file(url, landing_path)
        validate_file_size(csv_path, min_gb=1.0, max_gb=5.0)
        sha256 = compute_hash(csv_path)
        is_new = check_hash_changed(sha256, source=f"partb_{year}")

        if is_new:
            validate_and_process_partb(csv_path, year)  # Subflow
        else:
            log.info("partb_unchanged", year=year)
```

### 3. Validation & Quality

**Boundary**: Applied after download, before transformation.

**BLOCK rules**:
| Rule | Check | Rationale |
|------|-------|-----------|
| Required columns present | `Rndrng_NPI`, `HCPCS_Cd`, `Place_Of_Srvc`, `Tot_Benes`, `Tot_Srvcs`, `Avg_Mdcr_Pymt_Amt`, `Avg_Mdcr_Stdzd_Amt` all present | Core columns needed for all analyses |
| `Rndrng_NPI` format | All non-null values match `^\d{10}$` | NPI join integrity |
| `HCPCS_Cd` format | All non-null values match `^[A-Z0-9]{5}$` | HCPCS code validity |
| `Place_Of_Srvc` values | All values in {'F', 'O'} (Facility, Office/Non-Facility) | Composite key integrity |
| Composite key uniqueness | Zero duplicate (NPI, HCPCS, Place_Of_Srvc) combinations | Grain integrity — one row per provider-service-place |
| Row count | Within 8M-13M range | Catches truncated or wrong file |
| No all-null rows | Zero rows where all measure columns are null | Corrupt data detection |

**WARN rules**:
| Rule | Check | Rationale |
|------|-------|-----------|
| `Tot_Benes` range | All values >= 11 (suppression threshold) | CMS suppresses below 11; values below indicate data issue |
| `Avg_Mdcr_Pymt_Amt` non-negative | All values >= 0 | Negative payments are unusual (may be valid for adjustments but warrant review) |
| `Avg_Mdcr_Stdzd_Amt` non-negative | All values >= 0 | Same as above |
| NPI referential integrity | > 95% of `Rndrng_NPI` values exist in NPPES | Some providers may not be in NPPES (deactivated, etc.) but rate should be high |
| Year-over-year row count delta | Within +/- 10% of previous year | Large swings may indicate methodology change |
| `Rndrng_Prvdr_State_FIPS` completeness | < 1% null | Needed for geographic joins |
| Provider type distribution | Top 10 specialties account for > 40% of rows | Sanity check on data composition |

**Baseline**: Established from the first year loaded. Year-over-year comparisons track drift.

### 4. Processing & Transformation

- **Transform type**: Python (DuckDB SQL) — Wave 1; dbt models in Wave 2
- **Idempotent**: Yes — processing a year overwrites that year's output files completely.
- **Key transformations**:

| Transform | Input | Output | Description |
|-----------|-------|--------|-------------|
| Schema normalization | Year-specific column names | Standardized column names | Map older verbose names to current `Rndrng_Prvdr_*` convention. Maintain a schema registry mapping per year. |
| Type casting | All strings (CSV) | Typed columns | NPI → VARCHAR(10), HCPCS → VARCHAR(5), measures → DOUBLE, counts → INTEGER, FIPS → VARCHAR(2) |
| Suppressed value handling | CMS suppression markers | NULLs with suppression flag | CMS uses various markers for suppressed cells. Standardize to NULL + boolean `is_suppressed` column. |
| Computed columns | Raw measures | Derived analytics | `total_medicare_payment = Tot_Srvcs * Avg_Mdcr_Pymt_Amt` (estimated total, since CMS provides only averages) |
| HCPCS drug indicator | `HCPCS_Drug_Ind` | Boolean `is_drug_service` | Clean Y/N to boolean for easy filtering of Part B drugs vs. procedures |
| Entity type normalization | `Rndrng_Prvdr_Ent_Cd` | Standardized entity type | 'I' → 'Individual', 'O' → 'Organization' |
| Year column | None | `data_year` INTEGER | Add explicit year column for multi-year queries |

- **Lineage**: `raw/partb/{year}/*.csv` → `processed/partb/{year}/partb_utilization.parquet`
- **Output**:
  - `data/processed/partb/{year}/partb_utilization.parquet` — one Parquet file per data year
  - Parquet files use ZSTD compression, ~500MB-1GB each (significant compression from CSV)

**DuckDB processing sketch**:
```sql
COPY (
    SELECT
        Rndrng_NPI AS rendering_npi,
        Rndrng_Prvdr_Last_Org_Name AS provider_last_org_name,
        Rndrng_Prvdr_First_Name AS provider_first_name,
        Rndrng_Prvdr_Crdntls AS provider_credentials,
        Rndrng_Prvdr_Gndr AS provider_gender,
        Rndrng_Prvdr_Ent_Cd AS entity_code,
        Rndrng_Prvdr_St1 AS provider_street1,
        Rndrng_Prvdr_City AS provider_city,
        Rndrng_Prvdr_State_Abrvtn AS provider_state,
        Rndrng_Prvdr_State_FIPS AS provider_state_fips,
        Rndrng_Prvdr_Zip5 AS provider_zip5,
        Rndrng_Prvdr_RUCA AS provider_ruca,
        Rndrng_Prvdr_Type AS provider_type,
        HCPCS_Cd AS hcpcs_code,
        HCPCS_Desc AS hcpcs_description,
        CASE WHEN HCPCS_Drug_Ind = 'Y' THEN TRUE ELSE FALSE END AS is_drug_service,
        Place_Of_Srvc AS place_of_service,
        TRY_CAST(Tot_Benes AS INTEGER) AS total_beneficiaries,
        TRY_CAST(Tot_Srvcs AS INTEGER) AS total_services,
        TRY_CAST(Tot_Bene_Day_Srvcs AS INTEGER) AS total_bene_day_services,
        TRY_CAST(Avg_Sbmtd_Chrg AS DOUBLE) AS avg_submitted_charge,
        TRY_CAST(Avg_Mdcr_Alowd_Amt AS DOUBLE) AS avg_medicare_allowed_amt,
        TRY_CAST(Avg_Mdcr_Pymt_Amt AS DOUBLE) AS avg_medicare_payment_amt,
        TRY_CAST(Avg_Mdcr_Stdzd_Amt AS DOUBLE) AS avg_medicare_standardized_amt,
        -- Derived: estimated total payment
        TRY_CAST(Tot_Srvcs AS DOUBLE) * TRY_CAST(Avg_Mdcr_Pymt_Amt AS DOUBLE) AS est_total_medicare_payment,
        {year} AS data_year
    FROM read_csv_auto('data/raw/partb/{year}/*.csv',
                        all_varchar=true,
                        header=true)
    WHERE Rndrng_NPI IS NOT NULL
) TO 'data/processed/partb/{year}/partb_utilization.parquet'
  (FORMAT PARQUET, COMPRESSION ZSTD);
```

### 5. Storage & Organization

- **Hot tier (PostgreSQL)**:
  - `staging.partb_utilization` — most recent year only, for API serving (~10M rows)
  - Consider: only load a provider-level summary into Postgres (aggregate across HCPCS codes) to reduce row count if full detail is too large for Postgres
  - Alternative: `mart.partb_provider_summary` — one row per NPI per year with aggregate measures (total services, total payment, distinct HCPCS count, top specialty)
- **Warm tier (Parquet in lake)**:
  - `data/processed/partb/{year}/partb_utilization.parquet` — full detail, one file per year
  - DuckDB queries across all years: `SELECT * FROM read_parquet('data/processed/partb/*/partb_utilization.parquet')`
- **Partition keys**: Year (directory-level partitioning). State-level partitioning deferred — not needed until query performance requires it.
- **Indexes (PostgreSQL, on provider summary table)**:
  - `idx_partb_npi` — B-tree on `rendering_npi` (for provider lookups)
  - `idx_partb_state` — B-tree on `provider_state_fips` (for geographic filtering)
  - `idx_partb_hcpcs` — B-tree on `hcpcs_code` (for service-level queries)
  - `idx_partb_year` — B-tree on `data_year` (for temporal queries)
  - `idx_partb_npi_year` — composite (rendering_npi, data_year) for provider time-series

### 6. Serving & Access

- **API endpoints** (FastAPI):
  | Endpoint | Method | Description | Source |
  |----------|--------|-------------|--------|
  | `/api/v1/utilization/partb/provider/{npi}` | GET | All services billed by a provider (paginated, filterable by year) | DuckDB on Parquet |
  | `/api/v1/utilization/partb/provider/{npi}/summary` | GET | Provider-level aggregates (total payment, services, beneficiaries by year) | PostgreSQL or DuckDB |
  | `/api/v1/utilization/partb/service/{hcpcs_code}` | GET | All providers billing a specific service (paginated) | DuckDB on Parquet |
  | `/api/v1/utilization/partb/stats` | GET | Aggregate statistics (by state, by specialty, by year) | DuckDB pre-aggregations |
  | `/api/v1/utilization/partb/top-providers` | GET | Top providers by total payment (filterable by state, specialty, year) | DuckDB |

- **Pre-aggregations** (computed during processing):
  - Provider summary by year: `data/mart/partb/provider_summary_{year}.parquet` — one row per NPI per year (total services, total payment, beneficiary count, distinct HCPCS count, primary specialty)
  - Service summary by year: `data/mart/partb/service_summary_{year}.parquet` — one row per HCPCS code per year (provider count, total services, total payment)
  - State summary by year: `data/mart/partb/state_summary_{year}.parquet` — one row per state per year (provider count, total services, total payment, per capita standardized payment)
  - Specialty summary by year: `data/mart/partb/specialty_summary_{year}.parquet` — one row per provider type per year

- **Cache strategy**:
  - MVP: No caching. Pre-aggregated Parquet files serve as the "cache."
  - Wave 2: Valkey cache for provider summary endpoints (24-hour TTL). Pre-aggregation files served directly.

### 7. Retention & Archival

- **Raw**: Keep all annual files indefinitely. Annual releases are immutable per year (CMS rarely re-releases). Path: `data/raw/partb/{year}/`
- **Processed**: Keep all years. Annual data does not become stale — each year is a permanent historical record. Path: `data/processed/partb/{year}/`
- **Mart**: Regenerated on each processing run. Keep current version only; previous versions are reproducible from processed data.
- **Archive**: Raw files serve as the archive. No separate archive tier needed for annual data.
- **Estimated storage**: ~1 GB/year (compressed Parquet) processed + ~2-4 GB/year raw CSV. 3 years = ~15 GB total. Manageable.

## Gaps Identified

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| CMS data URL unverified | HIGH | Must verify current download URL before building pipeline. CMS portal has been restructured multiple times. |
| Schema version registry needed | HIGH | Column naming changed around 2017-2018. Before loading multiple years, build a column mapping registry that maps each year's column names to canonical names. This blocks multi-year processing. |
| Most recent data year unknown | MEDIUM | Need to verify whether 2022 or 2023 data is available. Determines MVP year range. |
| HCPCS reference table not in scope | MEDIUM | `HCPCS_Desc` from CMS is a truncated description. A full HCPCS reference table (code, short desc, long desc, category, RVU) is needed for rich UI. Add as a separate reference data pipeline. |
| Suppression marker handling undefined | MEDIUM | CMS uses various markers for suppressed cells (sometimes blank, sometimes special characters). Need to document the exact suppression markers per year by inspecting actual data files. |
| PostgreSQL row volume concern | LOW | 10M rows per year in Postgres is feasible but not trivial. May need to serve provider-level summaries from Postgres and full detail from DuckDB only. Monitor query performance. |

## Verdict: HAS GAPS (2 HIGH — URL verification and schema version registry block multi-year pipeline)

---

# 3. Data Lifecycle Review: Medicare Part D Prescribers (by Provider and Drug)
Date: 2026-03-03

## Source Profile

| Attribute | Value |
|-----------|-------|
| Source name | Medicare Part D Prescribers — by Provider and Drug |
| Publisher | CMS |
| URL/Endpoint | https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/ (NEEDS VERIFICATION) |
| Format | CSV download; also available via CMS Data API |
| Update frequency | Annual (typically released 18-24 months after the service year) |
| Estimated volume | ~25M rows per year; ~4-6 GB per annual file uncompressed |
| Schema stability | Evolving — opioid flags added ~2017, column naming may vary between years |
| Primary key | `Prscrbr_NPI` + `Brnd_Name` + `Gnrc_Name` (composite) |
| Role in MVP | **Prescribing patterns** — what drugs each provider prescribes, at what volume and cost |

## Lifecycle Plan

### 1. Discovery & Cataloging

- **Catalog entry**: Complete — `docs/sources/medicare_partd_prescribers.md`
- **Missing metadata**:
  - [ ] Confirm current URL on data.cms.gov
  - [ ] Verify most recent data year available (likely 2022 or 2023)
  - [ ] Check whether MA-PD claims are now included
  - [ ] Confirm whether new drug classification flags have been added
  - [ ] Verify suppression thresholds remain unchanged (11 claims / 11 beneficiaries)
  - [ ] Check actual file size for most recent year
- **Special note**: This is the largest MVP dataset by row count (~25M/year). Processing approach must account for this — DuckDB handles it well but Postgres may struggle with full detail.

### 2. Acquisition

- **Method**: HTTP download from `data.cms.gov`
  - Each annual file is a separate download
  - MVP scope: Most recent 3 years (matching Part B scope for consistent provider profiling)
  - CMS Data API available as fallback
- **Schedule**:
  - Initial load: One-time download of 3 years: `manual trigger`
  - Annual refresh: `0 2 20 6 *` (June 20 at 2:00 AM — slightly offset from Part B to avoid simultaneous large downloads)
  - Monitoring: Same as Part B — `0 6 1 3,4,5,6,7 *`
- **Landing zone**: `data/raw/partd/{YYYY}/`
  - Example: `data/raw/partd/2022/medicare_partd_prescribers_2022.csv`
- **Incremental strategy**: **Full replacement per year.** Same as Part B — annual files are complete and immutable.
- **Failure handling**: Same pattern as Part B (3 retries with exponential backoff).
- **Checksum/hash verification**: SHA-256 stored per file per year.
- **Size validation**:
  - Per-year CSV expected range: 2.0 GB - 8.0 GB (BLOCK if outside)
  - Row count expected range: 20,000,000 - 30,000,000 per year (WARN if outside)

**Prefect flow sketch**: Identical pattern to Part B, parameterized for Part D source.

### 3. Validation & Quality

**BLOCK rules**:
| Rule | Check | Rationale |
|------|-------|-----------|
| Required columns present | `Prscrbr_NPI`, `Brnd_Name`, `Gnrc_Name`, `Tot_Clms`, `Tot_Drug_Cst`, `Tot_Benes` all present | Core columns for all analyses |
| `Prscrbr_NPI` format | All non-null values match `^\d{10}$` | NPI join integrity |
| Composite key uniqueness | Zero duplicate (NPI, Brnd_Name, Gnrc_Name) combinations | Grain integrity |
| Row count | Within 20M-30M range | Catches truncated or wrong file |
| `Tot_Clms` non-negative | All values >= 0 | Negative claims are invalid |
| `Tot_Drug_Cst` non-negative | All values >= 0 | Negative costs are invalid |

**WARN rules**:
| Rule | Check | Rationale |
|------|-------|-----------|
| `Tot_Benes` minimum | All values >= 11 (suppression threshold) | CMS suppresses below 11; below indicates data issue |
| `Tot_Clms` minimum | All values >= 11 (suppression threshold) | Same as above |
| NPI referential integrity | > 95% of `Prscrbr_NPI` values exist in NPPES | Cross-source join quality |
| Opioid flag completeness | `Opioid_Drug_Flag` not null for > 90% of rows (if year >= 2017) | Expected field after CMS added opioid tracking |
| Drug name normalization check | < 100 distinct `Gnrc_Name` values with only whitespace/case differences | Drug name messiness indicator |
| Year-over-year row count delta | Within +/- 15% | Larger tolerance than Part B due to drug market changes |

### 4. Processing & Transformation

- **Transform type**: Python (DuckDB SQL) — Wave 1
- **Idempotent**: Yes — processing a year overwrites that year's output completely.
- **Key transformations**:

| Transform | Input | Output | Description |
|-----------|-------|--------|-------------|
| Schema normalization | Year-specific columns | Canonical names | Map older column names to current convention |
| Type casting | All strings | Typed columns | NPI → VARCHAR(10), costs → DOUBLE, counts → INTEGER, flags → BOOLEAN |
| Drug name normalization | `Brnd_Name`, `Gnrc_Name` | Cleaned, uppercased, trimmed names | `UPPER(TRIM(Gnrc_Name))`, collapse common variants |
| Opioid flag standardization | `Opioid_Drug_Flag`, `Opioid_LA_Drug_Flag` | Boolean columns | 'Y'/'N'/NULL → TRUE/FALSE/NULL |
| Antibiotic flag | `Antbtc_Drug_Flag` | Boolean | Same treatment |
| Cost-per-claim derivation | `Tot_Drug_Cst` / `Tot_Clms` | `avg_cost_per_claim` | Derived metric for drug pricing analysis |
| Cost-per-day derivation | `Tot_Drug_Cst` / `Tot_Day_Suply` | `avg_cost_per_day` | Derived metric for cost comparisons across drugs |
| 30-day fill normalization | `Tot_30day_Fills` | Already normalized | Use as-is; more comparable than raw claim counts across maintenance vs. acute drugs |
| Year column | None | `data_year` INTEGER | Explicit year for multi-year queries |

- **Lineage**: `raw/partd/{year}/*.csv` → `processed/partd/{year}/partd_prescribers.parquet`
- **Output**:
  - `data/processed/partd/{year}/partd_prescribers.parquet` — one Parquet file per data year (~1-2 GB compressed)

**Processing note**: At ~25M rows per year, this file is large but well within DuckDB's single-machine capability. DuckDB's streaming CSV reader handles this without requiring the full file in memory.

### 5. Storage & Organization

- **Hot tier (PostgreSQL)**:
  - Full detail (25M rows/year) is too large for Postgres as a serving layer.
  - Instead: `mart.partd_provider_summary` — one row per NPI per year with aggregate prescribing metrics (total claims, total cost, total drugs, opioid claim rate, top drug by cost)
  - `mart.partd_drug_summary` — one row per generic drug name per year (total claims, total cost, prescriber count, beneficiary count)
- **Warm tier (Parquet)**:
  - `data/processed/partd/{year}/partd_prescribers.parquet` — full provider-drug detail
  - DuckDB serves all detail-level queries directly from Parquet
- **Partition keys**: Year (directory-level). Drug-level partitioning not needed at this scale.
- **Indexes (PostgreSQL, on summary tables)**:
  - `idx_partd_prov_npi` — B-tree on `prescriber_npi` (provider lookup)
  - `idx_partd_prov_state` — B-tree on `prescriber_state_fips` (geographic filtering)
  - `idx_partd_prov_year` — B-tree on `data_year` (temporal queries)
  - `idx_partd_drug_name` — B-tree on `generic_name` (drug lookup)
  - `idx_partd_drug_year` — composite (generic_name, data_year) (drug trends)

### 6. Serving & Access

- **API endpoints** (FastAPI):
  | Endpoint | Method | Description | Source |
  |----------|--------|-------------|--------|
  | `/api/v1/prescribing/provider/{npi}` | GET | All drugs prescribed by a provider (paginated, filterable by year) | DuckDB on Parquet |
  | `/api/v1/prescribing/provider/{npi}/summary` | GET | Provider prescribing summary (total claims, cost, opioid rate by year) | PostgreSQL |
  | `/api/v1/prescribing/drug/{generic_name}` | GET | All providers prescribing a specific drug (paginated) | DuckDB on Parquet |
  | `/api/v1/prescribing/drug/{generic_name}/summary` | GET | Drug-level aggregate stats (prescriber count, total cost by year) | PostgreSQL |
  | `/api/v1/prescribing/stats` | GET | Aggregate statistics (by state, by specialty, by drug category) | DuckDB pre-aggregations |
  | `/api/v1/prescribing/opioids` | GET | Opioid prescribing dashboard data (top prescribers, trends, geographic view) | DuckDB |

- **Pre-aggregations**:
  - Provider prescribing summary: `data/mart/partd/provider_summary_{year}.parquet`
  - Drug summary: `data/mart/partd/drug_summary_{year}.parquet`
  - State prescribing summary: `data/mart/partd/state_summary_{year}.parquet`
  - Opioid prescribing by state: `data/mart/partd/opioid_by_state_{year}.parquet`
  - Top 100 drugs by total cost: `data/mart/partd/top_drugs_{year}.parquet`

- **Cache strategy**: MVP: No caching. Pre-aggregations serve as cache. Wave 2: Valkey for provider and drug summary endpoints.

### 7. Retention & Archival

- **Raw**: Keep all annual files indefinitely. Path: `data/raw/partd/{year}/`
- **Processed**: Keep all years. Same rationale as Part B — each year is a permanent record.
- **Mart**: Regenerated from processed data. Keep current version only.
- **Estimated storage**: ~2 GB/year (compressed Parquet) processed + ~4-6 GB/year raw CSV. 3 years = ~24 GB total.

## Gaps Identified

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| CMS data URL unverified | HIGH | Same as Part B — must verify before pipeline development. |
| Drug name normalization strategy undefined | HIGH | `Brnd_Name` and `Gnrc_Name` are free-text. The same molecule appears under different brand names and spelling variants. A drug name normalization table is critical for accurate drug-level aggregation. Build a canonical drug name mapping as part of the processing pipeline. Consider linking to RxNorm or FDA NDC directory as a reference. |
| Schema version registry needed | MEDIUM | Same concern as Part B — opioid fields added ~2017, earlier years may have different columns. |
| No NDC codes available | MEDIUM | The dataset uses brand/generic names, not NDC codes. This limits precise drug identification. Mitigation: build a `Gnrc_Name` → drug class mapping for high-level categorization (e.g., statins, opioids, antihypertensives). |
| PostgreSQL row volume limitation | LOW | 25M rows/year exceeds practical Postgres serving capacity for detail queries. Design confirms DuckDB serves detail; Postgres serves summaries only. |

## Verdict: HAS GAPS (2 HIGH — URL verification and drug name normalization block reliable analytics)

---

# 4. Data Lifecycle Review: Medicare Geographic Variation (by National, State, and County)
Date: 2026-03-03

## Source Profile

| Attribute | Value |
|-----------|-------|
| Source name | Medicare Geographic Variation — by National, State, and County |
| Publisher | CMS |
| URL/Endpoint | https://data.cms.gov/summary-statistics-on-beneficiary-use-of-health-services/medicare-geographic-variation/ (NEEDS VERIFICATION) |
| Format | CSV download; CMS Data API |
| Update frequency | Annual (typically released 18-24 months after the data year) |
| Estimated volume | ~3,250 rows per year (county-level); trivially small |
| Schema stability | Stable — measures have been consistent across years |
| Primary key | `BENE_GEO_LVL` + `State_FIPS` + `County_FIPS` (composite) |
| Role in MVP | **Population-level benchmarks** — provides denominator and context for all provider-level analysis |

## Lifecycle Plan

### 1. Discovery & Cataloging

- **Catalog entry**: Complete — `docs/sources/medicare_geographic_variation.md`
- **Missing metadata**:
  - [ ] Confirm current URL on data.cms.gov
  - [ ] Verify most recent data year available
  - [ ] Check whether CMS has added sub-county geography (ZIP, ZCTA, HRR/HSA)
  - [ ] Verify whether MA encounter data is now incorporated into utilization measures
  - [ ] Check for new measures (social determinants, telehealth utilization, COVID impact)
  - [ ] Confirm whether County FIPS is 5-digit (state+county) or separate fields
  - [ ] Verify HCC risk score version used (V22, V24, V28)
- **Note**: This is by far the simplest source in the MVP — tiny file, stable schema, high value. Pipeline should be proportionally simple.

### 2. Acquisition

- **Method**: HTTP download from `data.cms.gov`
  - CMS may publish national, state, and county as separate files or a single file with a geography level indicator. Need to verify structure.
  - MVP scope: All available years (2007-latest) — the dataset is so small that loading all years is trivial
- **Schedule**:
  - Initial load: One-time download of all available years: `manual trigger`
  - Annual refresh: `0 2 1 7 *` (July 1 at 2:00 AM — offset from Part B and Part D)
  - Monitoring: `0 6 1 3,4,5,6,7 *` (same as other annual sources)
- **Landing zone**: `data/raw/geovar/{YYYY}/`
  - Example: `data/raw/geovar/2022/medicare_geographic_variation_2022.csv`
  - If separate files per geography level: `data/raw/geovar/2022/{national,state,county}.csv`
- **Incremental strategy**: **Full replacement per year.** Annual data, immutable once released.
- **Failure handling**: Same pattern (3 retries). This is a tiny download — failures are unlikely.
- **Checksum/hash verification**: SHA-256 stored per file.
- **Size validation**:
  - Per-year CSV expected range: 100 KB - 50 MB (BLOCK if outside — these are tiny files)
  - Row count expected range: 3,000 - 5,000 per year for county-level (WARN if outside)

**Prefect flow sketch**: Same pattern as Part B/Part D but simpler. No need for streaming or chunking — entire file fits easily in memory.

### 3. Validation & Quality

**BLOCK rules**:
| Rule | Check | Rationale |
|------|-------|-----------|
| Required columns present | `BENE_GEO_LVL`, `State_FIPS` or `State`, spending columns (`Tot_Mdcr_Stdzd_Pymt_PC`, `Tot_Mdcr_Pymt_PC`) | Core structure |
| `BENE_GEO_LVL` values | All values in {'National', 'State', 'County'} (or numeric equivalents) | Geography level integrity |
| State count | 50-56 state-level rows (50 states + DC + territories) | All states represented |
| County count | 3,000 - 3,500 county-level rows | Reasonable county count for the US |
| National row | Exactly 1 national-level row | Benchmark row present |
| Spending columns non-negative | All per-capita spending measures >= 0 | Valid spending values |

**WARN rules**:
| Rule | Check | Rationale |
|------|-------|-----------|
| `Benes_FFS_Cnt` reasonable | State-level values between 1,000 and 5,000,000 | Plausible beneficiary counts |
| `Benes_Avg_HCC_Scr` range | All values between 0.5 and 3.0 | Plausible HCC risk score range |
| Per-capita spending range | `Tot_Mdcr_Stdzd_Pymt_PC` between $2,000 and $25,000 | Plausible per-capita spending |
| FFS vs MA count check | `Benes_FFS_Cnt` + `Benes_MA_Cnt` > 0 for all rows | Non-empty geographic areas |
| County FIPS format | All county FIPS match `^\d{5}$` | Valid FIPS code format |
| Year-over-year measure stability | Key national measures within +/- 10% of previous year | Catches methodology changes |

### 4. Processing & Transformation

- **Transform type**: Python (DuckDB SQL) — straightforward for this small dataset
- **Idempotent**: Yes — processing a year overwrites that year's output.
- **Key transformations**:

| Transform | Input | Output | Description |
|-----------|-------|--------|-------------|
| Type casting | All strings | Typed columns | FIPS → VARCHAR(5), counts → INTEGER, spending → DOUBLE, rates → DOUBLE |
| Geography level normalization | `BENE_GEO_LVL` | Standardized string | Ensure consistent 'National'/'State'/'County' values across years |
| FIPS code padding | `State_FIPS`, `County_FIPS` | Zero-padded strings | Ensure '1' becomes '01' for Alabama, '01001' for Autauga County |
| State name addition | State FIPS | `state_name`, `state_abbrev` | Lookup table join for human-readable state names |
| MA penetration rate | `Benes_MA_Cnt`, `Benes_FFS_Cnt` | `ma_penetration_rate` | `Benes_MA_Cnt / (Benes_MA_Cnt + Benes_FFS_Cnt)` — critical context variable |
| Dual-eligible rate | `Benes_Dual_Cnt`, total benes | `dual_eligible_rate` | Percentage of dual-eligible beneficiaries per area |
| Year column | None | `data_year` | Explicit year for multi-year queries |
| Per-capita spending spread | Service-specific spending cols | Individual columns retained + total | Keep all `*_Mdcr_Pymt_PC` and `*_Mdcr_Stdzd_Pymt_PC` columns |

- **Lineage**: `raw/geovar/{year}/*.csv` → `processed/geovar/{year}/geovar.parquet`
- **Output**:
  - `data/processed/geovar/{year}/geovar.parquet` — one tiny Parquet file per year
  - Multi-year combined: `data/processed/geovar/geovar_all_years.parquet` — all years in a single file for time-series analysis (still very small, < 100 MB total)

### 5. Storage & Organization

- **Hot tier (PostgreSQL)**:
  - `mart.geographic_variation` — ALL years, ALL geography levels (~50,000 rows total across all years). Fits trivially in Postgres.
  - This is a "load everything" table — no need for summary/detail split.
- **Warm tier (Parquet)**:
  - `data/processed/geovar/geovar_all_years.parquet` — all years combined for DuckDB analytical queries
  - Individual year files retained for lineage tracking
- **Partition keys**: None needed — entire dataset fits in a single file.
- **Indexes (PostgreSQL)**:
  - `idx_geovar_pk` — PRIMARY KEY on (data_year, bene_geo_lvl, state_fips, county_fips)
  - `idx_geovar_state` — B-tree on `state_fips` (for state-level queries)
  - `idx_geovar_county` — B-tree on `county_fips` (for county-level queries)
  - `idx_geovar_year` — B-tree on `data_year` (for temporal queries)
  - `idx_geovar_geo_level` — B-tree on `bene_geo_lvl` (for filtering national/state/county)

### 6. Serving & Access

- **API endpoints** (FastAPI):
  | Endpoint | Method | Description | Source |
  |----------|--------|-------------|--------|
  | `/api/v1/geography/national` | GET | National-level benchmarks (filterable by year) | PostgreSQL |
  | `/api/v1/geography/states` | GET | All state-level data (filterable by year, sortable by any measure) | PostgreSQL |
  | `/api/v1/geography/state/{state_fips}` | GET | Single state detail with time-series across years | PostgreSQL |
  | `/api/v1/geography/counties` | GET | County-level data (filterable by state, year, sortable) | PostgreSQL |
  | `/api/v1/geography/county/{county_fips}` | GET | Single county detail with time-series | PostgreSQL |
  | `/api/v1/geography/compare` | GET | Compare multiple geographies side-by-side | PostgreSQL |
  | `/api/v1/geography/rankings` | GET | Rank states/counties by any spending or utilization measure | PostgreSQL |

- **Pre-aggregations**: Not needed — the data IS already aggregated. Geographic variation is inherently a summary dataset. All queries serve directly from the Postgres table or Parquet file.

- **Cache strategy**: MVP: No caching needed. The entire dataset fits in memory. DuckDB and Postgres both serve sub-second responses on this volume.

### 7. Retention & Archival

- **Raw**: Keep all years indefinitely. Path: `data/raw/geovar/{year}/`
- **Processed**: Keep all years and the combined multi-year file. Zero reason to delete — total storage is < 100 MB for all years combined.
- **Archive**: None needed. Everything stays active.
- **Estimated storage**: < 100 MB total across all years, all tiers. Trivial.

## Gaps Identified

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| CMS data URL unverified | HIGH | Must verify before pipeline development. Same as other sources. |
| County FIPS format uncertain | MEDIUM | Need to verify whether CMS uses 5-digit combined FIPS (state+county) or separate state FIPS + county FIPS fields. This affects join logic to Part B and Part D provider ZIP-to-county crosswalks. |
| ZIP-to-County crosswalk not in scope | MEDIUM | Provider-level data (Part B, Part D) uses ZIP codes; Geographic Variation uses FIPS county codes. A ZIP-to-County crosswalk file is needed to connect them. Source: HUD USPS ZIP Crosswalk or Census ZCTA relationship file. Add as a separate reference data pipeline. |
| HCC risk score version undocumented | LOW | The HCC risk score methodology version (V22 vs. V24 vs. V28) affects interpretation. CMS methodology documents should clarify this. Capture in catalog metadata. |
| MA penetration nuance | LOW | As MA exceeds 50% of Medicare, FFS-only measures become less representative. All UI displays of Geographic Variation data should include a caveat about FFS-only limitation and show MA penetration rate alongside spending measures. |

## Verdict: HAS GAPS (1 HIGH — URL verification; 2 MEDIUM — FIPS format and ZIP-County crosswalk needed for cross-source joins)

---

# Shared Infrastructure Requirements

## Common Acquisition Utilities

These utilities are shared across all 4 sources and should be built as reusable Python modules:

| Utility | Description | Used By |
|---------|-------------|---------|
| `acquire.download_file(url, dest, retries=3)` | HTTP download with streaming, progress logging, retry with exponential backoff | All sources |
| `acquire.discover_url(source, year=None)` | Resolve current download URL for a source from a config registry (URLs change; keep them in one place) | All sources |
| `acquire.validate_file_size(path, min_bytes, max_bytes)` | BLOCK validation on file size | All sources |
| `acquire.compute_hash(path, algorithm='sha256')` | Compute file hash for change detection | All sources |
| `acquire.check_hash_changed(hash, source, year=None)` | Compare hash against stored metadata in Postgres | All sources |
| `acquire.extract_zip(zip_path, dest)` | Extract ZIP archive with validation | NPPES (zipped) |
| `acquire.store_metadata(source, run_date, hash, rows, size)` | Write acquisition metadata to `catalog_sources` | All sources |

**Module location**: `src/pipelines/common/acquire.py`

## Shared Validation Patterns

| Pattern | Description | Used By |
|---------|-------------|---------|
| `validate.check_required_columns(df, expected_columns)` | BLOCK if any required columns missing | All sources |
| `validate.check_column_format(df, column, regex_pattern)` | BLOCK/WARN if values don't match expected format | NPI validation across all |
| `validate.check_uniqueness(df, key_columns)` | BLOCK if composite key has duplicates | All sources |
| `validate.check_row_count(df, min_rows, max_rows)` | BLOCK/WARN on row count out of range | All sources |
| `validate.check_referential_integrity(df, column, reference_df, ref_column, min_match_rate)` | WARN if join rate below threshold | Part B, Part D (NPI → NPPES) |
| `validate.check_value_range(df, column, min_val, max_val)` | WARN on out-of-range values | Spending columns, counts |
| `validate.check_null_rate(df, column, max_null_rate)` | WARN on excessive nulls | Various |
| `validate.check_delta(current_count, previous_count, max_pct_change)` | WARN on large changes from previous run | All sources |
| `validate.store_results(source, run_date, results)` | Write validation results to `catalog_quality` | All sources |

**Module location**: `src/pipelines/common/validate.py`

**Validation result format**:
```python
@dataclass
class ValidationResult:
    rule_name: str
    severity: Literal["BLOCK", "WARN", "INFO"]
    passed: bool
    message: str
    metric_value: Any
    threshold: Any
```

## Common Transformation Patterns

| Pattern | Description | Used By |
|---------|-------------|---------|
| `transform.normalize_npi(column)` | Validate and zero-pad NPI to 10 digits | All NPI-bearing sources |
| `transform.normalize_fips(column, digits)` | Zero-pad FIPS codes to correct length | All sources with state/county FIPS |
| `transform.add_snapshot_metadata(run_date, source)` | Add `snapshot_date` and `source_name` columns | All sources |
| `transform.apply_schema_mapping(year, source)` | Apply year-specific column name mapping from registry | Part B, Part D (schema evolution) |
| `transform.cast_to_parquet_types(df, schema)` | Apply Pydantic-defined schema to DuckDB/Arrow types | All sources |
| State FIPS lookup table | State name/abbreviation → 2-digit FIPS | NPPES, Geographic Variation |
| ZIP-to-County crosswalk | 5-digit ZIP → 5-digit County FIPS | Part B, Part D (for geographic joins) |

**Module location**: `src/pipelines/common/transform.py`

**Reference data location**: `data/reference/`
- `data/reference/state_fips.csv` — state name, abbreviation, FIPS code
- `data/reference/zip_to_county.csv` — HUD ZIP-to-County crosswalk (NEEDS ACQUISITION)
- `data/reference/nucc_taxonomy.csv` — NUCC taxonomy codes to descriptions (NEEDS ACQUISITION)

## Shared Storage Conventions

```
data/
├── raw/                          # Immutable raw downloads
│   ├── nppes/{YYYY-MM-DD}/       # NPPES by download date (monthly snapshots)
│   ├── partb/{YYYY}/             # Part B by data year (annual, immutable)
│   ├── partd/{YYYY}/             # Part D by data year (annual, immutable)
│   ├── geovar/{YYYY}/            # Geographic Variation by data year
│   └── reference/                # Reference/crosswalk files
├── processed/                    # Transformed, typed, validated Parquet files
│   ├── nppes/                    # Current NPPES (overwritten monthly)
│   ├── partb/{YYYY}/             # Part B by data year
│   ├── partd/{YYYY}/             # Part D by data year
│   └── geovar/{YYYY}/            # Geographic Variation by data year
├── mart/                         # Pre-aggregated analytical files
│   ├── nppes/                    # Provider aggregations
│   ├── partb/                    # Part B aggregations
│   ├── partd/                    # Part D aggregations
│   └── geovar/                   # (Not needed — already aggregated)
└── archive/                      # Historical snapshots (NPPES only for MVP)
    └── nppes/{YYYY-MM-DD}/       # Monthly NPPES snapshots
```

**Naming conventions**:
- Raw files: keep CMS original filenames where possible
- Processed files: `{source}_{descriptor}.parquet` (e.g., `nppes_all.parquet`, `partb_utilization.parquet`)
- Mart files: `{source}_{aggregation}_{year}.parquet` (e.g., `partb_provider_summary_2022.parquet`)
- All Parquet files use ZSTD compression

**Metadata tables (PostgreSQL)**:
```sql
-- Acquisition tracking
CREATE TABLE catalog_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL,
    data_year INTEGER,
    run_date DATE NOT NULL,
    download_url TEXT,
    file_size_bytes BIGINT,
    sha256_hash VARCHAR(64),
    row_count INTEGER,
    status VARCHAR(20) NOT NULL, -- 'downloaded', 'validated', 'processed', 'failed'
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Validation results
CREATE TABLE catalog_quality (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL,
    data_year INTEGER,
    run_date DATE NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    severity VARCHAR(10) NOT NULL, -- 'BLOCK', 'WARN', 'INFO'
    passed BOOLEAN NOT NULL,
    metric_value TEXT,
    threshold TEXT,
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Column-level catalog
CREATE TABLE catalog_columns (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL,
    data_year INTEGER,
    column_name VARCHAR(100) NOT NULL,
    canonical_name VARCHAR(100),
    data_type VARCHAR(50),
    nullable BOOLEAN,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Recommended Pipeline DAG

### Task Dependency Graph

```
                    ┌──────────────────────────┐
                    │  URL Verification Task    │  ← Manual, one-time prerequisite
                    │  (all 4 sources)          │
                    └─────────┬────────────────┘
                              │
                    ┌─────────▼────────────────┐
                    │  Reference Data Load      │  ← state_fips.csv, zip_to_county.csv,
                    │  (seed data)              │     nucc_taxonomy.csv
                    └─────────┬────────────────┘
                              │
              ┌───────────────┼───────────────────────────┐
              │               │                           │
    ┌─────────▼──────┐ ┌─────▼────────────┐ ┌────────────▼───────────┐
    │  NPPES          │ │  Geographic      │ │  [WAIT for NPPES]      │
    │  Acquisition    │ │  Variation       │ │                        │
    │  + Processing   │ │  Acquisition     │ │                        │
    │                 │ │  + Processing    │ │                        │
    └────────┬───────┘ └────────┬─────────┘ │                        │
             │                  │            │                        │
             │                  │            │                        │
             ▼                  ▼            │                        │
    ┌────────────────┐ ┌────────────────┐   │                        │
    │  NPPES →       │ │  GeoVar →      │   │                        │
    │  PostgreSQL    │ │  PostgreSQL    │   │                        │
    │  Load          │ │  Load          │   │                        │
    └────────┬───────┘ └────────────────┘   │                        │
             │                              │                        │
             ▼                              │                        │
    ┌────────────────────────────────────────▼──────────────────────┐
    │                 NPPES Available in Postgres                    │
    │                 (NPI referential integrity checks enabled)     │
    └────────┬──────────────────────────────────┬──────────────────┘
             │                                  │
    ┌────────▼──────────┐            ┌──────────▼──────────┐
    │  Part B            │            │  Part D              │
    │  Acquisition       │            │  Acquisition         │
    │  + Validation      │            │  + Validation        │
    │  + Processing      │            │  + Processing        │
    │  (per year)        │            │  (per year)          │
    └────────┬──────────┘            └──────────┬──────────┘
             │                                  │
             │      ┌──────────────────┐        │
             └──────▶  Mart Generation  ◀───────┘
                    │  (pre-aggs for   │
                    │   all sources)   │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  PostgreSQL       │
                    │  Summary Load     │
                    │  (Part B + Part D │
                    │   summaries)      │
                    └──────────────────┘
```

### Parallelism Strategy

| Pipeline | Can Parallel With | Must Wait For | Rationale |
|----------|-------------------|---------------|-----------|
| NPPES acquisition | Geographic Variation acquisition | Reference data load | No dependencies between these downloads |
| Geographic Variation acquisition | NPPES acquisition | Reference data load | Same — independent downloads |
| NPPES processing | Geographic Variation processing | NPPES acquisition | Can process GeoVar while processing NPPES |
| Part B acquisition | Part D acquisition | NPPES Postgres load complete | NPI referential integrity check needs NPPES in Postgres |
| Part D acquisition | Part B acquisition | NPPES Postgres load complete | Same — but Part B and Part D can run in parallel |
| Part B processing (year N) | Part B processing (year N+1) | Part B acquisition (year N) | Can process multiple years in parallel |
| Part D processing (year N) | Part D processing (year N+1) | Part D acquisition (year N) | Same |
| Mart generation | Nothing | All processing complete | Aggregations depend on processed data |

### Estimated Execution Time (Initial Load)

| Pipeline Stage | Source | Estimated Time | Notes |
|----------------|--------|----------------|-------|
| Download | NPPES (full file, ~3 GB ZIP) | 10-30 min | Depends on internet speed |
| Download | Part B (3 years × ~3 GB each) | 20-60 min | Can parallelize years |
| Download | Part D (3 years × ~5 GB each) | 30-90 min | Can parallelize years |
| Download | Geographic Variation (all years) | 1-5 min | Tiny files |
| Processing | NPPES (8M rows → Parquet) | 5-15 min | DuckDB is fast on CSV |
| Processing | Part B (10M rows/year × 3 years) | 10-30 min | DuckDB streaming CSV |
| Processing | Part D (25M rows/year × 3 years) | 20-60 min | Largest dataset |
| Processing | Geographic Variation (all years) | < 1 min | Trivially small |
| Postgres Load | All sources (summaries + reference) | 5-15 min | COPY-based bulk load |
| Mart Generation | All pre-aggregations | 5-15 min | DuckDB on Parquet |
| **Total (sequential)** | | **~2-5 hours** | |
| **Total (with parallelism)** | | **~1-3 hours** | Download overlap + year-parallel processing |

### Ongoing Refresh Estimates

| Source | Frequency | Estimated Time |
|--------|-----------|----------------|
| NPPES | Monthly | 20-45 min (download + full reprocess) |
| Part B | Annual (1 new year) | 15-30 min |
| Part D | Annual (1 new year) | 20-45 min |
| Geographic Variation | Annual | < 5 min |

---

## Cross-Source Join Matrix (MVP)

These joins become available once all 4 sources are loaded:

| Join | Key | Type | Enables |
|------|-----|------|---------|
| Part B → NPPES | `Rndrng_NPI` = `NPI` | Direct (NPI) | Provider name, specialty, address enrichment on utilization data |
| Part D → NPPES | `Prscrbr_NPI` = `NPI` | Direct (NPI) | Provider name, specialty, address enrichment on prescribing data |
| Part B → Part D | `Rndrng_NPI` = `Prscrbr_NPI` | Direct (NPI) | Complete provider practice profile (procedures + drugs) |
| Part B → GeoVar | `Rndrng_Prvdr_State_FIPS` = `State_FIPS` | Contextual (FIPS) | Population spending context for provider billing |
| Part D → GeoVar | `Prscrbr_State_FIPS` = `State_FIPS` | Contextual (FIPS) | Population drug spending context for prescribing |
| NPPES → GeoVar | Derived `provider_state_fips` = `State_FIPS` | Contextual (FIPS) | Provider supply per geographic area |

**Note**: County-level joins between provider data and Geographic Variation require a ZIP-to-County crosswalk (flagged as a gap). State-level joins work directly via FIPS.

---

## Reference Data Pipelines (Supporting)

These small reference data pipelines are prerequisites for the main pipelines:

| Reference Source | Description | Priority | Acquisition |
|------------------|-------------|----------|-------------|
| State FIPS codes | State name, abbreviation, 2-digit FIPS | P0 (seed data) | Static CSV, bundled with project |
| ZIP-to-County crosswalk | HUD USPS ZIP → County FIPS mapping | P1 (before Part B/D geographic analysis) | Download from HUD Exchange: https://www.huduser.gov/portal/datasets/usps_crosswalk.html (NEEDS VERIFICATION) |
| NUCC Taxonomy codes | Taxonomy code → specialty description | P1 (before NPPES specialty analysis) | Download from NUCC: https://nucc.org/index.php/code-sets-mainmenu-41/provider-taxonomy-mainmenu-40/csv-mainmenu-57 (NEEDS VERIFICATION) |
| HCPCS code reference | HCPCS code → description, category, RVU | P2 (before Part B service analysis) | CMS HCPCS release: https://www.cms.gov/medicare/coding/hcpcsreleasecodesets (NEEDS VERIFICATION) |
| Drug classification | Generic name → drug class | P2 (before Part D drug analysis) | Build from FDA NDC directory or RxNorm |

---

## Overall Verdict: HAS GAPS

### Summary of All HIGH Severity Gaps

| # | Gap | Source(s) Affected | Resolution Required Before |
|---|-----|-------------------|---------------------------|
| 1 | CMS download URLs unverified | ALL 4 sources | Building ANY acquisition pipeline |
| 2 | Part B schema version registry | Part B Utilization | Loading pre-2018 data years |
| 3 | Part D drug name normalization strategy | Part D Prescribers | Reliable drug-level aggregation |

### Resolution Plan

| # | Gap | Recommended Action | Effort |
|---|-----|-------------------|--------|
| 1 | URL verification | Execute a manual verification script: HTTP HEAD requests to all 4 source URLs, capture response codes and content-type headers. Update catalog entries. **Blocks all pipeline development.** | 2-4 hours |
| 2 | Schema version registry | Download one file per year from Part B (2013-latest). Extract column headers only (first row). Build a YAML registry mapping year → column names → canonical names. | 4-8 hours |
| 3 | Drug name normalization | Download one year of Part D data. Extract unique `Gnrc_Name` values. Group by normalized form (uppercased, trimmed). Identify clusters. Build a canonical mapping table. Consider RxNorm integration for MVP or manual mapping for top 500 drugs. | 8-16 hours |

### Recommendation

**Proceed with pipeline development** using the lifecycle plans above, but execute Gap #1 (URL verification) as an immediate blocking prerequisite. Gaps #2 and #3 can be resolved iteratively during the processing stage — start with the most recent data year (which uses the current schema) and add historical years once the schema registry is built.

The lifecycle plans are comprehensive and actionable. The architecture is proportional to each source's characteristics: NPPES gets monthly processing with archival snapshots; Part B and Part D get annual batch processing with year-level partitioning; Geographic Variation gets the simplest possible pipeline befitting its tiny size. All pipelines share common infrastructure (acquisition, validation, transformation utilities) to avoid duplication.

**Priority order for implementation**:
1. Common infrastructure (acquire, validate, transform modules)
2. Reference data (state FIPS, NUCC taxonomy — seed data)
3. NPPES pipeline (identity hub — everything depends on it)
4. Geographic Variation pipeline (simple, high value, validates infrastructure)
5. Part B pipeline (core utilization — highest analytical value)
6. Part D pipeline (largest volume — validates scale handling)

---

*This review was produced by the Pipeline Architect subagent as part of the PUF Foundation Sprint (Wave 1). All URLs are flagged NEEDS VERIFICATION and must be confirmed before pipeline code is written.*
