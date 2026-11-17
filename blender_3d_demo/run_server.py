import http.server
import json
import mimetypes
import os
import socket
import socketserver
import subprocess
import sys
import threading
import urllib.parse
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PORT = 8088

mimetypes.add_type("model/gltf-binary", ".glb")
mimetypes.add_type("model/gltf+json", ".gltf")


ALLOWED_FLOW_THEMES = {
    "kids",
    "cyberpunk",
    "wuxia",
    "white",
    "bpm_shot01",
    "bpm_shot05",
    "bpm_shot08",
    "bpm_all",
    "bpm_c02",
    "bpm_c03",
    "bpm_c05",
    "bpm_plan_c",
}


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def _send_json(self, status_code: int, data: dict):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/upload-flow":
            qs = urllib.parse.parse_qs(parsed.query)
            theme = qs.get("theme", ["kids"])[0]
            if theme not in ALLOWED_FLOW_THEMES:
                theme = "kids"

            script_path = os.path.join(BASE_DIR, "auto_upload_flow.py")
            flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            subprocess.Popen(
                [sys.executable, script_path, "--theme", theme],
                cwd=BASE_DIR,
                creationflags=flags,
            )
            self._send_json(200, {"ok": True, "theme": theme})
            return

        if parsed.path == "/api/rebuild-bpm-video":
            qs = urllib.parse.parse_qs(parsed.query)
            plan = qs.get("plan", ["a"])[0].lower()
            voice = qs.get("voice", ["hsiaochen"])[0]
            if voice not in ("hsiaochen", "yunjhe", "hsiaoyu", "duet"):
                voice = "hsiaochen"
            rebuild_audio = qs.get("rebuild_audio", ["0"])[0] == "1"

            if plan == "c":
                script_path = os.path.join(BASE_DIR, "build_bpm_plan_c_video.py")
                cmd = [sys.executable, script_path, "--voice", voice]
                if rebuild_audio:
                    cmd.append("--rebuild-audio")
            else:
                script_path = os.path.join(BASE_DIR, "build_bpm_sop_video.py")
                cmd = [sys.executable, script_path, "--voice", voice]
                if rebuild_audio:
                    cmd.append("--rebuild-audio")
                else:
                    cmd.append("--only-flow")

            proc = subprocess.run(
                cmd,
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if proc.returncode == 0:
                self._send_json(200, {"ok": True, "log": proc.stdout[-1500:]})
            else:
                self._send_json(500, {"ok": False, "error": (proc.stderr or proc.stdout)[-1500:]})
            return

        self.send_error(404, "Not Found")


class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def get_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def find_available_port(start_port: int, max_tries: int = 40) -> int:
    for p in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    raise RuntimeError("No available port found.")


def main():
    args = sys.argv[1:]
    no_browser = "--no-browser" in args
    start_port = DEFAULT_PORT
    for arg in args:
        if arg.isdigit():
            start_port = int(arg)
            break

    port = find_available_port(start_port)
    if port != start_port:
        print(f"預設 Port {start_port} 已被佔用，已自動切換至可用 Port: {port}", flush=True)

    lan_ip = get_lan_ip()
    local_url = f"http://localhost:{port}/index.html"
    fpv_url = f"http://localhost:{port}/fpv_studio.html"
    bpm_url = f"http://localhost:{port}/bpm_storyboard_studio.html"
    lan_url = f"http://{lan_ip}:{port}/index.html"

    with ReusableTCPServer(("0.0.0.0", port), QuietHandler) as httpd:
        print("=" * 60, flush=True)
        print("  Blender 3D 智慧儲位 & FPV 白模工作室已啟動", flush=True)
        print(f"  3D 儲位看板 : {local_url}", flush=True)
        print(f"  FPV 工作室  : {fpv_url}", flush=True)
        print(f"  BPM 分鏡台  : {bpm_url}", flush=True)
        print(f"  區網預覽    : {lan_url}", flush=True)
        print("  按 Ctrl+C 可停止伺服器", flush=True)
        print("=" * 60, flush=True)
        if not no_browser:
            threading.Timer(1.2, lambda: webbrowser.open(local_url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n伺服器已關閉。")


if __name__ == "__main__":
    main()
