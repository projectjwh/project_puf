"""Prefect flow for Medicare Part B Physician/Supplier Utilization pipeline."""

from datetime import date

from prefect import flow, task
from prefect.tasks import task_input_hash

from pipelines._common.config import compute_data_year


@task(retries=2, retry_delay_seconds=300, cache_key_fn=task_input_hash, tags=["db-write"])
def run_partb_pipeline(data_year: int, run_date: date) -> dict[str, int]:
    from pipelines.partb.pipeline import run

    return run(run_date=run_date, data_year=data_year)


@flow(name="partb-utilization", log_prints=True)
def partb_flow(
    data_year: int | None = None,
    run_date: date | None = None,
) -> dict[str, int]:
    """Run the Part B utilization pipeline for a given data year."""
    run_date = run_date or date.today()
    data_year = data_year or compute_data_year("partb", run_date)

    print(f"Starting Part B pipeline for data_year={data_year}")
    results = run_partb_pipeline(data_year=data_year, run_date=run_date)
    print(f"Part B complete: {results}")
    return results


if __name__ == "__main__":
    partb_flow()
