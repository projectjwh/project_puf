"""ICD-10-CM Diagnosis Codes pipeline.

Source: CMS ICD-10-CM code files (annual, fiscal year)
Target: reference.ref_icd10_cm (~72,000 rows)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline

log = get_logger(source="icd10cm")

# ICD-10-CM chapter ranges
CHAPTER_MAP = {
    "A00-B99": ("01", "Certain infectious and parasitic diseases"),
    "C00-D49": ("02", "Neoplasms"),
    "D50-D89": ("03", "Diseases of the blood"),
    "E00-E89": ("04", "Endocrine, nutritional and metabolic diseases"),
    "F01-F99": ("05", "Mental, behavioral and neurodevelopmental disorders"),
    "G00-G99": ("06", "Diseases of the nervous system"),
    "H00-H59": ("07", "Diseases of the eye and adnexa"),
    "H60-H95": ("08", "Diseases of the ear and mastoid process"),
    "I00-I99": ("09", "Diseases of the circulatory system"),
    "J00-J99": ("10", "Diseases of the respiratory system"),
    "K00-K95": ("11", "Diseases of the digestive system"),
    "L00-L99": ("12", "Diseases of the skin"),
    "M00-M99": ("13", "Diseases of the musculoskeletal system"),
    "N00-N99": ("14", "Diseases of the genitourinary system"),
    "O00-O9A": ("15", "Pregnancy, childbirth and the puerperium"),
    "P00-P96": ("16", "Conditions originating in the perinatal period"),
    "Q00-Q99": ("17", "Congenital malformations"),
    "R00-R99": ("18", "Symptoms, signs and abnormal clinical findings"),
    "S00-T88": ("19", "Injury, poisoning"),
    "V00-Y99": ("20", "External causes of morbidity"),
    "Z00-Z99": ("21", "Factors influencing health status"),
}


def _derive_chapter(code: str) -> tuple[str, str]:
    """Derive ICD-10-CM chapter from code."""
    if not code or len(code) < 1:
        return ("", "")
    first_char = code[0].upper()
    for range_str, (chapter, desc) in CHAPTER_MAP.items():
        start, end = range_str.split("-")
        if start[0] <= first_char <= end[0]:
            return (chapter, desc)
    return ("", "")


def _transform_icd10cm(df: pd.DataFrame) -> pd.DataFrame:
    """Format codes, derive chapters, set billability."""
    # Strip and uppercase
    df["icd10_cm_code"] = df["icd10_cm_code"].str.strip().str.upper().str.replace(".", "", regex=False)

    # Formatted version with dot (e.g., E119 → E11.9)
    df["icd10_cm_code_formatted"] = df["icd10_cm_code"].apply(
        lambda c: c[:3] + "." + c[3:] if len(c) > 3 else c
    )

    # Billable = codes with >= 3 characters after the category (varies by code)
    # Simplified: header codes (3-char) are non-billable; longer codes are billable
    df["is_billable"] = df["icd10_cm_code"].str.len() > 3

    # Derive chapter
    chapters = df["icd10_cm_code"].apply(_derive_chapter)
    df["chapter"] = chapters.apply(lambda x: x[0])
    df["chapter_description"] = chapters.apply(lambda x: x[1])

    return df


config = ReferenceSourceConfig(
    source_name="icd10cm",
    target_table="ref_icd10_cm",
    column_mapping={
        "code": "icd10_cm_code",
        "short_description": "description_short",
        "long_description": "description_long",
    },
    required_source_columns=["code"],
    select_columns=[
        "icd10_cm_code", "icd10_cm_code_formatted", "description_short",
        "description_long", "chapter", "chapter_description", "is_billable",
    ],
    min_rows=60_000,
    max_rows=100_000,
    transform_fn=_transform_icd10cm,
    file_pattern="*icd10cm*.txt",
    read_options={"sep": "\t", "header": None, "names": ["code", "short_description", "long_description"]},
)


def run(source_path=None, run_date=None):
    return run_reference_pipeline(config, run_date=run_date, source_path=source_path)
