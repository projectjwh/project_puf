"""Tests for pipelines._common.acquire."""

from datetime import date
from pathlib import Path

import pytest

from pipelines._common.acquire import (
    compute_hash,
    extract_zip,
    resolve_landing_path,
    validate_file_size,
)


class TestResolveLandingPath:
    def test_with_run_date(self, monkeypatch, tmp_path):
        monkeypatch.setattr("pipelines._common.acquire.PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(
            "pipelines._common.acquire.get_pipeline_settings",
            lambda: type("S", (), {"storage": type("P", (), {"raw_base": "data/raw"})()})(),
        )
        path = resolve_landing_path("nppes", run_date=date(2026, 3, 4))
        assert path == tmp_path / "data" / "raw" / "nppes" / "2026-03-04"
        assert path.exists()

    def test_with_data_year(self, monkeypatch, tmp_path):
        monkeypatch.setattr("pipelines._common.acquire.PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(
            "pipelines._common.acquire.get_pipeline_settings",
            lambda: type("S", (), {"storage": type("P", (), {"raw_base": "data/raw"})()})(),
        )
        path = resolve_landing_path("partb", data_year=2022)
        assert path == tmp_path / "data" / "raw" / "partb" / "2022"


class TestComputeHash:
    def test_sha256(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        h = compute_hash(test_file)
        assert len(h) == 64  # SHA-256 hex digest
        # Deterministic
        assert compute_hash(test_file) == h

    def test_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("content a")
        f2.write_text("content b")
        assert compute_hash(f1) != compute_hash(f2)


class TestValidateFileSize:
    def test_within_range(self, tmp_path):
        f = tmp_path / "ok.bin"
        f.write_bytes(b"x" * 1000)
        validate_file_size(f, min_bytes=500, max_bytes=2000)

    def test_too_small(self, tmp_path):
        f = tmp_path / "small.bin"
        f.write_bytes(b"x" * 10)
        with pytest.raises(ValueError, match="outside expected range"):
            validate_file_size(f, min_bytes=500, max_bytes=2000)

    def test_too_large(self, tmp_path):
        f = tmp_path / "big.bin"
        f.write_bytes(b"x" * 5000)
        with pytest.raises(ValueError, match="outside expected range"):
            validate_file_size(f, min_bytes=500, max_bytes=2000)


class TestExtractZip:
    def test_extracts_files(self, sample_zip_file):
        extracted = extract_zip(sample_zip_file)
        assert len(extracted) == 1
        assert extracted[0].name == "test.csv"
        assert extracted[0].exists()

    def test_extracts_to_custom_dir(self, sample_zip_file, tmp_path):
        dest = tmp_path / "extracted"
        extracted = extract_zip(sample_zip_file, dest)
        assert all(str(p).startswith(str(dest)) for p in extracted)
