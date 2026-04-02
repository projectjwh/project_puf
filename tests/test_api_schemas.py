"""Tests for API Pydantic schemas — validates response shapes."""

from datetime import date

import pytest

from api.schemas.common import CatalogSource, HealthResponse, PaginationParams
from api.schemas.geographic import StateSpending, StateSummary
from api.schemas.national import NationalKPI
from api.schemas.opioid import OpioidByState, OpioidTopPrescriber
from api.schemas.providers import ProviderProfile, ProviderSearchResponse, ProviderSummary


class TestProviderSchemas:
    def test_provider_profile_minimal(self):
        profile = ProviderProfile(npi="1234567890", display_name="SMITH, JOHN MD")
        assert profile.npi == "1234567890"
        assert profile.display_name == "SMITH, JOHN MD"
        assert profile.has_part_b_data is None

    def test_provider_profile_full(self):
        profile = ProviderProfile(
            npi="1234567890",
            display_name="SMITH, JOHN MD",
            entity_type="Individual",
            practice_state="CA",
            practice_city="Los Angeles",
            specialty_classification="Internal Medicine",
            total_services_rendered=1500.0,
            total_medicare_payments=85000.00,
            total_drugs_prescribed=200,
            has_opioid_prescriptions=False,
            has_part_b_data=True,
            has_part_d_data=True,
            enumeration_date=date(2005, 5, 23),
        )
        assert profile.total_medicare_payments == 85000.00
        assert profile.has_part_b_data == True  # noqa: E712
        assert profile.enumeration_date == date(2005, 5, 23)

    def test_provider_summary(self):
        summary = ProviderSummary(
            npi="1234567890",
            display_name="SMITH, JOHN MD",
            entity_type="Individual",
            practice_state="CA",
        )
        assert summary.npi == "1234567890"

    def test_provider_search_response(self):
        response = ProviderSearchResponse(
            items=[
                ProviderSummary(npi="1234567890", display_name="SMITH, JOHN"),
                ProviderSummary(npi="0987654321", display_name="DOE, JANE"),
            ],
            total=100,
            page=1,
            page_size=25,
            has_next=True,
        )
        assert len(response.items) == 2
        assert response.has_next == True  # noqa: E712

    def test_provider_profile_from_dict(self):
        """Simulate constructing from database row dict."""
        row = {
            "npi": "1234567890",
            "display_name": "SMITH, JOHN MD",
            "entity_type": "Individual",
            "practice_state": "CA",
            "total_medicare_payments": 85000.00,
        }
        profile = ProviderProfile(**row)
        assert profile.practice_state == "CA"


class TestGeographicSchemas:
    def test_state_spending(self):
        state = StateSpending(
            state_fips="06",
            state_name="California",
            state_abbreviation="CA",
            data_year=2022,
            spending_index=1.05,
            actual_per_capita_costs=10500.00,
        )
        assert state.spending_index == 1.05

    def test_state_summary(self):
        summary = StateSummary(
            state_fips="06",
            state_name="California",
            state_abbreviation="CA",
            data_year=2022,
            total_beneficiaries=5000000,
        )
        assert summary.total_beneficiaries == 5000000


class TestNationalSchemas:
    def test_national_kpi(self):
        kpi = NationalKPI(
            data_year=2022,
            active_providers_partb=900000,
            national_total_medicare_payments=400_000_000_000.0,
            yoy_payment_change_pct=3.5,
        )
        assert kpi.data_year == 2022
        assert kpi.yoy_payment_change_pct == 3.5


class TestOpioidSchemas:
    def test_opioid_by_state(self):
        opioid = OpioidByState(
            state_fips="06",
            state_name="California",
            data_year=2022,
            opioid_prescriber_rate_pct=15.5,
            opioid_claim_share_pct=8.2,
        )
        assert opioid.opioid_prescriber_rate_pct == 15.5

    def test_opioid_top_prescriber(self):
        prescriber = OpioidTopPrescriber(
            prescriber_npi="1234567890",
            data_year=2022,
            display_name="SMITH, JOHN MD",
            opioid_claims=5000,
            state_opioid_rank=1,
        )
        assert prescriber.state_opioid_rank == 1


class TestCommonSchemas:
    def test_health_response(self):
        health = HealthResponse(
            status="healthy",
            version="0.1.0",
            pg_connected=True,
            duckdb_connected=True,
        )
        assert health.status == "healthy"

    def test_catalog_source(self):
        source = CatalogSource(
            source_name="NPPES",
            short_name="nppes",
            publisher="CMS",
            tier=1,
        )
        assert source.tier == 1

    def test_pagination_params(self):
        params = PaginationParams(page=3, page_size=50)
        assert params.offset == 100


try:
    import fastapi  # noqa: F401

    _has_fastapi = True
except ImportError:
    _has_fastapi = False

_skip_no_fastapi = pytest.mark.skipif(not _has_fastapi, reason="fastapi not installed")


@_skip_no_fastapi
class TestAPIRouterImports:
    """Verify all route modules are importable."""

    def test_import_health(self):
        from api.routes.health import router

        assert router is not None

    def test_import_providers(self):
        from api.routes.providers import router

        assert router is not None

    def test_import_geographic(self):
        from api.routes.geographic import router

        assert router is not None

    def test_import_national(self):
        from api.routes.national import router

        assert router is not None

    def test_import_opioid(self):
        from api.routes.opioid import router

        assert router is not None

    def test_import_specialties(self):
        from api.routes.specialties import router

        assert router is not None

    def test_import_catalog(self):
        from api.routes.catalog import router

        assert router is not None

    def test_import_main_app(self):
        from api.main import app

        assert app is not None
        # Check routes registered
        route_paths = [r.path for r in app.routes]
        assert "/health" in route_paths


@_skip_no_fastapi
class TestAPIAppRoutes:
    """Test that all expected routes are registered on the FastAPI app."""

    def test_all_route_prefixes(self):
        from api.main import app

        route_paths = [r.path for r in app.routes]
        expected_prefixes = [
            "/health",
            "/api/v1/providers",
            "/api/v1/geographic",
            "/api/v1/national",
            "/api/v1/opioid",
            "/api/v1/specialties",
            "/api/v1/catalog",
        ]
        for prefix in expected_prefixes:
            matching = [p for p in route_paths if p.startswith(prefix)]
            assert len(matching) > 0, f"No routes found with prefix {prefix}"
