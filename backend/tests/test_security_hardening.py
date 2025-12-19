from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.config import Settings
from app.main import validate_critical_settings
from app.models import License, LicenseStatus, LicenseType


@pytest.mark.asyncio
async def test_validate_critical_settings_detects_placeholders():
    settings = Settings(
        ENVIRONMENT="production",
        STRIPE_SECRET_KEY="sk_test_...",
        STRIPE_WEBHOOK_SECRET="whsec_...",
        SMTP_HOST="",
        SMTP_PORT=0,
        SMTP_USER="",
        SMTP_PASSWORD="",
        ADMIN_TOKEN="admin-token-super-secreto-mude-isso",
        JWT_SECRET_KEY="sua-chave-secreta-super-complexa-aqui-mude-isso-em-producao",
    )

    errors = validate_critical_settings(settings)

    assert "STRIPE_SECRET_KEY" in " | ".join(errors)
    assert "STRIPE_WEBHOOK_SECRET" in " | ".join(errors)
    assert "SMTP_HOST" in " | ".join(errors)
    assert "SMTP_PORT" in " | ".join(errors)
    assert "SMTP_USER" in " | ".join(errors)
    assert "SMTP_PASSWORD" in " | ".join(errors)
    assert "JWT_SECRET_KEY" in " | ".join(errors)
    assert "ADMIN_TOKEN" in " | ".join(errors)


@pytest.mark.asyncio
async def test_validate_license_blocks_activation_over_limit(db_session, client: AsyncClient):
    license_obj = License(
        id=uuid4(),
        key="LIMIT-TEST-001",
        customer_name="Activation Test",
        email="activation@test.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.BASIC,
        machine_id="MACHINE-1",
        max_activations=1,
        current_activations=1,
    )
    db_session.add(license_obj)
    await db_session.commit()

    response = await client.post(
        "/api/validate-license",
        json={
            "key": "LIMIT-TEST-001",
            "machine_id": "MACHINE-2",
            "app_version": "1.0.0",
        },
    )

    assert response.status_code == 403
    assert "Máximo de ativações" in response.json()["detail"]


@pytest.mark.asyncio
async def test_test_email_disabled_in_production(monkeypatch, client: AsyncClient):
    from app import config as app_config

    settings = app_config.get_settings()
    original_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        response = await client.post("/api/payments/test-email", params={"email": "user@test.com"})
    finally:
        settings.ENVIRONMENT = original_env

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_prices_include_configured_price_ids(monkeypatch, client: AsyncClient):
    from app import config as app_config

    settings = app_config.get_settings()
    original_values = {
        "STRIPE_PRICE_BASIC_MONTHLY": settings.STRIPE_PRICE_BASIC_MONTHLY,
        "STRIPE_PRICE_BASIC_YEARLY": settings.STRIPE_PRICE_BASIC_YEARLY,
    }
    try:
        settings.STRIPE_PRICE_BASIC_MONTHLY = "price_basic_monthly_123"
        settings.STRIPE_PRICE_BASIC_YEARLY = "price_basic_yearly_456"

        response = await client.get("/api/payments/prices")
        assert response.status_code == 200
        plans = response.json()["plans"]
        basic_monthly = next(p for p in plans if p["type"] == "basic_monthly")
        basic_yearly = next(p for p in plans if p["type"] == "basic_yearly")

        assert basic_monthly["price_id"] == "price_basic_monthly_123"
        assert basic_yearly["price_id"] == "price_basic_yearly_456"
    finally:
        settings.STRIPE_PRICE_BASIC_MONTHLY = original_values["STRIPE_PRICE_BASIC_MONTHLY"]
        settings.STRIPE_PRICE_BASIC_YEARLY = original_values["STRIPE_PRICE_BASIC_YEARLY"]
