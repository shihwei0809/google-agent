#!/usr/bin/env python3
"""
sync_sheet_to_firebase.py
直接從 Google Sheets（以 Sheets API）讀取設定與歷史記錄，
再透過 Firestore REST API（用 service account）寫入 Firebase。

用法：
    python sync_sheet_to_firebase.py

設定：
    在下方 CONFIG 區填入你的 SPREADSHEET_ID。
    firebase_key.json 必須在同一目錄。
"""

import json
import os
import sys
import datetime
import urllib.request
import urllib.parse
import ssl

# 強制將標準輸出與錯誤輸出設定為 UTF-8 編碼，防止 Windows 終端機顯示亂碼
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# ──────────────────────────────────────────────
# ★ 填入你的 Google Spreadsheet ID（網址 /d/ 後面那串）
SPREADSHEET_ID = "1cE__uNZfCd3Zm0_RZT0YVmRhqyTXeT-nWbhw8N3s37s"
# ──────────────────────────────────────────────

FIREBASE_KEY_FILE = os.path.join(os.path.dirname(__file__), "firebase_key.json")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/datastore",
]

ssl_ctx = ssl._create_unverified_context()


# ── 取得 OAuth2 access token ──────────────────
def get_access_token():
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        creds = service_account.Credentials.from_service_account_file(
            FIREBASE_KEY_FILE, scopes=SCOPES
        )
        req = Request()
        creds.refresh(req)
        return creds.token
    except ImportError:
        # fallback: 手動 JWT（不需要 google-auth 套件）
        return _get_token_manual()


def _get_token_manual():
    import base64
    import hmac
    import hashlib
    import time

    with open(FIREBASE_KEY_FILE) as f:
        key_data = json.load(f)

    now = int(time.time())
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "RS256", "typ": "JWT"}).encode()
    ).rstrip(b"=")
    payload = base64.urlsafe_b64encode(
        json.dumps(
            {
                "iss": key_data["client_email"],
                "sub": key_data["client_email"],
                "aud": "https://oauth2.googleapis.com/token",
                "iat": now,
                "exp": now + 3600,
                "scope": " ".join(SCOPES),
            }
        ).encode()
    ).rstrip(b"=")

    sign_input = header + b"." + payload

    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend

        private_key = serialization.load_pem_private_key(
            key_data["private_key"].encode(), password=None, backend=default_backend()
        )
        signature = private_key.sign(sign_input, padding.PKCS1v15(), hashes.SHA256())
        sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=")
    except ImportError:
        print("❌ 需要安裝 google-auth 或 cryptography: pip install google-auth cryptography")
        sys.exit(1)

    jwt = sign_input + b"." + sig_b64

    data = urllib.parse.urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt.decode(),
        }
    ).encode()

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST",
    )
    with urllib.request.urlopen(req, context=ssl_ctx) as resp:
        result = json.loads(resp.read())
    return result["access_token"]


# ── 讀 Google Sheets ───────────────────────────
def read_sheet(token, sheet_name, range_notation="A:Z"):
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}"
        f"/values/{urllib.parse.quote(sheet_name + '!' + range_notation)}"
    )
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
            data = json.loads(resp.read())
        return data.get("values", [])
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"⚠️  讀取 Sheet [{sheet_name}] 失敗: {e.code} {body[:200]}")
        return []


# ── Firestore helper ───────────────────────────
def firestore_put(token, collection, doc_id, fields_dict, update_only_sent_fields=False):
    """用 PATCH 寫入文件。若 update_only_sent_fields 為 True，只更新傳入的欄位，不影響其他欄位"""
    project_id = _get_project_id()
    url = (
        f"https://firestore.googleapis.com/v1/projects/{project_id}"
        f"/databases/(default)/documents/{collection}/{doc_id}"
    )
    if update_only_sent_fields:
        update_mask = "&".join(f"updateMask.fieldPaths={k}" for k in fields_dict)
        url += "?" + update_mask

    payload = json.dumps({"fields": fields_dict}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
        return json.loads(resp.read())


def firestore_add(token, collection, fields_dict):
    """POST 新增文件（自動產生 ID）"""
    project_id = _get_project_id()
    url = (
        f"https://firestore.googleapis.com/v1/projects/{project_id}"
        f"/databases/(default)/documents/{collection}"
    )
    payload = json.dumps({"fields": fields_dict}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
        return json.loads(resp.read())


def firestore_list(token, collection):
    """列出集合裡所有文件"""
    project_id = _get_project_id()
    url = (
        f"https://firestore.googleapis.com/v1/projects/{project_id}"
        f"/databases/(default)/documents/{collection}?pageSize=300"
    )
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
            return json.loads(resp.read()).get("documents", [])
    except Exception:
        return []


def _get_project_id():
    with open(FIREBASE_KEY_FILE) as f:
        return json.load(f)["project_id"]


def to_fs(value):
    """把 Python 值轉成 Firestore 欄位格式"""
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, int):
        return {"integerValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if value is None:
        return {"nullValue": None}
    return {"stringValue": str(value)}


# ── 解析設定頁 ─────────────────────────────────
def parse_config_sheet(rows):
    config = {
        "threshold": 28.0,
        "start_hour": 8,
        "end_hour": 24,
        "frequency": 60,
        "password": "admin888",
        "firebaseProjectId": "hongsheng-temp-523",
    }
    for row in rows[1:]:  # 跳過標頭
        if len(row) < 2:
            continue
        key = str(row[0]).strip()
        val = str(row[1]).strip()
        kl = key.lower()
        if "閾值" in key or "閥值" in key or "threshold" in kl or "溫度" in key:
            try:
                config["threshold"] = float(val)
            except ValueError:
                pass
        elif "開始" in key or "start" in kl:
            try:
                config["start_hour"] = int(val)
            except ValueError:
                pass
        elif "結束" in key or "end" in kl:
            try:
                config["end_hour"] = int(val)
            except ValueError:
                pass
        elif "頻率" in key or "frequency" in kl or "間隔" in key:
            try:
                config["frequency"] = int(val)
            except ValueError:
                pass
        elif "密碼" in key or "password" in kl:
            config["password"] = val
        elif "firebase" in kl or "專案" in key or "project" in kl:
            config["firebaseProjectId"] = val
    return config


# ── 解析歷史紀錄頁 ──────────────────────────────
def parse_history_sheet(rows):
    logs = []
    for row in rows[1:]:  # 跳過標頭
        if len(row) < 6:
            continue
        try:
            time_str = str(row[0])
            # 把時間字串轉成 timestamp（毫秒）
            try:
                dt = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                ts_ms = int(dt.timestamp() * 1000)
            except Exception:
                ts_ms = 0
            logs.append(
                {
                    "time": time_str,
                    "threshold": float(row[1]) if row[1] else 28.0,
                    "temp": float(row[2]) if row[2] else -99.0,
                    "obs_time": str(row[3]),      # snake_case ✅
                    "alert_state": str(row[4]),   # snake_case ✅
                    "status_text": str(row[5]),   # snake_case ✅
                    "timestamp": ts_ms,            # 排序用 ✅
                }
            )
        except (ValueError, IndexError):
            continue
    return logs


# ── 同步設定到 Firebase ─────────────────────────
def sync_config(token, config):
    fields = {
        "threshold": to_fs(config["threshold"]),
        "start_hour": to_fs(config["start_hour"]),
        "end_hour": to_fs(config["end_hour"]),
        "frequency": to_fs(config["frequency"]),
        "password": to_fs(config["password"]),
    }
    result = firestore_put(token, "realtime_data", "status", fields, update_only_sent_fields=True)
    print(f"✅ 設定已同步到 Firebase (threshold={config['threshold']}, frequency={config['frequency']})")
    return result


# ── 同步歷史紀錄到 Firebase ─────────────────────
def sync_history(token, logs, force=False):
    if not logs:
        print("ℹ️  Sheet 歷史紀錄為空，跳過")
        return

    # 先取得 Firebase 已有的歷史筆數（用 time 欄位比對）
    existing_docs = firestore_list(token, "history_logs")
    existing_times = set()
    for doc in existing_docs:
        fields = doc.get("fields", {})
        t = fields.get("time", {}).get("stringValue", "")
        if t:
            existing_times.add(t)

    new_count = 0
    skip_count = 0
    update_count = 0
    for log in logs:
        if not force and log["time"] in existing_times:
            skip_count += 1
            continue
        fields = {
            "time":        to_fs(log["time"]),
            "threshold":   to_fs(log["threshold"]),
            "temp":        to_fs(log["temp"]),
            "obs_time":    to_fs(log["obs_time"]),     # snake_case ✅
            "alert_state": to_fs(log["alert_state"]),  # snake_case ✅
            "status_text": to_fs(log["status_text"]),  # snake_case ✅
            "timestamp":   to_fs(log["timestamp"]),    # 排序用 ✅
        }
        try:
            if force and log["time"] in existing_times:
                # 找到舊文件 doc name 並 PATCH 修正欄位
                for doc in existing_docs:
                    t = doc.get("fields", {}).get("time", {}).get("stringValue", "")
                    if t == log["time"]:
                        doc_name = doc["name"].split("/")[-1]
                        firestore_put(token, "history_logs", doc_name, fields)
                        update_count += 1
                        break
            else:
                firestore_add(token, "history_logs", fields)
                new_count += 1
            print(f"  + {log['time']} | {log['temp']}C | {log['alert_state']}")
        except Exception as e:
            print(f"  ERROR [{log['time']}]: {e}")

    print(f"OK: 新增 {new_count} 筆, 修正 {update_count} 筆, 跳過 {skip_count} 筆")


# ── 主程式 ──────────────────────────────────────
def main():
    if SPREADSHEET_ID == "YOUR_SPREADSHEET_ID_HERE":
        print("❌ 請先在腳本裡填入 SPREADSHEET_ID！")
        print("   在 Google Sheets 網址列找到 /d/XXXXXXXX/edit 中間那段")
        sys.exit(1)

    print("🔑 取得 Google API 憑證...")
    token = get_access_token()
    print("✅ 憑證取得成功\n")

    # 讀設定
    print("📋 讀取「系統設定」分頁...")
    config_rows = read_sheet(token, "系統設定", "A:C")
    if config_rows:
        config = parse_config_sheet(config_rows)
        print(f"   閾值={config['threshold']}°C, 頻率={config['frequency']}分, "
              f"時段={config['start_hour']}-{config['end_hour']}")
        sync_config(token, config)
    else:
        print("⚠️  無法讀取設定頁，跳過")

    print()

    # 讀當月歷史
    now = datetime.datetime.now()
    sheet_name = f"紀錄_{now.strftime('%Y-%m')}"
    print(f"📋 讀取歷史分頁「{sheet_name}」...")
    history_rows = read_sheet(token, sheet_name, "A:F")
    if history_rows:
        logs = parse_history_sheet(history_rows)
        print(f"   共 {len(logs)} 筆紀錄")
        sync_history(token, logs, force=True)  # force=True 修正舊筆資料欄位名稱
    else:
        print(f"⚠️  分頁「{sheet_name}」不存在或無資料")

    # 也嘗試讀上個月（若月初資料少）
    last_month = (now.replace(day=1) - datetime.timedelta(days=1))
    last_sheet = f"紀錄_{last_month.strftime('%Y-%m')}"
    if now.day <= 5:  # 月初5天內補一下上個月
        print(f"\n📋 月初補讀上月「{last_sheet}」...")
        history_rows2 = read_sheet(token, last_sheet, "A:F")
        if history_rows2:
            logs2 = parse_history_sheet(history_rows2)
            print(f"   共 {len(logs2)} 筆")
            sync_history(token, logs2)
        else:
            print(f"ℹ️  無上月分頁")

    print("\n🎉 全部同步完成！")


if __name__ == "__main__":
    main()
