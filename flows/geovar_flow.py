"""Prefect flow for Medicare Geographic Variation pipeline."""

from datetime import date

from prefect import flow, task
from prefect.tasks import task_input_hash


@task(retries=2, retry_delay_seconds=300, cache_key_fn=task_input_hash)
def run_geovar_pipeline(data_year: int, run_date: date) -> dict[str, int]:
    from pipelines.geovar.pipeline import run

    return run(run_date=run_date, data_year=data_year)


@flow(name="geovar-geographic-variation", log_prints=True)
def geovar_flow(
    data_year: int | None = None,
    run_date: date | None = None,
) -> dict[str, int]:
    """Run the Geographic Variation pipeline for a given data year."""
    run_date = run_date or date.today()
    data_year = data_year or run_date.year - 2

    print(f"Starting GeoVar pipeline for data_year={data_year}")
    results = run_geovar_pipeline(data_year=data_year, run_date=run_date)
    print(f"GeoVar complete: {results}")
    return results


if __name__ == "__main__":
    geovar_flow()
