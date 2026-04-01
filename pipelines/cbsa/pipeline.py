"""Core-Based Statistical Areas (CBSA) pipeline.

Source: Census Bureau delineation files
Target: reference.ref_cbsa (~2,000 rows)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline
from pipelines._common.transform import normalize_fips_county, normalize_fips_state

log = get_logger(source="cbsa")


def _transform_cbsa(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize FIPS, classify metro/micro."""
    df["cbsa_code"] = df["cbsa_code"].str.strip().str.zfill(5)

    if "county_fips" in df.columns:
        df["county_fips"] = normalize_fips_county(df["county_fips"])
    if "state_fips" in df.columns:
        df["state_fips"] = normalize_fips_state(df["state_fips"])
    if "csa_code" in df.columns:
        df["csa_code"] = df["csa_code"].str.strip()

    return df


config = ReferenceSourceConfig(
    source_name="cbsa",
    target_table="ref_cbsa",
    column_mapping={
        "CBSA Code": "cbsa_code",
        "CBSA Title": "cbsa_title",
        "Metropolitan/Micropolitan Statistical Area": "cbsa_type",
        "CSA Code": "csa_code",
        "CSA Title": "csa_title",
        "FIPS County Code": "county_fips",
        "FIPS State Code": "state_fips",
        "Central/Outlying County": "central_outlying",
    },
    required_source_columns=["CBSA Code", "CBSA Title"],
    select_columns=[
        "cbsa_code", "cbsa_title", "cbsa_type", "csa_code", "csa_title",
        "county_fips", "state_fips", "central_outlying",
    ],
    min_rows=1_500,
    max_rows=3_000,
    transform_fn=_transform_cbsa,
    file_pattern="*.xlsx",
    read_options={"header": 0},
)


def run(source_path=None, run_date=None):
    return run_reference_pipeline(config, run_date=run_date, source_path=source_path)
