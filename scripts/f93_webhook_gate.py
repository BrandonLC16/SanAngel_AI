"""Temporary local gate exposing only the WhatsApp webhook to an HTTPS tunnel."""

import argparse
import http.client
import ssl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WEBHOOK_PATH = "/api/v1/whatsapp/webhook"
MAX_BODY_BYTES = 65536


class WebhookGate(BaseHTTPRequestHandler):
    certificate_file = ""

    def log_message(self, format_string: str, *args: object) -> None:
        pass

    def do_POST(self) -> None:
        if self.path != WEBHOOK_PATH:
            self.send_error(404)
            return

        authorizations = self.headers.get_all("Authorization", [])
        content_lengths = self.headers.get_all("Content-Length", [])
        if len(authorizations) != 1 or len(content_lengths) != 1:
            self.send_error(403)
            return
        try:
            content_length = int(content_lengths[0])
        except ValueError:
            self.send_error(400)
            return
        if content_length < 0 or content_length > MAX_BODY_BYTES:
            self.send_error(413)
            return

        connection = http.client.HTTPSConnection(
            "127.0.0.1",
            8000,
            context=ssl.create_default_context(cafile=self.certificate_file),
            timeout=20,
        )
        try:
            connection.request(
                "POST",
                WEBHOOK_PATH,
                body=self.rfile.read(content_length),
                headers={
                    "Authorization": authorizations[0],
                    "Content-Type": "application/json",
                },
            )
            response = connection.getresponse()
            response.read()
            self.send_response(response.status)
            self.send_header("Content-Length", "0")
            self.end_headers()
        except (OSError, http.client.HTTPException):
            self.send_error(502)
        finally:
            connection.close()

    def do_GET(self) -> None:
        self.send_error(404)

    do_HEAD = do_GET
    do_PUT = do_GET
    do_PATCH = do_GET
    do_DELETE = do_GET
    do_OPTIONS = do_GET


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--certificate", required=True)
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    WebhookGate.certificate_file = args.certificate
    server = ThreadingHTTPServer(("127.0.0.1", args.port), WebhookGate)
    server.serve_forever()


if __name__ == "__main__":
    main()
