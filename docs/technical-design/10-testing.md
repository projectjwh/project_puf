# 10. Testing Strategy

[← Back to Index](index.md) | [← Frontend](09-frontend.md)

---

## Test Inventory

Source: `tests/` (16 files, 258 tests — last run: 258 passed, 11 skipped)

| File | Tests | Category |
|------|-------|----------|
| `test_common_validate.py` | 25 | Validation framework checks |
| `test_api_schemas.py` | 22 | Pydantic schema validation |
| `test_common_transform.py` | 22 | NPI/FIPS/NDC normalization, type casting |
| `test_reference_pipelines.py` | 18 | Reference data pipeline runners |
| `test_tier2_hospital_ma_pipelines.py` | 17 | Hospital + MA pipeline transforms |
| `test_tier2_provider_geo_pipelines.py` | 16 | Provider + geographic pipeline transforms |
| `test_tier2_drug_quality_pipelines.py` | 15 | Drug + quality pipeline transforms |
| `test_nppes_pipeline.py` | 14 | NPPES acquisition + transform |
| `test_tier2_utilization_pipelines.py` | 12 | Utilization pipeline transforms |
| `test_partb_pipeline.py` | 11 | Part B pipeline (totals-from-averages) |
| `test_partd_pipeline.py` | 11 | Part D pipeline (opioid flag, aggregation) |
| `test_common_config.py` | 9 | Configuration loading + validation |
| `test_common_acquire.py` | 9 | HTTP download, hashing, ZIP extraction |
| `test_geovar_pipeline.py` | 9 | Geographic Variation pipeline |
| `test_pos_pipeline.py` | 6 | Provider of Services pipeline |
| `test_cost_reports_pipeline.py` | 5 | Cost reports pipeline |

---

## Test Markers

Source: `pyproject.toml`

| Marker | Purpose | Usage |
|--------|---------|-------|
| `integration` | Tests requiring database or Docker | `pytest -m "not integration"` to skip |
| `slow` | Tests taking >10 seconds | `pytest -m "not slow"` to skip |

Default `make test` runs with `-m "not integration"` to enable fast local development.

---

## Fixture Pattern

Source: `tests/conftest.py`

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `tmp_data_dir` | function | Temp directory with `raw/`, `processed/`, `mart/`, `archive/`, `reference/` subdirectories |
| `sample_npi_df` | function | 5-row DataFrame with NPI, entity type, name, state, ZIP, taxonomy |
| `sample_partb_df` | function | 3-row DataFrame with NPI, HCPCS, service counts, Medicare payments |
| `sample_geovar_df` | function | 4-row DataFrame with geographic levels, FIPS codes, beneficiary counts |
| `sample_zip_file` | function | Test ZIP archive containing CSV for extraction testing |

---

## pytest Configuration

Source: `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
markers = [
    "integration: marks tests requiring database or Docker",
    "slow: marks tests that take >10s",
]
```

Coverage: `pytest --cov=pipelines --cov=flows --cov=api --cov-report=term-missing`

Or via Makefile: `make test-cov`

---

**Next:** [Operations →](11-operations.md)
