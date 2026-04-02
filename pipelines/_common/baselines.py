"""Statistical baselines computed from historical validation data.

Computes per-metric baselines from catalog.validation_runs history and flags
values that deviate significantly. Baselines are always WARN severity —
a violation may be a legitimate data change, not necessarily an error.
"""

from __future__ import annotations

import math
from typing import Any

from pipelines._common.logging import get_logger
from pipelines._common.validate import ValidationReport, ValidationResult

log = get_logger(stage="baselines")


def compute_baselines(source: str, lookback_runs: int = 10) -> dict[str, Any]:
    """Compute per-metric baselines from recent successful pipeline runs.

    Queries catalog.validation_runs for the last N successful runs of this
    source and calculates mean, stddev, min, max for numeric metric values.

    Returns:
        Dict keyed by rule_name with baseline stats::

            {"row_count_range": {"mean": 9500000, "stddev": 200000,
             "min": 9100000, "max": 9900000, "sample_count": 8}}

        Empty dict if fewer than 3 historical runs exist.
    """
    from pipelines._common.db import query_pg

    try:
        result = query_pg(
            """
            SELECT v.rule_name,
                   AVG(CAST(v.metric_value AS NUMERIC)) AS baseline_mean,
                   STDDEV(CAST(v.metric_value AS NUMERIC)) AS baseline_stddev,
                   MIN(CAST(v.metric_value AS NUMERIC)) AS baseline_min,
                   MAX(CAST(v.metric_value AS NUMERIC)) AS baseline_max,
                   COUNT(*) AS sample_count
            FROM catalog.validation_runs v
            JOIN catalog.pipeline_runs r ON v.run_id = r.run_id
            JOIN catalog.sources s ON r.source_id = s.source_id
            WHERE s.short_name = :source
              AND r.status = 'success'
              AND v.passed = true
              AND v.metric_value ~ '^[0-9.]+$'
            GROUP BY v.rule_name
            HAVING COUNT(*) >= 3
            ORDER BY v.rule_name
            """,
            params={"source": source},
        )

        if result.empty:
            log.info("no_baselines_available", source=source, reason="insufficient_history")
            return {}

        baselines: dict[str, Any] = {}
        for _, row in result.iterrows():
            baselines[row["rule_name"]] = {
                "mean": float(row["baseline_mean"]),
                "stddev": float(row["baseline_stddev"]) if row["baseline_stddev"] else 0.0,
                "min": float(row["baseline_min"]),
                "max": float(row["baseline_max"]),
                "sample_count": int(row["sample_count"]),
            }

        log.info("baselines_computed", source=source, metrics=len(baselines))
        return baselines

    except Exception as e:
        log.warning("compute_baselines_failed", source=source, error=str(e))
        return {}


def check_against_baseline(
    current_metrics: dict[str, float],
    baselines: dict[str, Any],
    report: ValidationReport,
    z_threshold: float = 2.0,
) -> None:
    """Compare current run metrics against historical baselines.

    Flags values exceeding z_threshold standard deviations from the mean.
    Always WARN severity — baseline violations may be legitimate data changes.

    Args:
        current_metrics: Dict of {rule_name: current_value}.
        baselines: Output of compute_baselines().
        report: ValidationReport to add results to.
        z_threshold: Number of standard deviations to flag (default 2.0).
    """
    for rule_name, current_value in current_metrics.items():
        if rule_name not in baselines:
            continue

        baseline = baselines[rule_name]
        mean = baseline["mean"]
        stddev = baseline["stddev"]

        if stddev == 0 or math.isnan(stddev):
            # All historical values identical — any deviation is notable
            is_deviation = current_value != mean
            z_score = float("inf") if is_deviation else 0.0
        else:
            z_score = abs(current_value - mean) / stddev
            is_deviation = z_score > z_threshold

        report.add(
            ValidationResult(
                rule_name=f"{rule_name}_baseline",
                severity="WARN",
                passed=not is_deviation,
                metric_value=f"{current_value:.2f}",
                threshold=f"mean={mean:.2f}, stddev={stddev:.2f}, z={z_threshold}",
                message=(
                    f"{rule_name} value {current_value:.0f} deviates {z_score:.1f} "
                    f"stddevs from baseline mean {mean:.0f} (n={baseline['sample_count']})"
                    if is_deviation
                    else ""
                ),
            )
        )
