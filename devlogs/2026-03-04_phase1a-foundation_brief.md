# Phase 1a: Foundation Infrastructure — Brief

**Date**: 2026-03-04
**Task**: Build production-grade foundation for 45 public healthcare data sources
**Status**: IN PROGRESS

## Context

All seven subagent reviews are complete. Phase 1 is scoped to 45 fully public data sources. This brief covers Phase 1a — the foundation layer that everything else builds on.

## Scope

- `pyproject.toml` with all Phase 1 Python dependencies
- `.gitignore` for data artifacts, secrets, IDE files
- `Makefile` with common developer commands
- `config/` — sources.yaml, database.yaml, pipeline.yaml
- `config/docker-compose.yml` — PostgreSQL 16, PgBouncer, Prefect Server/Worker
- `pipelines/alembic/` — 4 migrations (schemas, roles, catalog, metadata)
- `pipelines/_common/` — acquire, validate, transform, logging, config, db utilities
- `tests/` — conftest.py + unit tests for _common modules

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Python packaging | pyproject.toml (PEP 621) | Modern standard, no setup.py needed |
| Dependency management | pip + venv (no Poetry) | Simpler, Arch Advisor approved |
| Migration tool | Alembic | Arch Advisor approved, dbt handles staging/int/mart DDL |
| Migration scope | schemas + roles + catalog + metadata only | dbt owns staging/intermediate/mart tables |
| Test framework | pytest | Industry standard |
| Docker network | Single bridge network | All services communicate internally |
| PgBouncer | Transaction pooling mode | Prefect + dbt + API all need connection pooling |

## Approach

1. Create project skeleton files (pyproject.toml, .gitignore, Makefile)
2. Create configuration files with all 45 source definitions
3. Create Docker Compose with all infrastructure services
4. Create Alembic migrations for database schema
5. Create shared pipeline utilities
6. Create test infrastructure
7. Verify: docker compose up, alembic upgrade head, pytest

## Risks

| Risk | Mitigation |
|------|-----------|
| Docker Compose not testable in this environment | Write correct config; user runs `docker compose up` to verify |
| Alembic role creation may need superuser | Migration 002 includes IF NOT EXISTS guards |
| Large config file for 45 sources | Group by category, document inline |

## Success Criteria

- [ ] All files created and internally consistent
- [ ] `docker compose up` would start all services (user verification)
- [ ] `alembic upgrade head` would create 7 schemas, 4 roles, 9 tables
- [ ] `pytest` would pass all unit tests
- [ ] Prefect UI accessible at :4200
- [ ] PostgreSQL accessible via PgBouncer at :6432
