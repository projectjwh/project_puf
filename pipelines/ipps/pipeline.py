"""Inpatient Prospective Payment System (IPPS) Rates pipeline.

Source: CMS IPPS Final Rule DRG relative weights
Target: reference.ref_ipps_rates (~800 rows per fiscal year)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline

log = get_logger(source="ipps")


def _transform_ipps(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize DRG codes and cast numeric fields."""
    df["drg_code"] = df["drg_code"].str.strip().str.zfill(3)

    numeric_cols = [
        "relative_weight", "geometric_mean_los", "arithmetic_mean_los",
        "average_payment", "discharge_count",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


config = ReferenceSourceConfig(
    source_name="ipps",
    target_table="ref_ipps_rates",
    column_mapping={
        "MS-DRG": "drg_code",
        "DRG": "drg_code",
        "MS-DRG Title": "drg_description",
        "DRG Description": "drg_description",
        "Weights": "relative_weight",
        "Relative Weight": "relative_weight",
        "Geometric Mean LOS": "geometric_mean_los",
        "Arithmetic Mean LOS": "arithmetic_mean_los",
        "Average Payment": "average_payment",
        "Number of Discharges": "discharge_count",
        "Discharges": "discharge_count",
    },
    required_source_columns=[],  # Column names vary by fiscal year
    select_columns=[
        "drg_code", "drg_description", "relative_weight",
        "geometric_mean_los", "arithmetic_mean_los",
        "average_payment", "discharge_count",
    ],
    min_rows=600,
    max_rows=1_000,
    transform_fn=_transform_ipps,
    file_pattern="*.xlsx",
    read_options={"header": 0},
)


def run(source_path=None, run_date=None, fiscal_year=None):
    return run_reference_pipeline(config, run_date=run_date, source_path=source_path)
