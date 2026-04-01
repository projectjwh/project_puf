"""MS-DRG Grouper pipeline.

Source: CMS MS-DRG Classifications and Software
Target: reference.ref_msdrg (~800 rows per fiscal year)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline

log = get_logger(source="msdrg")


def _transform_msdrg(df: pd.DataFrame) -> pd.DataFrame:
    """Clean DRG codes and classify as Medical/Surgical."""
    df["drg_code"] = df["drg_code"].str.strip().str.zfill(3)

    # DRG type heuristic: surgical DRGs typically have keywords
    surgical_keywords = ["surgery", "surgical", "procedure", "implant", "graft",
                         "transplant", "amputation", "craniotomy", "hip replacement",
                         "knee replacement", "appendectomy", "cholecystectomy"]
    desc_lower = df["drg_description"].fillna("").str.lower()
    df["drg_type"] = "Medical"
    for kw in surgical_keywords:
        df.loc[desc_lower.str.contains(kw, na=False), "drg_type"] = "Surgical"

    # Cast numeric columns
    for col in ("weight", "geometric_mean_los", "arithmetic_mean_los"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


config = ReferenceSourceConfig(
    source_name="msdrg",
    target_table="ref_msdrg",
    column_mapping={
        "MS-DRG": "drg_code",
        "MDC": "mdc_code",
        "TYPE": "drg_type",
        "MS-DRG Title": "drg_description",
        "Weights": "weight",
        "Geometric mean LOS": "geometric_mean_los",
        "Arithmetic mean LOS": "arithmetic_mean_los",
    },
    required_source_columns=["MS-DRG"],
    select_columns=[
        "drg_code", "drg_description", "mdc_code", "mdc_description",
        "drg_type", "weight", "geometric_mean_los", "arithmetic_mean_los",
    ],
    min_rows=700,
    max_rows=1000,
    transform_fn=_transform_msdrg,
    file_pattern="*.xlsx",
    read_options={"header": 0},
)


def run(source_path=None, run_date=None, fiscal_year=None):
    return run_reference_pipeline(config, run_date=run_date, source_path=source_path)
