"""RxNorm Drug Names and Codes pipeline.

Source: NLM RxNorm (~400K concepts)
Outputs:
  - data/processed/rxnorm/rxnorm.parquet
  - reference.ref_rxnorm (PostgreSQL)
  - reference.ref_ndc_rxcui (NDC↔RXCUI crosswalk)

RxNorm files use RRF format (pipe-delimited, no header).
The key files are RXNCONSO.RRF (concepts) and RXNSAT.RRF (attributes including NDC).
"""

from datetime import date
from pathlib import Path

import pandas as pd

from pipelines._common.acquire import download_file, extract_zip, resolve_landing_path
from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.db import copy_dataframe_to_pg, write_parquet
from pipelines._common.logging import get_logger
from pipelines._common.transform import add_snapshot_metadata, normalize_ndc_series
from pipelines._common.validate import (
    ValidationReport,
    check_column_not_null,
    check_required_columns,
    check_row_count,
)

log = get_logger(source="rxnorm")

# RXNCONSO.RRF columns (pipe-delimited, no header)
RXNCONSO_COLUMNS = [
    "rxcui", "lat", "ts", "lui", "stt", "sui", "ispref", "rxaui",
    "saui", "scui", "sdui", "sab", "tty", "code", "str_name", "srl",
    "suppress", "cvf",
]

RXNSAT_COLUMNS = [
    "rxcui", "lui", "sui", "rxaui", "stype", "code", "atui",
    "satui", "atn", "sab", "atv", "suppress", "cvf",
]


def validate_rxnorm(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport(source="rxnorm")
    check_required_columns(df, ["rxcui", "str_name"], report)
    check_column_not_null(df, "rxcui", report, severity="BLOCK")
    check_row_count(df, min_rows=100_000, max_rows=1_000_000, report=report, severity="WARN")
    return report


def read_rrf(filepath: Path, columns: list[str]) -> pd.DataFrame:
    """Read an RRF pipe-delimited file (no header, trailing pipe)."""
    df = pd.read_csv(
        filepath, sep="|", header=None, dtype=str,
        names=columns + ["_trailing"],  # RRF has trailing pipe
        low_memory=False,
    )
    df = df.drop(columns=["_trailing"], errors="ignore")
    return df


def transform_rxnorm(df: pd.DataFrame) -> pd.DataFrame:
    # Filter to RXNORM source (SAB=RXNORM) and preferred terms
    if "sab" in df.columns:
        df = df[df["sab"] == "RXNORM"].copy()

    # Rename for output
    df = df.rename(columns={"str_name": "name"})

    # Keep useful columns
    keep_cols = ["rxcui", "rxaui", "name", "tty", "suppress"]
    df = df[[c for c in keep_cols if c in df.columns]]

    # Deduplicate by rxcui (keep first preferred name)
    df = df.drop_duplicates(subset=["rxcui"], keep="first")

    df = add_snapshot_metadata(df, "rxnorm")
    return df


def extract_ndc_crosswalk(sat_df: pd.DataFrame) -> pd.DataFrame:
    """Extract NDC-RXCUI mappings from RXNSAT where ATN=NDC."""
    ndc_rows = sat_df[sat_df["atn"] == "NDC"].copy()
    ndc_rows = ndc_rows.rename(columns={"atv": "ndc"})
    ndc_rows = ndc_rows[["rxcui", "ndc"]].drop_duplicates()

    # Normalize NDC to 11 digits
    ndc_rows["ndc"] = normalize_ndc_series(ndc_rows["ndc"])

    return ndc_rows


def run(source_path: Path | None = None, run_date: date | None = None) -> dict[str, int]:
    run_date = run_date or date.today()
    settings = get_pipeline_settings()
    results: dict[str, int] = {}

    log.info("rxnorm_start", run_date=str(run_date))

    if source_path:
        landing = source_path if source_path.is_dir() else source_path.parent
    else:
        source_def = get_source("rxnorm")
        landing = resolve_landing_path("rxnorm", run_date)
        downloaded = download_file(source_def.url, landing)
        if downloaded.suffix == ".zip":
            extract_zip(downloaded, landing)

    # Find RRF files
    conso_files = list(landing.rglob("RXNCONSO.RRF"))
    sat_files = list(landing.rglob("RXNSAT.RRF"))

    if not conso_files:
        raise FileNotFoundError(f"RXNCONSO.RRF not found in {landing}")

    # Read concepts
    conso_df = read_rrf(conso_files[0], RXNCONSO_COLUMNS)
    log.info("rxnconso_read", rows=len(conso_df))

    report = validate_rxnorm(conso_df)
    report.raise_if_blocked()

    df = transform_rxnorm(conso_df)
    results["rxnorm_concepts"] = len(df)

    # Write concept Parquet
    parquet_path = PROJECT_ROOT / settings.storage.processed_base / "rxnorm" / "rxnorm.parquet"
    write_parquet(df, parquet_path)
    results["rxnorm_parquet"] = len(df)

    # Load concepts to PG
    rows = copy_dataframe_to_pg(df, "ref_rxnorm", "reference", if_exists="replace")
    results["ref_rxnorm"] = rows

    # NDC crosswalk (if RXNSAT available)
    if sat_files:
        sat_df = read_rrf(sat_files[0], RXNSAT_COLUMNS)
        ndc_xwalk = extract_ndc_crosswalk(sat_df)
        ndc_xwalk = add_snapshot_metadata(ndc_xwalk, "rxnorm")
        results["ndc_rxcui_mappings"] = len(ndc_xwalk)

        ndc_parquet = PROJECT_ROOT / settings.storage.processed_base / "rxnorm" / "ndc_rxcui.parquet"
        write_parquet(ndc_xwalk, ndc_parquet)

        xwalk_cols = [c for c in ["ndc", "rxcui"] if c in ndc_xwalk.columns]
        rows = copy_dataframe_to_pg(ndc_xwalk[xwalk_cols], "ref_ndc_rxcui", "reference", if_exists="replace")
        results["ref_ndc_rxcui"] = rows

    log.info("rxnorm_complete", **results)
    return results
