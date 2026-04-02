"""Place of Service Codes pipeline.

Source: CMS Place of Service Code Set
Target: reference.ref_place_of_service (~100 rows)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline

log = get_logger(source="pos_codes")

# Facility codes (as opposed to non-facility for billing purposes)
FACILITY_CODES = {
    "01",
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "08",
    "09",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "31",
    "32",
    "33",
    "34",
    "41",
    "42",
    "51",
    "52",
    "53",
    "54",
    "55",
    "56",
    "57",
    "58",
    "59",
    "61",
    "62",
    "65",
    "71",
    "72",
}


def _transform_pos(df: pd.DataFrame) -> pd.DataFrame:
    """Zero-pad code, derive facility flag."""
    df["pos_code"] = df["pos_code"].str.strip().str.zfill(2)
    df["is_facility"] = df["pos_code"].isin(FACILITY_CODES)
    df["is_active"] = True  # All published codes are active
    return df


config = ReferenceSourceConfig(
    source_name="pos_codes",
    target_table="ref_place_of_service",
    column_mapping={
        "Place of Service Code(s)": "pos_code",
        "Place of Service Name": "pos_name",
        "Place of Service Description": "pos_description",
    },
    required_source_columns=["Place of Service Code(s)"],
    select_columns=["pos_code", "pos_name", "pos_description", "is_facility", "is_active"],
    min_rows=50,
    max_rows=200,
    transform_fn=_transform_pos,
    file_pattern="*.csv",
)


def run(source_path=None, run_date=None):
    return run_reference_pipeline(config, run_date=run_date, source_path=source_path)
