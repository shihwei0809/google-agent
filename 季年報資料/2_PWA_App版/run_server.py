"""
鴻勝資材部｜季年報智慧分析系統 — PWA 本機伺服器 (run_server.py)
功能：
1. 自動偵測可用 Port (預設 8092，被佔用自動切換) 並顯示本機實體區網 IP
2. 內建 SQLite 持久化資料庫 (data/report_db.sqlite)，API 規格與 Cloudflare D1 完全一致
3. 內建 Gemini Vision OCR Proxy (/api/ocr)，嚴格遵守 3.8 -> 3.7 -> 3.6 -> 2.5 -> 1.5 降級鏈
"""
import json
import os
import socket
import sqlite3
import sys
import threading
import time
import urllib.request
import urllib.error
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "report_db.sqlite"

GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-2.5-flash",
    "gemini-1.5-flash",
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS monthly_metrics (
                ym TEXT NOT NULL,
                category TEXT NOT NULL,
                source TEXT NOT NULL,
                mt REAL,
                trips INTEGER,
                pallets INTEGER,
                rows_count INTEGER DEFAULT 0,
                breakdown_json TEXT DEFAULT '{}',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (ym, category, source)
            );
            CREATE TABLE IF NOT EXISTS daily_management (
                id INTEGER PRIMARY KEY,
                period TEXT NOT NULL,
                date TEXT,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT DEFAULT '記錄中'
            );
            CREATE TABLE IF NOT EXISTS key_projects (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                desc TEXT,
                effect TEXT,
                eta TEXT,
                status TEXT DEFAULT '進行中'
            );
            """
        )


init_db()

app = FastAPI(title="鴻勝資材部｜季年報智慧分析系統")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def api_health():
    return {"ok": True, "mode": "LOCAL_SQLITE", "db": str(DB_PATH.name)}


@app.get("/api/metrics")
def get_metrics():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM monthly_metrics ORDER BY ym ASC").fetchall()
    data = []
    for r in rows:
        data.append(
            {
                "ym": r["ym"],
                "category": r["category"],
                "source": r["source"],
                "mt": r["mt"],
                "trips": r["trips"],
                "pallets": r["pallets"],
                "rows": r["rows_count"],
                "breakdown": json.loads(r["breakdown_json"] or "{}"),
            }
        )
    return {"ok": True, "data": data}


@app.post("/api/metrics")
async def post_metrics(req: Request):
    body = await req.json()
    if body.get("action") == "delete_many" and isinstance(body.get("keys"), list):
        keys = body["keys"]
        with get_db() as conn:
            for k in keys:
                conn.execute(
                    "DELETE FROM monthly_metrics WHERE ym = ? AND category = ? AND source = ?",
                    (k["ym"], k["category"], k["source"]),
                )
        return {"ok": True, "deleted": len(keys)}

    records = body.get("records", [])
    fname = body.get("filename", "")
    with get_db() as conn:
        for r in records:
            bd = dict(r.get("breakdown") or {})
            if r.get("filename") or fname:
                bd["_filename"] = r.get("filename") or fname
            conn.execute(
                """
                INSERT INTO monthly_metrics (ym, category, source, mt, trips, pallets, rows_count, breakdown_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(ym, category, source) DO UPDATE SET
                    mt = excluded.mt,
                    trips = excluded.trips,
                    pallets = excluded.pallets,
                    rows_count = excluded.rows_count,
                    breakdown_json = excluded.breakdown_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    r["ym"],
                    r["category"],
                    r.get("source", "BI_EXCEL"),
                    r.get("mt"),
                    r.get("trips"),
                    r.get("pallets"),
                    r.get("rows", 0),
                    json.dumps(bd, ensure_ascii=False),
                ),
            )
    return {"ok": True, "saved": len(records)}


@app.delete("/api/metrics")
def delete_metric(ym: str, category: str, source: str):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM monthly_metrics WHERE ym = ? AND category = ? AND source = ?",
            (ym, category, source),
        )
    return {"ok": True, "deleted": 1}


@app.get("/api/management")
def get_management():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM daily_management ORDER BY id DESC").fetchall()
    return {"ok": True, "data": [dict(r) for r in rows]}


@app.post("/api/management")
async def post_management(req: Request):
    body = await req.json()
    items = body["records"] if isinstance(body.get("records"), list) else [body]
    base_id = int(time.time() * 1000)
    with get_db() as conn:
        for idx, r in enumerate(items):
            conn.execute(
                """
                INSERT INTO daily_management (id, period, date, type, content, status)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    period=excluded.period, date=excluded.date, type=excluded.type,
                    content=excluded.content, status=excluded.status
                """,
                (
                    int(r.get("id") or (base_id + idx)),
                    str(r.get("period") or "未指定"),
                    str(r.get("date") or ""),
                    str(r.get("type") or "其他管理"),
                    str(r.get("content") or ""),
                    str(r.get("status") or "記錄中"),
                ),
            )
    return {"ok": True, "saved": len(items)}


@app.delete("/api/management")
def delete_management(id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM daily_management WHERE id = ?", (id,))
    return {"ok": True}


@app.get("/api/projects")
def get_projects():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM key_projects ORDER BY id ASC").fetchall()
    return {"ok": True, "data": [dict(r) for r in rows]}


@app.post("/api/projects")
async def post_projects(req: Request):
    body = await req.json()
    items = body["records"] if isinstance(body.get("records"), list) else [body]
    base_id = int(time.time() * 1000)
    with get_db() as conn:
        for idx, r in enumerate(items):
            conn.execute(
                """
                INSERT INTO key_projects (id, title, desc, effect, eta, status)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title, desc=excluded.desc, effect=excluded.effect,
                    eta=excluded.eta, status=excluded.status
                """,
                (
                    int(r.get("id") or (base_id + idx)),
                    str(r.get("title") or "未命名工作項目"),
                    str(r.get("desc") or ""),
                    str(r.get("effect") or ""),
                    str(r.get("eta") or ""),
                    str(r.get("status") or "進行中"),
                ),
            )
    return {"ok": True, "saved": len(items)}


@app.delete("/api/projects")
def delete_projects(id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM key_projects WHERE id = ?", (id,))
    return {"ok": True}


@app.post("/api/ocr")
async def post_ocr(req: Request):
    body = await req.json()
    images = body.get("images", []) or []
    prompt = body.get("prompt", "")
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        # Try reading parent .env safely if present
        env_file = BASE_DIR.parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not api_key:
        return JSONResponse(status_code=400, content={"error": "伺服器未設定 GEMINI_API_KEY 環境變數"})

    image_parts = []
    for item in images:
        if isinstance(item, dict) and item.get("data"):
            image_parts.append({"inline_data": {"mime_type": item.get("mime_type", "image/jpeg"), "data": item["data"]}})
        else:
            image_parts.append({"inline_data": {"mime_type": "image/jpeg", "data": item}})

    parts = [{"text": prompt}] + image_parts
    payload = json.dumps({"contents": [{"parts": parts}], "generationConfig": {"temperature": 0.1}}).encode("utf-8")

    last_error = "所有模型皆無法回應"
    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req_obj = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req_obj, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw = data["candidates"][0]["content"]["parts"][0]["text"]
                cleaned = raw.replace("```json", "").replace("```", "").strip()
                start_idx = cleaned.find("[")
                end_idx = cleaned.rfind("]")
                if start_idx != -1 and end_idx > start_idx:
                    cleaned = cleaned[start_idx : end_idx + 1]
                records = json.loads(cleaned)
                return {"ok": True, "model": model, "records": records}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            last_error = f"[{model}] HTTP {e.code}: {err_body[:200]}"
        except Exception as e:
            last_error = f"[{model}] {str(e)}"

    return JSONResponse(status_code=502, content={"error": f"Gemini Vision OCR 降級鏈耗盡：{last_error}"})


# Mount static PWA files
app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")


def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def find_free_port(start_port: int = 8092) -> int:
    port = start_port
    while port < start_port + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    return start_port


if __name__ == "__main__":
    default_port = int(os.environ.get("PORT", "8092"))
    port = find_free_port(default_port)
    lan_ip = get_lan_ip()
    if port != default_port:
        print(f"[提示] 預設 Port {default_port} 已被佔用，已自動切換至可用 Port: {port}")
    print("=" * 60)
    print("  鴻勝資材部｜季年報智慧分析系統 (PWA 本機伺服器)")
    print(f"  本機網址：http://localhost:{port}")
    print(f"  區網分享：http://{lan_ip}:{port}")
    print("=" * 60)

    if "--no-browser" not in sys.argv:
        threading.Timer(1.8, lambda: webbrowser.open(f"http://localhost:{port}")).start()

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
