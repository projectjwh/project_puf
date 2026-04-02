"""Tests for provider SCD Type 2 snapshot and historical profile models."""

import pathlib

MODELS_DIR = pathlib.Path(__file__).resolve().parent.parent / "models"
SNAPSHOTS_DIR = MODELS_DIR / "snapshots"
MARTS_PROVIDER_DIR = MODELS_DIR / "marts" / "provider"


class TestSnapshotSql:
    """Verify the snapshot SQL file exists and is syntactically reasonable."""

    def test_snapshot_file_exists(self):
        snapshot_path = SNAPSHOTS_DIR / "snp_provider_history.sql"
        assert snapshot_path.exists(), f"Snapshot file not found at {snapshot_path}"

    def test_snapshot_has_required_directives(self):
        snapshot_path = SNAPSHOTS_DIR / "snp_provider_history.sql"
        content = snapshot_path.read_text()
        assert "{% snapshot snp_provider_history %}" in content
        assert "{% endsnapshot %}" in content
        assert "strategy='check'" in content
        assert "unique_key='npi'" in content
        assert "target_schema='mart'" in content

    def test_snapshot_selects_required_columns(self):
        snapshot_path = SNAPSHOTS_DIR / "snp_provider_history.sql"
        content = snapshot_path.read_text()
        required_columns = [
            "npi",
            "entity_type",
            "display_name",
            "primary_taxonomy_code",
            "practice_state",
            "practice_zip5",
            "is_active",
        ]
        for col in required_columns:
            assert col in content, f"Missing column {col} in snapshot SQL"

    def test_snapshot_references_int_providers(self):
        snapshot_path = SNAPSHOTS_DIR / "snp_provider_history.sql"
        content = snapshot_path.read_text()
        assert "ref('int_providers')" in content

    def test_snapshot_check_cols_match_tracked_attributes(self):
        snapshot_path = SNAPSHOTS_DIR / "snp_provider_history.sql"
        content = snapshot_path.read_text()
        tracked = [
            "primary_taxonomy_code",
            "practice_state",
            "practice_zip5",
            "is_active",
            "entity_type",
        ]
        for col in tracked:
            assert col in content, f"check_cols missing tracked attribute: {col}"


class TestHistoricalProfileMart:
    """Verify the historical profile mart has expected structure."""

    def test_historical_profile_file_exists(self):
        mart_path = MARTS_PROVIDER_DIR / "mart_provider__historical_profile.sql"
        assert mart_path.exists(), f"Historical profile mart not found at {mart_path}"

    def test_historical_profile_has_config(self):
        mart_path = MARTS_PROVIDER_DIR / "mart_provider__historical_profile.sql"
        content = mart_path.read_text()
        assert "materialized='table'" in content
        assert "'scd'" in content

    def test_historical_profile_has_expected_columns(self):
        mart_path = MARTS_PROVIDER_DIR / "mart_provider__historical_profile.sql"
        content = mart_path.read_text()
        expected_columns = [
            "npi",
            "version_number",
            "is_current",
            "days_in_version",
            "previous_state",
            "previous_taxonomy",
            "dbt_valid_from",
            "dbt_valid_to",
            "dbt_scd_id",
            "is_state_change",
            "is_taxonomy_change",
            "specialty_classification",
        ]
        for col in expected_columns:
            assert col in content, f"Missing column {col} in historical profile mart"

    def test_historical_profile_references_snapshot(self):
        mart_path = MARTS_PROVIDER_DIR / "mart_provider__historical_profile.sql"
        content = mart_path.read_text()
        assert "ref('snp_provider_history')" in content

    def test_historical_profile_joins_taxonomy(self):
        mart_path = MARTS_PROVIDER_DIR / "mart_provider__historical_profile.sql"
        content = mart_path.read_text()
        assert "ref_nucc_taxonomy" in content

    def test_historical_profile_has_grain_comment(self):
        mart_path = MARTS_PROVIDER_DIR / "mart_provider__historical_profile.sql"
        content = mart_path.read_text()
        assert "Grain:" in content


class TestPracticeProfileScdFields:
    """Verify the practice profile mart includes SCD summary fields."""

    def test_practice_profile_has_scd_fields(self):
        mart_path = MARTS_PROVIDER_DIR / "mart_provider__practice_profile.sql"
        content = mart_path.read_text()
        scd_fields = [
            "provider_versions",
            "first_seen_date",
            "state_changes",
            "specialty_changes",
        ]
        for field in scd_fields:
            assert field in content, f"Missing SCD summary field {field} in practice profile"

    def test_practice_profile_references_snapshot(self):
        mart_path = MARTS_PROVIDER_DIR / "mart_provider__practice_profile.sql"
        content = mart_path.read_text()
        assert "snp_provider_history" in content
