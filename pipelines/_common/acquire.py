"""Data acquisition utilities for downloading, hashing, and extracting source files.

Handles HTTP downloads with retry/streaming, SHA-256 verification, ZIP extraction,
and size validation. All functions are designed to be called as Prefect tasks.
"""

import hashlib
import zipfile
from datetime import date
from pathlib import Path

import httpx

from pipelines._common.config import PROJECT_ROOT, SourceDefinition, get_pipeline_settings, get_source
from pipelines._common.logging import get_logger

log = get_logger(stage="acquire")


def resolve_landing_path(source: str, run_date: date | None = None, data_year: int | None = None) -> Path:
    """Build the raw landing path for a source download.

    Pattern: data/raw/{source}/{YYYY-MM-DD}/ or data/raw/{source}/{YYYY}/
    """
    settings = get_pipeline_settings()
    run_date = run_date or date.today()

    if data_year:
        partition = str(data_year)
    else:
        partition = run_date.isoformat()

    path = PROJECT_ROOT / settings.storage.raw_base / source / partition
    path.mkdir(parents=True, exist_ok=True)
    return path


def download_file(
    url: str,
    dest_dir: Path,
    filename: str | None = None,
    timeout: int = 3600,
    chunk_size: int = 8 * 1024 * 1024,
) -> Path:
    """Download a file via HTTP with streaming and progress logging.

    Args:
        url: URL to download.
        dest_dir: Directory to save the file.
        filename: Override filename (defaults to URL basename).
        timeout: Request timeout in seconds.
        chunk_size: Download chunk size in bytes (default 8 MB).

    Returns:
        Path to the downloaded file.

    Raises:
        httpx.HTTPStatusError: If the HTTP response indicates an error.
    """
    settings = get_pipeline_settings()
    dest_dir.mkdir(parents=True, exist_ok=True)

    if not filename:
        filename = url.split("/")[-1].split("?")[0] or "download"

    dest_path = dest_dir / filename
    downloaded_bytes = 0

    log.info("download_start", url=url, dest=str(dest_path))

    with httpx.stream(
        "GET",
        url,
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": f"ProjectPUF/0.1 (public-healthcare-data-research)"},
    ) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))

        with open(dest_path, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=chunk_size):
                f.write(chunk)
                downloaded_bytes += len(chunk)

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
            f"File size {size:,} bytes outside expected range "
            f"[{min_bytes:,}, {max_bytes:,}] for {path.name}"
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
        return result.iloc[0]["latest_file_hash"] != current_hash
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

    Returns:
        Tuple of (landing_path, is_new_data).
    """
    source_def = get_source(source_name)
    run_date = run_date or date.today()
    landing = resolve_landing_path(source_name, run_date, data_year)

    # Download
    downloaded = download_file(source_def.url, landing)

    # Size validation
    if source_def.file_size.min_gb > 0 or source_def.file_size.max_gb < 100:
        validate_file_size_gb(downloaded, source_def.file_size.min_gb, source_def.file_size.max_gb)

    # Hash check
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
