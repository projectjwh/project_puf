# Retro: Governance Alignment — Commander + Opstool Integration

**Date**: 2026-04-01

## Outcome

Rewrote CLAUDE.md to replace 7 ad-hoc agent gates with commander/opstool integration. The document went from a "planning phase" placeholder to a comprehensive governance document reflecting Phase 1 completion and Phase 2 direction.

## What Changed

1. **Project status**: Updated from "Greenfield in planning phase" to "Phase 1 complete" with concrete metrics (258 tests, 48 sources, 47 models, etc.)
2. **Agent gates replaced**: 7 unnamed gates (Structure Sentinel, Arch Advisor, etc.) replaced with 12 named commander/opstool agents mapped to specific work types
3. **Skills referenced**: 6 commander skills linked by trigger condition (pipeline-design, data-modeling, observability-setup, incident-response, architecture-decision, code-review)
4. **Hard gates defined**: 7 opstool production readiness gates adapted for Project_PUF context — security and reliability downgraded to ADVISORY (public data, solo dev), quality/contracts/observability/metadata remain HARD
5. **Standards linked**: 6 opstool standards referenced by path
6. **Quick reference added**: Make targets, service URLs, key paths

## What Worked

- **Agent routing table by work type** is more useful than the old gate-per-phase model. Old model: "run Pipeline Architect before pipeline work." New model: "invoke Nikolai for pipeline design, Elena for quality, Oleg for security" — multiple agents collaborate on one task.
- **Adapted hard gates** avoid cargo-culting opstool for a public-data solo project. Security is ADVISORY (not HARD) because there's no PII/PHI. Reliability testing deferred to Phase 3.
- **Referencing by path** instead of copying content prevents drift between CLAUDE.md and commander/opstool definitions.

## What Could Be Better

- **Opstool project directory not created** — should eventually create `../opstool/projects/project_puf/` with brief and knowledge files
- **No automated enforcement** — hard gates are documented but not enforced by hooks or CI. Phase 2 should add pre-commit or CI checks.
- **Insight Engine concept dropped** — the old CLAUDE.md had an "Insight Engine" for tracking CMS/MedPAC publications. No direct commander equivalent. May need a custom skill in commander for this.

## Patterns Discovered

- **Gate severity adaptation**: Not all opstool gates apply at the same severity to every project. Context matters — public data projects need lighter security gates; solo projects need lighter reliability gates. The adaptation framework: keep the gate, adjust the severity, document why.
- **Agent routing > sequential gates**: The old "Domain Scholar -> Pipeline Architect -> Schema Smith -> UX Advocate" sequence was too rigid. Real work needs parallel consultation (Nikolai + Elena + Oleg review a pipeline simultaneously). The routing table enables this.

## Lessons for Commander Evolution

- Consider adding a "gate severity adaptation" section to the project integration template — projects should document which gates are HARD vs ADVISORY for their context, not assume all are HARD.
