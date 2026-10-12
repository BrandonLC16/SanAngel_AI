"""Bounded process-local operational metrics and allowlisted JSON events."""

import hashlib
import hmac
import json
import logging
import secrets
from collections import Counter, deque
from datetime import UTC, datetime
from decimal import Decimal
from functools import lru_cache
from threading import Lock

OBSERVABILITY_LOGGER_NAME = "backend.app.operations"
operations_logger = logging.getLogger(OBSERVABILITY_LOGGER_NAME)
_LOG_REFERENCE_KEY = secrets.token_bytes(32)
_LATENCY_BOUNDS_MS = (100, 500, 2_000, 10_000)
_PROVIDERS = ("openai", "greenapi")
_OUTCOMES = frozenset({"ok", "timeout", "rate_limit", "connection", "status", "response", "other"})
_SLOW_HTTP_MS = 2_000
_SLOW_PROVIDER_MS = {"openai": 15_000, "greenapi": 5_000}
_ERROR_ALERT_THRESHOLD = 5


def request_reference(request_id: str) -> str:
    """Correlate logs without echoing a client-supplied ID, number, or token."""

    return hmac.new(_LOG_REFERENCE_KEY, request_id.encode("utf-8"), hashlib.sha256).hexdigest()[:16]


def _event(event: str, **fields: str | int | float | None) -> None:
    payload = {"timestamp": datetime.now(UTC).isoformat(), "event": event, **fields}
    operations_logger.info(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


class OperationalMetrics:
    """Fixed labels and buckets; snapshots have no request content or identifiers."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._started_at = datetime.now(UTC)
        self._http_status: Counter[str] = Counter()
        self._provider_outcomes: dict[str, Counter[str]] = {
            provider: Counter() for provider in _PROVIDERS
        }
        self._latency: dict[str, list[int]] = {
            name: [0] * (len(_LATENCY_BOUNDS_MS) + 1) for name in ("http", *_PROVIDERS)
        }
        self._token_totals: Counter[str] = Counter()
        self._unpriced_responses = 0
        self._estimated_cost_usd = Decimal("0")
        self._daily_cost_usd = Decimal("0")
        self._cost_day = datetime.now(UTC).date()
        self._recent_errors: dict[str, deque[float]] = {
            provider: deque(maxlen=100) for provider in _PROVIDERS
        }
        self._last_alert_minute: dict[str, int] = {}
        self._alerts: Counter[str] = Counter()

    def _observe_latency(self, component: str, duration_ms: float) -> None:
        index = next(
            (i for i, bound in enumerate(_LATENCY_BOUNDS_MS) if duration_ms <= bound),
            len(_LATENCY_BOUNDS_MS),
        )
        self._latency[component][index] += 1

    def _alert_once(self, code: str, minute: int) -> bool:
        if self._last_alert_minute.get(code) == minute:
            return False
        self._last_alert_minute[code] = minute
        self._alerts[code] += 1
        return True

    def record_http(
        self,
        *,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        error_category: str,
        request_id: str,
    ) -> None:
        status_class = f"{status_code // 100}xx" if 100 <= status_code <= 599 else "other"
        safe_category = error_category if error_category in _HTTP_ERROR_CATEGORIES else "other"
        minute = int(datetime.now(UTC).timestamp() // 60)
        with self._lock:
            self._http_status[status_class] += 1
            self._observe_latency("http", duration_ms)
            slow_alert = duration_ms >= _SLOW_HTTP_MS and self._alert_once("http_slow", minute)
        _event(
            "http_request",
            method=method if method in _HTTP_METHODS else "other",
            endpoint=endpoint if endpoint.startswith("/") or endpoint == "<unmatched>" else "other",
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            error_category=safe_category,
            request_ref=request_reference(request_id),
        )
        if slow_alert:
            _event("alert", code="http_slow", component="http")

    def record_provider(
        self,
        provider: str,
        outcome: str,
        duration_ms: float,
        *,
        usage: tuple[int, int, int, int] | None = None,
        rates: tuple[Decimal | None, Decimal | None, Decimal | None, Decimal | None] | None = None,
        daily_cost_alert_usd: Decimal | None = None,
    ) -> None:
        if provider not in _PROVIDERS:
            raise ValueError("unsupported metrics provider")
        safe_outcome = outcome if outcome in _OUTCOMES else "other"
        now = datetime.now(UTC)
        minute = int(now.timestamp() // 60)
        error_alert = slow_alert = cost_alert = missing_usage_alert = pricing_missing_alert = False
        with self._lock:
            self._provider_outcomes[provider][safe_outcome] += 1
            self._observe_latency(provider, duration_ms)
            slow_alert = duration_ms >= _SLOW_PROVIDER_MS[provider] and self._alert_once(
                f"{provider}_slow", minute
            )
            if safe_outcome != "ok":
                recent = self._recent_errors[provider]
                recent.append(now.timestamp())
                while recent and recent[0] < now.timestamp() - 60:
                    recent.popleft()
                error_alert = len(recent) >= _ERROR_ALERT_THRESHOLD and self._alert_once(
                    f"{provider}_errors", minute
                )
            if provider == "openai" and safe_outcome == "ok":
                if usage is None:
                    self._unpriced_responses += 1
                    missing_usage_alert = self._alert_once("openai_usage_missing", minute)
                else:
                    input_tokens, cached_tokens, cache_write_tokens, output_tokens = usage
                    self._token_totals["input"] += input_tokens
                    self._token_totals["cached_input"] += cached_tokens
                    self._token_totals["cache_write"] += cache_write_tokens
                    self._token_totals["output"] += output_tokens
                    if rates is None or any(rate is None for rate in rates):
                        self._unpriced_responses += 1
                        pricing_missing_alert = self._alert_once("openai_pricing_missing", minute)
                    else:
                        input_rate, cached_rate, write_rate, output_rate = rates
                        assert all(rate is not None for rate in rates)
                        estimate = (
                            Decimal(input_tokens - cached_tokens - cache_write_tokens) * input_rate
                            + Decimal(cached_tokens) * cached_rate
                            + Decimal(cache_write_tokens) * write_rate
                            + Decimal(output_tokens) * output_rate
                        ) / Decimal(1_000_000)
                        self._estimated_cost_usd += estimate
                        if self._cost_day != now.date():
                            self._cost_day = now.date()
                            self._daily_cost_usd = Decimal("0")
                        self._daily_cost_usd += estimate
                        cost_alert = (
                            daily_cost_alert_usd is not None
                            and self._daily_cost_usd >= daily_cost_alert_usd
                            and self._alert_once("openai_daily_estimate", minute)
                        )
        _event(
            "provider_call",
            component=provider,
            outcome=safe_outcome,
            duration_ms=round(duration_ms, 2),
            input_tokens=usage[0] if provider == "openai" and usage else None,
            output_tokens=usage[3] if provider == "openai" and usage else None,
        )
        for enabled, code in (
            (slow_alert, f"{provider}_slow"),
            (error_alert, f"{provider}_errors"),
            (missing_usage_alert, "openai_usage_missing"),
            (pricing_missing_alert, "openai_pricing_missing"),
            (cost_alert, "openai_daily_estimate"),
        ):
            if enabled:
                _event("alert", code=code, component=provider)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            today = datetime.now(UTC).date()
            if self._cost_day != today:
                self._cost_day = today
                self._daily_cost_usd = Decimal("0")
            return {
                "started_at": self._started_at.isoformat(),
                "scope": "process",
                "http_status": dict(self._http_status),
                "provider_outcomes": {
                    provider: dict(outcomes)
                    for provider, outcomes in self._provider_outcomes.items()
                },
                "latency_buckets_ms": {
                    name: dict(zip((*_LATENCY_BOUNDS_MS, "+Inf"), buckets, strict=True))
                    for name, buckets in self._latency.items()
                },
                "openai_tokens": dict(self._token_totals),
                "openai_unpriced_responses": self._unpriced_responses,
                "openai_estimated_cost_usd": format(self._estimated_cost_usd.normalize(), "f"),
                "openai_estimated_cost_today_usd": format(self._daily_cost_usd.normalize(), "f"),
                "alerts_total": dict(self._alerts),
            }


# Only backend-owned route templates and categories may become log labels.
_HTTP_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"})
_HTTP_ERROR_CATEGORIES = frozenset(
    {
        "none",
        "unhandled_exception",
        "invalid_request",
        "webhook_rate_limited",
        "webhook_body_rejected",
        "webhook_body_timeout",
        "service_unavailable",
        "admin_authentication_failed",
        "admin_forbidden",
        "admin_https_required",
        "ai_service_unavailable",
        "whatsapp_service_unavailable",
    }
)


@lru_cache
def get_operational_metrics() -> OperationalMetrics:
    return OperationalMetrics()
