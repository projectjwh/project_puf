"""FIPS State and County Codes pipeline.

Source: Census Bureau ANSI FIPS codes
Targets: reference.ref_state_fips (~56 rows), reference.ref_county_fips (~3,250 rows)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline
from pipelines._common.transform import normalize_fips_county, normalize_fips_state

log = get_logger(source="fips")

# US Census region/division mapping
REGION_DIVISION = {
    "CT": ("Northeast", "New England"), "ME": ("Northeast", "New England"),
    "MA": ("Northeast", "New England"), "NH": ("Northeast", "New England"),
    "RI": ("Northeast", "New England"), "VT": ("Northeast", "New England"),
    "NJ": ("Northeast", "Mid-Atlantic"), "NY": ("Northeast", "Mid-Atlantic"),
    "PA": ("Northeast", "Mid-Atlantic"),
    "IL": ("Midwest", "East North Central"), "IN": ("Midwest", "East North Central"),
    "MI": ("Midwest", "East North Central"), "OH": ("Midwest", "East North Central"),
    "WI": ("Midwest", "East North Central"),
    "IA": ("Midwest", "West North Central"), "KS": ("Midwest", "West North Central"),
    "MN": ("Midwest", "West North Central"), "MO": ("Midwest", "West North Central"),
    "NE": ("Midwest", "West North Central"), "ND": ("Midwest", "West North Central"),
    "SD": ("Midwest", "West North Central"),
    "DE": ("South", "South Atlantic"), "FL": ("South", "South Atlantic"),
    "GA": ("South", "South Atlantic"), "MD": ("South", "South Atlantic"),
    "NC": ("South", "South Atlantic"), "SC": ("South", "South Atlantic"),
    "VA": ("South", "South Atlantic"), "DC": ("South", "South Atlantic"),
    "WV": ("South", "South Atlantic"),
    "AL": ("South", "East South Central"), "KY": ("South", "East South Central"),
    "MS": ("South", "East South Central"), "TN": ("South", "East South Central"),
    "AR": ("South", "West South Central"), "LA": ("South", "West South Central"),
    "OK": ("South", "West South Central"), "TX": ("South", "West South Central"),
    "AZ": ("West", "Mountain"), "CO": ("West", "Mountain"),
    "ID": ("West", "Mountain"), "MT": ("West", "Mountain"),
    "NV": ("West", "Mountain"), "NM": ("West", "Mountain"),
    "UT": ("West", "Mountain"), "WY": ("West", "Mountain"),
    "AK": ("West", "Pacific"), "CA": ("West", "Pacific"),
    "HI": ("West", "Pacific"), "OR": ("West", "Pacific"),
    "WA": ("West", "Pacific"),
}

# Territories
TERRITORIES = {"AS", "GU", "MP", "PR", "VI", "UM"}


def _transform_states(df: pd.DataFrame) -> pd.DataFrame:
    """Transform state FIPS data."""
    df["state_fips"] = normalize_fips_state(df["state_fips"])
    df["region"] = df["state_abbreviation"].map(lambda x: REGION_DIVISION.get(x, (None, None))[0])
    df["division"] = df["state_abbreviation"].map(lambda x: REGION_DIVISION.get(x, (None, None))[1])
    df["is_state"] = ~df["state_abbreviation"].isin(TERRITORIES | {"DC"})
    return df


def _transform_counties(df: pd.DataFrame) -> pd.DataFrame:
    """Transform county FIPS data."""
    df["county_fips"] = normalize_fips_county(df["county_fips"])
    df["state_fips"] = normalize_fips_state(df["state_fips"])
    return df


state_config = ReferenceSourceConfig(
    source_name="fips",
    target_table="ref_state_fips",
    column_mapping={
        "STATE": "state_fips",
        "STUSAB": "state_abbreviation",
        "STATE_NAME": "state_name",
        "STATENS": "state_ansi",
    },
    required_source_columns=["STATE", "STUSAB", "STATE_NAME"],
    select_columns=["state_fips", "state_abbreviation", "state_name", "region", "division", "is_state"],
    min_rows=50,
    max_rows=80,
    transform_fn=_transform_states,
    file_pattern="*state*.csv",
    read_options={"sep": "|"},
)

county_config = ReferenceSourceConfig(
    source_name="fips",
    target_table="ref_county_fips",
    column_mapping={
        "STATEFP": "state_fips",
        "COUNTYFP": "county_fips_3",
        "COUNTYNS": "county_ansi",
        "COUNTYNAME": "county_name",
        "STUSAB": "state_abbreviation",
        "CLASSFP": "class_code",
    },
    required_source_columns=["STATEFP", "COUNTYFP", "COUNTYNAME"],
    select_columns=["county_fips", "county_name", "state_fips", "state_abbreviation", "class_code"],
    min_rows=3000,
    max_rows=3500,
    transform_fn=_transform_counties,
    file_pattern="*county*.csv",
    read_options={"sep": "|"},
)


def run(source_path=None, run_date=None):
    """Run both state and county FIPS pipelines."""
    rows_states = run_reference_pipeline(state_config, run_date=run_date, source_path=source_path)
    rows_counties = run_reference_pipeline(county_config, run_date=run_date, source_path=source_path)
    log.info("fips_complete", states=rows_states, counties=rows_counties)
    return rows_states + rows_counties
