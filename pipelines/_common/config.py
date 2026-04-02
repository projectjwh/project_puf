"""Configuration loading for pipeline operations.

Loads sources.yaml, database.yaml, and pipeline.yaml using Pydantic models.
Supports environment variable overrides for deployment flexibility.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def _project_root() -> Path:
    """Walk up from this file to find the project root (contains pyproject.toml)."""
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return current.parent.parent  # fallback: two levels up from _common/


PROJECT_ROOT = _project_root()
CONFIG_DIR = PROJECT_ROOT / "config"


# ---------------------------------------------------------------------------
# Database settings
# ---------------------------------------------------------------------------


class DatabaseSettings(BaseSettings):
    """PostgreSQL connection settings. Environment variables override defaults."""

    host: str = "localhost"
    port: int = 5432
    database: str = "puf"
    user: str = "puf_admin"
    password: str = "puf_dev_password"
    pgbouncer_port: int = 6432

    model_config = {"env_prefix": "PUF_DB_"}

    @property
    def dsn(self) -> str:
        """Direct PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def pgbouncer_dsn(self) -> str:
        """PgBouncer connection string (for application use)."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.pgbouncer_port}/{self.database}"


# ---------------------------------------------------------------------------
# Pipeline settings
# ---------------------------------------------------------------------------


class RetryConfig(BaseModel):
    max_attempts: int = 3
    delay_seconds: list[int] = Field(default_factory=lambda: [300, 900, 2700])


class ParquetConfig(BaseModel):
    compression: str = "zstd"
    row_group_size: int = 500_000


class StoragePaths(BaseModel):
    raw_base: str = "data/raw"
    processed_base: str = "data/processed"
    mart_base: str = "data/mart"
    archive_base: str = "data/archive"
    reference_base: str = "data/reference"

    def resolve(self, relative: str) -> Path:
        """Resolve a relative path against the project root."""
        return PROJECT_ROOT / relative


class PipelineSettings(BaseModel):
    """Pipeline execution settings loaded from pipeline.yaml."""

    retry: RetryConfig = Field(default_factory=RetryConfig)
    parquet: ParquetConfig = Field(default_factory=ParquetConfig)
    storage: StoragePaths = Field(default_factory=StoragePaths)
    hash_algorithm: str = "sha256"
    quarantine_enabled: bool = True
    warn_escalation_threshold: float = 0.10


# ---------------------------------------------------------------------------
# Source definition
# ---------------------------------------------------------------------------


class FileSize(BaseModel):
    min_gb: float = 0.0
    max_gb: float = 100.0


class RowCount(BaseModel):
    min: int = 0
    max: int = 1_000_000_000
    severity: str = "WARN"


class SourceDefinition(BaseModel):
    """Single data source from sources.yaml."""

    name: str
    short_name: str
    publisher: str
    url: str = ""
    format: str = "csv"
    update_frequency: str = "annual"
    lag_months: int = 0
    tier: int = 1
    volume: int = 0
    primary_key: list[str] = Field(default_factory=list)
    schedule: str = ""
    file_size: FileSize = Field(default_factory=FileSize)
    row_count: RowCount = Field(default_factory=RowCount)


# ---------------------------------------------------------------------------
# Loading functions
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents."""
    with open(path) as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def get_database_settings() -> DatabaseSettings:
    """Load database settings from environment (with .yaml defaults)."""
    return DatabaseSettings()


@lru_cache(maxsize=1)
def get_pipeline_settings() -> PipelineSettings:
    """Load pipeline settings from pipeline.yaml."""
    yaml_path = CONFIG_DIR / "pipeline.yaml"
    if yaml_path.exists():
        raw = _load_yaml(yaml_path)
        return PipelineSettings(
            retry=RetryConfig(**raw.get("acquisition", {}).get("retry", {})),
            parquet=ParquetConfig(**raw.get("transformation", {}).get("parquet", {})),
            storage=StoragePaths(**raw.get("storage", {})),
            hash_algorithm=raw.get("acquisition", {}).get("hash_algorithm", "sha256"),
            quarantine_enabled=raw.get("validation", {}).get("quarantine_enabled", True),
            warn_escalation_threshold=raw.get("validation", {}).get("warn_escalation_threshold", 0.10),
        )
    return PipelineSettings()


@lru_cache(maxsize=1)
def get_sources() -> dict[str, SourceDefinition]:
    """Load all source definitions from sources.yaml, keyed by short_name."""
    yaml_path = CONFIG_DIR / "sources.yaml"
    if not yaml_path.exists():
        return {}
    raw = _load_yaml(yaml_path)
    sources: dict[str, SourceDefinition] = {}
    for category_data in raw.values():
        if not isinstance(category_data, dict):
            continue
        for _source_key, source_data in category_data.items():
            if isinstance(source_data, dict) and "short_name" in source_data:
                defn = SourceDefinition(**source_data)
                sources[defn.short_name] = defn
    return sources


def get_source(short_name: str) -> SourceDefinition:
    """Get a single source definition by short_name. Raises KeyError if not found."""
    sources = get_sources()
    if short_name not in sources:
        raise KeyError(f"Source '{short_name}' not found in sources.yaml")
    return sources[short_name]
