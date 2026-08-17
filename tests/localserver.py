"""Real in-process HTTP server returning scripted responses, for transport tests."""

from __future__ import annotations

import socket
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


@dataclass
class ScriptedResponse:
    status: int
    body: bytes = b""
    headers: dict[str, str] = field(default_factory=dict)
    declared_length: int | None = None
    """Content-Length to advertise; when larger than ``body`` the connection
    closes short, simulating a mid-stream transfer failure."""


@contextmanager
def scripted_server(responses: list[ScriptedResponse]) -> Iterator[str]:
    """Serve the given responses in order from a real local HTTP server."""
    pending = list(responses)

    class Handler(BaseHTTPRequestHandler):
        def _reply(self) -> None:
            body_length = int(self.headers.get("Content-Length") or 0)
            if body_length:
                self.rfile.read(body_length)
            scripted = pending.pop(0)
            self.send_response(scripted.status)
            for name, value in scripted.headers.items():
                self.send_header(name, value)
            declared = (
                scripted.declared_length
                if scripted.declared_length is not None
                else len(scripted.body)
            )
            self.send_header("Content-Length", str(declared))
            self.end_headers()
            self.wfile.write(scripted.body)

        do_GET = _reply
        do_POST = _reply
        do_PUT = _reply
        do_DELETE = _reply

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def closed_port_url() -> str:
    """URL of a port that is guaranteed to have no listener."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    return f"http://127.0.0.1:{port}"
