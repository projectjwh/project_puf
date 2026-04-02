"""Prefect flow for Medicare Part D Prescribers pipeline."""

from datetime import date

from prefect import flow, task
from prefect.tasks import task_input_hash

from pipelines._common.config import compute_data_year


@task(retries=2, retry_delay_seconds=300, cache_key_fn=task_input_hash, tags=["db-write"])
def run_partd_pipeline(data_year: int, run_date: date) -> dict[str, int]:
    from pipelines.partd.pipeline import run

    return run(run_date=run_date, data_year=data_year)


@flow(name="partd-prescribers", log_prints=True)
def partd_flow(
    data_year: int | None = None,
    run_date: date | None = None,
) -> dict[str, int]:
    """Run the Part D prescribers pipeline for a given data year."""
    run_date = run_date or date.today()
    data_year = data_year or compute_data_year("partd", run_date)

    print(f"Starting Part D pipeline for data_year={data_year}")
    results = run_partd_pipeline(data_year=data_year, run_date=run_date)
    print(f"Part D complete: {results}")
    return results


if __name__ == "__main__":
    partd_flow()
