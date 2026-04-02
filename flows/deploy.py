"""Register Prefect deployments for all pipeline flows.

Uses ``prefect.serve()`` to run all 8 flows as long-lived deployments
with cron schedules pulled from ``config/sources.yaml``.  Each deployment
gets tags for concurrency control.

Usage:
    python -m flows.deploy          # Serve all deployments
    make deploy                     # Via Makefile
"""

from __future__ import annotations

from prefect import serve

from flows.cost_reports_flow import cost_reports_acquisition
from flows.geovar_flow import geovar_flow
from flows.nppes_flow import nppes_acquisition
from flows.partb_flow import partb_flow
from flows.partd_flow import partd_flow
from flows.pos_flow import pos_acquisition
from flows.reference_flow import load_reference_data
from flows.utilization_flow import utilization_flow
from pipelines._common.config import get_source

# ---------------------------------------------------------------------------
# Helper: resolve cron schedule from sources.yaml
# ---------------------------------------------------------------------------


def _schedule(short_name: str) -> str | None:
    """Return the cron schedule for *short_name*, or ``None`` if absent."""
    try:
        src = get_source(short_name)
        return src.schedule or None
    except KeyError:
        return None


# ---------------------------------------------------------------------------
# Build deployments
# ---------------------------------------------------------------------------


def build_deployments() -> list:
    """Create ``flow.to_deployment()`` objects for every pipeline flow."""
    deployments = []

    # 1. NPPES — monthly on the 8th
    deployments.append(
        nppes_acquisition.to_deployment(
            name="nppes-monthly",
            cron=_schedule("nppes"),
            tags=["provider-identity", "tier-1"],
        )
    )

    # 2. POS — quarterly on the 15th
    deployments.append(
        pos_acquisition.to_deployment(
            name="pos-quarterly",
            cron=_schedule("pos"),
            tags=["provider-identity", "tier-1"],
        )
    )

    # 3. Part B — annual in June
    deployments.append(
        partb_flow.to_deployment(
            name="partb-annual",
            cron=_schedule("partb"),
            tags=["utilization", "tier-1"],
        )
    )

    # 4. Part D — annual in June
    deployments.append(
        partd_flow.to_deployment(
            name="partd-annual",
            cron=_schedule("partd"),
            tags=["utilization", "tier-1"],
        )
    )

    # 5. GeoVar — annual in July
    deployments.append(
        geovar_flow.to_deployment(
            name="geovar-annual",
            cron=_schedule("geovar"),
            tags=["utilization", "tier-1"],
        )
    )

    # 6. Cost Reports — quarterly
    deployments.append(
        cost_reports_acquisition.to_deployment(
            name="cost-reports-quarterly",
            cron=_schedule("cost_reports"),
            tags=["hospital-financial", "tier-1"],
        )
    )

    # 7. Reference — manual only (covers 14 sub-sources with their own cadences)
    deployments.append(
        load_reference_data.to_deployment(
            name="reference-manual",
            cron=None,
            tags=["reference", "tier-1"],
        )
    )

    # 8. Utilization orchestrator — manual only (coordinates Part B + D + GeoVar + dbt)
    deployments.append(
        utilization_flow.to_deployment(
            name="utilization-full-refresh",
            cron=None,
            tags=["utilization", "orchestrator"],
        )
    )

    return deployments


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    deployments = build_deployments()
    print(f"Serving {len(deployments)} deployments...")
    serve(*deployments)
