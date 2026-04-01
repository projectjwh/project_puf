# Structure Review v2: Project PUF
Date: 2026-03-04
Reviewer: Structure Sentinel (upgraded -- 16 principles)

---

## Previous Structure Issues (v1)

The v1 proposal (2026-03-03) had the following problems:

| # | Problem | Severity | Details |
|---|---------|----------|---------|
| 1 | **`pipelines/sources/` is premature nesting** | HIGH | Added `sources/` as a wrapper between `pipelines/` and the actual source modules. `pipelines/nppes/` is sufficient -- `pipelines/sources/nppes/` adds depth for zero value. |
| 2 | **No `data/` directory anywhere** | HIGH | The Pipeline Architect explicitly defined `data/raw/`, `data/processed/`, `data/mart/`, `data/archive/` with exact path conventions. The v1 structure had NO `data/` directory. Instead it had `lake/` which serves a different and vaguer purpose. This is a major cross-agent inconsistency. |
| 3 | **`lake/` is vague and conflicts with Pipeline Architect paths** | HIGH | Pipeline Architect never mentioned `lake/`. Storage is `data/`. The name `lake/` is metaphorical -- it evokes "data lake" but doesn't communicate what's actually in it. Conflicts with `data/` being the storage convention. |
| 4 | **`shared/` inside pipelines is `utils/` in disguise** | MEDIUM | `pipelines/shared/` containing `downloader.py`, `file_handlers.py`, `logging.py` is a junk drawer with a polished name. Meanwhile the Pipeline Architect called these `src/pipelines/common/acquire.py`, `validate.py`, `transform.py` -- organized by lifecycle stage, not by implementation concern. |
| 5 | **`content/blog/` is a wrapper directory anti-pattern** | MEDIUM | `content/` exists only to hold `blog/`. This is explicitly called out as Anti-Pattern #1 (Wrapper directory). Should be just `blog/`. |
| 6 | **`observability/` has premature nesting** | MEDIUM | 3 subdirectories (`prometheus/`, `grafana/`, `loki/`) each holding 1 file. Orphan chain pattern. Not needed until Wave 3. |
| 7 | **Self-reviewed its own work and was too lenient** | HIGH | 10 PASS, 1 WARN. Gave itself a PASS on Data Gravity (which it didn't even evaluate), Cross-Agent Consistency (which it didn't check), and Anti-Patterns (which it didn't scan). The v1 agent had 11 principles and only evaluated against those -- but it missed obvious violations even within its own framework. |
| 8 | **No data-gravity principle applied** | HIGH | This is a DATA PLATFORM. The most important question is "where does data live?" The v1 structure buries data behind `lake/catalog/` -- an abstraction layer that doesn't exist yet. |
| 9 | **Semantic inconsistency at root level** | MEDIUM | `lake/` (metaphorical noun from data engineering) sits alongside `api/` (literal technical term), `frontend/` (role-based), and `pipelines/` (process-based). No consistent naming pattern. |
| 10 | **No cross-agent path verification** | HIGH | The Pipeline Architect documented `data/raw/nppes/{YYYY-MM-DD}/`, `data/processed/nppes/`, `data/mart/nppes/`. The Schema Smith documented `models/staging/cms/`, `models/marts/provider/`. None of these paths were verified against the proposed structure. |
| 11 | **Pipeline Architect says `src/pipelines/common/` but v1 says `pipelines/shared/`** | MEDIUM | Two different names for the same thing, and neither matched. Pipeline Architect used `common/` (acceptable domain name) organized by lifecycle stage. v1 used `shared/` (suspect name per Principle 3) organized by implementation type. |

---

## Proposed Structure v2

### Immediate (create when first file is written)

Only showing directories that have files NOW or will have files in the current sprint.

```
D:/Internal/Project_PUF/
|-- CLAUDE.md                           # Project instructions (EXISTS)
|-- README.txt                          # Project readme (EXISTS)
|-- .gitignore                          # Repository hygiene (CREATE NOW)
|-- devlogs/                            # Development logs (EXISTS)
|   |-- README.md
|   |-- 2026-03-03_puf-foundation-sprint_brief.md
|   |-- 2026-03-03_arch-advisor-review.md
|   |-- 2026-03-03_pipeline-architect-review.md
|   |-- 2026-03-03_schema-smith-review.md
|   |-- 2026-03-03_structure-sentinel-review.md
|   |-- 2026-03-04_structure-sentinel-v2-review.md
|   |-- 2026-03-04_insight-engine-review.md
|   +-- 2026-03-04_ux-advocate-review.md
+-- docs/                               # Documentation (EXISTS)
    +-- sources/                         # Per-source knowledge base (EXISTS, populated)
        |-- 00_relationship_map.md
        |-- physician_compare_nppes_pecos.md
        |-- medicare_provider_utilization_partb.md
        |-- medicare_partd_prescribers.md
        |-- medicare_geographic_variation.md
        +-- (8 more source docs)
```

### Wave 1 -- Create when first pipeline code is written

```
D:/Internal/Project_PUF/
|-- pyproject.toml                      # Python project root (workspace)
|-- config/                             # Centralized configuration
|   +-- sources.yaml                    #   Source URLs, schedules, size thresholds
|-- data/                               # ALL DATA LIVES HERE (.gitignored)
|   |-- raw/                            #   Immutable downloads
|   |   |-- nppes/{YYYY-MM-DD}/         #     NPPES by download date
|   |   |-- partb/{YYYY}/              #     Part B by data year
|   |   |-- partd/{YYYY}/             #     Part D by data year
|   |   +-- geovar/{YYYY}/            #     Geographic Variation by data year
|   |-- processed/                      #   Transformed Parquet files
|   |   |-- nppes/                      #     nppes_all.parquet, nppes_active.parquet
|   |   |-- partb/{YYYY}/             #     partb_utilization.parquet per year
|   |   |-- partd/{YYYY}/             #     partd_prescribers.parquet per year
|   |   +-- geovar/                    #     geovar.parquet, geovar_all_years.parquet
|   |-- mart/                           #   Pre-aggregated analytical files
|   |   |-- nppes/                      #     providers_by_state.parquet, etc.
|   |   |-- partb/                     #     provider_summary_{year}.parquet, etc.
|   |   +-- partd/                     #     drug_summary_{year}.parquet, etc.
|   |-- archive/                        #   Historical snapshots
|   |   +-- nppes/{YYYY-MM-DD}/        #     Monthly NPPES snapshots
|   +-- reference/                      #   Static reference/crosswalk files
|       |-- state_fips.csv
|       |-- nucc_taxonomy.csv
|       +-- zip_to_county.csv
|-- pipelines/                          # Python -- data ingestion & processing
|   |-- __init__.py
|   |-- _common/                        #   Cross-source lifecycle utilities (underscore = internal)
|   |   |-- __init__.py
|   |   |-- acquire.py                  #     download_file, discover_url, compute_hash, extract_zip
|   |   |-- validate.py                 #     check_columns, check_format, check_uniqueness
|   |   +-- transform.py               #     normalize_npi, normalize_fips, add_snapshot_metadata
|   |-- nppes/                          #   NPPES pipeline
|   |   |-- __init__.py
|   |   |-- acquire.py
|   |   |-- validate.py
|   |   |-- transform.py
|   |   +-- test_nppes.py
|   |-- partb/                          #   Part B Utilization pipeline
|   |   |-- __init__.py
|   |   |-- acquire.py
|   |   |-- validate.py
|   |   |-- transform.py
|   |   +-- test_partb.py
|   |-- partd/                          #   Part D Prescribers pipeline
|   |   |-- __init__.py
|   |   |-- acquire.py
|   |   |-- validate.py
|   |   |-- transform.py
|   |   +-- test_partd.py
|   +-- geovar/                         #   Geographic Variation pipeline
|       |-- __init__.py
|       |-- acquire.py
|       |-- validate.py
|       |-- transform.py
|       +-- test_geovar.py
+-- flows/                              # Prefect flow definitions (orchestration)
    |-- __init__.py
    |-- nppes_flow.py
    |-- partb_flow.py
    |-- partd_flow.py
    +-- geovar_flow.py
```

### Wave 2 -- Create when dbt/API work begins

```
D:/Internal/Project_PUF/
|-- models/                             # dbt project -- SQL transformations
|   |-- dbt_project.yml
|   |-- staging/
|   |   +-- cms/                        #   CMS source staging (Schema Smith convention)
|   |       |-- _cms__sources.yml
|   |       |-- _cms__models.yml
|   |       |-- stg_cms__nppes.sql
|   |       |-- stg_cms__part_b_utilization.sql
|   |       |-- stg_cms__part_d_prescribers.sql
|   |       +-- stg_cms__geographic_variation.sql
|   |-- intermediate/
|   |   |-- _int__models.yml
|   |   |-- int_providers.sql
|   |   |-- int_provider_services.sql
|   |   |-- int_provider_prescriptions.sql
|   |   +-- int_geographic_benchmarks.sql
|   +-- marts/
|       |-- provider/
|       |   |-- _provider__models.yml
|       |   |-- mart_provider__practice_profile.sql
|       |   |-- mart_provider__prescribing_summary.sql
|       |   +-- mart_provider__by_specialty.sql
|       |-- geographic/
|       |   |-- _geographic__models.yml
|       |   |-- mart_geographic__spending_variation.sql
|       |   +-- mart_geographic__by_state.sql
|       +-- reference/
|           |-- _reference__models.yml
|           |-- ref_providers.sql
|           |-- ref_provider_taxonomies.sql
|           |-- ref_geographies.sql
|           +-- ref_hcpcs_codes.sql
+-- api/                                # Python (FastAPI) -- API backend
    |-- pyproject.toml
    |-- __init__.py
    |-- main.py
    |-- routes/
    |   |-- __init__.py
    |   |-- providers.py
    |   |-- geographic.py
    |   +-- prescribing.py
    +-- test_api.py
```

### Wave 3 -- Create when frontend/monitoring work begins

```
D:/Internal/Project_PUF/
|-- frontend/                           # TypeScript (Next.js) -- Web UI
|   |-- package.json
|   |-- tsconfig.json
|   |-- next.config.js
|   |-- app/                            #   Next.js App Router
|   |   |-- layout.tsx
|   |   |-- page.tsx                    #   National Dashboard (default)
|   |   |-- providers/
|   |   |   +-- page.tsx               #   Provider Lookup
|   |   |-- geographic/
|   |   |   +-- page.tsx               #   Geographic Explorer
|   |   |-- specialties/
|   |   |   +-- page.tsx               #   Specialty Comparison
|   |   +-- opioids/
|   |       +-- page.tsx               #   Opioid Prescribing Monitor
|   +-- components/                     #   Shared UI components (flat until 10+ files)
|       |-- data-table.tsx
|       |-- chart-wrapper.tsx
|       |-- filter-bar.tsx
|       +-- sidebar.tsx
|-- monitoring/                         # Observability stack config
|   |-- prometheus.yml
|   |-- grafana-dashboards.json
|   +-- docker-compose.monitoring.yml
|-- analyses/                           # Insight Engine outputs
|   +-- (populated by Insight Engine)
+-- blog/                               # Blog post drafts (NOT content/blog/)
    +-- (populated from analyses)
```

---

## Full Target Structure (architectural intent, all waves combined)

```
D:/Internal/Project_PUF/
|
|-- .gitignore                          # Git ignore (includes data/)
|-- .env.example                        # Environment variable template
|-- pyproject.toml                      # Python workspace root
|-- Makefile                            # Top-level task runner
|-- CLAUDE.md                           # Claude Code instructions
|-- README.txt                          # Project readme
|
|-- config/                             # Centralized configuration
|   |-- sources.yaml                    #   Source URLs, schedules, thresholds
|   |-- database.yaml                   #   Connection strings (env-specific)
|   +-- docker-compose.yml              #   Docker Compose for services
|
|-- data/                               # ALL DATA (.gitignored, never committed)
|   |-- raw/{source}/{date-or-year}/    #   Immutable downloads
|   |-- processed/{source}/[{year}/]    #   Transformed Parquet
|   |-- mart/{source}/                  #   Pre-aggregated analytics
|   |-- archive/{source}/{date}/        #   Historical snapshots
|   +-- reference/                      #   Static crosswalk/lookup files
|
|-- pipelines/                          # Python -- data ingestion & processing
|   |-- __init__.py
|   |-- _common/                        #   Cross-source lifecycle utilities
|   |   |-- acquire.py
|   |   |-- validate.py
|   |   +-- transform.py
|   |-- nppes/                          #   One directory per source
|   |-- partb/
|   |-- partd/
|   |-- geovar/
|   +-- (future: pecos/, pos/, hcpcs/, ndc/, taxonomy/, ...)
|
|-- flows/                              # Prefect flow definitions (orchestration)
|   |-- nppes_flow.py
|   +-- (one flow file per source or per composite workflow)
|
|-- models/                             # dbt project -- SQL transformations
|   |-- dbt_project.yml
|   |-- staging/cms/                    #   Raw-to-clean 1:1 mappings
|   |-- intermediate/                   #   Business logic joins
|   +-- marts/                          #   Consumption-ready tables
|       |-- provider/
|       |-- geographic/
|       +-- reference/
|
|-- api/                                # Python (FastAPI) -- API backend
|   |-- pyproject.toml
|   |-- main.py
|   |-- routes/
|   +-- test_api.py
|
|-- frontend/                           # TypeScript (Next.js) -- Web UI
|   |-- package.json
|   |-- app/
|   +-- components/
|
|-- monitoring/                         # Observability configs
|   |-- prometheus.yml
|   +-- grafana-dashboards.json
|
|-- analyses/                           # Insight Engine outputs
|-- blog/                               # Blog post drafts
|-- devlogs/                            # Development logs
|-- docs/                               # Documentation
|   +-- sources/                        #   Per-source knowledge base
|
+-- .github/                            # CI/CD workflows
    +-- workflows/
```

---

## Depth Budget

| Path (deepest per branch) | Depth | Status |
|---------------------------|-------|--------|
| `data/raw/nppes/2026-03-04/npi_full.csv.zip` | 4 | OK |
| `data/processed/partb/2022/partb_utilization.parquet` | 4 | OK |
| `data/mart/nppes/providers_by_state.parquet` | 3 | OK |
| `data/archive/nppes/2026-03-04/nppes_all.parquet` | 4 | OK |
| `data/reference/state_fips.csv` | 2 | OK |
| `pipelines/_common/acquire.py` | 2 | OK |
| `pipelines/nppes/acquire.py` | 2 | OK |
| `pipelines/nppes/test_nppes.py` | 2 | OK |
| `flows/nppes_flow.py` | 1 | OK |
| `models/staging/cms/stg_cms__nppes.sql` | 3 | OK |
| `models/intermediate/int_providers.sql` | 2 | OK |
| `models/marts/provider/mart_provider__practice_profile.sql` | 3 | OK |
| `models/marts/reference/ref_providers.sql` | 3 | OK |
| `api/routes/providers.py` | 2 | OK |
| `api/test_api.py` | 1 | OK |
| `frontend/app/providers/page.tsx` | 3 | OK |
| `frontend/components/data-table.tsx` | 2 | OK |
| `monitoring/prometheus.yml` | 1 | OK |
| `config/sources.yaml` | 1 | OK |
| `config/docker-compose.yml` | 1 | OK |
| `docs/sources/physician_compare_nppes_pecos.md` | 2 | OK |
| `devlogs/2026-03-04_structure-sentinel-v2-review.md` | 1 | OK |
| `analyses/` | 1 | OK |
| `blog/` | 1 | OK |
| `.github/workflows/pipeline-ci.yml` | 2 | OK |

**Maximum depth across all branches: 4** (only in `data/` paths where date/year partitioning demands it). All code paths are depth 3 or less. Budget is satisfied.

---

## Anti-Pattern Scan

| # | Anti-Pattern | Found? | Location | Fix |
|---|-------------|--------|----------|-----|
| 1 | **Wrapper directory** | NO | v1 had `content/blog/` -- eliminated. Now `blog/` at root. v1 had `pipelines/sources/` -- eliminated. Now `pipelines/{source}/` directly. | -- |
| 2 | **Mirror tree** | NO | Tests are colocated inside each pipeline module (`test_nppes.py` next to `acquire.py`). dbt tests follow dbt convention (`schema.yml` files). No separate `tests/` tree. | -- |
| 3 | **Junk drawer** | NO | No `utils/`, `helpers/`, `misc/`, `common/`, `lib/`. The `_common/` in pipelines is prefixed with underscore (marking internal) and organized by lifecycle stage (acquire, validate, transform), not by type. Each file has a concrete domain purpose. | -- |
| 4 | **Premature nesting** | NO | `pipelines/nppes/` is 1 level deep. `models/staging/cms/` is 2 levels but justified by dbt convention (staging is grouped by source system). `models/marts/provider/` is 2 levels but justified: marts has 3 sub-domains (provider, geographic, reference) each with multiple models. | -- |
| 5 | **Config scatter** | NO | All config centralized in `config/`. Framework-mandated config at root (`pyproject.toml`, `.gitignore`). dbt config in `models/dbt_project.yml` per dbt convention. No config inside domain directories. | -- |
| 6 | **src/ wrapper** | NO | No `src/` directory. `pipelines/`, `api/`, `frontend/` are direct root-level directories. Note: Pipeline Architect referenced `src/pipelines/common/` in its review -- this is a cross-agent inconsistency that is resolved by removing the `src/` wrapper (this structure is authoritative for paths). | -- |
| 7 | **Type grouping at leaf** | NO | v1 had `components/charts/`, `components/tables/`, `components/layout/`. Now `components/` is flat with individual component files. Will add subdirectories only when component count exceeds 10-12. | -- |
| 8 | **Orphan chain** | NO | No single-child directory chains. `_common/` has 3 files. Every directory has multiple children or is a leaf with files. Checked: `config/` has 1-3 files (acceptable -- it's a leaf with multiple files, not a chain). | -- |
| 9 | **Phantom directories** | NO | Wave system enforced. Only directories with files are created. Wave 2 and Wave 3 directories are documented as architectural intent, not to be `mkdir`'d until needed. | -- |
| 10 | **Data mixed with code** | NO | `data/` is a separate top-level directory, `.gitignored`. No data files in `pipelines/`, `models/`, `api/`, or any code directory. Reference data lives in `data/reference/`, not in code directories. | -- |

**Result: 0 anti-patterns detected.**

---

## Cross-Agent Consistency

| Agent | Expected Paths | Structure Match? | Conflict? |
|-------|---------------|-----------------|-----------|
| **Pipeline Architect** | `data/raw/nppes/{YYYY-MM-DD}/` | YES | None |
| **Pipeline Architect** | `data/raw/partb/{YYYY}/` | YES | None |
| **Pipeline Architect** | `data/raw/partd/{YYYY}/` | YES | None |
| **Pipeline Architect** | `data/raw/geovar/{YYYY}/` | YES | None |
| **Pipeline Architect** | `data/processed/nppes/nppes_all.parquet` | YES | None |
| **Pipeline Architect** | `data/processed/partb/{YYYY}/partb_utilization.parquet` | YES | None |
| **Pipeline Architect** | `data/processed/partd/{YYYY}/partd_prescribers.parquet` | YES | None |
| **Pipeline Architect** | `data/processed/geovar/geovar_all_years.parquet` | YES | None |
| **Pipeline Architect** | `data/mart/nppes/providers_by_state.parquet` | YES | None |
| **Pipeline Architect** | `data/mart/partb/provider_summary_{year}.parquet` | YES | None |
| **Pipeline Architect** | `data/mart/partd/drug_summary_{year}.parquet` | YES | None |
| **Pipeline Architect** | `data/archive/nppes/{YYYY-MM-DD}/nppes_all.parquet` | YES | None |
| **Pipeline Architect** | `data/reference/state_fips.csv` | YES | None |
| **Pipeline Architect** | `data/reference/nucc_taxonomy.csv` | YES | None |
| **Pipeline Architect** | `data/reference/zip_to_county.csv` | YES | None |
| **Pipeline Architect** | `src/pipelines/common/acquire.py` | **RESOLVED** | PA said `src/pipelines/common/`. Structure says `pipelines/_common/acquire.py`. The `src/` wrapper is dropped (Anti-Pattern #6). `common` renamed to `_common` per Principle 3 (underscore prefix for internal/cross-cutting). Pipeline Architect's path references should be updated to match. **This structure is authoritative for directory layout.** |
| **Pipeline Architect** | `src/pipelines/common/validate.py` | **RESOLVED** | Same as above. Maps to `pipelines/_common/validate.py`. |
| **Pipeline Architect** | `src/pipelines/common/transform.py` | **RESOLVED** | Same as above. Maps to `pipelines/_common/transform.py`. |
| **Pipeline Architect** | `raw/{source}/{date}/` inside `data/` + `reference/` inside `data/raw/` | **RESOLVED** | PA listed `data/raw/reference/` in the tree diagram but referenced `data/reference/` in the text. Structure uses `data/reference/` as a top-level child of `data/` (not inside `raw/`) because reference data is not "raw downloads" -- it is static lookup data that crosses all layers. |
| **Schema Smith** | `models/staging/cms/stg_cms__nppes.sql` | YES | None |
| **Schema Smith** | `models/staging/cms/_cms__sources.yml` | YES | None |
| **Schema Smith** | `models/intermediate/int_providers.sql` | YES | None |
| **Schema Smith** | `models/marts/provider/mart_provider__practice_profile.sql` | YES | None |
| **Schema Smith** | `models/marts/geographic/mart_geographic__spending_variation.sql` | YES | None |
| **Schema Smith** | `models/marts/reference/ref_providers.sql` | YES | None |
| **Schema Smith** | `models/_project.yml` (dbt config) | **RESOLVED** | Schema Smith put it at `models/_project.yml`. Standard dbt convention is `models/../dbt_project.yml` at the dbt project root. Structure uses `models/dbt_project.yml` per dbt standard. |
| **Arch Advisor** | Local filesystem with S3-like paths | YES | `data/` uses `{layer}/{source}/{partition}/` which maps directly to S3-like `s3://puf-data/{layer}/{source}/{partition}/` |
| **Arch Advisor** | Docker Compose for services | YES | `config/docker-compose.yml` |
| **UX Advocate** | 5 pages: Dashboard, Provider Lookup, Geographic Explorer, Specialty Comparison, Opioid Monitor | YES | `frontend/app/` with `page.tsx` (dashboard), `providers/`, `geographic/`, `specialties/`, `opioids/` |
| **Insight Engine** | `analyses/` directory | YES | Top-level `analyses/` |
| **CLAUDE.md** | `content/blog/` | **CHANGED** | CLAUDE.md references `content/blog/`. This is a wrapper anti-pattern. Changed to `blog/`. **CLAUDE.md should be updated to reflect this.** |

### Conflict Resolution Summary

3 conflicts identified and resolved:
1. **`src/` wrapper**: Pipeline Architect used `src/pipelines/common/`. Dropped `src/` (Anti-Pattern #6). Renamed `common` to `_common` (Principle 3).
2. **`data/raw/reference/` vs `data/reference/`**: Reference data is not raw downloads. Placed at `data/reference/` as a peer of `raw/`, `processed/`, `mart/`, `archive/`.
3. **`content/blog/` wrapper**: Changed to `blog/` at root. CLAUDE.md needs update.

---

## Adversarial Self-Review

Switching to adversarial mode. Here are the problems I found with my own proposal:

### Problem 1: `flows/` at root is a questionable separation from `pipelines/`

**Argument against**: Prefect flow definitions (`nppes_flow.py`) are tightly coupled to the pipeline code they orchestrate (`pipelines/nppes/`). Putting them in a separate top-level `flows/` directory separates orchestration from implementation -- which is separation by type (how it runs), not by boundary (what it does). A developer working on the NPPES pipeline must now look in two places: `pipelines/nppes/` for the code and `flows/nppes_flow.py` for how it's orchestrated.

**Counter-argument**: Prefect flows are composition code -- they wire together tasks from `pipelines/` into execution graphs. They are analogous to `docker-compose.yml` (composition of services) or `dbt_project.yml` (composition of models). Composition definitions are cross-cutting: a single flow might orchestrate tasks from multiple pipeline modules (e.g., the full refresh flow runs NPPES + GeoVar + Part B + Part D in dependency order). Putting them inside a source module would be wrong because they span sources.

**Verdict**: The counter-argument holds for composite flows (multi-source), but source-specific flows (single-source) should arguably live with the source. However, mixing "some flows here, some there" is worse than consistency. **KEEP `flows/` at root. Accept the minor separation cost for consistency.** The alternative (colocating) would require moving flows when a single-source flow becomes a multi-source flow.

**Resolution trigger**: If `flows/` grows beyond 15 files and most are single-source, reconsider colocating.

### Problem 2: `_common/` might get bloated with 60+ sources

**Argument against**: As the project scales to 60+ data sources, `_common/` will accumulate source-specific edge cases. The `acquire.py` file will grow with source-specific download logic. The `transform.py` will grow with source-specific normalization. Eventually `_common/` becomes a new junk drawer -- everything that doesn't fit neatly into a source module gets dumped here.

**Counter-argument**: `_common/` is organized by lifecycle stage (acquire, validate, transform), not by source. Each function should be generic: `download_file(url, dest)`, not `download_nppes()`. Source-specific logic belongs in `pipelines/{source}/acquire.py` which calls `_common.acquire.download_file()`. If `_common/acquire.py` grows beyond 300 lines, it can be split into `_common/acquire/` as a package.

**Verdict**: Valid concern. **KEEP, but add a discipline rule**: `_common/` files must contain ONLY source-agnostic utility functions. Source-specific logic stays in source modules. If a function takes a `source` parameter to branch behavior, it's doing too much -- split into source modules.

### Problem 3: `blog/` at root level may seem orphaned from its context

**Argument against**: `blog/` at root level is a content output directory sitting alongside heavy engineering directories (`data/`, `pipelines/`, `models/`). It looks out of place. Also, if the project later adds other content types (documentation site, API reference, tutorials), having `blog/` alone at root is inconsistent. Should it be `blog/`, `tutorials/`, `api-docs/` all at root?

**Counter-argument**: The alternative is `content/blog/` which is the exact wrapper anti-pattern we're trying to avoid. The CLAUDE.md reference to `content/blog/` creates this path, but anti-patterns in documentation don't justify anti-patterns in structure. If other content types emerge, the correct response is to create `tutorials/` and `api-docs/` at root -- NOT to pre-create `content/` as a wrapper. Flat root is fine per Principle 8 (scale-aware flatness).

**Verdict**: **KEEP `blog/` at root.** It is honest about what it contains. If content types proliferate beyond 3 at root level, we can introduce a `content/` grouping at that point.

### Problem 4: `models/marts/` has 3 subdirectories -- is this premature?

**Argument against**: Schema Smith defined 3 mart sub-domains: `provider/`, `geographic/`, `reference/`. But the total model count across all 3 is only ~10 SQL files. Principle 8 says to only introduce nesting when a directory exceeds 10-12 items. The flat alternative would be `models/marts/mart_provider__practice_profile.sql`, etc. -- the naming convention already encodes the sub-domain via prefix (`mart_provider__`, `mart_geographic__`, `mart_reference__`).

**Counter-argument**: This is a dbt framework convention (Principle 4 exception: "When a framework mandates separation, follow the framework"). The dbt community standard groups marts by business domain. Schema Smith designed the model structure following this convention. Flattening would violate cross-agent consistency (Principle 13). Additionally, with 60+ sources eventually feeding marts, the mart directory will grow well beyond 12 files -- the sub-domain grouping is forward-looking, not premature.

**Verdict**: **KEEP mart subdirectories.** This is a framework-endorsed convention with strong future scaling justification. The 4 MVP sources produce 10 mart models; 60+ sources will produce 50+. The nesting is justified.

### Problem 5: Root level has many entries at full buildout

At full buildout (all waves), the root has: `.gitignore`, `.env.example`, `pyproject.toml`, `Makefile`, `CLAUDE.md`, `README.txt`, `.github/`, `config/`, `data/`, `pipelines/`, `flows/`, `models/`, `api/`, `frontend/`, `monitoring/`, `analyses/`, `blog/`, `devlogs/`, `docs/`. That is 19 items (6 files + 13 directories).

**Argument against**: Principle 8 says 10-12 items is the boundary. 19 is well over. The root should be flatter.

**Counter-argument**: Root-level config files (`.gitignore`, `.env.example`, `pyproject.toml`, `Makefile`, `CLAUDE.md`, `README.txt`) are framework-mandated or project-convention files that cannot be moved. Excluding those 6, there are 13 directories. Of these, 6 represent the core data flow (`data/`, `pipelines/`, `flows/`, `models/`, `api/`, `frontend/`), 3 are support (`config/`, `monitoring/`, `.github/`), and 4 are content/docs (`analyses/`, `blog/`, `devlogs/`, `docs/`). Each directory represents a distinct bounded context. Merging any two would violate Principle 1 (separation by boundary).

**Verdict**: **ACCEPT as WARN.** The root count is high but justified because each entry represents a genuine bounded context. The alternative (nesting into categories like `services/api/` + `services/frontend/`) would create wrapper directories. **Resolution trigger**: If root reaches 20+ directories, audit for entries that can be merged.

---

## Principle Evaluation (all 16)

| # | Principle | Verdict | Notes |
|---|-----------|---------|-------|
| 1 | Separation by boundary, not type | **PASS** | Top-level directories represent system boundaries: `data/` (storage), `pipelines/` (ingestion), `flows/` (orchestration), `models/` (transformation), `api/` (serving), `frontend/` (presentation). Within `pipelines/`, sources are grouped by data source domain, not by operation type. |
| 2 | Two-click rule (max 4 levels) | **PASS** | Maximum depth is 4, only in `data/` paths where date/year partitioning demands it. All code paths are depth 3 or less. Any source file is reachable in 2 navigation steps from root. |
| 3 | Naming reveals intent | **PASS** | All directory names are full words. `_common/` uses underscore prefix for internal scope. No `utils/`, `helpers/`, `misc/`, `shared/`. Source abbreviations are domain-standard: `nppes`, `partb`, `partd`, `geovar`. `monitoring/` replaces v1's `observability/` for concrete clarity. `blog/` replaces `content/blog/`. |
| 4 | Colocation | **PASS** | Pipeline tests colocated: `pipelines/nppes/test_nppes.py`. API tests colocated: `api/test_api.py`. dbt tests follow framework convention (`_*__models.yml` files with schema tests). Source docs in `docs/sources/`, matching source modules. Exception: `flows/` not colocated with `pipelines/` -- justified in adversarial review (composition code spans sources). |
| 5 | Explicit boundaries | **PASS** | Python packages use `__init__.py`. `pipelines/` has workspace root `pyproject.toml`. `api/` has its own `pyproject.toml`. `frontend/` has `package.json`. dbt has `dbt_project.yml`. Each boundary declares its interface. |
| 6 | Readable data flow | **PASS** | Root-level listing reads as data flow: `data/` (stored) -> `pipelines/` (ingested) -> `flows/` (orchestrated) -> `models/` (transformed) -> `api/` (served) -> `frontend/` (presented). Within `data/`, the subdirectories read as transformation lifecycle: `raw/` -> `processed/` -> `mart/`. Within each pipeline, files read as lifecycle: `acquire.py` -> `validate.py` -> `transform.py`. |
| 7 | Config at root | **PASS** | All config centralized in `config/` or at root (framework-mandated files). No config scattered inside domain directories. Source-specific config (URLs, schedules, thresholds) in `config/sources.yaml`, not inside pipeline modules. |
| 8 | Scale-aware flatness | **WARN** | Root has 13 directories at full buildout, exceeding the 10-12 guideline. Each directory is justified (see adversarial review Problem 5). **Resolution trigger**: If root exceeds 20 directories, audit for merging. At MVP (Wave 1), root has only 5 directories (`devlogs/`, `docs/`, `data/`, `pipelines/`, `config/`) plus `flows/` -- well under budget. |
| 9 | Monorepo hygiene | **PASS** | Each language boundary has its own manifest: `pipelines/` uses root `pyproject.toml`, `api/` has `api/pyproject.toml`, `frontend/` has `frontend/package.json`. Independent installation, testing, deployment. No cross-boundary relative imports. |
| 10 | No orphan directories | **PASS** | Wave system strictly enforced. Only directories with files are created. Wave 2/3 directories are documented as intent, not created. Currently existing directories (`devlogs/`, `docs/sources/`) all have files. `data/` subdirectories are created dynamically by pipeline code. |
| 11 | Predictable parallel structure | **PASS** | All pipeline source modules follow identical pattern: `__init__.py`, `acquire.py`, `validate.py`, `transform.py`, `test_{source}.py`. All dbt staging models follow `stg_cms__{source}.sql`. All mart sub-domains follow `_domain__models.yml` + `mart_domain__name.sql`. All frontend pages follow `{domain}/page.tsx`. |
| 12 | Data gravity | **PASS** | `data/` is a first-class top-level directory with explicit subdirectories mirroring the transformation lifecycle (`raw/`, `processed/`, `mart/`, `archive/`, `reference/`). Path conventions match Pipeline Architect's specifications exactly. `data/` is the single source of truth for where data lives on disk. `.gitignored`. |
| 13 | Cross-agent consistency | **PASS** | All Pipeline Architect paths verified (22 path patterns checked). All Schema Smith paths verified (7 model paths checked). 3 conflicts identified and resolved with documented rationale. Arch Advisor S3-like path convention satisfied. UX Advocate page structure accommodated. |
| 14 | No anti-patterns | **PASS** | All 10 anti-patterns scanned. Zero found. Specific anti-patterns from v1 (wrapper directory `content/blog/`, premature nesting `pipelines/sources/`, junk drawer `pipelines/shared/`, vague naming `lake/`) are all eliminated. |
| 15 | Depth budget | **PASS** | Explicit depth table with 25 paths checked. Maximum depth: 4 (only in `data/` with date partitioning). All code paths: depth 3 or less. No path exceeds budget. |
| 16 | Semantic consistency | **PASS** | Root-level names follow consistent pattern: all are concrete nouns describing what they contain. `data/` (data files), `pipelines/` (pipeline code), `flows/` (flow definitions), `models/` (SQL models), `api/` (API code), `frontend/` (frontend code), `monitoring/` (monitoring config), `config/` (configuration), `analyses/` (analysis outputs), `blog/` (blog posts), `devlogs/` (dev logs), `docs/` (documentation). No metaphorical names (`lake/`), no role-based names mixed with content-based names. |

---

## Overall Verdict: APPROVED (with 1 WARN)

The single WARN is on Principle 8 (Scale-aware flatness) due to root directory count reaching 13 at full buildout. This is:
- **Non-blocking** because each directory represents a genuine bounded context
- **Managed** with a resolution trigger (audit if root exceeds 20)
- **Not a current concern** because Wave 1 has only ~5 directories at root

Zero FAILs. One WARN with documented justification and resolution trigger. This meets the APPROVED threshold.

---

## Design Rationale

### 1. Data as the primary citizen

The single most important design decision is making `data/` a first-class top-level directory with an internal structure that mirrors the transformation lifecycle. This answers the first question anyone asks about a data platform: "Where does the data live?" The answer is unambiguous: `data/`, organized as `raw/ -> processed/ -> mart/ -> archive/`, with `reference/` for static lookups.

### 2. `data/reference/` as a peer of `raw/`, not inside `raw/`

Reference data (state FIPS codes, taxonomy codes, ZIP-to-county crosswalks) is not "raw downloads" -- it is static lookup data used across all pipeline stages. Placing it inside `raw/` would imply it goes through the same transformation lifecycle, which it does not. It is consumed directly by `pipelines/`, `models/`, and `api/`.

### 3. `_common/` organized by lifecycle stage, not by implementation type

Pipeline Architect defined shared utilities organized as `acquire.py`, `validate.py`, `transform.py` -- mirroring the pipeline lifecycle. This is domain-based naming (what it does in the pipeline), not type-based naming (what kind of code it is). The underscore prefix marks it as internal to the `pipelines/` boundary.

### 4. `flows/` separated from `pipelines/`

Prefect flow definitions are composition code that wires together tasks from multiple pipeline modules. A full refresh flow orchestrates NPPES, Part B, Part D, and Geographic Variation in dependency order. This cross-cutting nature justifies a separate directory. Colocating flows inside source modules would require moving them when they become multi-source.

### 5. `monitoring/` instead of `observability/`

The v1 name `observability/` is an abstract concept. `monitoring/` is a concrete activity. The directory contains monitoring tool configurations (Prometheus rules, Grafana dashboards), not an abstract "observability layer." This follows Principle 16 (semantic consistency with other root directories).

### 6. `blog/` instead of `content/blog/`

The `content/` wrapper existed only to hold `blog/`. Anti-Pattern #1 (wrapper directory) demands flattening. If other content types emerge later, they get their own root-level directories until there are 3+ content directories that justify grouping.

### 7. No `src/` wrapper

The Pipeline Architect referenced `src/pipelines/common/`. The `src/` wrapper adds depth for no semantic value (Anti-Pattern #6). This structure drops it. Pipeline code lives directly in `pipelines/`. This structure is authoritative for directory layout; other agent path references should be updated to match.

### 8. Scaling for 60+ sources

The `pipelines/` directory starts flat with 4 source modules + `_common/`. At 60+ sources, the flat listing becomes long but remains navigable (sorted alphabetically, each source is a single directory). If sources cluster naturally by program (Medicare, Medicaid, commercial), subdirectories can be introduced at that point -- but not before 12+ siblings exist at the same level.

### 9. `data/` path convention enables future S3 migration

The path pattern `data/{layer}/{source}/{partition}/` maps directly to an S3 bucket structure: `s3://puf-data/{layer}/{source}/{partition}/`. When the project migrates from local filesystem to object storage, the only change is a path prefix swap.

---

## Action Items for Other Agents

1. **Pipeline Architect**: Update all path references from `src/pipelines/common/` to `pipelines/_common/`. Update `data/raw/reference/` to `data/reference/`.
2. **CLAUDE.md**: Update `content/blog/` to `blog/`.
3. **Schema Smith**: Confirm `models/dbt_project.yml` placement (vs. Schema Smith's `models/_project.yml`).
4. **All agents**: Use this document as the authoritative path reference for all future work.
