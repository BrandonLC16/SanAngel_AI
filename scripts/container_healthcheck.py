"""Check the loopback backend through the production HTTPS proxy contract."""

import http.client
import json
import os


def main() -> int:
    try:
        port = int(os.environ.get("APP_PORT", "8000"))
        if not 1 <= port <= 65535:
            return 1
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        try:
            connection.request("GET", "/health", headers={"X-Forwarded-Proto": "https"})
            response = connection.getresponse()
            if response.status != 200:
                return 1
            return int(
                json.loads(response.read(256))
                != {"status": "ok", "service": "carniceria-ai-chatbot"}
            )
        finally:
            connection.close()
    except (OSError, ValueError, http.client.HTTPException, json.JSONDecodeError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
