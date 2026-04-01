"""National Drug Code Directory pipeline.

Source: FDA NDC Directory
Target: reference.ref_ndc (~300,000 rows)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline
from pipelines._common.transform import normalize_ndc_series

log = get_logger(source="ndc")

# DEA schedules that indicate opioid potential
OPIOID_DEA_SCHEDULES = {"CII", "CIII"}


def _transform_ndc(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize NDC codes to 11-digit, derive flags."""
    # Normalize NDC
    if "ndc_code" in df.columns:
        df["ndc_code"] = normalize_ndc_series(df["ndc_code"])
        # Formatted with dashes: 5-4-2
        df["ndc_formatted"] = df["ndc_code"].apply(
            lambda c: f"{c[:5]}-{c[5:9]}-{c[9:]}" if len(str(c)) == 11 else c
        )

    # Opioid flag heuristic: DEA schedule II/III
    df["is_opioid"] = df.get("dea_schedule", pd.Series(dtype=str)).isin(OPIOID_DEA_SCHEDULES)

    # Active flag: no marketing end date or end date in future
    end_date = pd.to_datetime(df.get("marketing_end_date"), errors="coerce")
    df["is_active"] = end_date.isna() | (end_date > pd.Timestamp.now())

    return df


config = ReferenceSourceConfig(
    source_name="ndc",
    target_table="ref_ndc",
    column_mapping={
        "PRODUCTNDC": "ndc_code",
        "PROPRIETARYNAME": "brand_name",
        "NONPROPRIETARYNAME": "generic_name",
        "DOSAGEFORMNAME": "dosage_form",
        "ROUTENAME": "route",
        "ACTIVE_NUMERATOR_STRENGTH": "strength",
        "LABELERNAME": "labeler_name",
        "PRODUCTTYPENAME": "product_type",
        "DEASCHEDULE": "dea_schedule",
        "PACKAGEDESCRIPTION": "package_description",
        "STARTMARKETINGDATE": "marketing_start_date",
        "ENDMARKETINGDATE": "marketing_end_date",
        "LISTING_RECORD_CERTIFIED_THROUGH": "listing_date",
    },
    required_source_columns=["PRODUCTNDC", "NONPROPRIETARYNAME"],
    select_columns=[
        "ndc_code", "ndc_formatted", "labeler_name", "brand_name", "generic_name",
        "dosage_form", "route", "strength", "package_description", "product_type",
        "dea_schedule", "is_opioid", "listing_date", "marketing_start_date",
        "marketing_end_date", "is_active",
    ],
    min_rows=200_000,
    max_rows=500_000,
    transform_fn=_transform_ndc,
    file_pattern="*product*.txt",
    read_options={"sep": "\t"},
)


def run(source_path=None, run_date=None):
    return run_reference_pipeline(config, run_date=run_date, source_path=source_path)
