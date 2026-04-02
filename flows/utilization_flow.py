"""Orchestration flow: runs all utilization pipelines for a given data year.

Sequence:
  1. Part B, Part D, GeoVar pipelines (parallel — independent data sources)
  2. dbt run (intermediate + mart models depend on all staging data)
  3. Parquet export (reads mart tables written by dbt)
"""

from datetime import date

from prefect import flow, task
from prefect.tasks import task_input_hash


@task(retries=2, retry_delay_seconds=300, cache_key_fn=task_input_hash)
def run_partb(data_year: int, run_date: date) -> dict[str, int]:
    from pipelines.partb.pipeline import run

    return run(run_date=run_date, data_year=data_year)


@task(retries=2, retry_delay_seconds=300, cache_key_fn=task_input_hash)
def run_partd(data_year: int, run_date: date) -> dict[str, int]:
    from pipelines.partd.pipeline import run

    return run(run_date=run_date, data_year=data_year)


@task(retries=2, retry_delay_seconds=300, cache_key_fn=task_input_hash)
def run_geovar(data_year: int, run_date: date) -> dict[str, int]:
    from pipelines.geovar.pipeline import run

    return run(run_date=run_date, data_year=data_year)


@task(retries=1, retry_delay_seconds=60)
def run_dbt() -> None:
    """Run dbt for intermediate and mart models."""
    import subprocess

    subprocess.run(
        ["dbt", "run", "--select", "tag:intermediate tag:mart"],
        check=True,
        cwd="models",
    )


@task(retries=1)
def export_parquet() -> dict[str, int]:
    from scripts.export_marts_to_parquet import export_all

    return export_all()


@flow(name="utilization-full-refresh", log_prints=True)
def utilization_flow(
    data_year: int | None = None,
    run_date: date | None = None,
    skip_dbt: bool = False,
    skip_export: bool = False,
) -> dict[str, dict]:
    """Full utilization pipeline: ingest → transform → serve.

    Steps:
      1. Part B + Part D + GeoVar in parallel
      2. dbt run (intermediate + mart)
      3. Parquet export for DuckDB
    """
    run_date = run_date or date.today()
    data_year = data_year or run_date.year - 2
    all_results: dict[str, dict] = {}

    print(f"Starting utilization flow for data_year={data_year}")

    # Phase 1: Parallel ingestion
    partb_future = run_partb.submit(data_year=data_year, run_date=run_date)
    partd_future = run_partd.submit(data_year=data_year, run_date=run_date)
    geovar_future = run_geovar.submit(data_year=data_year, run_date=run_date)

    all_results["partb"] = partb_future.result()
    all_results["partd"] = partd_future.result()
    all_results["geovar"] = geovar_future.result()
    print(f"Ingestion complete: {all_results}")

    # Phase 2: dbt transformation
    if not skip_dbt:
        run_dbt()
        print("dbt run complete")

    # Phase 3: Parquet export
    if not skip_export:
        export_results = export_parquet()
        all_results["export"] = export_results
        print(f"Export complete: {export_results}")

    print(f"Utilization flow complete: {list(all_results.keys())}")
    return all_results


if __name__ == "__main__":
    utilization_flow()
