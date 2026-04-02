"""Hospital Wage Index pipeline.

Source: CMS IPPS Wage Index files
Target: reference.ref_wage_index (~4,000 rows per fiscal year)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline

log = get_logger(source="wage_index")


def _transform_wage_index(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize CBSA codes and cast numeric values."""
    df["cbsa_code"] = df["cbsa_code"].str.strip().str.zfill(5)

    if "state_fips" in df.columns:
        df["state_fips"] = df["state_fips"].str.strip().str.zfill(2)

    numeric_cols = [
        "wage_index",
        "reclassified_wage_index",
        "gpci_work",
        "gpci_pe",
        "gpci_mp",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


config = ReferenceSourceConfig(
    source_name="wage_index",
    target_table="ref_wage_index",
    column_mapping={
        "CBSA No.": "cbsa_code",
        "CBSA": "cbsa_code",
        "CBSA Name": "cbsa_name",
        "Wage Index": "wage_index",
        "Reclassified Wage Index": "reclassified_wage_index",
        "GPCI - Work": "gpci_work",
        "GPCI Work": "gpci_work",
        "GPCI - PE": "gpci_pe",
        "GPCI PE": "gpci_pe",
        "GPCI - MP": "gpci_mp",
        "GPCI MP": "gpci_mp",
        "State": "state_fips",
    },
    required_source_columns=[],  # Column names vary by year
    select_columns=[
        "cbsa_code",
        "cbsa_name",
        "state_fips",
        "wage_index",
        "reclassified_wage_index",
        "gpci_work",
        "gpci_pe",
        "gpci_mp",
    ],
    min_rows=3_000,
    max_rows=5_000,
    transform_fn=_transform_wage_index,
    file_pattern="*.xlsx",
    read_options={"header": 0},
)


def run(source_path=None, run_date=None, fiscal_year=None):
    return run_reference_pipeline(config, run_date=run_date, source_path=source_path)
