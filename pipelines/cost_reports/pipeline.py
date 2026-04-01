"""Hospital Cost Reports (HCRIS) pipeline.

Source: CMS Hospital Cost Report Information System (~6K reports/year)
Outputs:
  - data/processed/cost_reports/{year}/cost_reports.parquet
  - staging.stg_cms__cost_reports (dbt-managed, but pipeline writes Parquet)

Cost reports are complex: multiple worksheets with line/column references.
This pipeline extracts key financial metrics from the raw reports.
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, extract_zip, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import add_data_year
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="cost_reports")

# HCRIS consists of 3 related files per year:
# RPT - report-level data (one row per cost report)
# NMRC - numeric data (worksheet/line/column values)
# ALPHA - alpha data (text worksheet values)

RPT_COLUMN_MAPPING = {
    "RPT_REC_NUM": "rpt_rec_num",
    "PRVDR_CTRL_TYPE_CD": "control_type_code",
    "PRVDR_NUM": "ccn",
    "RPT_STUS_CD": "report_status_code",
    "FY_BGN_DT": "fiscal_year_begin",
    "FY_END_DT": "fiscal_year_end",
    "PROC_DT": "process_date",
    "INITL_RPT_SW": "initial_report",
    "LAST_RPT_SW": "last_report",
    "TRNSMTL_NUM": "transmittal_number",
    "FI_NUM": "fiscal_intermediary",
    "ADR_VNDR_CD": "vendor_code",
    "FI_CREAT_DT": "fi_create_date",
    "UTIL_CD": "utilization_code",
    "NPR_DT": "npr_date",
    "SPEC_IND": "special_indicator",
    "FI_RCPT_DT": "fi_receipt_date",
}

# Key financial metrics extracted from NMRC worksheet data
# Format: (worksheet, line, column) → metric_name
# Worksheet S-3, Part I: Revenue and expenses
# Worksheet G-3: Balance sheet
FINANCIAL_METRICS = {
    # Total revenue
    ("S300001", "0010", "0010"): "total_patient_revenue",
    ("S300001", "0010", "0020"): "total_operating_revenue",
    # Operating expenses
    ("S300001", "0020", "0010"): "total_operating_expenses",
    # Net income
    ("S300001", "0030", "0010"): "net_income",
    # Total beds
    ("S300001", "0014", "0080"): "total_beds_available",
    # Total discharges
    ("S300001", "0014", "0150"): "total_discharges",
    # Total patient days
    ("S300001", "0014", "0060"): "total_inpatient_days",
    # FTE employees
    ("S300001", "0014", "0090"): "fte_employees",
    # Total charges
    ("S100000", "0010", "0010"): "total_charges",
    # Total costs
    ("S100000", "0010", "0030"): "total_costs",
}


def validate_cost_reports(df: pd.DataFrame) -> ValidationReport:
    """Cost report validation."""
    report = ValidationReport(source="cost_reports")
    check_required_columns(df, ["rpt_rec_num", "ccn"], report)
    check_column_not_null(df, "rpt_rec_num", report, severity="BLOCK")
    check_row_count(df, min_rows=3_000, max_rows=10_000, report=report, severity="WARN")
    return report


def extract_financial_metrics(
    rpt_df: pd.DataFrame,
    nmrc_df: pd.DataFrame,
) -> pd.DataFrame:
    """Extract key financial metrics from NMRC worksheet data.

    Joins numeric data back to report-level data using rpt_rec_num.
    """
    # Standardize column names
    nmrc_rename = {
        "RPT_REC_NUM": "rpt_rec_num",
        "WKSHT_CD": "worksheet",
        "LINE_NUM": "line",
        "CLMN_NUM": "column",
        "ITM_VAL_NUM": "value",
    }
    nmrc_df = nmrc_df.rename(columns={k: v for k, v in nmrc_rename.items() if k in nmrc_df.columns})

    # Ensure rpt_rec_num is consistent type for join
    nmrc_df["rpt_rec_num"] = pd.to_numeric(nmrc_df["rpt_rec_num"], errors="coerce").astype("Int64")

    # Clean line/column numbers (strip whitespace, zero-pad)
    for col in ("line", "column"):
        if col in nmrc_df.columns:
            nmrc_df[col] = nmrc_df[col].astype(str).str.strip().str.zfill(4)

    if "worksheet" in nmrc_df.columns:
        nmrc_df["worksheet"] = nmrc_df["worksheet"].astype(str).str.strip()

    # Pivot metrics from long to wide
    metrics = {}
    for (ws, line, col), metric_name in FINANCIAL_METRICS.items():
        mask = (
            (nmrc_df["worksheet"] == ws) &
            (nmrc_df["line"] == line) &
            (nmrc_df["column"] == col)
        )
        metric_data = nmrc_df.loc[mask, ["rpt_rec_num", "value"]].copy()
        metric_data["value"] = pd.to_numeric(metric_data["value"], errors="coerce")
        metric_data = metric_data.rename(columns={"value": metric_name})
        metrics[metric_name] = metric_data.set_index("rpt_rec_num")[metric_name]

    # Join all metrics to report data
    result = rpt_df.set_index("rpt_rec_num")
    for metric_name, series in metrics.items():
        result = result.join(series, how="left")
    result = result.reset_index()

    # Derive financial ratios
    rev = pd.to_numeric(result.get("total_operating_revenue", 0), errors="coerce")
    exp = pd.to_numeric(result.get("total_operating_expenses", 0), errors="coerce")
    charges = pd.to_numeric(result.get("total_charges", 0), errors="coerce")
    costs = pd.to_numeric(result.get("total_costs", 0), errors="coerce")

    # Operating margin = (revenue - expenses) / revenue
    result["operating_margin"] = ((rev - exp) / rev.replace(0, pd.NA)).round(4)

    # Cost-to-charge ratio = costs / charges
    result["cost_to_charge_ratio"] = (costs / charges.replace(0, pd.NA)).round(4)

    # Occupancy rate = patient_days / (beds * 365)
    beds = pd.to_numeric(result.get("total_beds_available", 0), errors="coerce")
    days = pd.to_numeric(result.get("total_inpatient_days", 0), errors="coerce")
    result["occupancy_rate"] = (days / (beds * 365).replace(0, pd.NA)).round(4)

    return result


def transform_cost_reports(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    """Transform report-level data."""
    df["ccn"] = df["ccn"].astype(str).str.strip().str.zfill(6)
    df["rpt_rec_num"] = pd.to_numeric(df["rpt_rec_num"], errors="coerce").astype("Int64")

    # Parse dates
    for col in ("fiscal_year_begin", "fiscal_year_end", "process_date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Filter to most recent report per provider (last_report = 'Y' or latest)
    if "last_report" in df.columns:
        df["is_last_report"] = df["last_report"] == "Y"

    df = add_data_year(df, data_year)
    return df


def run(
    source_path: Path | None = None,
    run_date: date | None = None,
    data_year: int | None = None,
) -> dict[str, int]:
    """Execute the cost reports pipeline."""
    run_date = run_date or date.today()
    data_year = data_year or run_date.year - 2  # ~2 year lag
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("cost_reports_start", run_date=str(run_date), data_year=data_year)

    # Acquire
    if source_path:
        landing = source_path if source_path.is_dir() else source_path.parent
    else:
        source_def = get_source("cost_reports")
        landing = resolve_landing_path("cost_reports", run_date, data_year)
        downloaded = download_file(source_def.url, landing)
        if downloaded.suffix == ".zip":
            extract_zip(downloaded, landing)

    # Find RPT and NMRC files
    rpt_files = list(landing.glob("*RPT*.CSV")) + list(landing.glob("*rpt*.csv"))
    nmrc_files = list(landing.glob("*NMRC*.CSV")) + list(landing.glob("*nmrc*.csv"))

    if not rpt_files:
        raise FileNotFoundError(f"No RPT file found in {landing}")

    rpt_path = rpt_files[0]
    log.info("reading_rpt", path=str(rpt_path))

    # Read RPT file
    rpt_df = pd.read_csv(rpt_path, dtype=str, low_memory=False)
    rpt_df = rpt_df.rename(columns={k: v for k, v in RPT_COLUMN_MAPPING.items() if k in rpt_df.columns})

    # Validate
    report = validate_cost_reports(rpt_df)
    report.raise_if_blocked()

    # Transform
    rpt_df = transform_cost_reports(rpt_df, data_year)
    results["rpt_rows"] = len(rpt_df)

    # Extract financial metrics if NMRC file exists
    if nmrc_files:
        nmrc_path = nmrc_files[0]
        log.info("reading_nmrc", path=str(nmrc_path))
        nmrc_df = pd.read_csv(nmrc_path, dtype=str, low_memory=False)
        rpt_df = extract_financial_metrics(rpt_df, nmrc_df)
        log.info("financial_metrics_extracted")

    # Write Parquet
    parquet_path = (
        PROJECT_ROOT / settings.storage.processed_base /
        "cost_reports" / str(data_year) / "cost_reports.parquet"
    )
    write_parquet(rpt_df, parquet_path)
    results["cost_reports_parquet"] = len(rpt_df)

    log.info("cost_reports_complete", **results)
    return results
