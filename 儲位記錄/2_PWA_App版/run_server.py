"""
倉儲儲位 PWA 系統 - 本機與區網 FastAPI 後端伺服器
- 直接讀寫 崙尾倉儲儲位表.xlsm 與 鴻勝儲位表.xlsm
- 支援 Port 佔用自動切換 (Port Fallback) 與本機區網 IP 自動偵測
- 記錄每日錄入板數、數量與各批號彙整，供出入庫核對
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import socket
import sys
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from excel_engine import ExcelEngine, ExcelLockedError

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_FILE = DATA_DIR / "daily_logs.json"
SETTINGS_FILE = DATA_DIR / "warehouse_settings.json"
USERS_FILE = DATA_DIR / "users.json"

DEFAULT_PORT = int(os.environ.get("PORT", "8010"))

app = FastAPI(title="倉儲儲位 PWA 系統", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ExcelEngine(PROJECT_ROOT)
ACTIVE_PORT = DEFAULT_PORT


class RecordPayload(BaseModel):
    wh_id: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    action: Literal["in", "out", "set"] = "in"
    in_mode: Literal["add", "replace", "merge"] = "add"
    item_name: str = ""
    item_no: str = ""
    lot_no: str = ""
    package: str = ""
    qty: float = Field(..., ge=0)
    pallets: int = Field(default=1, ge=0)
    note: str = ""
    clear_on_zero: bool = True
    operator: str = "現場人員"
    client_tx_id: Optional[str] = None


def normalize_lot_nos(raw: str) -> str:
    """將逗號、頓號、分號或換行分隔的多批號，統一轉為 Excel 換行格式。"""
    import re
    parts = [p.strip() for p in re.split(r"[,，、;\n\r]+", raw or "") if p.strip()]
    # 去重並維持輸入順序
    seen: list[str] = []
    for p in parts:
        if p not in seen:
            seen.append(p)
    return "\n".join(seen)


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def find_available_port(start_port: int) -> int:
    port = start_port
    while port < start_port + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    return start_port


def load_logs() -> list[dict]:
    if not LOGS_FILE.exists():
        return []
    try:
        return json.loads(LOGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_logs(logs: list[dict]) -> None:
    LOGS_FILE.write_text(
        json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_all_settings() -> dict:
    if not SETTINGS_FILE.exists():
        return {}
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_all_settings(data: dict) -> None:
    SETTINGS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def hash_password(pw: str) -> str:
    return hashlib.sha256(f"storage_pwa::{pw}".encode("utf-8")).hexdigest()


def load_users() -> list[dict]:
    if not USERS_FILE.exists():
        default_users = [
            {
                "username": "admin",
                "display_name": "管理員",
                "password_hash": hash_password("1234"),
                "role": "admin",
                "enabled": True,
            },
            {
                "username": "staff1",
                "display_name": "現場人員1",
                "password_hash": hash_password("1234"),
                "role": "staff",
                "enabled": True,
            },
        ]
        save_users(default_users)
        return default_users
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_users(users: list[dict]) -> None:
    USERS_FILE.write_text(
        json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class LoginPayload(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserUpsertPayload(BaseModel):
    username: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    password: str = ""
    role: Literal["admin", "staff"] = "staff"
    enabled: bool = True


class WarehouseUpsertPayload(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    icon: str = "🏬"
    filename: str = ""
    master_sheet: str = ""
    form_sheet: str = ""
    form_layout: Literal["name_first", "code_first"] = "name_first"


class WarehouseItemSetting(BaseModel):
    item_name: str = Field(..., min_length=1)
    item_no: str = ""
    package: str = ""
    enabled: bool = True


class WarehouseSettingsPayload(BaseModel):
    items: list[WarehouseItemSetting]
    packages: list[str]


def build_daily_stats(
    target_date: str,
    wh_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    s_date = (start_date or target_date or datetime.now().strftime("%Y-%m-%d")).strip()
    e_date = (end_date or s_date).strip()
    if s_date > e_date:
        s_date, e_date = e_date, s_date

    logs = load_logs()
    filtered = [
        r
        for r in logs
        if s_date <= str(r.get("date", "")) <= e_date
        and (not wh_id or wh_id.upper() == "ALL" or r.get("wh_id") == wh_id)
    ]

    in_pallets = 0
    out_pallets = 0
    set_pallets = 0
    in_qty = 0.0
    out_qty = 0.0

    batch_map: dict[tuple[str, str, str], dict] = defaultdict(
        lambda: {
            "lot_no": "",
            "item_name": "",
            "package": "(未指定)",
            "in_pallets": 0,
            "in_qty": 0.0,
            "in_count": 0,
            "out_pallets": 0,
            "out_qty": 0.0,
            "out_count": 0,
            "set_pallets": 0,
            "set_qty": 0.0,
            "record_count": 0,
        }
    )
    pkg_map: dict[str, dict] = defaultdict(
        lambda: {
            "package": "(未指定)",
            "in_qty": 0.0,
            "out_qty": 0.0,
            "net_qty": 0.0,
            "in_pallets": 0,
            "out_pallets": 0,
        }
    )
    product_map: dict[tuple[str, str], dict] = defaultdict(
        lambda: {
            "item_name": "",
            "package": "(未指定)",
            "in_pallets": 0,
            "in_qty": 0.0,
            "in_count": 0,
            "out_pallets": 0,
            "out_qty": 0.0,
            "out_count": 0,
            "net_qty": 0.0,
            "set_pallets": 0,
            "record_count": 0,
        }
    )
    op_map: dict[str, dict] = defaultdict(
        lambda: {
            "operator": "未填人員",
            "in_pallets": 0,
            "in_qty": 0.0,
            "in_count": 0,
            "out_pallets": 0,
            "out_qty": 0.0,
            "out_count": 0,
            "set_pallets": 0,
            "set_count": 0,
            "record_count": 0,
        }
    )
    month_map: dict[str, dict] = defaultdict(
        lambda: {
            "month": "",
            "in_pallets": 0,
            "in_qty": 0.0,
            "in_count": 0,
            "out_pallets": 0,
            "out_qty": 0.0,
            "out_count": 0,
            "net_qty": 0.0,
            "set_pallets": 0,
            "record_count": 0,
        }
    )

    for r in filtered:
        act = r.get("action", "in")
        pallets = int(r.get("pallets", 1) or 0)
        q = float(r.get("op_qty", 0) or 0)
        lot = r.get("lot_no") or "(無批號)"
        item = r.get("item_name") or "(未填品名)"
        pkg = (r.get("package") or "").strip() or "(未指定)"
        operator = (r.get("operator") or "").strip() or "未填人員"
        month = str(r.get("date") or "")[:7] or "未知月份"

        b = batch_map[(lot, item, pkg)]
        b["lot_no"] = lot
        b["item_name"] = item
        b["package"] = pkg
        b["record_count"] += 1

        pm = pkg_map[pkg]
        pm["package"] = pkg

        p = product_map[(item, pkg)]
        p["item_name"] = item
        p["package"] = pkg
        p["record_count"] += 1

        op = op_map[operator]
        op["operator"] = operator
        op["record_count"] += 1

        mo = month_map[month]
        mo["month"] = month
        mo["record_count"] += 1

        if act == "in":
            in_pallets += pallets
            in_qty += q
            b["in_pallets"] += pallets
            b["in_qty"] += q
            b["in_count"] += 1
            pm["in_pallets"] += pallets
            pm["in_qty"] += q
            pm["net_qty"] += q
            p["in_pallets"] += pallets
            p["in_qty"] += q
            p["in_count"] += 1
            p["net_qty"] += q
            op["in_pallets"] += pallets
            op["in_qty"] += q
            op["in_count"] += 1
            mo["in_pallets"] += pallets
            mo["in_qty"] += q
            mo["in_count"] += 1
            mo["net_qty"] += q
        elif act == "out":
            out_pallets += pallets
            out_qty += q
            b["out_pallets"] += pallets
            b["out_qty"] += q
            b["out_count"] += 1
            pm["out_pallets"] += pallets
            pm["out_qty"] += q
            pm["net_qty"] -= q
            p["out_pallets"] += pallets
            p["out_qty"] += q
            p["out_count"] += 1
            p["net_qty"] -= q
            op["out_pallets"] += pallets
            op["out_qty"] += q
            op["out_count"] += 1
            mo["out_pallets"] += pallets
            mo["out_qty"] += q
            mo["out_count"] += 1
            mo["net_qty"] -= q
        else:
            set_pallets += pallets
            b["set_pallets"] += pallets
            b["set_qty"] += q
            p["set_pallets"] += pallets
            op["set_pallets"] += pallets
            op["set_count"] += 1
            mo["set_pallets"] += pallets

    def fmt_num(v: float) -> int | float:
        return int(v) if float(v).is_integer() else round(v, 3)

    by_batch = sorted(batch_map.values(), key=lambda x: (x["lot_no"], x["item_name"]))
    for row in by_batch:
        row["in_qty"] = fmt_num(row["in_qty"])
        row["out_qty"] = fmt_num(row["out_qty"])
        row["set_qty"] = fmt_num(row["set_qty"])

    by_package = sorted(pkg_map.values(), key=lambda x: -(x["in_qty"] + x["out_qty"]))
    for row in by_package:
        row["in_qty"] = fmt_num(row["in_qty"])
        row["out_qty"] = fmt_num(row["out_qty"])
        row["net_qty"] = fmt_num(row["net_qty"])

    by_product = sorted(product_map.values(), key=lambda x: -(x["in_qty"] + x["out_qty"]))
    for row in by_product:
        row["in_qty"] = fmt_num(row["in_qty"])
        row["out_qty"] = fmt_num(row["out_qty"])
        row["net_qty"] = fmt_num(row["net_qty"])

    by_operator = sorted(op_map.values(), key=lambda x: -x["record_count"])
    for row in by_operator:
        row["in_qty"] = fmt_num(row["in_qty"])
        row["out_qty"] = fmt_num(row["out_qty"])

    by_month = sorted(month_map.values(), key=lambda x: x["month"])
    for row in by_month:
        row["in_qty"] = fmt_num(row["in_qty"])
        row["out_qty"] = fmt_num(row["out_qty"])
        row["net_qty"] = fmt_num(row["net_qty"])

    sorted_records = sorted(
        filtered,
        key=lambda r: (str(r.get("date", "")), str(r.get("time", ""))),
        reverse=True,
    )

    return {
        "date": s_date,
        "start_date": s_date,
        "end_date": e_date,
        "wh_id": wh_id or "all",
        "total_records": len(filtered),
        "total_pallets": in_pallets + out_pallets + set_pallets,
        "in_pallets": in_pallets,
        "out_pallets": out_pallets,
        "set_pallets": set_pallets,
        "in_qty": fmt_num(in_qty),
        "out_qty": fmt_num(out_qty),
        "net_qty": fmt_num(in_qty - out_qty),
        "by_package": by_package,
        "by_batch": by_batch,
        "by_product": by_product,
        "by_operator": by_operator,
        "by_month": by_month,
        "records": sorted_records,
    }


@app.get("/api/network-info")
def api_network_info():
    ip = get_local_ip()
    return {
        "local_url": f"http://localhost:{ACTIVE_PORT}",
        "lan_url": f"http://{ip}:{ACTIVE_PORT}",
        "ip": ip,
        "port": ACTIVE_PORT,
    }


@app.post("/api/login")
def api_login(payload: LoginPayload):
    users = load_users()
    uname = payload.username.strip()
    pw_hash = hash_password(payload.password)
    for u in users:
        if u["username"] == uname:
            if not u.get("enabled", True):
                raise HTTPException(status_code=403, detail="此帳號已被停用")
            if u["password_hash"] != pw_hash:
                raise HTTPException(status_code=401, detail="帳號或密碼錯誤")
            return {
                "ok": True,
                "user": {
                    "username": u["username"],
                    "display_name": u["display_name"],
                    "role": u.get("role", "staff"),
                },
            }
    raise HTTPException(status_code=401, detail="帳號或密碼錯誤")


@app.get("/api/users")
def api_list_users():
    return {
        "users": [
            {
                "username": u["username"],
                "display_name": u["display_name"],
                "role": u.get("role", "staff"),
                "enabled": u.get("enabled", True),
            }
            for u in load_users()
        ]
    }


@app.post("/api/users")
def api_upsert_user(payload: UserUpsertPayload):
    users = load_users()
    uname = payload.username.strip()
    existing = next((u for u in users if u["username"] == uname), None)
    if existing:
        existing["display_name"] = payload.display_name.strip()
        existing["role"] = payload.role
        existing["enabled"] = payload.enabled
        if payload.password.strip():
            existing["password_hash"] = hash_password(payload.password.strip())
    else:
        if not payload.password.strip():
            raise HTTPException(status_code=400, detail="新增帳號必須設定密碼")
        users.append(
            {
                "username": uname,
                "display_name": payload.display_name.strip(),
                "password_hash": hash_password(payload.password.strip()),
                "role": payload.role,
                "enabled": payload.enabled,
            }
        )
    save_users(users)
    return {"ok": True, "message": f"已儲存帳號 {uname}"}


@app.post("/api/users/import")
def api_import_users(payload: dict):
    raw_users = payload.get("users") or []
    if not raw_users:
        raise HTTPException(status_code=400, detail="匯入帳號清單為空")
    users = load_users()
    by_name = {u["username"]: u for u in users}
    count = 0
    for item in raw_users:
        uname = str(item.get("username", "")).strip()
        if not uname:
            continue
        dn = str(item.get("display_name") or uname).strip() or uname
        role = "admin" if item.get("role") == "admin" else "staff"
        enabled = item.get("enabled", True) is not False
        pw = str(item.get("password") or "").strip()
        if uname in by_name:
            u = by_name[uname]
            u["display_name"] = dn
            u["role"] = role
            u["enabled"] = enabled
            if pw:
                u["password_hash"] = hash_password(pw)
        else:
            new_u = {
                "username": uname,
                "display_name": dn,
                "password_hash": hash_password(pw or "1234"),
                "role": role,
                "enabled": enabled,
            }
            users.append(new_u)
            by_name[uname] = new_u
        count += 1
    save_users(users)
    return {"ok": True, "count": count, "message": f"已匯入更新 {count} 筆人員帳號"}


@app.delete("/api/users/{username}")
def api_delete_user(username: str):
    if username == "admin":
        raise HTTPException(status_code=400, detail="不可刪除預設管理員帳號 admin")
    users = load_users()
    new_users = [u for u in users if u["username"] != username]
    if len(new_users) == len(users):
        raise HTTPException(status_code=404, detail="找不到該帳號")
    save_users(new_users)
    return {"ok": True}


@app.get("/api/warehouses")
def api_warehouses():
    return {"warehouses": engine.list_warehouses()}


@app.get("/api/warehouses/files")
def api_warehouse_files():
    """掃描專案根目錄下的 .xlsm / .xlsx 檔案與工作表名稱，供新增倉庫時直接選取。"""
    import openpyxl
    files = []
    for p in sorted(PROJECT_ROOT.glob("*.xls*")):
        if p.name.startswith("~$"):
            continue
        try:
            wb = openpyxl.load_workbook(p, read_only=True)
            sheets = list(wb.sheetnames)
            wb.close()
        except Exception:
            sheets = []
        files.append({"filename": p.name, "sheets": sheets})
    return {"files": files}


@app.post("/api/warehouses")
def api_upsert_warehouse(payload: WarehouseUpsertPayload):
    whs = engine.get_warehouses()
    wid = payload.id.strip()
    whs[wid] = {
        "id": wid,
        "name": payload.name.strip(),
        "icon": payload.icon.strip() or "🏬",
        "filename": payload.filename.strip(),
        "master_sheet": payload.master_sheet.strip(),
        "form_sheet": payload.form_sheet.strip(),
        "form_layout": payload.form_layout,
    }
    engine.save_warehouses(whs)
    return {"ok": True, "message": f"已儲存倉庫 {payload.name}", "warehouses": engine.list_warehouses()}


@app.delete("/api/warehouses/{wh_id}")
def api_delete_warehouse(wh_id: str):
    if wh_id in ("lunwei", "hongsheng"):
        raise HTTPException(status_code=400, detail="不可刪除預設倉庫")
    whs = engine.get_warehouses()
    if wh_id not in whs:
        raise HTTPException(status_code=404, detail="找不到指定倉庫")
    del whs[wh_id]
    engine.save_warehouses(whs)
    return {"ok": True, "warehouses": engine.list_warehouses()}


@app.get("/api/warehouse/{wh_id}/data")
def api_warehouse_data(wh_id: str):
    whs = engine.get_warehouses()
    if wh_id not in whs:
        raise HTTPException(status_code=404, detail="找不到指定倉庫")
    try:
        data = engine.read_warehouse_data(wh_id)
        all_settings = load_all_settings()
        wh_cfg = all_settings.get(wh_id)
        if wh_cfg:
            enabled_items = [
                {
                    "item_name": it["item_name"],
                    "item_no": it.get("item_no", ""),
                    "package": it.get("package", ""),
                }
                for it in wh_cfg.get("items", [])
                if it.get("enabled", True)
            ]
            data["catalog"] = enabled_items
            if wh_cfg.get("packages"):
                data["packages"] = wh_cfg["packages"]
        return data
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/warehouse/{wh_id}/settings")
def api_get_warehouse_settings(wh_id: str, reset: bool = False):
    whs = engine.get_warehouses()
    if wh_id not in whs:
        raise HTTPException(status_code=404, detail="找不到指定倉庫")
    all_settings = load_all_settings()
    if not reset and wh_id in all_settings:
        return {"wh_id": wh_id, **all_settings[wh_id]}
    data = engine.read_warehouse_data(wh_id)
    seeded = {
        "items": [
            {
                "item_name": c["item_name"],
                "item_no": c.get("item_no", ""),
                "package": c.get("package", ""),
                "enabled": True,
            }
            for c in data["catalog"]
        ],
        "packages": data["packages"],
    }
    all_settings[wh_id] = seeded
    save_all_settings(all_settings)
    return {"wh_id": wh_id, **seeded}


@app.post("/api/warehouse/{wh_id}/settings")
def api_save_warehouse_settings(wh_id: str, payload: WarehouseSettingsPayload):
    whs = engine.get_warehouses()
    if wh_id not in whs:
        raise HTTPException(status_code=404, detail="找不到指定倉庫")
    all_settings = load_all_settings()
    all_settings[wh_id] = {
        "items": [it.model_dump() for it in payload.items],
        "packages": [p.strip() for p in payload.packages if p.strip()],
    }
    save_all_settings(all_settings)
    return {"ok": True, "message": f"已儲存 {whs[wh_id]['name']} 的品名與包材設定"}


@app.get("/api/warehouse/{wh_id}/download")
def api_warehouse_download(wh_id: str):
    whs = engine.get_warehouses()
    if wh_id not in whs:
        raise HTTPException(status_code=404, detail="找不到指定倉庫")
    fpath = engine.get_file_path(wh_id)
    if not fpath.exists():
        raise HTTPException(status_code=404, detail=f"找不到檔案: {fpath.name}")
    export_dir = DATA_DIR / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    out_path = export_dir / f"{fpath.stem}_儲位專用.xlsm"
    engine.export_storage_only_xlsm(wh_id, out_path)
    return FileResponse(
        path=out_path,
        filename=f"{fpath.stem}_儲位專用.xlsm",
        media_type="application/vnd.ms-excel.sheet.macroEnabled.12",
    )


@app.post("/api/record")
def api_record(payload: RecordPayload):
    # 離線補傳冪等性檢查，避免重複計數
    logs = load_logs()
    if payload.client_tx_id:
        for existing in logs:
            if existing.get("client_tx_id") == payload.client_tx_id:
                today = datetime.now().strftime("%Y-%m-%d")
                return {
                    "ok": True,
                    "duplicate": True,
                    "message": "此筆離線紀錄先前已同步完成",
                    "log": existing,
                    "daily_stats": build_daily_stats(today),
                }

    try:
        wh_data = engine.read_warehouse_data(payload.wh_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    whs = engine.get_warehouses()
    if payload.wh_id not in whs:
        raise HTTPException(status_code=404, detail=f"未知倉庫: {payload.wh_id}")
    wh_cfg = whs[payload.wh_id]
    target_loc = next(
        (loc for loc in wh_data["locations"] if loc["location"] == payload.location),
        None,
    )
    if not target_loc:
        raise HTTPException(
            status_code=404, detail=f"在 {wh_cfg['name']} 找不到儲位: {payload.location}"
        )

    catalog_map = {c["item_name"]: c["item_no"] for c in wh_data["catalog"]}

    before_qty = float(target_loc["qty"] or 0)
    op_qty = float(payload.qty)

    # 決定寫入後的新欄位
    input_lot_norm = normalize_lot_nos(payload.lot_no)
    new_item_name = payload.item_name.strip() or target_loc["item_name"]
    new_lot_no = input_lot_norm or target_loc["lot_no"]
    new_package = payload.package.strip() or target_loc["package"]
    new_item_no = payload.item_no.strip() or catalog_map.get(new_item_name, target_loc["item_no"])
    new_note = payload.note.strip() if payload.note.strip() else target_loc["note"]

    if payload.action == "in":
        if payload.in_mode == "replace":
            # 忘記出庫時，直接以新入庫資料覆蓋舊儲位
            after_qty = op_qty
            new_item_name = payload.item_name.strip()
            new_lot_no = input_lot_norm
            new_package = payload.package.strip()
            new_item_no = payload.item_no.strip() or catalog_map.get(new_item_name, "")
            new_note = payload.note.strip()
        elif payload.in_mode == "merge" and target_loc["occupied"]:
            # 併板：將新舊批號以換行合併，數量累加
            after_qty = before_qty + op_qty
            new_lot_no = normalize_lot_nos(f"{target_loc['lot_no']}\n{input_lot_norm}")
            if target_loc["note"] and payload.note.strip() and payload.note.strip() != target_loc["note"]:
                new_note = f"{target_loc['note']} {payload.note.strip()}"
        elif not target_loc["occupied"]:
            after_qty = op_qty
        else:
            after_qty = before_qty + op_qty
            if input_lot_norm and target_loc["lot_no"] and input_lot_norm != target_loc["lot_no"]:
                new_lot_no = normalize_lot_nos(f"{target_loc['lot_no']}\n{input_lot_norm}")
    elif payload.action == "out":
        after_qty = max(0.0, before_qty - op_qty)
    else:  # set (盤點覆寫)
        after_qty = op_qty
        new_item_name = payload.item_name.strip()
        new_lot_no = input_lot_norm
        new_package = payload.package.strip()
        new_item_no = payload.item_no.strip() or catalog_map.get(new_item_name, "")
        new_note = payload.note.strip()

    after_qty_fmt: int | float | str = (
        int(after_qty) if float(after_qty).is_integer() else round(after_qty, 3)
    )

    if after_qty <= 0 and payload.clear_on_zero:
        write_item_no = ""
        write_item_name = ""
        write_lot_no = ""
        write_package = ""
        write_qty: int | float | str = ""
        write_note = ""
    else:
        write_item_no = new_item_no
        write_item_name = new_item_name
        write_lot_no = new_lot_no
        write_package = new_package
        write_qty = after_qty_fmt
        write_note = new_note

    try:
        engine.update_location_row(
            wh_id=payload.wh_id,
            row_idx=target_loc["row"],
            item_no=write_item_no,
            item_name=write_item_name,
            lot_no=write_lot_no,
            package=write_package,
            qty=write_qty,
            note=write_note,
        )
    except ExcelLockedError as e:
        raise HTTPException(status_code=423, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"寫入 Excel 失敗: {e}")

    now = datetime.now()
    log_entry = {
        "id": uuid.uuid4().hex[:12],
        "client_tx_id": payload.client_tx_id,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "wh_id": payload.wh_id,
        "wh_name": wh_cfg["name"],
        "zone": target_loc["zone"],
        "location": payload.location,
        "action": payload.action,
        "item_no": new_item_no,
        "item_name": new_item_name,
        "lot_no": new_lot_no,
        "package": new_package,
        "before_qty": int(before_qty) if before_qty.is_integer() else before_qty,
        "op_qty": int(op_qty) if op_qty.is_integer() else op_qty,
        "after_qty": after_qty_fmt,
        "pallets": payload.pallets,
        "note": new_note,
        "operator": payload.operator,
    }
    logs.append(log_entry)
    save_logs(logs)

    return {
        "ok": True,
        "message": f"已成功回寫 {wh_cfg['filename']} 儲位 {payload.location}",
        "log": log_entry,
        "updated_location": {
            "row": target_loc["row"],
            "zone": target_loc["zone"],
            "location": payload.location,
            "item_no": write_item_no,
            "item_name": write_item_name,
            "lot_no": write_lot_no,
            "package": write_package,
            "qty": 0 if write_qty == "" else write_qty,
            "note": write_note,
            "occupied": bool(write_item_name or write_lot_no or (isinstance(write_qty, (int, float)) and write_qty > 0)),
        },
        "daily_stats": build_daily_stats(log_entry["date"]),
    }


@app.get("/api/daily-stats")
def api_daily_stats(
    date: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    wh_id: Optional[str] = Query(default=None),
):
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    return build_daily_stats(
        target_date,
        None if wh_id in (None, "", "all", "ALL") else wh_id,
        start_date=start_date,
        end_date=end_date,
    )


@app.delete("/api/record/{log_id}")
def api_delete_log(log_id: str):
    logs = load_logs()
    new_logs = [r for r in logs if r.get("id") != log_id]
    if len(new_logs) == len(logs):
        raise HTTPException(status_code=404, detail="找不到該筆日誌")
    save_logs(new_logs)
    return {"ok": True}


@app.get("/api/daily-export")
def api_daily_export(
    date: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    wh_id: Optional[str] = Query(default=None),
    mode: str = Query(default="detail"),
    label: Optional[str] = Query(default=None),
):
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    stats = build_daily_stats(
        target_date,
        None if wh_id in (None, "", "all", "ALL") else wh_id,
        start_date=start_date,
        end_date=end_date,
    )
    period_tag = (label or "").strip() or (
        stats["start_date"]
        if stats["start_date"] == stats["end_date"]
        else f"{stats['start_date']}_{stats['end_date']}"
    )

    buf = io.StringIO()
    writer = csv.writer(buf)
    if mode == "summary":
        writer.writerow([f"倉儲儲位統計彙總報表 - {stats['start_date']} ~ {stats['end_date']}"])
        writer.writerow(["總筆數", stats["total_records"], "總板數", stats["total_pallets"], "入庫板數", stats["in_pallets"], "入庫總數量", stats["in_qty"], "出庫板數", stats["out_pallets"], "出庫總數量", stats["out_qty"], "淨異動量", stats["net_qty"]])
        writer.writerow([])
        writer.writerow(["=== 按月趨勢彙總 ==="])
        writer.writerow(["月份", "入庫筆數", "入庫板數", "入庫數量", "出庫筆數", "出庫板數", "出庫數量", "淨異動量", "盤點板數", "總筆數"])
        for m in stats["by_month"]:
            writer.writerow([m["month"], m["in_count"], m["in_pallets"], m["in_qty"], m["out_count"], m["out_pallets"], m["out_qty"], m["net_qty"], m["set_pallets"], m["record_count"]])
        writer.writerow([])
        writer.writerow(["=== 依品名／包材彙總排行 ==="])
        writer.writerow(["品名", "包材", "入庫筆數", "入庫板數", "入庫數量", "出庫筆數", "出庫板數", "出庫數量", "淨異動量", "盤點板數", "總筆數"])
        for p in stats["by_product"]:
            writer.writerow([p["item_name"], p["package"], p["in_count"], p["in_pallets"], p["in_qty"], p["out_count"], p["out_pallets"], p["out_qty"], p["net_qty"], p["set_pallets"], p["record_count"]])
        writer.writerow([])
        writer.writerow(["=== 依操作人員作業量彙總 ==="])
        writer.writerow(["操作人員", "總筆數", "入庫筆數", "入庫板數", "入庫數量", "出庫筆數", "出庫板數", "出庫數量", "盤點筆數", "盤點板數"])
        for o in stats["by_operator"]:
            writer.writerow([o["operator"], o["record_count"], o["in_count"], o["in_pallets"], o["in_qty"], o["out_count"], o["out_pallets"], o["out_qty"], o["set_count"], o["set_pallets"]])
        writer.writerow([])
        writer.writerow(["=== 依批號核對彙總 ==="])
        writer.writerow(["批號", "品名", "包材", "入庫板數", "入庫數量", "出庫板數", "出庫數量", "盤點板數", "總筆數"])
        for b in stats["by_batch"]:
            writer.writerow([b["lot_no"], b["item_name"], b["package"], b["in_pallets"], b["in_qty"], b["out_pallets"], b["out_qty"], b["set_pallets"], b["record_count"]])
        filename = f"storage_summary_{period_tag}.csv"
    else:
        writer.writerow(["日期", "時間", "倉庫", "區域", "儲位", "動作", "品號", "品名", "批號", "包材", "異動前數量", "異動數量", "異動後數量", "板數", "備註", "操作人員"])
        act_label = {"in": "入庫", "out": "出庫", "set": "盤點覆寫"}
        for r in stats["records"]:
            writer.writerow([
                r.get("date", ""), r.get("time", ""), r.get("wh_name", ""), r.get("zone", ""), r.get("location", ""),
                act_label.get(r.get("action"), r.get("action")),
                r.get("item_no", ""), r.get("item_name", ""), r.get("lot_no", ""), r.get("package", ""),
                r.get("before_qty", 0), r.get("op_qty", 0), r.get("after_qty", 0), r.get("pallets", 1),
                r.get("note", ""), r.get("operator", ""),
            ])
        filename = f"storage_detail_{period_tag}.csv"

    csv_bytes = ("\ufeff" + buf.getvalue()).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/")
def serve_index():
    return FileResponse(APP_DIR / "index.html")


@app.get("/manifest.json")
def serve_manifest():
    return FileResponse(APP_DIR / "manifest.json", media_type="application/manifest+json")


@app.get("/sw.js")
def serve_sw():
    return FileResponse(APP_DIR / "sw.js", media_type="application/javascript")


@app.get("/pwa_offline_sync.js")
def serve_offline_sync():
    return FileResponse(APP_DIR / "pwa_offline_sync.js", media_type="application/javascript")


app.mount("/icons", StaticFiles(directory=str(APP_DIR / "icons")), name="icons")


if __name__ == "__main__":
    ACTIVE_PORT = find_available_port(DEFAULT_PORT)
    if ACTIVE_PORT != DEFAULT_PORT:
        print(f"[注意] 預設 Port {DEFAULT_PORT} 已被佔用，已自動切換至可用 Port: {ACTIVE_PORT}")
    lan_ip = get_local_ip()
    print("=" * 56)
    print("  倉儲儲位 PWA 系統 已啟動！")
    print(f"  本機電腦開啟: http://localhost:{ACTIVE_PORT}")
    print(f"  手機區網連線: http://{lan_ip}:{ACTIVE_PORT}")
    print("=" * 56)
    uvicorn.run(app, host="0.0.0.0", port=ACTIVE_PORT)
