import httpx
import pytest

from scripts.manual_chat_probe import build_safe_summary, validate_loopback_url


def make_response(status_code: int, payload: dict[str, object]) -> httpx.Response:
    return httpx.Response(
        status_code,
        headers={"X-Request-ID": "manual-probe-request"},
        json=payload,
    )


def test_success_summary_does_not_include_response_text() -> None:
    answer_marker = "private-real-provider-answer"

    summary = build_safe_summary(make_response(200, {"answer": answer_marker}), "success")

    assert summary == {
        "status_code": 200,
        "request_id_present": True,
        "json_object": True,
        "answer_present": True,
        "answer_chars": len(answer_marker),
        "checks_passed": True,
    }
    assert answer_marker not in str(summary)


def test_provider_error_summary_accepts_only_fixed_safe_shape() -> None:
    summary = build_safe_summary(
        make_response(
            503,
            {
                "error": {
                    "code": "ai_service_unavailable",
                    "message": "El asistente no está disponible temporalmente.",
                }
            },
        ),
        "provider-error",
    )

    assert summary["safe_provider_error"] is True
    assert summary["checks_passed"] is True


@pytest.mark.parametrize(
    "url",
    (
        "https://127.0.0.1:8000/api/v1/chat",
        "http://api.openai.com/api/v1/chat",
        "http://127.0.0.1:8000/health",
        "http://127.0.0.1:8000/api/v1/chat?debug=true",
    ),
)
def test_probe_rejects_non_loopback_or_unexpected_urls(url: str) -> None:
    with pytest.raises(ValueError):
        validate_loopback_url(url)
