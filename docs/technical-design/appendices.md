# Appendices

[← Back to Index](index.md) | [← Source Inventory](12-source-inventory.md)

---

## A. Directory Structure

```
project_puf/
├── api/                          # FastAPI backend
│   ├── main.py                   # App factory, CORS, router registration
│   ├── routes/                   # 10 route modules (+ health)
│   │   ├── catalog.py
│   │   ├── drugs.py
│   │   ├── geographic.py
│   │   ├── health.py
│   │   ├── hospitals.py
│   │   ├── national.py
│   │   ├── opioid.py
│   │   ├── postacute.py
│   │   ├── providers.py
│   │   └── specialties.py
│   ├── schemas/                  # Pydantic response models (9 modules)
│   └── services/
│       └── database.py           # Dual-engine query routing
│
├── config/                       # Centralized configuration
│   ├── docker-compose.yml        # 6-service Docker stack
│   ├── database.yaml             # Schemas, RBAC roles, DuckDB paths
│   ├── pipeline.yaml             # Acquisition, validation, transform settings
│   ├── sources.yaml              # 48 source definitions
│   └── Dockerfile.api            # API container build
│
├── data/                         # ALL data artifacts (.gitignored)
│   ├── raw/                      # Downloaded source files
│   ├── processed/                # Parquet files
│   ├── mart/                     # Mart-layer Parquet exports
│   ├── archive/                  # Historical snapshots
│   └── reference/                # Reference data files
│
├── devlogs/                      # Planning briefs and retrospectives
│
├── docs/                         # Documentation
│   ├── sources/                  # Per-source knowledge base
│   └── technical-design/         # This catalog (13 D2 diagrams + 14 docs)
│
├── flows/                        # Prefect flow definitions (8 flows)
│   ├── reference_flow.py
│   ├── nppes_flow.py
│   ├── pos_flow.py
│   ├── cost_reports_flow.py
│   ├── partb_flow.py
│   ├── partd_flow.py
│   ├── geovar_flow.py
│   └── utilization_flow.py
│
├── frontend/                     # Next.js web UI
│   ├── app/                      # 8 page routes + layout
│   ├── components/               # 4 reusable components
│   └── lib/                      # api.ts, format.ts utilities
│
├── models/                       # dbt SQL models (40 total)
│   ├── dbt_project.yml           # dbt configuration
│   ├── staging/cms/              # 11 staging models
│   ├── intermediate/             # 13 intermediate models
│   └── marts/                    # 16 mart models
│       ├── provider/
│       ├── national/
│       ├── geographic/
│       ├── opioid/
│       ├── hospital/
│       ├── drug/
│       ├── postacute/
│       ├── ma/
│       ├── quality/
│       └── reference/
│
├── monitoring/                   # Prometheus/Grafana config (planned)
│
├── pipelines/                    # Python data pipelines
│   ├── _common/                  # 7 shared modules
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── acquire.py
│   │   ├── validate.py
│   │   ├── transform.py
│   │   ├── db.py
│   │   └── reference.py
│   ├── alembic/                  # Database migrations (10)
│   │   └── versions/
│   └── {source}/                 # 48 source-specific pipeline modules
│
├── tests/                        # pytest test suite (16 files, 258 tests)
│
├── analyses/                     # Completed analyses (Insight Engine)
├── blog/                         # Blog post drafts
├── scripts/                      # Utility scripts
│
├── Makefile                      # 20 development targets
├── pyproject.toml                # Python project config + tool settings
└── CLAUDE.md                     # AI assistant instructions
```

---

## B. Naming Conventions

### Database Tables

| Layer | Pattern | Example |
|-------|---------|---------|
| Reference | `reference.{domain}_{entity}` | `reference.fips_states`, `reference.ndc_directory` |
| Staging | `staging.stg_{source}` | `staging.stg_part_b_utilization` |
| Catalog | `catalog.{entity}` | `catalog.pipeline_runs` |

### dbt Models

| Layer | Pattern | Example |
|-------|---------|---------|
| Staging | `stg_cms__{source}` | `stg_cms__nppes`, `stg_cms__part_b_utilization` |
| Intermediate | `int_{domain}` | `int_providers`, `int_hospital_discharges` |
| Mart | `mart_{domain}__{metric}` | `mart_provider__practice_profile`, `mart_opioid__by_state` |

### API Routes

| Pattern | Example |
|---------|---------|
| `/api/v1/{domain}/{action}` | `/api/v1/providers/by-specialty/{specialty}` |
| `/api/v1/{domain}/{id}` | `/api/v1/providers/{npi}` |
| `/api/v1/{domain}` | `/api/v1/geographic/spending` |

### Files

| Type | Pattern | Example |
|------|---------|---------|
| Pipeline module | `pipelines/{source}/pipeline.py` | `pipelines/nppes/pipeline.py` |
| Flow definition | `flows/{source}_flow.py` | `flows/partb_flow.py` |
| Test file | `tests/test_{module}.py` | `tests/test_nppes_pipeline.py` |
| Frontend page | `frontend/app/{path}/page.tsx` | `frontend/app/providers/page.tsx` |
| Devlog brief | `devlogs/YYYY-MM-DD_{slug}_brief.md` | `devlogs/2026-03-04_structure-sentinel-v2-review.md` |

### Type Standards

| Healthcare Type | Python Type | SQL Type | Width |
|----------------|------------|----------|-------|
| NPI | `str` | `VARCHAR(10)` | 10 digits, zero-padded |
| HCPCS | `str` | `VARCHAR(5)` | 5 characters |
| FIPS State | `str` | `VARCHAR(2)` | 2 digits, zero-padded |
| FIPS County | `str` | `VARCHAR(5)` | 5 digits, zero-padded |
| Money | `Decimal` | `DECIMAL(18,2)` | 18 total, 2 decimal |
| Rate | `Decimal` | `DECIMAL(7,4)` | 7 total, 4 decimal |
| NDC | `str` | `VARCHAR(11)` | 11 digits, normalized |
| CCN | `str` | `VARCHAR(6)` | 6 characters |

---

## C. Healthcare Glossary

| Term | Definition |
|------|-----------|
| **APC** | Ambulatory Payment Classification — grouping for outpatient services |
| **ASP** | Average Sales Price — CMS drug pricing benchmark |
| **CAHPS** | Consumer Assessment of Healthcare Providers and Systems — patient experience survey |
| **CBSA** | Core-Based Statistical Area — metro/micro area geography |
| **CCN** | CMS Certification Number — unique facility identifier |
| **CLFS** | Clinical Laboratory Fee Schedule |
| **CMI** | Case Mix Index — average DRG weight reflecting patient acuity |
| **CMS** | Centers for Medicare & Medicaid Services |
| **DMEPOS** | Durable Medical Equipment, Prosthetics, Orthotics, and Supplies |
| **DRG** | Diagnosis Related Group — inpatient payment classification |
| **FIPS** | Federal Information Processing Standards — geographic codes |
| **HCPCS** | Healthcare Common Procedure Coding System |
| **HCRIS** | Healthcare Cost Report Information System |
| **HHA** | Home Health Agency |
| **HRR** | Hospital Referral Region — Dartmouth Atlas geography |
| **HSA** | Health Service Area — Dartmouth Atlas geography |
| **ICD-10-CM** | International Classification of Diseases, 10th Revision, Clinical Modification |
| **ICD-10-PCS** | International Classification of Diseases, 10th Revision, Procedure Coding System |
| **IPPS** | Inpatient Prospective Payment System |
| **MA** | Medicare Advantage (Medicare Part C) |
| **MS-DRG** | Medicare Severity Diagnosis Related Group |
| **NDC** | National Drug Code — 11-digit drug product identifier |
| **NLM** | National Library of Medicine |
| **NPI** | National Provider Identifier — 10-digit unique provider number |
| **NPPES** | National Plan and Provider Enumeration System |
| **NUCC** | National Uniform Claim Committee |
| **PBJ** | Payroll-Based Journal — CMS staffing reporting system |
| **PDPM** | Patient-Driven Payment Model — SNF payment system |
| **PECOS** | Provider Enrollment, Chain, and Ownership System |
| **POS** | Place of Service (codes) or Provider of Services (file) |
| **PPS** | Prospective Payment System |
| **PUF** | Public Use File |
| **RUCA** | Rural-Urban Commuting Area |
| **RVU** | Relative Value Unit — physician fee schedule component |
| **SDUD** | State Drug Utilization Data (Medicaid) |
| **SNF** | Skilled Nursing Facility |
