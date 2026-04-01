# Brief: PUF Foundation Sprint — Data Source Research + Architecture + Structure
Date: 2026-03-03
Status: Planning

## Context
- Project PUF is greenfield — no code, no pipelines, no models, no tech stack selected
- The MVP roadmap starts with: "Research data dimensions and sources (PUF data sources first)"
- Seven subagents gate the development workflow; three can run independently as Wave 1

## Objective
Complete the foundational research layer that unblocks all downstream development:
1. Comprehensive catalog of major CMS/PUF data sources with relationships, schemas, and regulatory context
2. Approved project directory structure
3. Validated technology stack recommendation

## Thought Process
- The agent dependency chain is: Domain Scholar → Pipeline Architect → Schema Smith → UX Advocate → Insight Engine
- Structure Sentinel and Arch Advisor have no upstream dependencies — they can run parallel to Domain Scholar
- Launching all three as Wave 1 maximizes throughput without violating critical path constraints
- Wave 2 (Pipeline Architect, Schema Smith) is blocked until Wave 1 completes
- Wave 3 (UX Advocate, Insight Engine) is blocked until Wave 2 completes

## Decisions
| Decision | Chosen Option | Rationale | Alternatives Rejected |
|----------|--------------|-----------|----------------------|
| Which PUF sources first | Major CMS Medicare PUFs | Largest, most well-documented, most joined | Medicaid (fewer PUFs), AHRQ (different ecosystem) |
| Parallelization strategy | Wave-based (3 waves) | Respects agent dependencies while maximizing throughput | Sequential (too slow), Full parallel (violates dependencies) |
| Scope of Wave 1 | Research only, no code | Per workflow rules: understand domain before pipeline/model design | Prototype pipelines (premature without domain understanding) |

## Approach
### Wave 1 (Parallel — no dependencies)
- **Domain Scholar**: Research and catalog 8–12 major CMS PUF data sources. Produce knowledge base entries in `docs/sources/`. Map join relationships, regulatory context, update cadences, and data quality notes.
- **Structure Sentinel**: Design the full project directory structure for all planned components (pipelines, models, serving, frontend, observability, config, docs). Evaluate against 11 structural principles.
- **Arch Advisor**: Recommend the initial technology stack for all layers (ingestion, database, catalog, lake, observability, backend, frontend, infrastructure). Verify recommendations via web search for current maintenance status.

### Wave 2 (Blocked by Wave 1)
- **Pipeline Architect**: Design 7-stage lifecycle plans per data source using Domain Scholar output
- **Schema Smith**: Design 3-layer data models (staging → intermediate → mart) using Domain Scholar + Pipeline Architect output

### Wave 3 (Blocked by Wave 2)
- **UX Advocate**: Define frontend data contracts and upstream requirements
- **Insight Engine**: Identify initial analyses and replication opportunities

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| CMS data source URLs/schemas have changed since last knowledge update | HIGH | MEDIUM | Agents use WebSearch to verify current state |
| Domain Scholar scope too broad (too many sources) | MEDIUM | LOW | Cap at 8–12 major PUFs for MVP |
| Arch Advisor recommends tools that are deprecated | MEDIUM | MEDIUM | Mandatory web search verification before recommendation |
| Structure Sentinel over-engineers initial layout | LOW | LOW | Scale-aware flatness principle should prevent this |

## Success Criteria
- [ ] 8+ PUF data source knowledge base entries in `docs/sources/` with verified URLs and schemas
- [ ] Relationship map showing join keys between data sources
- [ ] Directory structure proposal with APPROVED verdict from Structure Sentinel
- [ ] Technology stack recommendation with verdicts per component from Arch Advisor
- [ ] All Wave 1 outputs appended to this brief under their respective sections

## Open Questions
- Which specific PUF sources to prioritize for MVP? (Domain Scholar will recommend based on research)
- Should the tech stack be validated against the Windows development environment? (User runs Windows 11)
