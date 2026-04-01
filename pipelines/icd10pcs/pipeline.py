"""ICD-10-PCS Procedure Codes pipeline.

Source: CMS ICD-10-PCS code files (annual, fiscal year)
Target: reference.ref_icd10_pcs (~78,000 rows)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline

log = get_logger(source="icd10pcs")

# PCS section descriptions (first character)
SECTION_MAP = {
    "0": "Medical and Surgical",
    "1": "Obstetrics",
    "2": "Placement",
    "3": "Administration",
    "4": "Measurement and Monitoring",
    "5": "Extracorporeal or Systemic Assistance and Performance",
    "6": "Extracorporeal or Systemic Therapies",
    "7": "Osteopathic",
    "8": "Other Procedures",
    "9": "Chiropractic",
    "B": "Imaging",
    "C": "Nuclear Medicine",
    "D": "Radiation Therapy",
    "F": "Physical Rehabilitation and Diagnostic Audiology",
    "G": "Mental Health",
    "H": "Substance Abuse Treatment",
    "X": "New Technology",
}


def _transform_icd10pcs(df: pd.DataFrame) -> pd.DataFrame:
    """Derive section and body system from 7-character PCS code."""
    df["icd10_pcs_code"] = df["icd10_pcs_code"].str.strip().str.upper()
    df["section"] = df["icd10_pcs_code"].str[0]
    df["section_description"] = df["section"].map(SECTION_MAP).fillna("")
    df["body_system"] = df["icd10_pcs_code"].str[1]
    df["is_billable"] = df["icd10_pcs_code"].str.len() == 7
    return df


config = ReferenceSourceConfig(
    source_name="icd10pcs",
    target_table="ref_icd10_pcs",
    column_mapping={
        "code": "icd10_pcs_code",
        "short_description": "description_short",
        "long_description": "description_long",
    },
    required_source_columns=["code"],
    select_columns=[
        "icd10_pcs_code", "description_short", "description_long",
        "section", "section_description", "body_system", "is_billable",
    ],
    min_rows=70_000,
    max_rows=100_000,
    transform_fn=_transform_icd10pcs,
    file_pattern="*icd10pcs*.txt",
    read_options={"sep": "\t", "header": None, "names": ["code", "short_description", "long_description"]},
)


def run(source_path=None, run_date=None):
    return run_reference_pipeline(config, run_date=run_date, source_path=source_path)
