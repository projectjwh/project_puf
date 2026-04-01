# Brief: Governance Alignment — Commander + Opstool Integration

**Date**: 2026-04-01
**Task**: Rewrite Project_PUF CLAUDE.md to integrate commander agents and opstool operational standards

## Context

Project_PUF completed Phase 1 (1a-1f) on 2026-03-04 with 258 passing tests, 48 data sources, 47 dbt models, 11 API routes, and 8 frontend pages. The CLAUDE.md still says "Greenfield project in planning phase" and defines 7 ad-hoc agent gates (Structure Sentinel, Arch Advisor, Domain Scholar, Pipeline Architect, Schema Smith, UX Advocate, Insight Engine) that exist only as names — no personas, no challenge protocols, no skill definitions.

Meanwhile, the workspace now has two mature governance frameworks:
- **commander** (v0.3.0): 21 agents with full personas and challenge protocols, 28+ skills with SKILL.md workflow definitions, 5 curated framework references
- **opstool**: 25-agent consulting team with 8 workflows, 10 cross-stream pairs, 5 strategic priorities, 8 operational standards, and formal hard gate definitions

The current CLAUDE.md's governance model is disconnected from both. This creates three problems:
1. Agent gates are unenforceable — no challenge protocols, no approval criteria, no skill workflows
2. No hard gate definitions — quality, security, observability, reliability gates are undefined
3. No link to operational standards — naming, data modeling, pipeline design patterns are not referenced

## Thought Process

| Decision | Option A | Option B | Choice | Why |
|----------|----------|----------|--------|-----|
| Integration depth | Light reference (just link to commander/opstool) | Deep integration (map agents to project work types, list applicable standards) | B | Light reference doesn't change behavior — Claude needs to know which agent to invoke for which situation |
| Agent mapping | 1:1 replacement of old gates | Many-to-many mapping by work type | Many-to-many | Old gates were artificial boundaries. Real work crosses agent domains (e.g., new pipeline needs Nikolai + Elena + Oleg + Lena) |
| Hard gates | Copy opstool gates verbatim | Adapt for Project_PUF context (public data, single dev) | Adapt | Not all 7 gates apply equally — security is lighter for public data, cross-stream pairs don't apply for solo dev |
| CLAUDE.md length | Minimal (< 80 lines) | Comprehensive (100-150 lines) | Comprehensive | This is the primary governance document. Short = skipped steps. But not bloated — every line must change behavior. |
| Opstool project directory | Create `opstool/projects/project_puf/` | Defer | Defer | Focus on CLAUDE.md first. Project directory is a follow-up task. |

## Approach

1. Rewrite CLAUDE.md with these sections:
   - **Project Overview** — Updated description with current metrics
   - **Current Status** — Phase 1 complete, Phase 2 scope
   - **Technology Stack** — Actual decisions made (not "TBD")
   - **Development Workflow** — Keep brief→execute→retro, tie to commander 7-stage lifecycle
   - **Commander Integration** — Agent routing table by work type
   - **Opstool Standards** — Which standards apply, where to find them
   - **Hard Gates** — Adapted from opstool for Project_PUF context
   - **Quick Reference** — Commands, paths, service URLs

2. Map old ad-hoc gates to commander/opstool agents:
   - Structure Sentinel → Aisha Okafor (Data Architect) + Viktor Novak (Solutions Architect)
   - Arch Advisor → Marcus Chen (CTO)
   - Domain Scholar → Camille Dubois (Business Analyst) + docs/sources/
   - Pipeline Architect → Nikolai Petrov (Pipeline Engineer) + pipeline-design skill
   - Schema Smith → Tomas Guerrero (Data Modeler) + Rachel Kim (DB Engineer)
   - UX Advocate → Derek Nakamura (DX) + Lena Osei (UX)
   - Insight Engine → keep as project-specific concept (no direct commander equivalent)

## Risks

| Risk | Mitigation |
|------|-----------|
| CLAUDE.md too long → Claude ignores it | Keep under 150 lines. Every section must change behavior. |
| Over-engineering for single-dev project | Adapt gates to solo context — advisory where opstool says mandatory |
| Commander/opstool drift | Reference by path, not by copying content |

## Success Criteria

- [ ] CLAUDE.md reflects Phase 1 complete status
- [ ] All 7 old ad-hoc gates replaced with commander agent references
- [ ] Hard gates defined with adapted severity for Project_PUF
- [ ] Commander/opstool paths referenced (not content copied)
- [ ] Development workflow connects brief→retro cycle to commander lifecycle
- [ ] Quick reference section enables immediate productivity
