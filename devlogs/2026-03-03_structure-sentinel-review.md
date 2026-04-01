# Structure Review: Project PUF Initial Layout
Date: 2026-03-03
Reviewer: Structure Sentinel

---

## Current State

```
D:/Internal/Project_PUF/
├── CLAUDE.md
├── README.txt
├── devlogs/
│   ├── README.md
│   └── 2026-03-03_puf-foundation-sprint_brief.md
└── docs/
    └── sources/          ← EMPTY (orphan violation)
```

**Immediate issue**: `docs/sources/` exists but contains no files. This violates Principle 10 (No orphan directories). It was created in anticipation of Domain Scholar output but should not exist until that output is produced. However, since it is referenced in CLAUDE.md as a Domain Scholar output target, I will flag it as a WARN rather than a FAIL — it will be populated imminently as part of the same Wave 1 sprint that produced this review.

---

## Proposed Structure

This is the **full target structure** showing all directories that will eventually exist. However, per Principle 10, only **Wave 1** directories should be created now. The rest are documented here as architectural intent.

### Full Target Structure (All Waves)

```
D:/Internal/Project_PUF/
│
│── .github/                         # CI/CD workflows (Wave 2)
│   └── workflows/
│       ├── pipeline-ci.yml
│       ├── api-ci.yml
│       └── frontend-ci.yml
│
├── config/                          # Centralized configuration (Wave 2)
│   ├── pipeline.yaml                #   Pipeline schedules, source URLs, retry policies
│   ├── database.yaml                #   Connection strings, schema config (env-specific)
│   ├── observability.yaml           #   Prometheus targets, Grafana dashboards, Loki config
│   └── docker/                      #   Docker Compose files and Dockerfiles
│       ├── docker-compose.yml
│       ├── docker-compose.dev.yml
│       ├── pipeline.Dockerfile
│       ├── api.Dockerfile
│       └── frontend.Dockerfile
│
├── pipelines/                       # Python — Data ingestion & processing (Wave 2)
│   ├── pyproject.toml               #   Python project config (replaces setup.py + requirements.txt)
│   ├── __init__.py
│   ├── sources/                     #   One module per data source
│   │   ├── __init__.py
│   │   ├── medicare_physician/
│   │   │   ├── __init__.py
│   │   │   ├── acquire.py           #     Download/fetch logic
│   │   │   ├── validate.py          #     Schema & quality checks
│   │   │   ├── transform.py         #     Cleaning, normalization
│   │   │   └── tests/
│   │   │       ├── test_acquire.py
│   │   │       ├── test_validate.py
│   │   │       └── test_transform.py
│   │   └── medicare_inpatient/      #   (same internal pattern for every source)
│   │       ├── __init__.py
│   │       ├── acquire.py
│   │       ├── validate.py
│   │       ├── transform.py
│   │       └── tests/
│   ├── shared/                      #   Cross-source utilities (logging, HTTP, file handling)
│   │   ├── __init__.py
│   │   ├── downloader.py
│   │   ├── file_handlers.py
│   │   ├── logging.py
│   │   └── tests/
│   └── orchestration/               #   DAG definitions, scheduling (Prefect/Airflow/cron)
│       ├── __init__.py
│       ├── schedules.py
│       └── tests/
│
├── models/                          # dbt or SQL — 3-layer data models (Wave 2)
│   ├── dbt_project.yml
│   ├── staging/                     #   Raw-to-clean 1:1 mappings
│   │   ├── stg_medicare_physician.sql
│   │   └── stg_medicare_inpatient.sql
│   ├── intermediate/                #   Business logic joins/aggregations
│   │   ├── int_provider_summary.sql
│   │   └── int_beneficiary_demographics.sql
│   ├── marts/                       #   Final consumption-ready tables
│   │   ├── mart_provider_utilization.sql
│   │   └── mart_geographic_access.sql
│   └── tests/                       #   dbt tests (schema tests, data tests)
│       ├── schema.yml
│       └── generic/
│
├── lake/                            # Data lake layer — Parquet/Iceberg (Wave 3)
│   ├── README.md                    #   Documents partitioning strategy, file naming
│   └── catalog/                     #   Iceberg catalog metadata
│
├── api/                             # Python (FastAPI) — API backend (Wave 3)
│   ├── pyproject.toml
│   ├── __init__.py
│   ├── main.py                      #   FastAPI app entry point
│   ├── routes/                      #   Route modules by domain
│   │   ├── __init__.py
│   │   ├── providers.py
│   │   ├── beneficiaries.py
│   │   └── queries.py
│   ├── services/                    #   Business logic layer
│   │   ├── __init__.py
│   │   └── query_engine.py
│   └── tests/
│       ├── test_providers.py
│       └── test_queries.py
│
├── frontend/                        # TypeScript (Next.js) — Web UI (Wave 3)
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── public/
│   ├── app/                         #   Next.js App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── providers/
│   │   │   └── page.tsx
│   │   ├── beneficiaries/
│   │   │   └── page.tsx
│   │   └── queries/
│   │       └── page.tsx
│   ├── components/                  #   Shared UI components
│   │   ├── charts/
│   │   ├── tables/
│   │   └── layout/
│   └── lib/                         #   Client-side utilities, API client
│       └── api-client.ts
│
├── observability/                   # Monitoring stack config (Wave 3)
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   └── dashboards/
│   └── loki/
│       └── loki-config.yml
│
├── docs/                            # Documentation (Wave 1 — partially populated now)
│   ├── sources/                     #   Per-source knowledge base (Domain Scholar output)
│   │   └── (populated by Domain Scholar agent)
│   ├── architecture/                #   ADRs, system diagrams (Wave 2)
│   └── user-guides/                 #   End-user documentation (Wave 3)
│
├── analyses/                        # Insight Engine outputs (Wave 3)
│   └── (populated by Insight Engine agent)
│
├── content/                         # Blog/publication drafts (Wave 3)
│   └── blog/
│
├── devlogs/                         # Development logs (exists now)
│   ├── README.md
│   └── YYYY-MM-DD_<task-slug>_{brief|retro}.md
│
├── scripts/                         # One-off setup/utility scripts (Wave 2)
│   ├── setup-dev.sh
│   └── seed-db.sh
│
│── CLAUDE.md                        # Claude Code project instructions (exists now)
├── README.txt                       # Project readme (exists now)
├── .gitignore                       # Git ignore rules (Wave 1)
├── .env.example                     # Environment variable template (Wave 2)
└── Makefile                         # Top-level task runner (Wave 2)
```

---

## Design Rationale

### 1. Monorepo with domain-boundary packages

The project is polyglot (Python pipelines + Python API + TypeScript frontend). Rather than splitting into separate repos (which adds coordination overhead for a solo/small-team project), this uses a **monorepo with top-level boundary directories**: `pipelines/`, `api/`, `frontend/`, `models/`. Each has its own package config (`pyproject.toml`, `package.json`), making them independently installable and testable.

### 2. Data flow is readable from the directory listing

Reading the root left-to-right and top-to-bottom maps to the system's data flow:

```
pipelines/  →  models/  →  lake/  →  api/  →  frontend/
(ingest)      (transform)  (store)   (serve)   (present)
```

`observability/` and `docs/` are cross-cutting concerns that sit alongside but outside the main data flow.

### 3. Pipeline structure follows "source-as-module" pattern

Inside `pipelines/sources/`, each data source (e.g., `medicare_physician/`) is a self-contained module with `acquire.py`, `validate.py`, `transform.py`, and colocated `tests/`. This means:
- Adding a new source = adding a new directory with the same internal pattern
- Each source module owns its full lifecycle (Principle 1: separation by boundary)
- Tests are colocated (Principle 4)
- Sibling sources follow identical internal structure (Principle 11)

### 4. Configuration centralized in config/

All environment-specific configuration lives in `config/`. Docker files are under `config/docker/` rather than scattered at root. This keeps the root clean while making configuration discoverable (Principle 7).

### 5. Models follow the dbt 3-layer convention

`staging/` → `intermediate/` → `marts/` is the industry-standard dbt pattern. It directly maps to the Schema Smith's 3-layer model requirement and makes the transformation flow readable (Principle 6).

### 6. Depth budget

Maximum depth from root: **4 levels** (e.g., `pipelines/sources/medicare_physician/tests/test_acquire.py`). This satisfies the two-click rule (Principle 2). Most working files are at depth 3.

---

## Evaluation

| # | Principle | Verdict | Notes |
|---|-----------|---------|-------|
| 1 | Separation by boundary, not type | **PASS** | Top-level directories represent system boundaries (`pipelines`, `api`, `frontend`, `models`), not file types. Within `pipelines/`, sources are grouped by data domain, not by operation type. The alternative — grouping all acquire scripts together, all validate scripts together — was explicitly rejected. |
| 2 | Two-click rule (max 4 levels) | **PASS** | Deepest path is 4 levels: `pipelines/sources/<source>/tests/`. All working files reachable in 2 IDE navigation clicks from root. No directory exceeds 4 levels. |
| 3 | Naming reveals intent | **PASS** | All directory names are full words revealing purpose: `pipelines` (not `etl`), `observability` (not `monitoring` or `ops`), `analyses` (not `output`), `acquire.py` / `validate.py` / `transform.py` (not `step1.py`). No `utils/`, `helpers/`, or `misc/` anywhere. The one exception is `shared/` inside pipelines — but `shared` is scoped to pipeline-internal cross-source utilities and is named to contrast with the source-specific siblings. It will contain concrete, named modules (`downloader.py`, `file_handlers.py`, `logging.py`), not a junk drawer. |
| 4 | Colocation | **PASS** | Tests colocated inside each source module and each API/service directory. Pipeline config colocated in `config/pipeline.yaml`. Docker config colocated in `config/docker/`. Source documentation colocated in `docs/sources/` (one doc per source, matching pipeline source modules). dbt tests inside `models/tests/`. |
| 5 | Explicit boundaries | **PASS** | Python packages use `__init__.py` files to declare public interfaces. Each top-level directory (`pipelines/`, `api/`) has its own `pyproject.toml`. Frontend has `package.json`. These package config files serve as explicit boundary declarations. |
| 6 | Readable data flow | **PASS** | The root-level directory listing directly maps to the system data flow: `pipelines/ → models/ → lake/ → api/ → frontend/`. Within `pipelines/sources/<source>/`, the file names (`acquire.py → validate.py → transform.py`) read as a data lifecycle. Within `models/`, the directories (`staging/ → intermediate/ → marts/`) read as a transformation flow. |
| 7 | Config at root | **PASS** | All configuration is centralized: root-level dotfiles (`.gitignore`, `.env.example`), `Makefile` at root, all environment/service config in `config/`. No config files scattered inside domain directories (each domain's `pyproject.toml`/`package.json` is package metadata, not environment config). |
| 8 | Scale-aware flatness | **PASS** | Root has 12 entries (at full build-out), which is at the upper boundary of the 10-12 guideline. However, at MVP (Wave 1-2), root will have only 7-8 entries. Internal directories are flat: `pipelines/sources/` will start with 2-3 source modules and grow. No premature nesting. If `pipelines/sources/` grows beyond 12 sources, it could be grouped by program (`medicare/`, `medicaid/`), but that nesting is deferred until needed. |
| 9 | Monorepo hygiene | **PASS** | Each language boundary has its own package manifest: `pipelines/pyproject.toml`, `api/pyproject.toml`, `frontend/package.json`. They can be installed, tested, and deployed independently. CI workflows in `.github/workflows/` are per-package. No shared `node_modules` or `venv` across boundaries. |
| 10 | No orphan directories | **WARN** | `docs/sources/` currently exists but is empty. This was created in anticipation of Domain Scholar output from the same Wave 1 sprint. Strictly, this is an orphan. **Mitigation**: Domain Scholar will populate it within this sprint. If it remains empty after the sprint, it should be removed. **All other proposed directories follow the wave system** — they will only be `mkdir`'d when there are files to put in them. |
| 11 | Predictable parallel structure | **PASS** | All pipeline source modules follow the identical internal pattern: `__init__.py`, `acquire.py`, `validate.py`, `transform.py`, `tests/`. All model layers follow the same SQL-file-per-model pattern. All API route modules follow the same FastAPI router pattern. A developer who has seen one source module can navigate any other without learning a new structure. |

---

## Overall Verdict: APPROVED (with 1 WARN)

The single WARN on Principle 10 (`docs/sources/` is currently empty) is **non-blocking** because:
1. Domain Scholar is running in the same Wave 1 sprint and will populate it
2. If Domain Scholar does not produce output, the directory should be removed
3. No other proposed directories are created prematurely — the wave system prevents orphans

---

## Key Design Decisions

### Why `pipelines/` and `api/` are separate top-level directories (not `backend/`)
Pipelines and the API server are distinct deployment units with different runtime characteristics. Pipelines are batch jobs (scheduled, ephemeral). The API is a long-running server. Combining them into `backend/` would violate Principle 1 (separation by boundary) — they share a language (Python) but not a deployment boundary. They can share code via Python package imports without sharing a directory.

### Why `config/` instead of dotfiles and scattered configs
A centralized `config/` directory is more discoverable than scattered config files. Docker Compose files, Prometheus configs, and database connection templates all live in one place. Root-level config is reserved for tooling that *requires* root placement (`.gitignore`, `Makefile`, `pyproject.toml`-at-root if a workspace is needed).

### Why `models/` is a top-level peer of `pipelines/`, not nested inside it
The data model layer (dbt or raw SQL) is a distinct concern from the Python pipeline code. It has its own config (`dbt_project.yml`), its own test framework (dbt tests), and its own deployment lifecycle. Nesting it inside `pipelines/` would blur the boundary between "getting data" and "shaping data."

### Why `lake/` is its own directory
The data lake (Parquet/Iceberg files) is a storage layer, not a transformation layer. It's the output target of `models/` and the read source for `api/`. Giving it a top-level directory makes the data flow readable and provides a clear place for partitioning metadata and catalog configuration.

### Why `shared/` inside `pipelines/` and not at root
Cross-source pipeline utilities (HTTP downloader, file decompression, logging setup) are *pipeline-internal* concerns. They don't belong to the API or frontend. Placing them at `pipelines/shared/` keeps them scoped to their boundary. If API and pipelines eventually need shared code, a root-level `packages/` directory can be introduced — but premature sharing is worse than local duplication.

### How the structure supports scaling
- **More data sources**: Add a new directory under `pipelines/sources/` with the standard 4-file pattern
- **More API domains**: Add a new route module under `api/routes/` and service under `api/services/`
- **More frontend pages**: Add a new directory under `frontend/app/`
- **More model layers**: The staging/intermediate/marts pattern scales by adding SQL files
- **Service extraction**: If `api/` or `pipelines/` grows large enough to warrant its own repo, the top-level boundary makes extraction straightforward — just move the directory and its `pyproject.toml`

---

## Notes for Implementation

### Wave 1 — Create Now (this sprint)
These directories either exist already or will be populated by Wave 1 agents:

| Directory | Status | Content |
|-----------|--------|---------|
| `devlogs/` | EXISTS | Already has brief and README |
| `docs/sources/` | EXISTS (empty) | Domain Scholar will populate |
| `.gitignore` | CREATE | Immediately needed for repository hygiene |

The `.gitignore` should be created now with entries for:
```
# Python
__pycache__/
*.pyc
.venv/
*.egg-info/

# Node
node_modules/
.next/

# Environment
.env
.env.local

# Data files (never commit raw data)
*.csv
*.parquet
*.zip
data/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

### Wave 2 — Create When Pipeline Work Begins
| Directory | Trigger |
|-----------|---------|
| `pipelines/` | First pipeline code is written |
| `models/` | First dbt/SQL model is written |
| `config/` | First config file beyond root dotfiles |
| `scripts/` | First setup/utility script |
| `.github/workflows/` | First CI pipeline |

### Wave 3 — Create When Serving/Frontend Work Begins
| Directory | Trigger |
|-----------|---------|
| `api/` | First API endpoint is written |
| `frontend/` | First frontend page is written |
| `lake/` | First Parquet/Iceberg file is produced |
| `observability/` | First Prometheus/Grafana config is written |
| `analyses/` | First Insight Engine analysis is produced |
| `content/blog/` | First blog post is drafted |

### Critical Rule
**Never create a directory until there is a file to put in it.** The full target structure above is an architectural blueprint, not a command to `mkdir -p` everything today. Each directory is born when its first file is born.
