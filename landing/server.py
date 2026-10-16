"""DecisionOS Landing Server — serves static + proxies /api/chat/stream to ROMA bridge."""
import http.server
import urllib.request
import urllib.error
import json
import os
import sys

ROMA_BRIDGE = os.environ.get("ROMA_BRIDGE_INTERNAL", "http://127.0.0.1:8900")

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/chat/stream":
            self._proxy_chat()
        elif self.path == "/api/deepseek":
            self._proxy_deepseek()
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, X-API-Key")
        self.end_headers()

    def _proxy_stream(self, url, timeout=120):
        """Generic SSE-streaming proxy to internal service."""
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"

        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            method="POST",
        )

        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache, no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode(errors="replace")[:500]
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Upstream {e.code}", "detail": err_body}).encode())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Upstream unreachable: {e}"}).encode())

    def _proxy_chat(self):
        self._proxy_stream(f"{ROMA_BRIDGE}/api/chat/stream")

    def _proxy_deepseek(self):
        self._proxy_stream("http://127.0.0.1:3099/api/deepseek")

    def log_message(self, format, *args):
        print(f"[landing] {args[0]}", file=sys.stderr)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    directory = os.path.dirname(os.path.abspath(__file__))

    class CWDProxyHandler(ProxyHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

    server = http.server.HTTPServer(("0.0.0.0", port), CWDProxyHandler)
    print(f"DecisionOS Landing + Chat Proxy on :{port}", file=sys.stderr)
    server.serve_forever()
