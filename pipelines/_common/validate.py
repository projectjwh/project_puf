"""Data validation utilities for pipeline quality gates.

Implements BLOCK (stops pipeline) and WARN (logs, continues) severity checks.
All results are recorded for catalog.validation_runs storage.
"""

import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from pipelines._common.logging import get_logger

log = get_logger(stage="validate")


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    rule_name: str
    severity: str  # BLOCK, WARN, INFO
    passed: bool
    metric_value: str = ""
    threshold: str = ""
    message: str = ""
    rows_affected: int = 0


@dataclass
class ValidationReport:
    """Collection of validation results for a single load."""

    source: str
    results: list[ValidationResult] = field(default_factory=list)
    run_id: int | None = None
    _quarantine_masks: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def passed(self) -> bool:
        """True if no BLOCK-severity checks failed."""
        return not any(r.severity == "BLOCK" and not r.passed for r in self.results)

    @property
    def block_failures(self) -> list[ValidationResult]:
        return [r for r in self.results if r.severity == "BLOCK" and not r.passed]

    @property
    def warnings(self) -> list[ValidationResult]:
        return [r for r in self.results if r.severity == "WARN" and not r.passed]

    def add(self, result: ValidationResult) -> None:
        self.results.append(result)
        if not result.passed:
            log_fn = log.error if result.severity == "BLOCK" else log.warning
            log_fn(
                "validation_failed",
                source=self.source,
                rule=result.rule_name,
                severity=result.severity,
                metric=result.metric_value,
                threshold=result.threshold,
                message=result.message,
            )

    def add_quarantine_mask(self, rule_name: str, mask: Any) -> None:
        """Record a boolean mask of rows that failed a validation check.

        Masks are accumulated and applied in a single pass via apply_quarantine().
        """
        self._quarantine_masks[rule_name] = mask

    def persist(self) -> None:
        """Persist all validation results to catalog.validation_runs.

        No-op if run_id is not set or is negative (tracking disabled).
        """
        if self.run_id is None or self.run_id < 0:
            return
        from pipelines._common.catalog import persist_validation_report
        persist_validation_report(self, self.run_id)

    def raise_if_blocked(self) -> None:
        """Raise ValueError if any BLOCK-severity checks failed.

        Persists validation results before raising so blocked runs
        still have their audit trail recorded.
        """
        if not self.passed:
            self.persist()
            failures = "; ".join(f"{r.rule_name}: {r.message}" for r in self.block_failures)
            raise ValueError(f"Validation BLOCKED for {self.source}: {failures}")


# ---------------------------------------------------------------------------
# Quarantine application
# ---------------------------------------------------------------------------

def apply_quarantine(
    df: pd.DataFrame,
    report: ValidationReport,
    run_id: int = -1,
) -> pd.DataFrame:
    """Apply accumulated quarantine masks to remove failing rows.

    For each mask in the report, moves failing rows to catalog.quarantine_rows
    (if quarantine is enabled and run tracking is active), then returns the
    clean DataFrame.

    Masks are OR'd: a row quarantined by ANY rule is removed.
    """
    from pipelines._common.config import get_pipeline_settings

    if not report._quarantine_masks:
        return df

    settings = get_pipeline_settings()
    if not settings.quarantine_enabled:
        return df

    # Combine all masks with OR — any rule failure quarantines the row
    combined_mask = pd.Series(False, index=df.index)
    for mask in report._quarantine_masks.values():
        combined_mask = combined_mask | mask.reindex(df.index, fill_value=False)

    if not combined_mask.any():
        return df

    # Write quarantined rows per rule for granular tracking
    from pipelines._common.catalog import write_quarantine_rows

    clean_df = df
    for rule_name, mask in report._quarantine_masks.items():
        aligned_mask = mask.reindex(clean_df.index, fill_value=False)
        if aligned_mask.any():
            clean_df = write_quarantine_rows(
                clean_df, aligned_mask, rule_name, run_id, report.source,
            )

    return clean_df


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

def check_required_columns(df: pd.DataFrame, expected: list[str], report: ValidationReport) -> None:
    """Verify all expected columns are present. Severity: BLOCK."""
    missing = set(expected) - set(df.columns)
    report.add(ValidationResult(
        rule_name="required_columns",
        severity="BLOCK",
        passed=len(missing) == 0,
        metric_value=str(sorted(missing)) if missing else "all_present",
        threshold=str(expected),
        message=f"Missing columns: {sorted(missing)}" if missing else "",
    ))


def check_column_not_null(df: pd.DataFrame, column: str, report: ValidationReport, severity: str = "BLOCK") -> None:
    """Verify a column has zero null values."""
    null_mask = df[column].isna()
    null_count = int(null_mask.sum())
    report.add(ValidationResult(
        rule_name=f"{column}_not_null",
        severity=severity,
        passed=null_count == 0,
        metric_value=str(null_count),
        threshold="0",
        message=f"{null_count:,} null values in {column}" if null_count > 0 else "",
        rows_affected=null_count,
    ))
    if null_count > 0:
        report.add_quarantine_mask(f"{column}_not_null", null_mask)


def check_column_format(
    df: pd.DataFrame,
    column: str,
    pattern: str,
    report: ValidationReport,
    severity: str = "BLOCK",
) -> None:
    """Verify all non-null values in a column match a regex pattern."""
    non_null = df[column].dropna().astype(str)
    if len(non_null) == 0:
        return  # Nothing to check
    regex = re.compile(pattern)
    invalid_mask_partial = ~non_null.str.match(regex)
    invalid = non_null[invalid_mask_partial]
    report.add(ValidationResult(
        rule_name=f"{column}_format",
        severity=severity,
        passed=len(invalid) == 0,
        metric_value=str(len(invalid)),
        threshold=f"pattern={pattern}",
        message=f"{len(invalid):,} rows don't match {pattern}" if len(invalid) > 0 else "",
        rows_affected=len(invalid),
    ))
    if len(invalid) > 0:
        # Build full-index mask (False for null rows, True for format failures)
        full_mask = pd.Series(False, index=df.index)
        full_mask.loc[invalid.index] = True
        report.add_quarantine_mask(f"{column}_format", full_mask)


def check_uniqueness(df: pd.DataFrame, columns: list[str], report: ValidationReport, severity: str = "BLOCK") -> None:
    """Verify no duplicate rows for the given key columns."""
    dupes = df.duplicated(subset=columns, keep=False).sum()
    report.add(ValidationResult(
        rule_name=f"{'_'.join(columns)}_unique",
        severity=severity,
        passed=int(dupes) == 0,
        metric_value=str(int(dupes)),
        threshold="0",
        message=f"{int(dupes):,} duplicate rows on {columns}" if dupes > 0 else "",
        rows_affected=int(dupes),
    ))


def check_row_count(
    df: pd.DataFrame,
    min_rows: int,
    max_rows: int,
    report: ValidationReport,
    severity: str = "WARN",
) -> None:
    """Verify row count is within expected range."""
    count = len(df)
    in_range = min_rows <= count <= max_rows
    report.add(ValidationResult(
        rule_name="row_count_range",
        severity=severity,
        passed=in_range,
        metric_value=str(count),
        threshold=f"[{min_rows:,}, {max_rows:,}]",
        message=f"Row count {count:,} outside expected range [{min_rows:,}, {max_rows:,}]" if not in_range else "",
        rows_affected=0 if in_range else count,
    ))


def check_value_set(
    df: pd.DataFrame,
    column: str,
    allowed_values: set[Any],
    report: ValidationReport,
    severity: str = "BLOCK",
) -> None:
    """Verify all non-null values in a column are in the allowed set."""
    non_null = df[column].dropna()
    invalid_mask_partial = ~non_null.isin(allowed_values)
    invalid = non_null[invalid_mask_partial]
    unique_invalid = set(invalid.unique())
    report.add(ValidationResult(
        rule_name=f"{column}_value_set",
        severity=severity,
        passed=len(invalid) == 0,
        metric_value=str(sorted(unique_invalid)[:10]) if unique_invalid else "all_valid",
        threshold=str(sorted(allowed_values)),
        message=f"{len(invalid):,} rows with invalid values: {sorted(unique_invalid)[:5]}" if invalid.any() else "",
        rows_affected=len(invalid),
    ))
    if len(invalid) > 0:
        full_mask = pd.Series(False, index=df.index)
        full_mask.loc[invalid.index] = True
        report.add_quarantine_mask(f"{column}_value_set", full_mask)


def check_null_rate(
    df: pd.DataFrame,
    column: str,
    max_rate: float,
    report: ValidationReport,
    severity: str = "WARN",
) -> None:
    """Verify null rate for a column doesn't exceed threshold."""
    null_count = int(df[column].isna().sum())
    rate = null_count / len(df) if len(df) > 0 else 0
    report.add(ValidationResult(
        rule_name=f"{column}_null_rate",
        severity=severity,
        passed=rate <= max_rate,
        metric_value=f"{rate:.4f}",
        threshold=f"<={max_rate:.4f}",
        message=f"{column} null rate {rate:.2%} exceeds {max_rate:.2%}" if rate > max_rate else "",
        rows_affected=null_count,
    ))


def check_value_range(
    df: pd.DataFrame,
    column: str,
    min_val: float | None = None,
    max_val: float | None = None,
    report: ValidationReport | None = None,
    severity: str = "WARN",
) -> None:
    """Verify numeric values are within a specified range."""
    if report is None:
        return
    non_null = pd.to_numeric(df[column], errors="coerce").dropna()
    violations = 0
    if min_val is not None:
        violations += int((non_null < min_val).sum())
    if max_val is not None:
        violations += int((non_null > max_val).sum())
    report.add(ValidationResult(
        rule_name=f"{column}_value_range",
        severity=severity,
        passed=violations == 0,
        metric_value=str(violations),
        threshold=f"[{min_val}, {max_val}]",
        message=f"{violations:,} values outside [{min_val}, {max_val}] in {column}" if violations > 0 else "",
        rows_affected=violations,
    ))


def check_referential_integrity(
    df: pd.DataFrame,
    column: str,
    reference_df: pd.DataFrame,
    ref_column: str,
    min_match_rate: float,
    report: ValidationReport,
    severity: str = "WARN",
) -> None:
    """Check that values in column exist in a reference table at a minimum rate."""
    non_null = df[column].dropna()
    ref_values = set(reference_df[ref_column].dropna())
    match_mask = non_null.isin(ref_values)
    matched = match_mask.sum()
    match_rate = int(matched) / len(non_null) if len(non_null) > 0 else 1.0
    unmatched = len(non_null) - int(matched)
    report.add(ValidationResult(
        rule_name=f"{column}_referential_integrity",
        severity=severity,
        passed=match_rate >= min_match_rate,
        metric_value=f"{match_rate:.4f}",
        threshold=f">={min_match_rate:.4f}",
        message=f"{unmatched:,} unmatched {column} values ({match_rate:.2%} match rate)" if match_rate < min_match_rate else "",
        rows_affected=unmatched,
    ))
    if match_rate < min_match_rate:
        full_mask = pd.Series(False, index=df.index)
        unmatched_idx = non_null[~match_mask].index
        full_mask.loc[unmatched_idx] = True
        report.add_quarantine_mask(f"{column}_referential_integrity", full_mask)


def check_row_count_delta(
    current_count: int,
    previous_count: int,
    max_pct_change: float,
    report: ValidationReport,
    severity: str = "WARN",
) -> None:
    """Check that row count hasn't changed by more than a percentage."""
    if previous_count == 0:
        return  # No baseline to compare
    pct_change = abs(current_count - previous_count) / previous_count
    report.add(ValidationResult(
        rule_name="row_count_delta",
        severity=severity,
        passed=pct_change <= max_pct_change,
        metric_value=f"{pct_change:.4f}",
        threshold=f"<={max_pct_change:.4f}",
        message=(
            f"Row count changed by {pct_change:.2%} ({previous_count:,} → {current_count:,})"
            if pct_change > max_pct_change else ""
        ),
    ))
