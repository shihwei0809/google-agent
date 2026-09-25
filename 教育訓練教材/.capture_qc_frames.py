from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote

root = Path(r"C:\GOOGLE ANGET\QC-系統客製化電子化工廠\.video_demo\frames").resolve()
root.mkdir(parents=True, exist_ok=True)

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/frame":
            self.send_error(404)
            return
        name = Path(unquote(self.headers.get("X-Frame-Name", "frame.png"))).name
        if not name.endswith(".png") or name in {".png", "..png"}:
            self.send_error(400)
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 20_000_000:
            self.send_error(413)
            return
        data = self.rfile.read(length)
        (root / name).write_bytes(data)
        self.send_response(201)
        self.end_headers()
        self.wfile.write(b"saved")
        print(f"saved {name} ({len(data)} bytes)", flush=True)

    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)

HTTPServer(("127.0.0.1", 8134), Handler).serve_forever()
