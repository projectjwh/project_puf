"""Tests for procedure domain API schemas and route imports."""

import pytest

from api.schemas.procedures import (
    ProcedureDetail,
    ProcedurePriceVariation,
    ProcedureTopResponse,
    ProcedureTopResult,
)


class TestProcedureDetailSchema:
    def test_minimal(self):
        detail = ProcedureDetail(hcpcs_code="99213", data_year=2022)
        assert detail.hcpcs_code == "99213"
        assert detail.data_year == 2022
        assert detail.total_services is None
        assert detail.total_rvu is None

    def test_full(self):
        detail = ProcedureDetail(
            hcpcs_code="99213",
            hcpcs_description="Office/outpatient visit est",
            data_year=2022,
            total_services=250_000_000.0,
            total_beneficiaries=45_000_000.0,
            provider_count=500_000,
            total_submitted_charge=50_000_000_000.0,
            total_medicare_payment=20_000_000_000.0,
            total_medicare_standardized=19_500_000_000.0,
            avg_payment_per_service=80.00,
            avg_charge_per_service=200.00,
            avg_payment_per_beneficiary=444.44,
            pct_office=85.5,
            pct_facility=14.5,
            work_rvu=0.97,
            facility_pe_rvu=0.41,
            malpractice_rvu=0.06,
            total_rvu=1.44,
            conversion_factor=33.89,
            total_rvu_volume=360_000_000.0,
            yoy_services_change_pct=2.5,
            yoy_payment_change_pct=3.1,
        )
        assert detail.total_services == 250_000_000.0
        assert detail.total_rvu == 1.44
        assert detail.pct_office == 85.5
        assert detail.yoy_services_change_pct == 2.5

    def test_from_dict(self):
        """Simulate constructing from database row dict."""
        row = {
            "hcpcs_code": "99214",
            "hcpcs_description": "Office/outpatient visit est",
            "data_year": 2022,
            "total_services": 120000000.0,
            "total_medicare_payment": 15000000000.0,
            "provider_count": 450000,
            "avg_payment_per_service": 125.0,
            "work_rvu": 1.50,
            "total_rvu": 2.10,
        }
        detail = ProcedureDetail(**row)
        assert detail.hcpcs_code == "99214"
        assert detail.provider_count == 450000


class TestProcedureTopResultSchema:
    def test_minimal(self):
        result = ProcedureTopResult(hcpcs_code="99213", data_year=2022)
        assert result.hcpcs_code == "99213"
        assert result.total_services is None

    def test_full(self):
        result = ProcedureTopResult(
            hcpcs_code="99213",
            hcpcs_description="Office/outpatient visit est",
            data_year=2022,
            total_services=250_000_000.0,
            total_medicare_payment=20_000_000_000.0,
            provider_count=500_000,
            avg_payment_per_service=80.0,
            total_rvu=1.44,
            yoy_services_change_pct=2.5,
        )
        assert result.provider_count == 500_000
        assert result.total_rvu == 1.44

    def test_from_dict(self):
        row = {
            "hcpcs_code": "99213",
            "hcpcs_description": "Office/outpatient visit est",
            "data_year": 2022,
            "total_services": 250000000.0,
            "total_medicare_payment": 20000000000.0,
            "provider_count": 500000,
        }
        result = ProcedureTopResult(**row)
        assert result.hcpcs_code == "99213"


class TestProcedureTopResponseSchema:
    def test_response(self):
        response = ProcedureTopResponse(
            items=[
                ProcedureTopResult(hcpcs_code="99213", data_year=2022, total_services=250e6),
                ProcedureTopResult(hcpcs_code="99214", data_year=2022, total_services=120e6),
            ],
            total=5000,
            page=1,
            page_size=25,
            has_next=True,
        )
        assert len(response.items) == 2
        assert response.has_next is True
        assert response.total == 5000

    def test_empty_response(self):
        response = ProcedureTopResponse(items=[], total=0, page=1, page_size=25, has_next=False)
        assert len(response.items) == 0
        assert response.has_next is False


class TestProcedurePriceVariationSchema:
    def test_minimal(self):
        var = ProcedurePriceVariation(hcpcs_code="99213", provider_state="CA", data_year=2022)
        assert var.hcpcs_code == "99213"
        assert var.provider_state == "CA"
        assert var.coefficient_of_variation is None

    def test_full(self):
        var = ProcedurePriceVariation(
            hcpcs_code="99213",
            hcpcs_description="Office/outpatient visit est",
            provider_state="CA",
            data_year=2022,
            provider_count=45000,
            total_services=25_000_000.0,
            total_medicare_payment=2_000_000_000.0,
            avg_payment=80.0,
            min_payment=40.0,
            max_payment=200.0,
            stddev_payment=25.5,
            p25_payment=65.0,
            p75_payment=95.0,
            coefficient_of_variation=0.3188,
        )
        assert var.avg_payment == 80.0
        assert var.min_payment == 40.0
        assert var.max_payment == 200.0
        assert var.coefficient_of_variation == 0.3188

    def test_from_dict(self):
        """Simulate constructing from database row dict."""
        row = {
            "hcpcs_code": "99213",
            "hcpcs_description": "Office/outpatient visit est",
            "provider_state": "TX",
            "data_year": 2022,
            "provider_count": 38000,
            "avg_payment": 75.50,
            "min_payment": 35.0,
            "max_payment": 180.0,
            "stddev_payment": 22.3,
            "p25_payment": 60.0,
            "p75_payment": 90.0,
            "coefficient_of_variation": 0.2954,
        }
        var = ProcedurePriceVariation(**row)
        assert var.provider_state == "TX"
        assert var.p25_payment == 60.0


try:
    import fastapi  # noqa: F401

    _has_fastapi = True
except ImportError:
    _has_fastapi = False

_skip_no_fastapi = pytest.mark.skipif(not _has_fastapi, reason="fastapi not installed")


@_skip_no_fastapi
class TestProcedureRouterImports:
    """Verify procedure route module is importable and registered."""

    def test_import_procedures_router(self):
        from api.routes.procedures import router

        assert router is not None

    def test_procedures_router_registered(self):
        from api.main import app

        route_paths = [r.path for r in app.routes]
        matching = [p for p in route_paths if p.startswith("/api/v1/procedures")]
        assert len(matching) > 0, "No routes found with prefix /api/v1/procedures"

    def test_procedure_endpoints_exist(self):
        from api.main import app

        route_paths = [r.path for r in app.routes]
        assert "/api/v1/procedures/top" in route_paths
        assert "/api/v1/procedures/variation/{hcpcs_code}" in route_paths
        assert "/api/v1/procedures/{hcpcs_code}" in route_paths
