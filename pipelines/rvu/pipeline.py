"""Physician Fee Schedule — Relative Value Units (RVU) pipeline.

Source: CMS Physician Fee Schedule RVU files
Target: reference.ref_rvu_fee_schedule (~16,000 rows per year)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline

log = get_logger(source="rvu")


def _transform_rvu(df: pd.DataFrame) -> pd.DataFrame:
    """Compute total RVUs and payment amounts."""
    df["hcpcs_code"] = df["hcpcs_code"].str.strip().str.upper()
    df["modifier"] = df.get("modifier", pd.Series(dtype=str)).fillna("").str.strip()

    # Cast numeric columns
    numeric_cols = [
        "work_rvu", "facility_pe_rvu", "nonfacility_pe_rvu",
        "malpractice_rvu", "conversion_factor",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Compute total RVUs
    work = df.get("work_rvu", 0).fillna(0)
    fac_pe = df.get("facility_pe_rvu", 0).fillna(0)
    nonfac_pe = df.get("nonfacility_pe_rvu", 0).fillna(0)
    mp = df.get("malpractice_rvu", 0).fillna(0)

    df["total_facility_rvu"] = work + fac_pe + mp
    df["total_nonfacility_rvu"] = work + nonfac_pe + mp

    # Compute payment amounts (RVU * Conversion Factor)
    cf = df.get("conversion_factor", pd.Series(dtype=float)).fillna(0)
    df["facility_payment"] = (df["total_facility_rvu"] * cf).round(2)
    df["nonfacility_payment"] = (df["total_nonfacility_rvu"] * cf).round(2)

    return df


config = ReferenceSourceConfig(
    source_name="rvu",
    target_table="ref_rvu_fee_schedule",
    column_mapping={
        "HCPCS": "hcpcs_code",
        "MOD": "modifier",
        "DESCRIPTION": "description",
        "STATUS CODE": "status_code",
        "WORK RVU": "work_rvu",
        "FACILITY PE RVU": "facility_pe_rvu",
        "NON-FACILITY PE RVU": "nonfacility_pe_rvu",
        "MP RVU": "malpractice_rvu",
        "CONV FACTOR": "conversion_factor",
        "GLOBAL": "global_days",
        "PCTC IND": "pctc_indicator",
    },
    required_source_columns=["HCPCS"],
    select_columns=[
        "hcpcs_code", "modifier", "description", "status_code",
        "work_rvu", "facility_pe_rvu", "nonfacility_pe_rvu", "malpractice_rvu",
        "total_facility_rvu", "total_nonfacility_rvu",
        "conversion_factor", "facility_payment", "nonfacility_payment",
        "global_days", "pctc_indicator",
    ],
    min_rows=10_000,
    max_rows=20_000,
    transform_fn=_transform_rvu,
    file_pattern="*.csv",
)


def run(source_path=None, run_date=None, calendar_year=None):
    return run_reference_pipeline(config, run_date=run_date, source_path=source_path)
