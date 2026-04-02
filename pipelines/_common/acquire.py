"""Data acquisition utilities for downloading, hashing, and extracting source files.

Handles HTTP downloads with retry/streaming, SHA-256 verification, ZIP extraction,
and size validation. All functions are designed to be called as Prefect tasks.
"""

import hashlib
import zipfile
from datetime import date
from pathlib import Path

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_fixed,
)

from pipelines._common.config import PROJECT_ROOT, get_pipeline_settings, get_source
from pipelines._common.logging import get_logger

log = get_logger(stage="acquire")


def _is_retryable_error(error: BaseException) -> bool:
    """Determine if an HTTP error should be retried."""
    if isinstance(error, (httpx.ConnectError, httpx.TimeoutException)):
        return True
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code >= 500
    return False


def resolve_landing_path(source: str, run_date: date | None = None, data_year: int | None = None) -> Path:
    """Build the raw landing path for a source download.

    Pattern: data/raw/{source}/{YYYY-MM-DD}/ or data/raw/{source}/{YYYY}/
    """
    settings = get_pipeline_settings()
    run_date = run_date or date.today()

    partition = str(data_year) if data_year else run_date.isoformat()

    path = PROJECT_ROOT / settings.storage.raw_base / source / partition
    path.mkdir(parents=True, exist_ok=True)
    return path


def _do_download(
    url: str,
    dest_path: Path,
    timeout: int,
    chunk_size: int,
) -> int:
    """Execute a single download attempt. Raises on failure."""
    downloaded_bytes = 0
    with httpx.stream(
        "GET",
        url,
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "ProjectPUF/0.1 (public-healthcare-data-research)"},
    ) as response:
        response.raise_for_status()

        with open(dest_path, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=chunk_size):
                f.write(chunk)
                downloaded_bytes += len(chunk)

    return downloaded_bytes


def download_file(
    url: str,
    dest_dir: Path,
    filename: str | None = None,
    timeout: int = 3600,
    chunk_size: int = 8 * 1024 * 1024,
) -> Path:
    """Download a file via HTTP with streaming, retry, and progress logging.

    Retry policy is loaded from pipeline.yaml (default: 3 attempts with
    [300, 900, 2700] second delays). Retries on connection errors, timeouts,
    and HTTP 5xx errors. Does NOT retry 4xx errors.

    Args:
        url: URL to download.
        dest_dir: Directory to save the file.
        filename: Override filename (defaults to URL basename).
        timeout: Request timeout in seconds.
        chunk_size: Download chunk size in bytes (default 8 MB).

    Returns:
        Path to the downloaded file.

    Raises:
        httpx.HTTPStatusError: If the HTTP response indicates a non-retryable error.
        tenacity.RetryError: If all retry attempts are exhausted.
    """
    settings = get_pipeline_settings()
    retry_config = settings.retry
    dest_dir.mkdir(parents=True, exist_ok=True)

    if not filename:
        filename = url.split("/")[-1].split("?")[0] or "download"

    dest_path = dest_dir / filename

    log.info("download_start", url=url, dest=str(dest_path), max_attempts=retry_config.max_attempts)

    # Build retry-wrapped download with configured delays
    delays = retry_config.delay_seconds

    retrying_download = retry(
        retry=retry_if_exception(_is_retryable_error),
        stop=stop_after_attempt(retry_config.max_attempts),
        wait=wait_fixed(delays[0] if delays else 300),
        before_sleep=lambda state: log.warning(
            "download_retry",
            url=url,
            attempt=state.attempt_number,
            delay_seconds=delays[min(state.attempt_number - 1, len(delays) - 1)] if delays else 300,
            error=str(state.outcome.exception()) if state.outcome else "unknown",
        ),
        reraise=True,
    )(_do_download)

    downloaded_bytes = retrying_download(url, dest_path, timeout, chunk_size)

    log.info("download_complete", path=str(dest_path), bytes=downloaded_bytes)
    return dest_path


def compute_hash(path: Path, algorithm: str = "sha256") -> str:
    """Compute a file hash (default SHA-256). Reads in 8 MB chunks for memory efficiency."""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while chunk := f.read(8 * 1024 * 1024):
            h.update(chunk)
    file_hash = h.hexdigest()
    log.info("hash_computed", path=str(path), algorithm=algorithm, hash=file_hash[:16] + "...")
    return file_hash


def validate_file_size(path: Path, min_bytes: int, max_bytes: int) -> None:
    """Validate file size is within expected range. Raises ValueError if outside bounds.

    Args:
        path: File to check.
        min_bytes: Minimum acceptable size in bytes.
        max_bytes: Maximum acceptable size in bytes.
    """
    size = path.stat().st_size
    if size < min_bytes or size > max_bytes:
        raise ValueError(
            f"File size {size:,} bytes outside expected range [{min_bytes:,}, {max_bytes:,}] for {path.name}"
        )
    log.info("size_validated", path=str(path), size_bytes=size)


def validate_file_size_gb(path: Path, min_gb: float, max_gb: float) -> None:
    """Convenience wrapper that accepts GB values."""
    validate_file_size(path, int(min_gb * 1e9), int(max_gb * 1e9))


def extract_zip(zip_path: Path, dest_dir: Path | None = None) -> list[Path]:
    """Extract a ZIP file and return paths to extracted files.

    Args:
        zip_path: Path to the ZIP file.
        dest_dir: Extraction directory (defaults to same directory as ZIP).

    Returns:
        List of paths to extracted files.
    """
    dest_dir = dest_dir or zip_path.parent
    dest_dir.mkdir(parents=True, exist_ok=True)

    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            if member.endswith("/"):
                continue  # skip directories
            zf.extract(member, dest_dir)
            extracted.append(dest_dir / member)

    log.info("zip_extracted", source=str(zip_path), files=len(extracted))
    return extracted


def check_remote_freshness(
    url: str,
    source: str,
    data_year: int | None = None,
) -> bool:
    """Send a HEAD request to check ETag/Last-Modified before downloading.

    Returns True if remote data appears newer than local (should download).
    Returns False if unchanged (skip download).
    Falls back to True if the server doesn't support ETags or an error occurs.
    """
    try:
        response = httpx.head(
            url,
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": "ProjectPUF/0.1 (public-healthcare-data-research)"},
        )
        response.raise_for_status()
    except Exception as e:
        log.warning("remote_freshness_check_failed", url=url, error=str(e))
        return True  # Assume new data on failure

    remote_etag = response.headers.get("etag", "").strip('"')
    remote_last_modified = response.headers.get("last-modified", "")

    if not remote_etag and not remote_last_modified:
        log.info("no_etag_support", url=url)
        return True  # Server doesn't support freshness headers

    # Compare against stored values
    from pipelines._common.db import query_pg

    try:
        result = query_pg(
            "SELECT latest_etag, latest_last_modified FROM catalog.data_freshness "
            "WHERE source_id = (SELECT source_id FROM catalog.sources WHERE short_name = :source) "
            "AND (data_year = :data_year OR (data_year IS NULL AND :data_year IS NULL)) "
            "ORDER BY updated_at DESC LIMIT 1",
            params={"source": source, "data_year": data_year},
        )
        if result.empty:
            return True  # No previous record

        stored_etag = result.iloc[0].get("latest_etag", "")
        stored_last_modified = result.iloc[0].get("latest_last_modified", "")

        if remote_etag and stored_etag and remote_etag == stored_etag:
            log.info("source_unchanged_etag", source=source, etag=remote_etag[:20])
            return False

        if remote_last_modified and stored_last_modified and remote_last_modified == stored_last_modified:
            log.info("source_unchanged_last_modified", source=source)
            return False

    except Exception:
        pass  # Graceful degradation — assume new data

    return True


def check_hash_changed(
    current_hash: str,
    source: str,
    data_year: int | None = None,
) -> bool:
    """Check if a file hash differs from the last recorded hash in catalog.

    Returns True if the data is new (hash changed or no previous record).
    Returns False if the hash matches (data unchanged, skip processing).

    Note: This queries the catalog.data_freshness table. If the table doesn't
    exist yet (pre-migration), it returns True (assume new data).
    """
    from pipelines._common.db import query_pg

    try:
        year_filter = f"AND data_year = {data_year}" if data_year else "AND data_year IS NULL"
        result = query_pg(
            f"SELECT latest_file_hash FROM catalog.data_freshness "
            f"WHERE source_id = (SELECT source_id FROM catalog.sources WHERE short_name = :source) "
            f"{year_filter} "
            f"ORDER BY updated_at DESC LIMIT 1",
            params={"source": source},
        )
        if result.empty:
            return True  # No previous record — data is new
        return bool(result.iloc[0]["latest_file_hash"] != current_hash)
    except Exception:
        # Table doesn't exist yet or other DB error — assume new data
        return True


def acquire_source(
    source_name: str,
    run_date: date | None = None,
    data_year: int | None = None,
    skip_if_unchanged: bool = True,
) -> tuple[Path, bool]:
    """High-level acquisition: download, hash, validate size, extract if ZIP.

    Flow:
        1. ETag/Last-Modified pre-check (cheap HEAD request)
        2. If unchanged: skip download entirely
        3. If changed or no ETag: full download with retry
        4. Size validation + hash check (existing logic)

    Returns:
        Tuple of (landing_path, is_new_data).
    """
    source_def = get_source(source_name)
    run_date = run_date or date.today()
    landing = resolve_landing_path(source_name, run_date, data_year)

    # Pre-check: ETag/Last-Modified (saves bandwidth for large files)
    if skip_if_unchanged and source_def.url:
        remote_is_new = check_remote_freshness(source_def.url, source_name, data_year)
        if not remote_is_new:
            log.info("source_unchanged_remote", source=source_name)
            return landing, False

    # Download (with retry)
    downloaded = download_file(source_def.url, landing)

    # Size validation
    if source_def.file_size.min_gb > 0 or source_def.file_size.max_gb < 100:
        validate_file_size_gb(downloaded, source_def.file_size.min_gb, source_def.file_size.max_gb)

    # Hash check (post-download dedup)
    file_hash = compute_hash(downloaded)
    is_new = True
    if skip_if_unchanged:
        is_new = check_hash_changed(file_hash, source_name, data_year)
        if not is_new:
            log.info("source_unchanged", source=source_name, hash=file_hash[:16])
            return landing, False

    # Extract if ZIP
    if source_def.format in ("csv_zip", "zip_txt", "zip_csv", "zip_xlsx", "zip_rrf"):
        extract_zip(downloaded, landing)

    log.info("acquisition_complete", source=source_name, landing=str(landing), is_new=is_new)
    return landing, is_new
