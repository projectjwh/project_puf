"""Prefect flow for NPPES provider data acquisition and loading.

Runs monthly on the 8th. Downloads NPPES full file, transforms,
writes Parquet, and loads to PostgreSQL reference tables.
"""

from datetime import date

from prefect import flow, task

from pipelines._common.logging import get_logger, setup_logging

log = get_logger(source="nppes_flow")


@task(name="run-nppes-pipeline", retries=2, retry_delay_seconds=[300, 900], tags=["db-write"])
def run_nppes_pipeline(run_date: date) -> dict[str, int]:
    from pipelines.nppes.pipeline import run

    return run(run_date=run_date)


@flow(name="nppes-acquisition", log_prints=True)
def nppes_acquisition(run_date: date | None = None) -> dict[str, int]:
    """Download and load NPPES provider data.

    Args:
        run_date: Override run date. Defaults to today.

    Returns:
        Dict with row counts per output table.
    """
    setup_logging()
    run_date = run_date or date.today()
    log.info("nppes_flow_start", run_date=str(run_date))

    results = run_nppes_pipeline(run_date)

    log.info("nppes_flow_complete", **results)
    return results


if __name__ == "__main__":
    nppes_acquisition()
