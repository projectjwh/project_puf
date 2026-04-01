"""Shared test fixtures for Project PUF."""

import pandas as pd
import pytest


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Temporary directory structure mimicking data/ layout."""
    for subdir in ("raw", "processed", "mart", "archive", "reference"):
        (tmp_path / subdir).mkdir()
    return tmp_path


@pytest.fixture
def sample_npi_df():
    """Small DataFrame with NPI-like data for testing."""
    return pd.DataFrame({
        "npi": ["1234567890", "0987654321", "1111111111", "2222222222", "3333333333"],
        "entity_type_code": ["1", "2", "1", "1", "2"],
        "provider_last_name": ["SMITH", "ACME HEALTH", "DOE", "JONES", "BIGCORP"],
        "provider_first_name": ["JOHN", None, "JANE", "BOB", None],
        "practice_state_code": ["CA", "NY", "TX", "FL", "CA"],
        "practice_postal_code": ["90210-1234", "10001", "73301", "33101-0000", "94102"],
        "taxonomy_code_1": ["207Q00000X", "282N00000X", "207R00000X", "208000000X", "282N00000X"],
        "taxonomy_primary_switch_1": ["Y", "Y", "Y", "Y", "Y"],
        "deactivation_date": [None, None, None, None, "2023-01-15"],
    })


@pytest.fixture
def sample_partb_df():
    """Small DataFrame with Part B utilization data for testing."""
    return pd.DataFrame({
        "rendering_npi": ["1234567890", "1234567890", "0987654321"],
        "hcpcs_code": ["99213", "99214", "99213"],
        "place_of_service_code": ["O", "O", "F"],
        "service_count": [500, 200, 300],
        "beneficiary_count": [350, 150, 250],
        "avg_submitted_charge_amount": [150.00, 250.00, 180.00],
        "avg_medicare_allowed_amount": [100.00, 175.00, 120.00],
        "avg_medicare_payment_amount": [80.00, 140.00, 96.00],
        "avg_medicare_standardized_amount": [85.00, 145.00, 100.00],
        "data_year": [2022, 2022, 2022],
    })


@pytest.fixture
def sample_geovar_df():
    """Small DataFrame with Geographic Variation data."""
    return pd.DataFrame({
        "bene_geo_lvl": ["National", "State", "State", "County"],
        "state_fips": [None, "06", "36", "06001"],
        "county_fips": [None, None, None, "06001"],
        "beneficiary_count_ffs": [30_000_000, 3_000_000, 2_000_000, 100_000],
        "beneficiary_count_ma": [28_000_000, 2_500_000, 1_800_000, 80_000],
        "total_medicare_payment_pc": [12000.00, 11500.00, 13200.00, 10800.00],
        "data_year": [2022, 2022, 2022, 2022],
    })


@pytest.fixture
def sample_zip_file(tmp_path):
    """Create a small test ZIP file."""
    import zipfile

    csv_content = "npi,name\n1234567890,Test Provider\n0987654321,Another Provider\n"
    csv_path = tmp_path / "test.csv"
    csv_path.write_text(csv_content)

    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(csv_path, "test.csv")
    return zip_path
