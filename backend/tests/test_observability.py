"""Bounded measurements, safe JSON events, costs, alerts, and owner access."""

import json
import logging
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.core.admin_roles import AdminRole
from backend.app.core.config import Settings
from backend.app.core.observability import (
    OperationalMetrics,
    get_operational_metrics,
    operations_logger,
    request_reference,
)
from backend.app.services.admin_auth_service import AdminAuthService
from backend.tests.test_admin_commercial import PASSWORD, login, settings

pytest_plugins = ("backend.tests.test_admin_commercial",)
METRICS_PATH = "/api/v1/admin/operations/metrics"


class CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def test_metrics_and_alert_events_are_bounded_and_redacted() -> None:
    metrics = OperationalMetrics()
    handler = CaptureHandler()
    operations_logger.addHandler(handler)
    operations_logger.setLevel(logging.INFO)
    private_marker = "5215550000001@c.us-test-only-private-token"
    try:
        metrics.record_http(
            method="GET",
            endpoint="/api/v1/admin/users/{user_id}",
            status_code=503,
            duration_ms=2_500,
            error_category=private_marker,
            request_id=private_marker,
        )
        for _ in range(5):
            metrics.record_provider("greenapi", "status", 15)
        metrics.record_provider(
            "openai",
            "ok",
            120,
            usage=(1_000, 200, 100, 500),
            rates=(Decimal("1"), Decimal("0.5"), Decimal("2"), Decimal("4")),
            daily_cost_alert_usd=Decimal("0.002"),
        )
    finally:
        operations_logger.removeHandler(handler)

    snapshot = metrics.snapshot()
    assert snapshot["http_status"] == {"5xx": 1}
    assert snapshot["provider_outcomes"] == {"openai": {"ok": 1}, "greenapi": {"status": 5}}
    assert snapshot["latency_buckets_ms"]["http"][10_000] == 1
    assert snapshot["openai_tokens"] == {
        "input": 1000,
        "cached_input": 200,
        "cache_write": 100,
        "output": 500,
    }
    assert snapshot["openai_estimated_cost_usd"] == "0.003"
    assert snapshot["alerts_total"] == {
        "http_slow": 1,
        "greenapi_errors": 1,
        "openai_daily_estimate": 1,
    }
    events = [json.loads(message) for message in handler.messages]
    assert any(event["event"] == "provider_call" for event in events)
    assert any(event.get("code") == "greenapi_errors" for event in events)
    assert any(event.get("code") == "openai_daily_estimate" for event in events)
    assert events[0]["request_ref"] == request_reference(private_marker)
    assert events[0]["error_category"] == "other"
    assert private_marker not in json.dumps(events) + json.dumps(snapshot)


def test_unpriced_or_missing_usage_is_not_reported_as_zero_cost() -> None:
    metrics = OperationalMetrics()
    metrics.record_provider("openai", "ok", 10, usage=None)
    metrics.record_provider("openai", "ok", 10, usage=(20, 0, 0, 10))

    snapshot = metrics.snapshot()
    assert snapshot["openai_unpriced_responses"] == 2
    assert snapshot["openai_estimated_cost_usd"] == "0"
    assert snapshot["alerts_total"]["openai_usage_missing"] == 1
    assert snapshot["alerts_total"]["openai_pricing_missing"] == 1


def test_owner_only_metrics_route_has_no_customer_data(app, sessions) -> None:
    get_operational_metrics.cache_clear()
    auth = AdminAuthService(sessions, settings=settings())
    auth.create_user("owner", PASSWORD, role=AdminRole.OWNER)
    auth.create_user("viewer", PASSWORD)
    with (
        TestClient(app, base_url="https://testserver") as owner,
        TestClient(app, base_url="https://testserver") as viewer,
    ):
        assert owner.get(METRICS_PATH).status_code == 401
        login(viewer, "viewer")
        assert viewer.get(METRICS_PATH).status_code == 403
        login(owner, "owner")
        response = owner.get(METRICS_PATH)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["scope"] == "process"
        assert response.json()["http_status"]["4xx"] >= 2
        assert "owner" not in response.text
        assert PASSWORD not in response.text
        assert "token" not in response.text.lower().replace("openai_tokens", "")
    get_operational_metrics.cache_clear()


def test_config_requires_explicit_nonnegative_rates() -> None:
    settings_obj = Settings(
        assistant_branch_code="sucursal-demo",
        openai_api_key="test-only-placeholder",
        _env_file=None,
    )
    assert settings_obj.observability_input_usd_per_million is None
    assert settings_obj.observability_daily_cost_alert_usd is None


@pytest.mark.parametrize(
    "overrides",
    (
        {"observability_input_usd_per_million": "-1"},
        {"observability_input_usd_per_million": "1"},
        {"observability_daily_cost_alert_usd": "0"},
        {"observability_daily_cost_alert_usd": "1"},
    ),
)
def test_invalid_or_incomplete_cost_configuration_fails_closed(overrides: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        Settings(
            assistant_branch_code="sucursal-demo",
            openai_api_key="test-only-placeholder",
            _env_file=None,
            **overrides,
        )
