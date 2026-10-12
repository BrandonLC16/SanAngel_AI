"""Production-safe Uvicorn entry point for the local Caddy reverse proxy."""

from ipaddress import ip_address

import uvicorn

from backend.app.core.config import HttpSettings, get_http_settings, validate_runtime_secrets


def server_config(settings: HttpSettings) -> uvicorn.Config:
    if settings.app_env == "production":
        try:
            loopback = ip_address(settings.app_host).is_loopback
        except ValueError:
            loopback = False
        if not loopback:
            raise ValueError("production backend must bind to a loopback IP")
    return uvicorn.Config(
        "backend.app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        proxy_headers=False,
        access_log=False,
    )


def main() -> None:
    validate_runtime_secrets()
    uvicorn.Server(server_config(get_http_settings())).run()


if __name__ == "__main__":
    main()
