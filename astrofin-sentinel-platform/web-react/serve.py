import http.server
import os
import socketserver

PORT = int(os.environ.get("PORT", 4200))
DIR = os.path.join(os.path.dirname(__file__), "dist")

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

with socketserver.TCPServer(("", PORT), NoCacheHandler) as httpd:
    print(f"Serving {DIR} on port {PORT}")
    httpd.serve_forever()
