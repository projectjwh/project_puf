"""Tests for pipelines._common.acquire."""

from datetime import date
from unittest.mock import MagicMock, patch

import httpx
import pytest

from pipelines._common.acquire import (
    _is_retryable_error,
    check_remote_freshness,
    compute_hash,
    download_file,
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


# ---------------------------------------------------------------------------
# Phase 2: Retry and ETag tests
# ---------------------------------------------------------------------------


class TestIsRetryableError:
    def test_connect_error_is_retryable(self):
        assert _is_retryable_error(httpx.ConnectError("connection refused")) is True

    def test_timeout_is_retryable(self):
        assert _is_retryable_error(httpx.TimeoutException("timed out")) is True

    def test_500_is_retryable(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError("server error", request=MagicMock(), response=mock_response)
        assert _is_retryable_error(error) is True

    def test_503_is_retryable(self):
        mock_response = MagicMock()
        mock_response.status_code = 503
        error = httpx.HTTPStatusError("unavailable", request=MagicMock(), response=mock_response)
        assert _is_retryable_error(error) is True

    def test_404_is_not_retryable(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError("not found", request=MagicMock(), response=mock_response)
        assert _is_retryable_error(error) is False

    def test_403_is_not_retryable(self):
        mock_response = MagicMock()
        mock_response.status_code = 403
        error = httpx.HTTPStatusError("forbidden", request=MagicMock(), response=mock_response)
        assert _is_retryable_error(error) is False

    def test_value_error_is_not_retryable(self):
        assert _is_retryable_error(ValueError("bad value")) is False


class TestDownloadFileRetry:
    @patch("pipelines._common.acquire._do_download")
    @patch("pipelines._common.acquire.get_pipeline_settings")
    def test_succeeds_on_first_attempt(self, mock_settings, mock_download, tmp_path):
        from pipelines._common.config import PipelineSettings, RetryConfig

        mock_settings.return_value = PipelineSettings(retry=RetryConfig(max_attempts=3, delay_seconds=[1]))
        mock_download.return_value = 1000

        result = download_file("http://example.com/data.csv", tmp_path)
        assert result == tmp_path / "data.csv"
        mock_download.assert_called_once()

    @patch("pipelines._common.acquire._do_download")
    @patch("pipelines._common.acquire.get_pipeline_settings")
    def test_retries_on_connect_error_then_succeeds(self, mock_settings, mock_download, tmp_path):
        from pipelines._common.config import PipelineSettings, RetryConfig

        mock_settings.return_value = PipelineSettings(retry=RetryConfig(max_attempts=3, delay_seconds=[0]))
        mock_download.side_effect = [httpx.ConnectError("refused"), 1000]

        result = download_file("http://example.com/data.csv", tmp_path)
        assert result == tmp_path / "data.csv"
        assert mock_download.call_count == 2

    @patch("pipelines._common.acquire._do_download")
    @patch("pipelines._common.acquire.get_pipeline_settings")
    def test_does_not_retry_404(self, mock_settings, mock_download, tmp_path):
        from pipelines._common.config import PipelineSettings, RetryConfig

        mock_settings.return_value = PipelineSettings(retry=RetryConfig(max_attempts=3, delay_seconds=[0]))
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_download.side_effect = httpx.HTTPStatusError("not found", request=MagicMock(), response=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            download_file("http://example.com/missing.csv", tmp_path)
        assert mock_download.call_count == 1  # No retry

    @patch("pipelines._common.acquire._do_download")
    @patch("pipelines._common.acquire.get_pipeline_settings")
    def test_exhausts_retries(self, mock_settings, mock_download, tmp_path):
        from pipelines._common.config import PipelineSettings, RetryConfig

        mock_settings.return_value = PipelineSettings(retry=RetryConfig(max_attempts=2, delay_seconds=[0]))
        mock_download.side_effect = httpx.ConnectError("refused")

        with pytest.raises(httpx.ConnectError):
            download_file("http://example.com/data.csv", tmp_path)
        assert mock_download.call_count == 2


class TestCheckRemoteFreshness:
    @patch("httpx.head")
    def test_returns_true_when_no_etag_support(self, mock_head):
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()
        mock_head.return_value = mock_response

        assert check_remote_freshness("http://example.com/data.csv", "partb") is True

    @patch("httpx.head")
    def test_returns_true_on_head_failure(self, mock_head):
        mock_head.side_effect = httpx.ConnectError("refused")

        assert check_remote_freshness("http://example.com/data.csv", "partb") is True

    @patch("pipelines._common.db.query_pg")
    @patch("httpx.head")
    def test_returns_false_when_etag_matches(self, mock_head, mock_query):
        import pandas as pd

        mock_response = MagicMock()
        mock_response.headers = {"etag": '"abc123"'}
        mock_response.raise_for_status = MagicMock()
        mock_head.return_value = mock_response

        mock_query.return_value = pd.DataFrame(
            {
                "latest_etag": ["abc123"],
                "latest_last_modified": [""],
            }
        )

        assert check_remote_freshness("http://example.com/data.csv", "partb") is False

    @patch("pipelines._common.db.query_pg")
    @patch("httpx.head")
    def test_returns_true_when_etag_differs(self, mock_head, mock_query):
        import pandas as pd

        mock_response = MagicMock()
        mock_response.headers = {"etag": '"new456"'}
        mock_response.raise_for_status = MagicMock()
        mock_head.return_value = mock_response

        mock_query.return_value = pd.DataFrame(
            {
                "latest_etag": ["old123"],
                "latest_last_modified": [""],
            }
        )

        assert check_remote_freshness("http://example.com/data.csv", "partb") is True

    @patch("pipelines._common.db.query_pg")
    @patch("httpx.head")
    def test_returns_true_when_no_stored_record(self, mock_head, mock_query):
        import pandas as pd

        mock_response = MagicMock()
        mock_response.headers = {"etag": '"abc123"'}
        mock_response.raise_for_status = MagicMock()
        mock_head.return_value = mock_response

        mock_query.return_value = pd.DataFrame()  # Empty — no record

        assert check_remote_freshness("http://example.com/data.csv", "partb") is True
