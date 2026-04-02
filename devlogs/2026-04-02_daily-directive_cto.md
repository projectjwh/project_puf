# Daily Directive — 2026-04-02

**Issued by**: Marcus Chen (CTO)
**Status**: Active

---

## State Assessment

| Metric | Value | Health |
|--------|-------|--------|
| Tests | 308 passed, 2 skipped | GREEN |
| Lint | 0 errors | GREEN |
| Typecheck | 0 errors | GREEN |
| Commits (Phase 2) | 7 (Sprints 0-3 + CI fix + README + agents) | ON TRACK |
| Git | Initialized, CI live, remote synced | GREEN |

**Phase 2 completed**: Sprint 0 (Git+CI), Sprint 1 (Validation persistence), Sprint 2 (Acquire hardening), Sprint 3 (Run tracking)
**Phase 2 remaining**: Sprint 4 (Orchestration), Sprint 5 (Data contracts), Sprint 6 (Baselines), Sprint 7 (Integration tests)

### Hard Gate Status

| Gate | Before Phase 2 | Now | Next Action |
|------|---------------|-----|-------------|
| 1: Data Contracts | Not started | Not started | Sprint 5 — schema versioning per source |
| 2: Quality Rules | Passing | ENHANCED | Persistence + quarantine wired |
| 3: Security Review | Advisory/light | No change | Public data — low risk |
| 4: Observability | Not started | PARTIAL | Catalog data exists; dashboards Phase 3 |
| 5: Metadata | Not started | PASSING | catalog.sources seeded, freshness tracked |
| 6: Deployment | Advisory/local | ENHANCED | CI/CD live on GitHub Actions |
| 7: Reliability | Advisory | PARTIAL | Retry + catalog tracking; no chaos tests |

---

## Theme

Ship orchestration and data contracts in parallel — these are the two remaining blockers to production readiness.

---

## Priorities (ranked)

1. **Sprint 4: Prefect deployment registration + dbt wrapper**
   - Assign: @platform-engineer (Sana) + @pipeline-engineer (Nikolai)
   - Success: `prefect deployment ls` shows 8 deployments with cron schedules; dbt failures classified in catalog.pipeline_failures
   - Blocked by: none

2. **Sprint 5: Data contracts for Tier 1 sources**
   - Assign: @data-modeler (Tomas) + @data-quality (Elena)
   - Success: 6 contract YAMLs in `config/contracts/`, `validate_against_contract()` wired into pipelines, contract alignment tests pass
   - Blocked by: none (parallel with Sprint 4)

3. **Red Team review of Sprints 0-3**
   - Assign: @red-team (Yuki)
   - Success: Challenge report covering all Phase 2 code shipped so far. Every CRITICAL finding addressed before Sprint 6.
   - Blocked by: none

4. **QA Gate audit of current codebase**
   - Assign: @qa-gate (Mei-Lin)
   - Success: 7-point gate checklist run against HEAD. Confirm all Tier 1 pipelines pass all 7 gates.
   - Blocked by: none

5. **Incident Commander failure scenario review**
   - Assign: @incident-commander (Rafael)
   - Success: 5 highest-risk failure scenarios documented with blast radius and current mitigations
   - Blocked by: none

---

## Technical Debt Flagged

- `STATE_ABBREV_TO_FIPS` duplicated in nppes, partb, partd, inpatient — Severity: low — Owner: @pipeline-engineer
- `data_year = year - 2` hardcoded in flows (not using `lag_months` from sources.yaml) — Severity: medium — Owner: @platform-engineer (Sprint 4.4)
- DuckDB configured but unused in API — Severity: low — Owner: @api-engineer (Phase 3)
- No Prefect deployments registered (flows are CLI-only) — Severity: high — Owner: @platform-engineer (Sprint 4)

---

## Decisions Made

- **Sprint 4 and 5 run in parallel** — Rationale: Different teams (infra vs. data modeling), no dependency between them. Challenged by: @red-team — Resolution: pending review
- **Antagonist agents activated today** — Rationale: 3 sprints of code shipped without adversarial review. Red Team, QA Gate, and Incident Commander should audit before we build more.

---

## Backlog Changes

- Promoted: Red Team audit P2 → P0 — Reason: 3 sprints shipped without adversarial review
- Promoted: QA Gate audit P2 → P0 — Reason: need baseline gate report before Sprint 4
- Added: Incident scenario documentation — Reason: no failure scenarios documented for catalog infrastructure
- Deferred: Tier 2 source implementation — Reason: integrity infrastructure must be complete first (Sprints 4-7)
- Deferred: Prometheus/Grafana dashboards — Reason: Phase 3; catalog data is sufficient for now
