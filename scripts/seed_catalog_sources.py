"""Seed catalog.sources table from config/sources.yaml.

Populates the source registry that enables foreign key relationships
from pipeline_runs, validation_runs, quarantine_rows, and data_freshness.

Usage:
    python scripts/seed_catalog_sources.py
    # or: make seed-catalog
"""

from sqlalchemy import text

from pipelines._common.config import get_sources
from pipelines._common.db import get_pg_engine
from pipelines._common.logging import get_logger, setup_logging

log = get_logger(stage="seed")


def seed_sources() -> int:
    """Read all sources from sources.yaml and upsert into catalog.sources.

    Returns number of sources seeded.
    """
    sources = get_sources()
    if not sources:
        log.warning("no_sources_found", message="sources.yaml is empty or not found")
        return 0

    engine = get_pg_engine(use_pgbouncer=False)
    count = 0

    with engine.connect() as conn:
        for _short_name, defn in sources.items():
            # Determine category from the source's position in sources.yaml
            # (not available directly from SourceDefinition, use tier as proxy)
            conn.execute(
                text("""
                    INSERT INTO catalog.sources
                        (source_name, short_name, publisher, category, download_url,
                         format, update_frequency, tier, primary_key_columns)
                    VALUES
                        (:source_name, :short_name, :publisher, :category, :download_url,
                         :format, :update_frequency, :tier, :primary_key_columns)
                    ON CONFLICT (short_name) DO UPDATE SET
                        source_name = EXCLUDED.source_name,
                        publisher = EXCLUDED.publisher,
                        download_url = EXCLUDED.download_url,
                        format = EXCLUDED.format,
                        update_frequency = EXCLUDED.update_frequency,
                        tier = EXCLUDED.tier,
                        primary_key_columns = EXCLUDED.primary_key_columns,
                        updated_at = NOW()
                """),
                {
                    "source_name": defn.name,
                    "short_name": defn.short_name,
                    "publisher": defn.publisher,
                    "category": f"tier_{defn.tier}",
                    "download_url": defn.url or None,
                    "format": defn.format,
                    "update_frequency": defn.update_frequency,
                    "tier": defn.tier,
                    "primary_key_columns": ",".join(defn.primary_key) if defn.primary_key else None,
                },
            )
            count += 1

        conn.commit()

    log.info("catalog_sources_seeded", count=count)
    return count


if __name__ == "__main__":
    setup_logging()
    n = seed_sources()
    print(f"Seeded {n} sources into catalog.sources")
