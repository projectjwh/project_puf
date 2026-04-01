"""Prefect flow for loading all Tier 1 reference data.

Orchestrates 14 reference pipeline modules in dependency order:
1. Geographic (no dependencies)
2. Code systems (no dependencies)
3. Fee schedules (HCPCS must exist for RVU joins, DRG for IPPS)

Usage:
    prefect deployment run 'load-reference-data/manual'
    python -m flows.reference_flow  # Direct execution
"""

from datetime import date

from prefect import flow, task
from prefect.futures import wait

from pipelines._common.logging import get_logger, setup_logging

log = get_logger(source="reference_flow")

# ---------------------------------------------------------------------------
# Tasks: one per reference source
# ---------------------------------------------------------------------------


@task(name="load-fips", retries=2, retry_delay_seconds=60)
def load_fips(run_date: date | None = None) -> int:
    from pipelines.fips.pipeline import run
    return run(run_date=run_date)


@task(name="load-taxonomy", retries=2, retry_delay_seconds=60)
def load_taxonomy(run_date: date | None = None) -> int:
    from pipelines.taxonomy.pipeline import run
    return run(run_date=run_date)


@task(name="load-icd10cm", retries=2, retry_delay_seconds=60)
def load_icd10cm(run_date: date | None = None) -> int:
    from pipelines.icd10cm.pipeline import run
    return run(run_date=run_date)


@task(name="load-icd10pcs", retries=2, retry_delay_seconds=60)
def load_icd10pcs(run_date: date | None = None) -> int:
    from pipelines.icd10pcs.pipeline import run
    return run(run_date=run_date)


@task(name="load-hcpcs", retries=2, retry_delay_seconds=60)
def load_hcpcs(run_date: date | None = None) -> int:
    from pipelines.hcpcs.pipeline import run
    return run(run_date=run_date)


@task(name="load-msdrg", retries=2, retry_delay_seconds=60)
def load_msdrg(run_date: date | None = None) -> int:
    from pipelines.msdrg.pipeline import run
    return run(run_date=run_date)


@task(name="load-ndc", retries=2, retry_delay_seconds=60)
def load_ndc(run_date: date | None = None) -> int:
    from pipelines.ndc.pipeline import run
    return run(run_date=run_date)


@task(name="load-pos-codes", retries=2, retry_delay_seconds=60)
def load_pos_codes(run_date: date | None = None) -> int:
    from pipelines.pos_codes.pipeline import run
    return run(run_date=run_date)


@task(name="load-zip-county", retries=2, retry_delay_seconds=60)
def load_zip_county(run_date: date | None = None) -> int:
    from pipelines.zip_county.pipeline import run
    return run(run_date=run_date)


@task(name="load-cbsa", retries=2, retry_delay_seconds=60)
def load_cbsa(run_date: date | None = None) -> int:
    from pipelines.cbsa.pipeline import run
    return run(run_date=run_date)


@task(name="load-ruca", retries=2, retry_delay_seconds=60)
def load_ruca(run_date: date | None = None) -> int:
    from pipelines.ruca.pipeline import run
    return run(run_date=run_date)


@task(name="load-rvu", retries=2, retry_delay_seconds=60)
def load_rvu(run_date: date | None = None) -> int:
    from pipelines.rvu.pipeline import run
    return run(run_date=run_date)


@task(name="load-wage-index", retries=2, retry_delay_seconds=60)
def load_wage_index(run_date: date | None = None) -> int:
    from pipelines.wage_index.pipeline import run
    return run(run_date=run_date)


@task(name="load-ipps", retries=2, retry_delay_seconds=60)
def load_ipps(run_date: date | None = None) -> int:
    from pipelines.ipps.pipeline import run
    return run(run_date=run_date)


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------


@flow(name="load-reference-data", log_prints=True)
def load_reference_data(
    run_date: date | None = None,
    sources: list[str] | None = None,
) -> dict[str, int]:
    """Load all (or selected) Tier 1 reference data sources.

    Args:
        run_date: Override the run date. Defaults to today.
        sources: List of source names to load. Defaults to all 14.

    Returns:
        Dict of source_name → rows_loaded.
    """
    setup_logging()
    run_date = run_date or date.today()

    all_tasks = {
        "fips": load_fips,
        "taxonomy": load_taxonomy,
        "icd10cm": load_icd10cm,
        "icd10pcs": load_icd10pcs,
        "hcpcs": load_hcpcs,
        "msdrg": load_msdrg,
        "ndc": load_ndc,
        "pos_codes": load_pos_codes,
        "zip_county": load_zip_county,
        "cbsa": load_cbsa,
        "ruca": load_ruca,
        "rvu": load_rvu,
        "wage_index": load_wage_index,
        "ipps": load_ipps,
    }

    # Filter to selected sources if specified
    if sources:
        tasks_to_run = {k: v for k, v in all_tasks.items() if k in sources}
    else:
        tasks_to_run = all_tasks

    log.info("reference_flow_start", sources=list(tasks_to_run.keys()), run_date=str(run_date))

    # Phase 1: Geographic + Code systems (no dependencies, run in parallel)
    phase1_names = {"fips", "taxonomy", "icd10cm", "icd10pcs", "hcpcs", "msdrg",
                    "ndc", "pos_codes", "zip_county", "cbsa", "ruca"}
    phase1_tasks = {k: v for k, v in tasks_to_run.items() if k in phase1_names}

    # Phase 2: Fee schedules (depend on HCPCS and DRG existing)
    phase2_names = {"rvu", "wage_index", "ipps"}
    phase2_tasks = {k: v for k, v in tasks_to_run.items() if k in phase2_names}

    results: dict[str, int] = {}

    # Run Phase 1 concurrently
    phase1_futures = {}
    for name, task_fn in phase1_tasks.items():
        phase1_futures[name] = task_fn.submit(run_date=run_date)

    for name, future in phase1_futures.items():
        try:
            results[name] = future.result()
            log.info("source_loaded", source=name, rows=results[name])
        except Exception as e:
            log.error("source_failed", source=name, error=str(e))
            results[name] = -1

    # Run Phase 2 concurrently (after Phase 1 completes)
    phase2_futures = {}
    for name, task_fn in phase2_tasks.items():
        phase2_futures[name] = task_fn.submit(run_date=run_date)

    for name, future in phase2_futures.items():
        try:
            results[name] = future.result()
            log.info("source_loaded", source=name, rows=results[name])
        except Exception as e:
            log.error("source_failed", source=name, error=str(e))
            results[name] = -1

    total_rows = sum(v for v in results.values() if v > 0)
    failed = [k for k, v in results.items() if v < 0]

    log.info(
        "reference_flow_complete",
        total_rows=total_rows,
        sources_loaded=len([v for v in results.values() if v > 0]),
        sources_failed=len(failed),
        failed_sources=failed,
    )

    return results


if __name__ == "__main__":
    load_reference_data()
