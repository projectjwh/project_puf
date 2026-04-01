"""Rural-Urban Commuting Area (RUCA) Codes pipeline.

Source: USDA Economic Research Service
Target: reference.ref_ruca (~75,000 rows)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline
from pipelines._common.transform import normalize_fips_county, normalize_fips_state

log = get_logger(source="ruca")

# RUCA primary codes → descriptions
RUCA_DESCRIPTIONS = {
    "1": "Metropolitan area core: primary flow within an urbanized area",
    "2": "Metropolitan area high commuting: primary flow 30%+ to urbanized area",
    "3": "Metropolitan area low commuting: primary flow 5-30% to urbanized area",
    "4": "Micropolitan area core: primary flow within an urban cluster 10K-50K",
    "5": "Micropolitan high commuting: primary flow 30%+ to urban cluster 10K-50K",
    "6": "Micropolitan low commuting: primary flow 5-30% to urban cluster 10K-50K",
    "7": "Small town core: primary flow within urban cluster 2.5K-10K",
    "8": "Small town high commuting: primary flow 30%+ to urban cluster 2.5K-10K",
    "9": "Small town low commuting: primary flow 5-30% to urban cluster 2.5K-10K",
    "10": "Rural areas: primary flow to tract outside UA/UC",
    "99": "Not coded: tract has zero population or no data",
}


def _transform_ruca(df: pd.DataFrame) -> pd.DataFrame:
    """Add descriptions and rural classification."""
    df["zip_code"] = df["zip_code"].str.strip().str.zfill(5)
    df["ruca_code"] = df["ruca_code"].str.strip()

    # Primary code is first digit(s) before the decimal
    primary_code = df["ruca_code"].str.split(".").str[0]
    df["ruca_description"] = primary_code.map(RUCA_DESCRIPTIONS).fillna("")

    # Rural = RUCA primary codes 4-10 (everything outside metropolitan areas)
    primary_numeric = pd.to_numeric(primary_code, errors="coerce")
    df["is_rural"] = primary_numeric >= 4

    if "state_fips" in df.columns:
        df["state_fips"] = normalize_fips_state(df["state_fips"])
    if "county_fips" in df.columns:
        df["county_fips"] = normalize_fips_county(df["county_fips"])

    return df


config = ReferenceSourceConfig(
    source_name="ruca",
    target_table="ref_ruca",
    column_mapping={
        "ZIP_CODE": "zip_code",
        "RUCA1": "ruca_code",
        "RUCA2": "ruca_secondary",
        "STATE": "state_fips",
        "COUNTY": "county_fips",
        "TRACTFIPS": "tract_fips",
    },
    required_source_columns=["ZIP_CODE", "RUCA1"],
    select_columns=[
        "zip_code", "ruca_code", "ruca_secondary", "ruca_description",
        "is_rural", "state_fips", "county_fips", "tract_fips",
    ],
    min_rows=40_000,
    max_rows=100_000,
    transform_fn=_transform_ruca,
    file_pattern="*.xlsx",
    read_options={"sheet_name": "Data", "header": 0},
)


def run(source_path=None, run_date=None):
    return run_reference_pipeline(config, run_date=run_date, source_path=source_path)
