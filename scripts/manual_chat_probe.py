import argparse
import asyncio
import ipaddress
import json
from typing import Literal
from urllib.parse import urlsplit

import httpx

Expectation = Literal["success", "provider-error"]
DEFAULT_URL = "http://127.0.0.1:8000/api/v1/chat"
DEFAULT_MESSAGE = "Responde con un saludo breve y nada más."
SAFE_PROVIDER_ERROR = {
    "code": "ai_service_unavailable",
    "message": "El asistente no está disponible temporalmente.",
}


def validate_loopback_url(url: str) -> str:
    parsed = urlsplit(url)
    hostname = parsed.hostname
    if parsed.scheme != "http" or hostname is None:
        raise ValueError("probe URL must be HTTP on loopback")
    try:
        is_loopback = ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        is_loopback = hostname.lower() == "localhost"
    if not is_loopback or parsed.path != "/api/v1/chat" or parsed.query or parsed.fragment:
        raise ValueError("probe URL must target the loopback /api/v1/chat endpoint")
    return url


def build_safe_summary(response: httpx.Response, expectation: Expectation) -> dict[str, object]:
    try:
        payload = response.json()
    except ValueError:
        payload = None

    summary: dict[str, object] = {
        "status_code": response.status_code,
        "request_id_present": bool(response.headers.get("X-Request-ID")),
        "json_object": isinstance(payload, dict),
    }

    if expectation == "success":
        answer = payload.get("answer") if isinstance(payload, dict) else None
        answer_present = isinstance(answer, str) and bool(answer.strip())
        summary.update(
            {
                "answer_present": answer_present,
                "answer_chars": len(answer) if isinstance(answer, str) else 0,
                "checks_passed": response.status_code == 200 and answer_present,
            }
        )
        return summary

    error = payload.get("error") if isinstance(payload, dict) else None
    error_is_safe = error == SAFE_PROVIDER_ERROR
    summary.update(
        {
            "safe_provider_error": error_is_safe,
            "checks_passed": response.status_code == 503 and error_is_safe,
        }
    )
    return summary


async def run_probe(url: str, message: str, expectation: Expectation, timeout: float) -> int:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json={"message": message})
    except httpx.HTTPError as exc:
        print(json.dumps({"probe_error": type(exc).__name__, "checks_passed": False}))
        return 2

    summary = build_safe_summary(response, expectation)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["checks_passed"] else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe the local chat endpoint without printing credentials or response text."
    )
    parser.add_argument("--url", type=validate_loopback_url, default=DEFAULT_URL)
    parser.add_argument("--message", default=DEFAULT_MESSAGE)
    parser.add_argument("--expect", choices=("success", "provider-error"), default="success")
    parser.add_argument("--timeout", type=float, default=60.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return asyncio.run(run_probe(args.url, args.message, args.expect, args.timeout))


if __name__ == "__main__":
    raise SystemExit(main())
