"""Structured dbt runner with JSON log parsing and error classification.

Replaces bare ``subprocess.run(["dbt", "run", ...])`` calls with a wrapper
that captures structured output, classifies errors, and returns model-level
results.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pipelines._common.config import PROJECT_ROOT
from pipelines._common.logging import get_logger

log = get_logger(source="dbt_runner")


class DbtErrorType(StrEnum):
    """Classification of dbt failure modes."""

    COMPILE = "compile"
    RUNTIME = "runtime"
    TEST = "test"
    UNKNOWN = "unknown"


@dataclass
class ModelResult:
    """Result for a single dbt model or test."""

    unique_id: str
    status: str  # "success", "error", "skipped", "fail", "warn"
    execution_time: float = 0.0
    message: str = ""


@dataclass
class DbtRunResult:
    """Aggregated result from a ``dbt run`` invocation."""

    success: bool
    models: list[ModelResult] = field(default_factory=list)
    error_type: DbtErrorType | None = None
    error_message: str = ""
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialise for Prefect result storage."""
        return {
            "success": self.success,
            "models_passed": sum(1 for m in self.models if m.status == "success"),
            "models_errored": sum(1 for m in self.models if m.status == "error"),
            "models_skipped": sum(1 for m in self.models if m.status == "skipped"),
            "error_type": self.error_type.value if self.error_type else None,
            "error_message": self.error_message,
            "model_details": [
                {
                    "unique_id": m.unique_id,
                    "status": m.status,
                    "execution_time": m.execution_time,
                    "message": m.message,
                }
                for m in self.models
            ],
        }


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

_COMPILE_MARKERS = [
    "Compilation Error",
    "CompilationError",
    "parsing error",
    "YML Error",
    "schema.yml",
    "Could not find",
]

_RUNTIME_MARKERS = [
    "Runtime Error",
    "RuntimeError",
    "Database Error",
    "DatabaseError",
    "Encountered an error",
    "relation",
    "column",
    "Permission denied",
]

_TEST_MARKERS = [
    "test failure",
    "Test failure",
    "Failure in test",
    "FAIL ",
]


def classify_error(stderr: str, stdout: str) -> DbtErrorType:
    """Classify a dbt error based on output text."""
    combined = stderr + stdout
    for marker in _COMPILE_MARKERS:
        if marker in combined:
            return DbtErrorType.COMPILE
    for marker in _TEST_MARKERS:
        if marker in combined:
            return DbtErrorType.TEST
    for marker in _RUNTIME_MARKERS:
        if marker in combined:
            return DbtErrorType.RUNTIME
    return DbtErrorType.UNKNOWN


# ---------------------------------------------------------------------------
# JSON log parsing
# ---------------------------------------------------------------------------


def _parse_json_logs(raw_stdout: str) -> list[ModelResult]:
    """Extract per-model results from dbt ``--log-format json`` output."""
    results: list[ModelResult] = []
    for line in raw_stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        # dbt 1.x/core emits structured log entries with 'data' key
        data = entry.get("data", {})
        node_info = data.get("node_info", {})

        # We care about "NodeFinished" events (LogModelResult, LogTestResult, etc.)
        if node_info.get("node_status") in ("success", "error", "fail", "warn", "skipped"):
            results.append(
                ModelResult(
                    unique_id=node_info.get("unique_id", ""),
                    status=node_info.get("node_status", ""),
                    execution_time=float(node_info.get("execution_time", 0.0) or 0.0),
                    message=data.get("description", ""),
                )
            )
    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_dbt(
    select: str = "tag:intermediate tag:mart",
    project_dir: str | None = None,
    profiles_dir: str | None = None,
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    """Run dbt with structured output capture.

    Args:
        select: dbt ``--select`` expression.
        project_dir: Path to the dbt project directory. Defaults to
            ``<project_root>/models``.
        profiles_dir: Optional ``--profiles-dir`` override.
        extra_args: Additional CLI arguments forwarded to dbt.

    Returns:
        Dict with model results (via ``DbtRunResult.to_dict()``).

    Raises:
        RuntimeError: If dbt exits with a non-zero code and the error is
            classified as a compile error (irrecoverable).
    """
    project_dir = project_dir or str(PROJECT_ROOT / "models")
    cmd: list[str] = [
        "dbt",
        "run",
        "--select",
        select,
        "--log-format",
        "json",
    ]
    if profiles_dir:
        cmd.extend(["--profiles-dir", profiles_dir])
    if extra_args:
        cmd.extend(extra_args)

    log.info("dbt_run_start", select=select, project_dir=project_dir)

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=project_dir,
    )

    models = _parse_json_logs(proc.stdout)

    if proc.returncode != 0:
        error_type = classify_error(proc.stderr, proc.stdout)
        error_msg = proc.stderr.strip() or proc.stdout.strip()
        # Truncate very long error messages
        if len(error_msg) > 2000:
            error_msg = error_msg[:2000] + "...(truncated)"

        result = DbtRunResult(
            success=False,
            models=models,
            error_type=error_type,
            error_message=error_msg,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
        log.error(
            "dbt_run_failed",
            error_type=error_type.value,
            returncode=proc.returncode,
            models_passed=sum(1 for m in models if m.status == "success"),
            models_errored=sum(1 for m in models if m.status == "error"),
        )
        return result.to_dict()

    result = DbtRunResult(
        success=True,
        models=models,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )
    log.info(
        "dbt_run_complete",
        models_passed=sum(1 for m in models if m.status == "success"),
        models_skipped=sum(1 for m in models if m.status == "skipped"),
    )
    return result.to_dict()
