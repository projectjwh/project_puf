"""Hospice Cost Reports (HCRIS) pipeline.

Source: CMS HCRIS Hospice (~5K reports/year)
Outputs:
  - data/processed/cost_reports_hospice/{data_year}/cost_reports_hospice.parquet
  - staging.stg_cms__cost_reports_hospice (PostgreSQL)
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, extract_zip, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)
from pipelines.cost_reports.pipeline import (
    RPT_COLUMN_MAPPING,
    extract_financial_metrics,
    transform_cost_reports,
)

log = get_logger(source="cost_reports_hospice")

STAGING_COLUMNS = [
    "rpt_rec_num",
    "ccn",
    "report_status_code",
    "fiscal_year_begin",
    "fiscal_year_end",
    "total_patient_revenue",
    "total_operating_expenses",
    "net_income",
    "total_beds_available",
    "total_patient_days",
    "total_discharges",
    "operating_margin",
    "cost_to_charge_ratio",
    "data_year",
]


def validate_hospice_cr(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="cost_reports_hospice")
    check_required_columns(df, ["rpt_rec_num", "ccn"], report)
    check_column_not_null(df, "rpt_rec_num", report, severity="BLOCK")
    check_row_count(df, min_rows=1_000, max_rows=10_000, report=report, severity="WARN")
    return report


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    data_year: int | None = None,
) -> dict[str, int]:
    run_date = run_date or date.today()
    data_year = data_year or run_date.year - 2  # TODO: replace with compute_data_year()
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("cost_reports_hospice_start", run_date=str(run_date), data_year=data_year)

    if source_path:
        landing = source_path if source_path.is_dir() else source_path.parent
    else:
        source_def = get_source("cost_reports_hospice")
        landing = resolve_landing_path("cost_reports_hospice", run_date, data_year)
        downloaded = download_file(source_def.url, landing)
        if downloaded.suffix == ".zip":
            extract_zip(downloaded, landing)

    rpt_files = list(landing.glob("*RPT*.CSV")) + list(landing.glob("*rpt*.csv"))
    nmrc_files = list(landing.glob("*NMRC*.CSV")) + list(landing.glob("*nmrc*.csv"))

    if not rpt_files:
        raise FileNotFoundError(f"No RPT file found in {landing}")

    rpt_df = pd.read_csv(rpt_files[0], dtype=str, low_memory=False)
    rpt_df = rpt_df.rename(columns={k: v for k, v in RPT_COLUMN_MAPPING.items() if k in rpt_df.columns})

    report = validate_hospice_cr(rpt_df)
    report.raise_if_blocked()

    rpt_df = transform_cost_reports(rpt_df, data_year)
    results["rpt_rows"] = len(rpt_df)

    if nmrc_files:
        nmrc_df = pd.read_csv(nmrc_files[0], dtype=str, low_memory=False)
        rpt_df = extract_financial_metrics(rpt_df, nmrc_df)

    parquet_path = (
        PROJECT_ROOT
        / settings.storage.processed_base
        / "cost_reports_hospice"
        / str(data_year)
        / "cost_reports_hospice.parquet"
    )
    write_parquet(rpt_df, parquet_path)
    results["cost_reports_hospice_parquet"] = len(rpt_df)

    out_cols = [c for c in STAGING_COLUMNS if c in rpt_df.columns]
    rows = copy_dataframe_to_pg(rpt_df[out_cols], "stg_cms__cost_reports_hospice", "staging", if_exists="append")
    results["stg_cost_reports_hospice"] = rows

    log.info("cost_reports_hospice_complete", **results)
    return results
