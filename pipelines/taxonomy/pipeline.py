"""NUCC Health Care Provider Taxonomy pipeline.

Source: NUCC.org taxonomy code set
Target: reference.ref_nucc_taxonomy (~900 rows)
"""

import pandas as pd

from pipelines._common.logging import get_logger
from pipelines._common.reference import ReferenceSourceConfig, run_reference_pipeline

log = get_logger(source="taxonomy")


def _transform_taxonomy(df: pd.DataFrame) -> pd.DataFrame:
    """Build display_name and is_individual flag."""
    # Display name: classification + specialization
    df["display_name"] = df["classification"].fillna("")
    mask = df["specialization"].notna() & (df["specialization"] != "")
    df.loc[mask, "display_name"] = df.loc[mask, "classification"] + " - " + df.loc[mask, "specialization"]

    # Individual vs. organization heuristic based on grouping
    org_groups = {"agencies", "suppliers", "group", "hospital", "laboratory", "pharmacy", "facility"}
    df["is_individual"] = ~df["grouping"].fillna("").str.lower().apply(lambda g: any(k in g for k in org_groups))
    return df


config = ReferenceSourceConfig(
    source_name="taxonomy",
    target_table="ref_nucc_taxonomy",
    column_mapping={
        "Code": "taxonomy_code",
        "Grouping": "grouping",
        "Classification": "classification",
        "Specialization": "specialization",
        "Definition": "definition",
    },
    required_source_columns=["Code", "Classification"],
    select_columns=[
        "taxonomy_code",
        "grouping",
        "classification",
        "specialization",
        "definition",
        "display_name",
        "is_individual",
    ],
    min_rows=800,
    max_rows=1500,
    transform_fn=_transform_taxonomy,
    file_pattern="*.csv",
)


def run(source_path=None, run_date=None):
    return run_reference_pipeline(config, run_date=run_date, source_path=source_path)
