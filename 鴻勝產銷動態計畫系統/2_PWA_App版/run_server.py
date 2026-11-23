#!/usr/bin/env python3
"""
鴻勝產銷動態計畫系統 - 本機 PWA FastAPI + SQLite 後端伺服器
遵循 Rule 6：顯示本機區域網路 IP、支援 Port 佔用自動順延切換。
"""
from __future__ import annotations

import json
import os
import socket
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "sales_planner.db"
SCHEMA_PATH = BASE_DIR / "schema_sqlite.sql"

app = FastAPI(title="鴻勝產銷動態計畫系統 Local PWA API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        if SCHEMA_PATH.exists():
            conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        else:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sp_plan_state (
                  id TEXT PRIMARY KEY,
                  plan_json TEXT NOT NULL,
                  version INTEGER NOT NULL DEFAULT 1,
                  updated_by TEXT DEFAULT '系統',
                  updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sp_plan_archives (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  description TEXT DEFAULT '',
                  plan_json TEXT NOT NULL,
                  created_by TEXT DEFAULT '系統',
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sp_change_logs (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  action TEXT NOT NULL,
                  actor TEXT NOT NULL,
                  summary TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                """
            )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


init_db()


@app.get("/api/health")
def health() -> Dict[str, Any]:
    with get_conn() as conn:
        cnt = conn.execute("SELECT COUNT(*) FROM sp_plan_archives").fetchone()[0]
    return {
        "ok": True,
        "mode": "local-sqlite",
        "db": str(DB_PATH),
        "archiveCount": cnt,
        "timestamp": now_iso(),
    }


@app.get("/api/plan")
def get_plan() -> Dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT plan_json, version, updated_by, updated_at FROM sp_plan_state WHERE id = 'current'"
        ).fetchone()
    if not row:
        return {"ok": True, "exists": False, "version": 0, "updatedBy": None, "updatedAt": None, "plan": None}
    return {
        "ok": True,
        "exists": True,
        "version": row["version"],
        "updatedBy": row["updated_by"],
        "updatedAt": row["updated_at"],
        "plan": json.loads(row["plan_json"]),
    }


@app.post("/api/plan")
async def save_plan(req: Request):
    body = await req.json()
    plan_obj = body.get("plan")
    if not isinstance(plan_obj, dict) or not isinstance(plan_obj.get("items"), list):
        raise HTTPException(status_code=400, detail="Invalid plan payload")

    client_ver = int(body.get("version") or 0)
    force = bool(body.get("force"))
    updated_by = str(body.get("updatedBy") or "本機人員")[:50]
    summary = str(body.get("summary") or "更新產銷計畫")[:200]
    ts = now_iso()

    with get_conn() as conn:
        cur = conn.execute(
            "SELECT plan_json, version, updated_by, updated_at FROM sp_plan_state WHERE id = 'current'"
        ).fetchone()
        if cur and not force and client_ver > 0 and cur["version"] > client_ver:
            return JSONResponse(
                status_code=409,
                content={
                    "ok": False,
                    "error": "conflict",
                    "message": f"本機版本 (v{cur['version']} 由「{cur['updated_by']}」更新) 較新於您的版本 (v{client_ver})",
                    "serverVersion": cur["version"],
                    "serverUpdatedBy": cur["updated_by"],
                    "serverUpdatedAt": cur["updated_at"],
                    "serverPlan": json.loads(cur["plan_json"]),
                },
            )
        next_ver = (cur["version"] + 1) if cur else 1
        conn.execute(
            """
            INSERT INTO sp_plan_state (id, plan_json, version, updated_by, updated_at)
            VALUES ('current', ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              plan_json = excluded.plan_json,
              version = excluded.version,
              updated_by = excluded.updated_by,
              updated_at = excluded.updated_at
            """,
            (json.dumps(plan_obj, ensure_ascii=False), next_ver, updated_by, ts),
        )
        conn.execute(
            "INSERT INTO sp_change_logs (action, actor, summary, created_at) VALUES (?, ?, ?, ?)",
            ("FORCE_SAVE" if force else "SAVE", updated_by, f"{summary} (v{next_ver})", ts),
        )
        conn.execute(
            "DELETE FROM sp_change_logs WHERE id NOT IN (SELECT id FROM sp_change_logs ORDER BY id DESC LIMIT 200)"
        )
        conn.commit()
    return {"ok": True, "version": next_ver, "updatedBy": updated_by, "updatedAt": ts}


@app.get("/api/logs")
def get_logs() -> Dict[str, Any]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, action, actor, summary, created_at FROM sp_change_logs ORDER BY id DESC LIMIT 40"
        ).fetchall()
    return {"ok": True, "logs": [dict(r) for r in rows]}


@app.get("/api/archives")
def list_archives() -> Dict[str, Any]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, description, created_by, created_at, updated_at FROM sp_plan_archives ORDER BY updated_at DESC, id DESC"
        ).fetchall()
    return {"ok": True, "archives": [dict(r) for r in rows]}


@app.post("/api/archives")
async def create_archive(req: Request) -> Dict[str, Any]:
    body = await req.json()
    name = str(body.get("name") or "").strip()[:100]
    plan_obj = body.get("plan")
    if not name or not isinstance(plan_obj, dict):
        raise HTTPException(status_code=400, detail="Snapshot name and plan required")
    desc = str(body.get("description") or "")[:200]
    actor = str(body.get("created_by") or "本機人員")[:50]
    ts = now_iso()
    serialized = json.dumps(plan_obj, ensure_ascii=False)
    ow_id = body.get("overwrite_id")

    with get_conn() as conn:
        if ow_id:
            conn.execute(
                "UPDATE sp_plan_archives SET name = ?, description = ?, plan_json = ?, created_by = ?, updated_at = ? WHERE id = ?",
                (name, desc, serialized, actor, ts, int(ow_id)),
            )
            conn.execute(
                "INSERT INTO sp_change_logs (action, actor, summary, created_at) VALUES ('ARCHIVE_OVERWRITE', ?, ?, ?)",
                (actor, f"覆蓋快照「{name}」", ts),
            )
            conn.commit()
            return {"ok": True, "id": int(ow_id), "updated_at": ts}
        cur = conn.execute(
            "INSERT INTO sp_plan_archives (name, description, plan_json, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (name, desc, serialized, actor, ts, ts),
        )
        conn.execute(
            "INSERT INTO sp_change_logs (action, actor, summary, created_at) VALUES ('ARCHIVE_SAVE', ?, ?, ?)",
            (actor, f"建立快照「{name}」", ts),
        )
        conn.commit()
        return {"ok": True, "id": cur.lastrowid, "created_at": ts}


@app.get("/api/archives/{arch_id}")
def get_archive(arch_id: int) -> Dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, description, plan_json, created_by, created_at, updated_at FROM sp_plan_archives WHERE id = ?",
            (arch_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Archive not found")
    return {
        "ok": True,
        "archive": {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "created_by": row["created_by"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "plan": json.loads(row["plan_json"]),
        },
    }


@app.put("/api/archives/{arch_id}")
async def rename_archive(arch_id: int, req: Request) -> Dict[str, Any]:
    body = await req.json()
    new_name = str(body.get("name") or "").strip()[:100]
    new_desc = str(body.get("description") or "")[:200]
    if not new_name:
        raise HTTPException(status_code=400, detail="Name required")
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            "UPDATE sp_plan_archives SET name = ?, description = ?, updated_at = ? WHERE id = ?",
            (new_name, new_desc, ts, arch_id),
        )
        conn.commit()
    return {"ok": True, "id": arch_id, "updated_at": ts}


@app.delete("/api/archives/{arch_id}")
async def delete_archive(arch_id: int, req: Request, password: Optional[str] = None):
    pwd = password or ""
    if not pwd:
        try:
            b = await req.json()
            pwd = str(b.get("password") or "")
        except Exception:
            pass
    if pwd != "8888":
        return JSONResponse(status_code=403, content={"ok": False, "error": "刪除密碼錯誤（預設 8888）"})
    with get_conn() as conn:
        conn.execute("DELETE FROM sp_plan_archives WHERE id = ?", (arch_id,))
        conn.commit()
    return {"ok": True, "deletedId": arch_id}


@app.get("/")
def serve_index():
    return FileResponse(str(PUBLIC_DIR / "index.html"))


app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="public")


def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def find_available_port(preferred: int = 8005, max_tries: int = 20) -> int:
    for p in range(preferred, preferred + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", p))
                return p
            except OSError:
                continue
    return preferred


if __name__ == "__main__":
    pref = int(os.environ.get("PORT", "8005"))
    port = find_available_port(pref)
    lan_ip = get_lan_ip()
    if port != pref:
        print(f"預設 Port {pref} 已被佔用，已自動切換至可用 Port: {port}")
    print("=" * 60)
    print("  鴻勝產銷動態計畫系統 - 本機 PWA + SQLite 伺服器啟動成功")
    print(f"  本機網址 : http://localhost:{port}")
    print(f"  區網分享 : http://{lan_ip}:{port}")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
