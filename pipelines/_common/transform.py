"""Data transformation utilities shared across all pipelines.

Handles NPI/FIPS normalization, column renaming, type casting,
schema mapping, and snapshot metadata injection.
"""

from datetime import date

import pandas as pd

from pipelines._common.logging import get_logger

log = get_logger(stage="transform")


# ---------------------------------------------------------------------------
# NPI normalization
# ---------------------------------------------------------------------------


def normalize_npi(series: pd.Series) -> pd.Series:
    """Validate and zero-pad NPI values to 10 digits.

    NPIs are always stored as VARCHAR(10). This strips whitespace,
    zero-pads short values, and sets invalid values to NaN.
    """
    cleaned = series.astype(str).str.strip()
    # Pad short NPIs with leading zeros
    cleaned = cleaned.str.zfill(10)
    # Invalidate non-10-digit values
    invalid_mask = ~cleaned.str.match(r"^\d{10}$")
    cleaned[invalid_mask] = pd.NA
    invalid_count = int(invalid_mask.sum())
    if invalid_count > 0:
        log.warning("npi_normalization", invalid_count=invalid_count)
    return cleaned


# ---------------------------------------------------------------------------
# FIPS normalization
# ---------------------------------------------------------------------------


def normalize_fips_state(series: pd.Series) -> pd.Series:
    """Zero-pad state FIPS codes to 2 digits. E.g., '6' → '06'."""
    return series.astype(str).str.strip().str.zfill(2)


def normalize_fips_county(series: pd.Series) -> pd.Series:
    """Zero-pad county FIPS codes to 5 digits. E.g., '1001' → '01001'."""
    return series.astype(str).str.strip().str.zfill(5)


def extract_zip5(series: pd.Series) -> pd.Series:
    """Extract 5-digit ZIP from ZIP+4 or other formats. E.g., '90210-1234' → '90210'."""
    return series.astype(str).str.strip().str[:5]


# ---------------------------------------------------------------------------
# NDC normalization
# ---------------------------------------------------------------------------


def normalize_ndc_to_11(ndc: str) -> str:
    """Convert a 10-digit NDC (various formats) to 11-digit (5-4-2).

    NDC formats:
      4-4-2 → 04-4-2 (pad labeler)
      5-3-2 → 5-03-2 (pad product)
      5-4-1 → 5-4-01 (pad package)

    If already 11 digits (with or without dashes), normalize to 5-4-2 plain.
    """
    digits = ndc.replace("-", "").replace(" ", "")

    if len(digits) == 11:
        return digits
    elif len(digits) == 10:
        # Heuristic: try each format pattern
        # Most common is 5-4-1 → pad package
        # We can't always distinguish, so default to 5-4-1 → 5-4-01
        return digits[:5] + digits[5:9] + "0" + digits[9]
    else:
        return digits  # Return as-is if unexpected length


def normalize_ndc_series(series: pd.Series) -> pd.Series:
    """Apply NDC normalization to a pandas Series."""
    return series.astype(str).str.strip().apply(normalize_ndc_to_11)


# ---------------------------------------------------------------------------
# Column renaming and type casting
# ---------------------------------------------------------------------------


def rename_columns(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Rename DataFrame columns using a mapping dict.

    Only renames columns that exist in the DataFrame (ignores missing keys).
    """
    existing_renames = {k: v for k, v in mapping.items() if k in df.columns}
    return df.rename(columns=existing_renames)


def apply_schema_mapping(df: pd.DataFrame, source: str, data_year: int | None = None) -> pd.DataFrame:
    """Apply year-specific column name mapping for a source.

    CMS changes column names across years. This loads the appropriate
    mapping from config and normalizes to canonical names.

    Mappings are stored in config/schema_mappings/{source}.yaml (created per source).
    """
    import yaml

    from pipelines._common.config import CONFIG_DIR

    mapping_file = CONFIG_DIR / "schema_mappings" / f"{source}.yaml"
    if not mapping_file.exists():
        log.debug("no_schema_mapping", source=source, year=data_year)
        return df

    with open(mapping_file) as f:
        mappings = yaml.safe_load(f) or {}

    # Try year-specific mapping first, then default
    year_mapping = mappings.get(str(data_year), mappings.get("default", {}))
    if year_mapping:
        df = rename_columns(df, year_mapping)
        log.info("schema_mapping_applied", source=source, year=data_year, columns_renamed=len(year_mapping))

    return df


def cast_types(df: pd.DataFrame, type_map: dict[str, str]) -> pd.DataFrame:
    """Cast DataFrame columns to specified types.

    Type map values: 'str', 'int', 'float', 'date', 'bool', 'decimal'.
    Uncastable values become NaN (no exceptions raised).
    """
    for col, dtype in type_map.items():
        if col not in df.columns:
            continue
        if dtype == "str":
            df[col] = df[col].astype(str).replace("nan", pd.NA)
        elif dtype in ("int", "integer"):
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        elif dtype in ("float", "decimal"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif dtype == "date":
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
        elif dtype == "bool":
            df[col] = df[col].map(
                {"Y": True, "N": False, "y": True, "n": False, "1": True, "0": False, True: True, False: False}
            )
    return df


# ---------------------------------------------------------------------------
# Snapshot metadata
# ---------------------------------------------------------------------------


def add_snapshot_metadata(df: pd.DataFrame, source: str, run_date: date | None = None) -> pd.DataFrame:
    """Add _loaded_at and _source columns to a DataFrame."""
    df["_loaded_at"] = pd.Timestamp.now()
    df["_source"] = source
    return df


def add_data_year(df: pd.DataFrame, data_year: int) -> pd.DataFrame:
    """Add a data_year column if not already present."""
    if "data_year" not in df.columns:
        df["data_year"] = data_year
    return df


# ---------------------------------------------------------------------------
# Common cleaning
# ---------------------------------------------------------------------------


def clean_string_columns(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Strip whitespace and uppercase string columns.

    If columns is None, applies to all object/string columns.
    """
    if columns is None:
        columns = df.select_dtypes(include=["object", "string"]).columns.tolist()
    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper().replace("NAN", pd.NA)
    return df


def standardize_flags(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Convert Y/N string flags to boolean. NULL remains NULL."""
    for col in columns:
        if col in df.columns:
            df[col] = df[col].map({"Y": True, "N": False, "y": True, "n": False}).astype("boolean")
    return df


def compute_totals_from_averages(
    df: pd.DataFrame,
    avg_col: str,
    count_col: str,
    total_col: str,
) -> pd.DataFrame:
    """Compute total amounts from average and count columns.

    Critical for Part B where CMS provides averages, not totals:
      total_charge = avg_charge * service_count
    """
    df[total_col] = pd.to_numeric(df[avg_col], errors="coerce") * pd.to_numeric(df[count_col], errors="coerce")
    return df
