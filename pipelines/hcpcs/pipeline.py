"""HCPCS Level II Codes pipeline.

Source: CMS HCPCS code files (quarterly updates)
Target: reference.ref_hcpcs_codes (~7,500 rows)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline

log = get_logger(source="hcpcs")


def _transform_hcpcs(df: pd.DataFrame) -> pd.DataFrame:
    """Clean HCPCS codes and derive drug code indicator."""
    df["hcpcs_code"] = df["hcpcs_code"].str.strip().str.upper()

    # J-codes are drug codes (J0000-J9999), plus Q-codes for some drugs
    df["is_drug_code"] = df["hcpcs_code"].str.match(r"^J\d{4}$", na=False)

    # Determine active status
    df["is_active"] = df.get("termination_date", pd.Series(dtype=str)).isna() | (
        df.get("termination_date", pd.Series(dtype=str)) == ""
    )
    return df


config = ReferenceSourceConfig(
    source_name="hcpcs",
    target_table="ref_hcpcs_codes",
    column_mapping={
        "HCPC": "hcpcs_code",
        "SHORT_DESCRIPTION": "description_short",
        "LONG_DESCRIPTION": "description_long",
        "PRICE_IND_CODE": "pricing_indicator",
        "COVERAGE_CODE": "coverage_code",
        "TOS": "type_of_service",
        "ASC_PYMT_IND": "asc_payment_indicator",
        "EFFECTIVE_DATE": "effective_date",
        "TERMINATION_DATE": "termination_date",
    },
    required_source_columns=["HCPC"],
    select_columns=[
        "hcpcs_code",
        "description_short",
        "description_long",
        "pricing_indicator",
        "coverage_code",
        "type_of_service",
        "asc_payment_indicator",
        "is_drug_code",
        "effective_date",
        "termination_date",
        "is_active",
    ],
    min_rows=6_000,
    max_rows=10_000,
    transform_fn=_transform_hcpcs,
    file_pattern="*HCPC*.csv",
)


def run(source_path=None, run_date=None):
    return run_reference_pipeline(config, run_date=run_date, source_path=source_path)
