"""ZIP-County Crosswalk pipeline.

Source: HUD USPS ZIP Crosswalk files
Target: reference.ref_zip_county_crosswalk (~50,000 rows)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline
from pipelines._common.transform import normalize_fips_county

log = get_logger(source="zip_county")


def _transform_zip_county(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize FIPS codes and ratios."""
    df["zip_code"] = df["zip_code"].str.strip().str.zfill(5)
    df["county_fips"] = normalize_fips_county(df["county_fips"])
    df["state_fips"] = df["county_fips"].str[:2]

    # Cast ratios to numeric
    for col in ("residential_ratio", "business_ratio", "other_ratio", "total_ratio"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


config = ReferenceSourceConfig(
    source_name="zip_county",
    target_table="ref_zip_county_crosswalk",
    column_mapping={
        "ZIP": "zip_code",
        "COUNTY": "county_fips",
        "USPS_ZIP_PREF_STATE": "state_abbreviation",
        "RES_RATIO": "residential_ratio",
        "BUS_RATIO": "business_ratio",
        "OTH_RATIO": "other_ratio",
        "TOT_RATIO": "total_ratio",
    },
    required_source_columns=["ZIP", "COUNTY"],
    select_columns=[
        "zip_code",
        "county_fips",
        "state_fips",
        "state_abbreviation",
        "residential_ratio",
        "business_ratio",
        "other_ratio",
        "total_ratio",
    ],
    min_rows=40_000,
    max_rows=60_000,
    transform_fn=_transform_zip_county,
    file_pattern="*.xlsx",
    read_options={"header": 0},
)


def run(source_path=None, run_date=None):
    return run_reference_pipeline(config, run_date=run_date, source_path=source_path)
