# Product Backlog — 5 Analytical Domains

**Issued by**: Grace Park (Product Lead)
**Date**: 2026-04-02
**Aligned to**: CTO Directive 2026-04-02

---

## Domain Priorities

| # | Domain | Priority | Effort | Status |
|---|--------|----------|--------|--------|
| 1 | UniProvDB (SCD provider history) | P0 | 3d | **COMPLETE** (2026-04-02) |
| 2 | Population Analytics (public aggregates) | P1 | 4d | Planned |
| 3 | Provider Profiles+ (quality + cost overlay) | P0 | 4d | **COMPLETE** (2026-04-02) |
| 4 | Procedure Analytics (HCPCS-level marts) | P0 | 3d | **COMPLETE** (2026-04-02) |
| 5 | County Geography (sub-state variation) | P1 | 2d | Planned |

## Key Decision: Beneficiary Data Scope

Individual-level MBSF/CCW data requires ResDAC DUA — NOT available as public data.
Reframed as "Population Analytics" using public aggregates from Geographic Variation + MA Enrollment.
This delivers ~80% of analytical value at population level.

## Build Order

Phase 2A (parallel): UniProvDB SCD + Procedure Marts + Provider Profiles+
Phase 2B (sequential): County Geography + Population Analytics
Phase 3 (future): Individual beneficiary data if DUA obtained

## Killer Feature Target

Part B (cost) + Inpatient (hospital) + Five-Star (quality) + Cost Reports (margins)
All joined on CCN/NPI → "Which hospitals cost the most AND deliver the worst outcomes?"
Estimated: ~2 weeks from today
