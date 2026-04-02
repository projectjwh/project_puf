"""Prefect flow for Provider of Services facility data."""

from datetime import date

from prefect import flow, task

from pipelines._common.logging import get_logger, setup_logging

log = get_logger(source="pos_flow")


@task(name="run-pos-pipeline", retries=2, retry_delay_seconds=[300, 900], tags=["db-write"])
def run_pos_pipeline(run_date: date) -> dict[str, int]:
    from pipelines.pos.pipeline import run

    return run(run_date=run_date)


@flow(name="pos-acquisition", log_prints=True)
def pos_acquisition(run_date: date | None = None) -> dict[str, int]:
    setup_logging()
    run_date = run_date or date.today()
    log.info("pos_flow_start", run_date=str(run_date))
    results = run_pos_pipeline(run_date)
    log.info("pos_flow_complete", **results)
    return results


if __name__ == "__main__":
    pos_acquisition()
