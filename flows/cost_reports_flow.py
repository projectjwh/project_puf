"""Prefect flow for Hospital Cost Reports (HCRIS) data."""

from datetime import date

from prefect import flow, task

from pipelines._common.config import compute_data_year
from pipelines._common.logging import get_logger, setup_logging

log = get_logger(source="cost_reports_flow")


@task(name="run-cost-reports-pipeline", retries=2, retry_delay_seconds=[300, 900], tags=["db-write"])
def run_cost_reports_pipeline(run_date: date, data_year: int) -> dict[str, int]:
    from pipelines.cost_reports.pipeline import run

    return run(run_date=run_date, data_year=data_year)


@flow(name="cost-reports-acquisition", log_prints=True)
def cost_reports_acquisition(
    run_date: date | None = None,
    data_year: int | None = None,
) -> dict[str, int]:
    setup_logging()
    run_date = run_date or date.today()
    data_year = data_year or compute_data_year("cost_reports", run_date)
    log.info("cost_reports_flow_start", run_date=str(run_date), data_year=data_year)
    results = run_cost_reports_pipeline(run_date, data_year)
    log.info("cost_reports_flow_complete", **results)
    return results


if __name__ == "__main__":
    cost_reports_acquisition()
