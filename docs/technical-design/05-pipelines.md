# 5. Data Pipeline Architecture

[← Back to Index](index.md) | [← Database](04-database.md)

---

## Pipeline Lifecycle (8 Stages)

```d2
direction: right

idle: Idle {style.fill: "#e2e8f0"; shape: circle}
discovering: Discovering {style.fill: "#fef3c7"}
acquiring: Acquiring {style.fill: "#fed7aa"}
validating: Validating {style.fill: "#fecaca"}
transforming: Transforming {style.fill: "#e9d5ff"}
loading: Loading {style.fill: "#bfdbfe"}
storing: Storing {style.fill: "#bbf7d0"}
modeling: Modeling {style.fill: "#a7f3d0"}
serving: Serving {style.fill: "#93c5fd"; shape: double_circle}
failed: Failed {style.fill: "#fca5a5"; shape: circle}

idle -> discovering -> acquiring -> validating -> transforming -> loading -> storing -> modeling -> serving
validating -> failed: "BLOCK"  {style.stroke: "#ef4444"}
acquiring -> failed: "3 retries exhausted" {style.stroke: "#ef4444"}
validating -> validating: "WARN: log + continue" {style.stroke: "#f59e0b"; style.stroke-dash: 3}
```

Full diagram: [`diagrams/pipeline-state-machine.d2`](diagrams/pipeline-state-machine.d2)

1. **Discover**: Read source definition from `config/sources.yaml`
2. **Acquire**: Download file via HTTP with retry (3 attempts: 5min, 15min, 45min delays), compute SHA-256 hash, extract ZIP if needed
3. **Validate**: Run quality checks against data (BLOCK failures halt pipeline, WARN failures log and continue)
4. **Transform**: Normalize identifiers (NPI, FIPS, NDC), cast types, rename columns, compute derived fields
5. **Load**: Bulk COPY into PostgreSQL staging/reference tables
6. **Store**: Write Parquet to `data/processed/` for DuckDB consumption
7. **Model**: dbt transforms staging → intermediate → mart
8. **Serve**: FastAPI reads mart tables and Parquet files

---

## Shared Utility Layer

Source: `pipelines/_common/` (7 modules)

| Module | Key Functions | Purpose |
|--------|--------------|---------|
| `config.py` | `get_database_settings()`, `get_pipeline_settings()`, `get_sources()`, `get_source(name)` | Pydantic-validated config loading from YAML with env var overrides |
| `logging.py` | `setup_logging(level)`, `get_logger(source, stage)` | structlog JSON logging with bound context (source, stage, run_id) |
| `acquire.py` | `acquire_source()`, `download_file()`, `compute_hash()`, `extract_zip()`, `check_hash_changed()` | HTTP download with retry, SHA-256 hashing, ZIP extraction, freshness detection |
| `validate.py` | `ValidationReport`, `ValidationResult`, 10 check functions | BLOCK/WARN validation framework (see below) |
| `transform.py` | `normalize_npi()`, `normalize_ndc_to_11()`, `compute_totals_from_averages()`, `cast_types()` | NPI/FIPS/NDC normalization, type casting, snapshot metadata |
| `db.py` | `copy_dataframe_to_pg()`, `get_pg_engine()`, `read_parquet()`, `write_parquet()` | PostgreSQL bulk COPY, DuckDB Parquet I/O |
| `reference.py` | `run_reference_pipeline(config)`, `ReferenceSourceConfig` | Generic pipeline runner for reference/lookup data |

---

## Validation Framework

Source: `pipelines/_common/validate.py`

### Dataclass Definitions

```python
@dataclass
class ValidationResult:
    rule_name: str
    severity: str       # BLOCK, WARN, INFO
    passed: bool
    metric_value: str
    threshold: str
    message: str
    rows_affected: int

@dataclass
class ValidationReport:
    source: str
    results: list[ValidationResult]

    @property
    def passed(self) -> bool:
        """True if no BLOCK-severity checks failed."""

    def raise_if_blocked(self) -> None:
        """Raise ValueError if any BLOCK checks failed."""
```

### Severity Model

| Severity | Behavior | Example |
|----------|----------|---------|
| `BLOCK` | Halts pipeline, records failure in `catalog.pipeline_failures` | Missing required column, duplicate primary keys |
| `WARN` | Logs warning, continues processing, records in `catalog.validation_runs` | Row count outside expected range, high null rate |
| `INFO` | Logs info only | Informational metrics |

Escalation: If >10% of rows fail WARN rules, severity escalates to BLOCK (`pipeline.yaml`: `warn_escalation_threshold: 0.10`).

### Validation Check Functions (10)

| Function | Default Severity | Purpose |
|----------|-----------------|---------|
| `check_required_columns()` | BLOCK | All expected columns present |
| `check_column_not_null()` | BLOCK | Zero nulls in column |
| `check_column_format()` | BLOCK | Values match regex pattern |
| `check_uniqueness()` | BLOCK | No duplicate rows for key columns |
| `check_value_set()` | BLOCK | Values in allowed set |
| `check_row_count()` | WARN | Row count within expected range |
| `check_null_rate()` | WARN | Null rate below threshold |
| `check_value_range()` | WARN | Numeric values within bounds |
| `check_referential_integrity()` | WARN | Values exist in reference table at minimum rate |
| `check_row_count_delta()` | WARN | Row count change from previous load within percentage |

---

## Critical Transform: Totals from Averages

Source: `pipelines/_common/transform.py`

CMS publishes Part B data with **average** charges and payments, not totals. The pipeline reconstructs totals:

```python
def compute_totals_from_averages(df, avg_col, count_col, total_col):
    """total_charge = avg_charge * service_count"""
    df[total_col] = (
        pd.to_numeric(df[avg_col], errors="coerce")
        * pd.to_numeric(df[count_col], errors="coerce")
    )
    return df
```

This produces `total_medicare_payment`, `total_submitted_charge`, and `total_allowed_amount` columns used throughout intermediate and mart models.

---

## NDC 10→11 Digit Normalization

Source: `pipelines/_common/transform.py`

NDCs come in three 10-digit dash-separated formats. The pipeline normalizes to 11-digit (5-4-2) plain format:

```python
def normalize_ndc_to_11(ndc: str) -> str:
    """
    4-4-2 → 04-4-2 (pad labeler)
    5-3-2 → 5-03-2 (pad product)
    5-4-1 → 5-4-01 (pad package)  ← most common, default
    """
    digits = ndc.replace("-", "").replace(" ", "")
    if len(digits) == 11:
        return digits
    elif len(digits) == 10:
        return digits[:5] + digits[5:9] + "0" + digits[9]
    else:
        return digits
```

---

## Per-Source Pipeline Pattern

Each source has a dedicated module in `pipelines/{source}/` with a standard structure:

```
pipelines/nppes/
├── __init__.py          # Exports run_pipeline()
├── pipeline.py          # acquire → validate → transform → load
├── validate.py          # Source-specific validation rules
└── transform.py         # Source-specific transformations
```

**NPPES pipeline walkthrough** (representative of all source pipelines):

1. **Acquire**: Download ~4GB ZIP from CMS, extract CSV, compute SHA-256
2. **Validate**: Check NPI format (`^\d{10}$`), required columns, row count (7M–10M, BLOCK severity)
3. **Transform**: Normalize NPI, extract ZIP5, standardize entity type flags, clean names
4. **Load**: Bulk COPY to `reference.nppes_providers` via psycopg2 COPY protocol

---

## Prefect Orchestration

Source: `flows/` (8 flow definitions)

```d2
direction: right

util_flow: "utilization-full-refresh" {
  style.fill: "#fef3c7"
  style.stroke: "#f59e0b"

  ingest: "Phase 1 (parallel)" {
    style.fill: "#fed7aa"
    partb: "Part B" {style.fill: "#93c5fd"}
    partd: "Part D" {style.fill: "#93c5fd"}
    geovar: "GeoVar" {style.fill: "#93c5fd"}
  }
  dbt: "Phase 2: dbt run" {style.fill: "#a7f3d0"}
  export: "Phase 3: Parquet export" {style.fill: "#c4b5fd"}

  ingest -> dbt: "all 3 complete"
  dbt -> export
}
```

Full diagram: [`diagrams/prefect-orchestration.d2`](diagrams/prefect-orchestration.d2)

| Flow | File | Task Composition |
|------|------|-----------------|
| `load-reference-data` | `reference_flow.py` | Phase 1: 11 reference loads in parallel; Phase 2: 3 fee schedule loads (depends on Phase 1) |
| `nppes-acquisition` | `nppes_flow.py` | Single task: full NPPES pipeline (retries=2, backoff=5m/15m) |
| `pos-acquisition` | `pos_flow.py` | Single task: POS facilities pipeline (retries=2) |
| `cost-reports-acquisition` | `cost_reports_flow.py` | Single task: hospital cost reports |
| `partb-utilization` | `partb_flow.py` | Single task: Part B pipeline for a given data_year (task_input_hash cache) |
| `partd-prescribers` | `partd_flow.py` | Single task: Part D pipeline for a given data_year (task_input_hash cache) |
| `geovar-geographic-variation` | `geovar_flow.py` | Single task: Geographic Variation pipeline (task_input_hash cache) |
| `utilization-full-refresh` | `utilization_flow.py` | Master: Part B + Part D + GeoVar in parallel → dbt run → Parquet export |

---

**Next:** [Data Models →](06-data-models.md)
