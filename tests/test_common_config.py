"""Tests for pipelines._common.config."""

from pathlib import Path

from pipelines._common.config import (
    DatabaseSettings,
    PipelineSettings,
    SourceDefinition,
    get_database_settings,
    get_pipeline_settings,
    get_sources,
)


class TestDatabaseSettings:
    def test_defaults(self):
        settings = DatabaseSettings()
        assert settings.host == "localhost"
        assert settings.port == 5432
        assert settings.database == "puf"

    def test_dsn_format(self):
        settings = DatabaseSettings()
        assert settings.dsn.startswith("postgresql://")
        assert "puf" in settings.dsn

    def test_pgbouncer_dsn_uses_different_port(self):
        settings = DatabaseSettings()
        assert f":{settings.pgbouncer_port}/" in settings.pgbouncer_dsn
        assert f":{settings.port}/" in settings.dsn


class TestPipelineSettings:
    def test_defaults(self):
        settings = PipelineSettings()
        assert settings.parquet.compression == "zstd"
        assert settings.retry.max_attempts == 3
        assert settings.hash_algorithm == "sha256"
        assert settings.quarantine_enabled is True

    def test_storage_paths(self):
        settings = PipelineSettings()
        assert settings.storage.raw_base == "data/raw"
        assert settings.storage.processed_base == "data/processed"


class TestSourceDefinition:
    def test_basic_source(self):
        source = SourceDefinition(
            name="Test Source",
            short_name="test",
            publisher="CMS",
            url="https://example.com/data.csv",
        )
        assert source.tier == 1
        assert source.format == "csv"
        assert source.primary_key == []

    def test_source_with_validation(self):
        source = SourceDefinition(
            name="NPPES",
            short_name="nppes",
            publisher="CMS",
            volume=8_000_000,
            primary_key=["NPI"],
            file_size={"min_gb": 1.5, "max_gb": 4.0},
            row_count={"min": 7_000_000, "max": 10_000_000, "severity": "BLOCK"},
        )
        assert source.file_size.min_gb == 1.5
        assert source.row_count.severity == "BLOCK"


class TestGetSources:
    def test_loads_sources_from_yaml(self):
        sources = get_sources()
        # Should load at least some sources if sources.yaml exists
        if sources:  # May be empty in CI without config
            assert all(isinstance(v, SourceDefinition) for v in sources.values())

    def test_sources_keyed_by_short_name(self):
        sources = get_sources()
        if sources:
            for key, source in sources.items():
                assert key == source.short_name
