import asyncio
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlsplit

from app import app as flaxon_app


class handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _handle(self):
        parsed = urlsplit(self.path)
        length = int(self.headers.get("content-length", "0") or 0)
        body = self.rfile.read(min(max(length, 0), 2 * 1024 * 1024))
        sent = {"status": 500, "headers": [], "body": bytearray()}
        scope = {"type": "http", "asgi": {"version": "3.0", "spec_version": "2.0"}, "http_version": "1.1", "method": self.command,
                 "scheme": "https", "path": parsed.path or "/", "raw_path": (parsed.path or "/").encode(), "query_string": parsed.query.encode(),
                 "headers": [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in self.headers.items()], "server": (self.headers.get("host", "localhost"), 443), "client": ("vercel", 0), "root_path": ""}
        consumed = False
        async def receive():
            nonlocal consumed
            if consumed:
                return {"type": "http.disconnect"}
            consumed = True
            return {"type": "http.request", "body": body, "more_body": False}
        async def send(message):
            if message["type"] == "http.response.start":
                sent["status"] = message["status"]
                sent["headers"] = message.get("headers", [])
            elif message["type"] == "http.response.body":
                sent["body"].extend(message.get("body", b""))
        asyncio.run(flaxon_app(scope, receive, send))
        self.send_response(sent["status"])
        for key, value in sent["headers"]:
            self.send_header(key.decode("latin-1"), value.decode("latin-1"))
        self.end_headers()
        self.wfile.write(bytes(sent["body"]))

    def do_GET(self): self._handle()
    def do_POST(self): self._handle()
    def do_OPTIONS(self): self._handle()


__all__ = ["app"]
