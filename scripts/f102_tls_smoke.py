"""Optional local TLS smoke test with a separately installed Caddy binary."""

import argparse
import http.client
import os
import socket
import ssl
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTTP_PORT = 18080
HTTPS_PORT = 18443
BACKEND_PORT = 8000


def _wait_for_tcp(port: int, process: subprocess.Popen[bytes]) -> None:
    for _ in range(50):
        if process.poll() is not None:
            raise RuntimeError("local TLS test service exited")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("local TLS test service did not start")


def _stop(process: subprocess.Popen[bytes] | None) -> None:
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def run(caddy: Path) -> None:
    if not caddy.is_file():
        raise ValueError("Caddy executable not found")
    dist = ROOT / "frontend" / "dist"
    if not (dist / "index.html").is_file():
        raise ValueError("build the panel before the TLS smoke test")
    for port in (BACKEND_PORT, HTTP_PORT, HTTPS_PORT):
        with socket.socket() as listener:
            try:
                listener.bind(("127.0.0.1", port))
            except OSError as exc:
                raise RuntimeError("a local TLS test port is already in use") from exc

    with tempfile.TemporaryDirectory(prefix="sanangel-f102-") as temporary:
        test_dir = Path(temporary).resolve()
        if test_dir.parent != Path(tempfile.gettempdir()).resolve():
            raise RuntimeError("unexpected temporary test directory")

        caddyfile = (ROOT / "deploy" / "Caddyfile").read_text(encoding="utf-8")
        if caddyfile.count("{$PUBLIC_DOMAIN} {") != 1 or caddyfile.count("{$PANEL_DIST}") != 1:
            raise RuntimeError("Caddyfile placeholders changed")
        caddyfile = caddyfile.replace(
            "{$PUBLIC_DOMAIN} {", f"localhost:{HTTPS_PORT} {{\n    bind 127.0.0.1"
        ).replace("{$PANEL_DIST}", dist.as_posix())
        caddyfile = (
            "{\n    skip_install_trust\n    admin off\n"
            f"    http_port {HTTP_PORT}\n    https_port {HTTPS_PORT}\n}}\n" + caddyfile
        )
        config_path = test_dir / "Caddyfile"
        config_path.write_text(caddyfile, encoding="utf-8")

        environment = os.environ.copy()
        environment.update(
            APP_ENV="production",
            APP_HOST="127.0.0.1",
            APP_PORT=str(BACKEND_PORT),
            TRUSTED_PROXY_IPS="127.0.0.1",
            XDG_DATA_HOME=str(test_dir),
            XDG_CONFIG_HOME=str(test_dir),
        )
        backend = None
        proxy = None
        try:
            backend = subprocess.Popen(
                [sys.executable, "-m", "scripts.run_backend"],
                cwd=ROOT,
                env=environment,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            _wait_for_tcp(BACKEND_PORT, backend)
            proxy = subprocess.Popen(
                [str(caddy), "run", "--config", str(config_path), "--adapter", "caddyfile"],
                cwd=ROOT,
                env=environment,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            _wait_for_tcp(HTTPS_PORT, proxy)

            direct = http.client.HTTPConnection("127.0.0.1", BACKEND_PORT, timeout=3)
            direct.request("GET", "/health")
            assert direct.getresponse().status == 403
            direct.close()

            plain = http.client.HTTPConnection("localhost", HTTP_PORT, timeout=3)
            plain.request("GET", "/health", headers={"X-Forwarded-Proto": "https"})
            redirect = plain.getresponse()
            assert redirect.status == 308
            location = redirect.getheader("Location")
            assert location == "https://localhost/health", location
            plain.close()

            root_cert = test_dir / "caddy" / "pki" / "authorities" / "local" / "root.crt"
            if not root_cert.is_file():
                raise RuntimeError("local TLS root certificate missing")
            context = ssl.create_default_context(cafile=str(root_cert))
            secure = http.client.HTTPSConnection(
                "localhost", HTTPS_PORT, context=context, timeout=3
            )
            secure.request("GET", "/health", headers={"X-Forwarded-Proto": "http"})
            health = secure.getresponse()
            assert health.status == 200
            assert health.getheader("Strict-Transport-Security") == "max-age=31536000"
            health.read()
            secure.request("GET", "/")
            panel = secure.getresponse()
            assert panel.status == 200
            assert "script-src 'self'" in panel.getheader("Content-Security-Policy", "")
            panel.read()
            secure.close()
        finally:
            _stop(proxy)
            _stop(backend)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--caddy", type=Path, required=True)
    run(parser.parse_args().caddy)
    print("Local TLS, redirect, backend rejection, health, and panel CSP: OK")
