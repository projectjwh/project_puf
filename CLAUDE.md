# CLAUDE.md — Project PUF

## Project Overview

**Public Healthcare Data Repository** — interactive platform for accessing, visualizing, and querying publicly available healthcare data across Medicare, Medicaid, State, and Regional sources. 48 public data sources, dual-engine serving (PostgreSQL + DuckDB), FastAPI backend, Next.js 15 frontend.

Key domains: providers, beneficiaries, utilization, geographic variation, hospital finance, drug spending, post-acute care, opioid prescribing, quality ratings.

## Current Status

**Phase 1 complete** (2026-03-04). Delivered:
- 48 data sources configured (`config/sources.yaml`), 45+ pipeline modules
- 47 dbt models (16 staging, 11 intermediate, 20+ marts)
- 12 FastAPI route modules, 32 endpoints
- 8 Next.js pages with 5 shared components
- 12 Alembic migrations, 484 passing tests
- 15 technical design docs, 14 source knowledge base entries
- GitHub Actions CI (lint + typecheck + test + integration)
- 15 subagents (3 executive, 3 antagonist, 9 operational)

**Phase 2 COMPLETE**: Pipeline integrity (7 sprints), analytical domains (UniProvDB SCD, Procedure Analytics, Provider Profiles+), data contracts, Prefect orchestration, statistical baselines, integration tests.

**Phase 2B planned**: Population Analytics (Domain 2), County Geography (Domain 5).

**Phase 3 planned**: Tier 2 source expansion, Prometheus/Grafana dashboards, chaos testing, DuckDB activation.

## Technology Stack

| Layer | Choice | Version |
|-------|--------|---------|
| Orchestration | Prefect | 3.x |
| Database (OLTP) | PostgreSQL | 16 |
| Database (OLAP) | DuckDB | embedded |
| Connection pooling | PgBouncer | transaction mode |
| Transformations | dbt | core |
| API | FastAPI | latest |
| Frontend | Next.js (App Router) | 15 |
| Data format | Parquet (zstd) | — |
| Logging | structlog (JSON) | — |
| Python | 3.12+ | — |

## Development Workflow

Every task follows **Brief -> Execute -> Retro**:

1. **Before coding**: Write brief to `devlogs/YYYY-MM-DD_<task-slug>_brief.md`
2. **During execution**: Append `## Amendments` if plan changes significantly
3. **After completion**: Write retro to `devlogs/YYYY-MM-DD_<task-slug>_retro.md`
4. **After retro**: Promote stable lessons to memory or this document

This maps to the commander 7-stage lifecycle: brief = Think + Plan, execution = Build + Review + Test, retro = Reflect.

## Commander Integration

This project uses agents and skills from `../commander/`.

- **Agents**: Read definitions from `../commander/agents/<category>/<name>.md` before invoking
- **Skills**: Read SKILL.md from `../commander/skills/<category>/<skill-name>/SKILL.md` before executing
- Do NOT modify commander files — changes go through commander only

### Agent Routing by Work Type

| Work Type | Primary Agent(s) | Commander Path | When |
|-----------|-----------------|----------------|------|
| **Architecture decisions** | Marcus Chen (Tech Lead) | `agents/leadership/tech-lead.md` | Tech stack changes, new components, design trade-offs |
| **Data modeling** | Tomas Guerrero (Data Modeler), Rachel Kim (DB Engineer) | `../opstool/agents/s3_operations/` | Schema changes, new dbt models, grain definitions |
| **Pipeline design** | Nikolai Petrov (Pipeline Engineer) | `agents/data/pipeline-engineer.md` | New data sources, ETL changes, orchestration |
| **Data quality** | Elena Vasquez (Data Quality) | `agents/data/data-quality-analyst.md` | Validation rules, statistical baselines, quality gates |
| **Security review** | Oleg Volkov (Security Engineer) | `../opstool/agents/s4_tooling/oleg_volkov.md` | Credential handling, access control, PII/PHI |
| **API + DX** | Derek Nakamura (Software Engineer) | `agents/engineering/software-engineer.md` | API design, CLI, developer experience |
| **Frontend UX** | Lena Osei (UX Advocate) | `agents/analysis/ux-advocate.md` | User-facing features, data visualization |
| **Infrastructure** | Sana Malik (Platform Engineer) | `../opstool/agents/s4_tooling/sana_malik.md` | Docker, deployment, CI/CD |
| **Observability** | Lena Hoffmann (DataOps) | `../opstool/agents/s4_tooling/lena_hoffmann.md` | SLOs, alerts, dashboards, runbooks |
| **Domain research** | Camille Dubois (Business Analyst) | `agents/analysis/business-analyst.md` | New data sources — research domain FIRST, then pipeline |
| **Data governance** | Grace Okonkwo (Governance), Samuel Osei (Metadata) | `../opstool/agents/s3_operations/` | Classification, ownership, retention, catalog |
| **Reliability testing** | Mei-Lin Chang (QA & Reliability) | `../opstool/agents/s4_tooling/mei_lin_chang.md` | Contract tests, load tests, chaos testing |

### Key Skills

| Skill | Path | Trigger |
|-------|------|---------|
| `pipeline-design` | `../commander/skills/data-engineering/pipeline-design/SKILL.md` | Building or modifying any data pipeline |
| `data-modeling` | `../commander/skills/data-engineering/data-modeling/SKILL.md` | Schema changes, new models |
| `observability-setup` | `../commander/skills/data-engineering/observability-setup/SKILL.md` | Deploying new components to production |
| `incident-response` | `../commander/skills/data-engineering/incident-response/SKILL.md` | **MANDATORY** — any pipeline failure or data quality alert |
| `architecture-decision` | `../commander/skills/planning/architecture-decision/SKILL.md` | Tech stack changes, new architectural patterns |
| `code-review` | `../commander/skills/development/code-review/SKILL.md` | Reviewing changes (4-lens: correctness, security, perf, DX) |

### New Data Source Order

When adding a new data source, invoke agents in this sequence:
```
Camille (domain research) -> Nikolai (pipeline design) -> Tomas + Rachel (data model) -> Derek (API) -> Lena H. (observability)
```

## Opstool Standards

This project follows operational standards from `../opstool/knowledge/standards/`:

| Standard | Path | Applies To |
|----------|------|-----------|
| Pipeline design patterns | `standards/pipeline_design_patterns.md` | All 48 pipeline modules |
| Data modeling standards | `standards/data_modeling_standards.md` | All dbt models |
| Naming conventions | `standards/naming_conventions.md` | Tables, columns, files |
| Governance framework | `standards/governance_framework.md` | Data classification, ownership |
| Security standards | `standards/security_standards.md` | Credential handling, access control |
| Incident response SOPs | `standards/incident_response_sops.md` | Production failures |

Templates available at `../opstool/knowledge/templates/` — use `data_contract.md` and `pipeline_design_doc.md` for new pipelines.

## Hard Gates

Adapted from opstool production readiness checklist. Gates marked **HARD** block production deployment. Gates marked **ADVISORY** are recommended but not blocking for this project's public-data context.

| # | Gate | Owner Agent | Severity | What Must Exist |
|---|------|------------|----------|----------------|
| 1 | Data contract | Tomas Guerrero | **HARD** | Versioned producer/consumer contract per `opstool/knowledge/templates/data_contract.md` |
| 2 | Quality rules | Elena Vasquez | **HARD** | Schema + business rule + statistical checks in `validate.py` |
| 3 | Security review | Oleg Volkov | **ADVISORY** | Credential handling reviewed. All data is public — no PII/PHI. Lightweight review acceptable. |
| 4 | Observability | Lena Hoffmann | **HARD** | Metrics, alerts, dashboard spec, SLO definition, runbook |
| 5 | Metadata | Samuel Osei | **HARD** | Catalog entry with owner, SLA, classification label |
| 6 | Deployment | Sana Malik | **ADVISORY** | Container, health checks, rollback strategy. Local Docker Compose is acceptable for MVP. |
| 7 | Reliability | Mei-Lin Chang | **ADVISORY** | Contract tests + load test at 2x volume. Defer chaos testing to Phase 3. |

**Gate 2 (Quality) is the only gate currently passing.** Gates 1, 4, 5 are Phase 2 priorities.

## MVP Principles

- Start with major PUF data sources and small data points
- Scalable architecture from day one
- Strong logging as source of truth
- Minimal UI/UX initially but architecture-ready for future design improvements
- Strong visualization focus

## Quick Reference

### Commands
```bash
make up              # Start all services (Docker Compose)
make down            # Stop all services
make test            # Run pytest (excludes integration)
make test-all        # Run all tests including integration
make lint            # Ruff check
make format          # Ruff format
make typecheck       # MyPy
make migrate         # Run Alembic migrations
make migrate-down    # Revert last migration
make dbt-run         # Run dbt models
make dbt-test        # Run dbt tests
```

### Service URLs (local)
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Prefect UI: http://localhost:4200
- PostgreSQL: localhost:5432
- PgBouncer: localhost:6432

### Key Paths
- Pipeline modules: `pipelines/<source_name>/`
- Shared utilities: `pipelines/_common/`
- dbt models: `models/{staging,intermediate,marts}/`
- API routes: `api/routes/`
- Frontend pages: `frontend/app/`
- Config: `config/{sources,pipeline,database}.yaml`
- Tests: `tests/`
- Devlogs: `devlogs/`
- Source docs: `docs/sources/`
- Technical design: `docs/technical-design/`
