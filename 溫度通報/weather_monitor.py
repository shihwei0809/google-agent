#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CWA Weather Monitor and Notifier (CWA Open Data API 版)
透過 CWA Open Data API 拓取彰化縣線西鄉線西站即時觀測資料，自行計算體感溫度。
當溫度首次超標或首次回落時發送通知，並提供狀態防重複機制。
"""

import os
import sys
import re
import ast
import json
import datetime
import urllib.request
import urllib.error
import smtplib
import csv
import io
import math
import ssl
import time
from email.mime.text import MIMEText
from email.header import Header

# 強制將標準輸出與錯誤輸出設定為 UTF-8 編碼，防止 Windows 終端機顯示亂碼
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 設定工作目錄為腳本所在的目錄，以便讀取相對路徑的設定檔
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
STATE_PATH = os.path.join(SCRIPT_DIR, "last_notified.json")

def load_config():
    """載入設定檔 config.json"""
    if not os.path.exists(CONFIG_PATH):
        print(f"【錯誤】找不到設定檔: {CONFIG_PATH}", file=sys.stderr)
        print("請參考 config.json 範例建立設定檔。", file=sys.stderr)
        sys.exit(1)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"【錯誤】讀取設定檔失敗: {e}", file=sys.stderr)
        sys.exit(1)

def load_state():
    """載入最後發送狀態，用以防重複通知"""
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_state": "COOL"}

def save_state(state_name, last_run_time_str=None):
    """儲存發送狀態與最後執行時間"""
    try:
        data = {"last_state": state_name}
        if last_run_time_str:
            data["last_run_time"] = last_run_time_str
        else:
            tz_taiwan = datetime.timezone(datetime.timedelta(hours=8))
            data["last_run_time"] = datetime.datetime.now(tz_taiwan).strftime('%Y-%m-%d %H:%M:%S')
            
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"【警告】儲存發送狀態失敗: {e}", file=sys.stderr)

import ssl

def fetch_url(url):
    """安全地下載網頁/資料內容"""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=15, context=context) as response:
        return response.read().decode("utf-8")

def calc_apparent_temp(temp, rh, wind):
    """依 CWA 公式計算體感溫度 AT
    AT = T + 0.33*e - 0.70*V - 4.0
    e  = (RH/100) * 6.105 * exp(17.27*T / (237.7+T))
    """
    e = (rh / 100.0) * 6.105 * math.exp((17.27 * temp) / (237.7 + temp))
    at = temp + 0.33 * e - 0.70 * wind - 4.0
    return round(at, 1)

# ── Firebase 直接寫入（不依賴 GAS web_app_url）──────────────────────
_fb_token = None
_fb_token_expire = 0
_fb_project_id = None
_fb_ssl_ctx = ssl._create_unverified_context()

def _get_firebase_token():
    """取得 Firebase service account access token（有快取，每小時重新取一次）"""
    global _fb_token, _fb_token_expire, _fb_project_id
    now = time.time()
    if _fb_token and now < _fb_token_expire - 60:
        return _fb_token, _fb_project_id
    key_path = os.path.join(SCRIPT_DIR, "firebase_key.json")
    if not os.path.exists(key_path):
        return None, None
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request as GRequest
        creds = service_account.Credentials.from_service_account_file(
            key_path,
            scopes=["https://www.googleapis.com/auth/datastore"]
        )
        creds.refresh(GRequest())
        with open(key_path) as f:
            _fb_project_id = json.load(f)["project_id"]
        _fb_token = creds.token
        _fb_token_expire = now + 3600
        return _fb_token, _fb_project_id
    except Exception as e:
        print(f"【Firebase 憑證】取得失敗: {e}", file=sys.stderr)
        return None, None

def send_heartbeat_firebase(current_temp=None, threshold=None, obs_time=None,
                            alert_state=None, status_text=None):
    """直接用 service account 把心跳資料寫入 Firestore realtime_data/status"""
    token, project_id = _get_firebase_token()
    if not token:
        return
    url = (f"https://firestore.googleapis.com/v1/projects/{project_id}"
           f"/databases/(default)/documents/realtime_data/status")
    now_ms = int(time.time() * 1000)

    def _fs(v):
        if isinstance(v, bool):  return {"booleanValue": v}
        if isinstance(v, int):   return {"integerValue": str(v)}
        if isinstance(v, float): return {"doubleValue": v}
        if v is None:            return {"nullValue": None}
        return {"stringValue": str(v)}

    fields = {"last_heartbeat": _fs(now_ms), "heartbeat_source": _fs("local")}
    if current_temp is not None: fields["current_temp"] = _fs(current_temp)
    if threshold is not None:    fields["threshold"]    = _fs(threshold)
    if obs_time is not None:     fields["obs_time"]     = _fs(obs_time)
    if alert_state is not None:  fields["alert_state"]  = _fs(alert_state)
    if status_text is not None:  fields["status_text"]  = _fs(status_text)

    # 只 PATCH 這幾個欄位（不覆蓋其他設定欄位）
    update_mask = "&".join(f"updateMask.fieldPaths={k}" for k in fields)
    patch_url = url + "?" + update_mask

    payload = json.dumps({"fields": fields}).encode("utf-8")
    req = urllib.request.Request(
        patch_url, data=payload, method="PATCH",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=_fb_ssl_ctx):
            pass
        print("【Firebase 心跳】已直接寫入 Firestore")
    except Exception as e:
        print(f"【Firebase 心跳】寫入失敗: {e}", file=sys.stderr)
# ─────────────────────────────────────────────────────────────────────

def add_realtime_log_to_firebase(current_temp, obs_time):
    """將即時 10 分鐘觀測數據寫入 Firestore realtime_logs，並自動清理 24 小時前舊資料"""
    token, project_id = _get_firebase_token()
    if not token:
        return
    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/realtime_logs"
    now_ms = int(time.time() * 1000)
    
    # 1. 寫入 10 分鐘即時記錄
    doc_id = "rt_" + str(now_ms)
    doc_url = f"{url}/{doc_id}"
    
    def _fs(v):
        if isinstance(v, float): return {"doubleValue": v}
        return {"stringValue": str(v)}
        
    fields = {
        "temp": _fs(current_temp),
        "time": _fs(datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')),
        "obs_time": _fs(obs_time),
        "timestamp": {"integerValue": str(now_ms)}
    }
    
    payload = json.dumps({"fields": fields}).encode("utf-8")
    req = urllib.request.Request(
        doc_url, data=payload, method="PATCH",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=_fb_ssl_ctx):
            pass
        print("【Firebase 即時紀錄】已寫入 realtime_logs")
    except Exception as e:
        print(f"【Firebase 即時紀錄】寫入失敗: {e}", file=sys.stderr)
        
    # 2. 自動清理 24 小時前的舊資料
    try:
        cutoff_ms = now_ms - 24 * 60 * 60 * 1000
        query_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents:runQuery"
        query_payload = {
            "structuredQuery": {
                "from": [{"collectionId": "realtime_logs"}],
                "where": {
                    "fieldFilter": {
                        "field": {"fieldPath": "timestamp"},
                        "op": "LESS_THAN",
                        "value": {"integerValue": str(cutoff_ms)}
                    }
                }
            }
        }
        req_query = urllib.request.Request(
            query_url, data=json.dumps(query_payload).encode("utf-8"), method="POST",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_query, timeout=10, context=_fb_ssl_ctx) as resp:
            results = json.loads(resp.read().decode("utf-8"))
            for res in results:
                doc = res.get("document")
                if doc:
                    doc_name = doc.get("name")
                    del_url = f"https://firestore.googleapis.com/v1/{doc_name}"
                    req_del = urllib.request.Request(
                        del_url, method="DELETE",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    with urllib.request.urlopen(req_del, timeout=5, context=_fb_ssl_ctx):
                        pass
        print("【Firebase 即時紀錄】已清理 24 小時前舊資料")
    except Exception as e:
        print(f"【Firebase 即時紀錄】清理舊資料失敗: {e}", file=sys.stderr)

def send_heartbeat(url, state_name=None, sync_type="heartbeat", current_temp=None, threshold=None, obs_time=None, alert_state=None, status_text=None):
    """發送心跳與狀態同步給 Google Apps Script 雲端 Web App"""
    payload = {
        "action": "heartbeat",
        "type": sync_type
    }
    if state_name:
        payload["local_state"] = state_name
    if current_temp is not None:
        payload["current_temp"] = current_temp
    if threshold is not None:
        payload["threshold"] = threshold
    if obs_time is not None:
        payload["obs_time"] = obs_time
    if alert_state is not None:
        payload["alert_state"] = alert_state
    if status_text is not None:
        payload["status_text"] = status_text
        
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0"
            },
            method="POST"
        )
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("status") == "success":
                return res_data.get("cloud_state")
    except Exception as e:
        print(f"【同步警告】與雲端同步失敗: {e}", file=sys.stderr)
    return None

def parse_js_var(js_content, var_name):
    """解析 JavaScript 檔案中的變數並轉換成 Python 物件"""
    pattern = r"(?:var\s+)?{var_name}\s*=\s*({{.*?}}|[\[\'].*?[\]\'])\s*;".format(var_name=var_name)
    match = re.search(pattern, js_content, re.DOTALL)
    if not match:
        pattern_no_semicolon = r"(?:var\s+)?{var_name}\s*=\s*({{.*?}}|[\[\'].*?[\]\'])".format(var_name=var_name)
        match = re.search(pattern_no_semicolon, js_content, re.DOTALL)
        
    if match:
        raw_str = match.group(1).strip()
        raw_str = re.sub(r"//.*?\n", "\n", raw_str)
        raw_str = re.sub(r"/\*.*?\*/", "", raw_str, flags=re.DOTALL)
        
        try:
            return ast.literal_eval(raw_str)
        except Exception as e:
            try:
                json_str = raw_str.replace("'", '"')
                return json.loads(json_str)
            except Exception:
                raise ValueError(f"無法解析變數 {var_name}: {e}")
                
    raise ValueError(f"在 JavaScript 中找不到變數 {var_name}")

def fetch_recipients_from_google_sheet(csv_url):
    """從 Google 試算表（已發布為 CSV）載入收件者清單與設定"""
    recipients = {"emails": [], "line_ids": []}
    threshold_override = None
    if not csv_url or "YOUR_GOOGLE_SHEET" in csv_url:
        return recipients, threshold_override
        
    try:
        print(f"正在從 Google 試算表載入聯絡人資料... ({csv_url})")
        csv_data = fetch_url(csv_url)
        
        # 使用 StringIO 將字串轉為類檔案物件以利 csv 讀取
        f = io.StringIO(csv_data)
        reader = csv.DictReader(f)
        
        for row in reader:
            # 清理鍵值與資料前後的空白
            row = {k.strip(): v.strip() for k, v in row.items() if k}
            
            name = row.get("Name", "").strip()
            name_lower = name.lower()
            
            # 檢查是否為溫度閾值設定列
            if any(k in name_lower for k in ("threshold", "溫度", "閥值", "閾值")):
                for col in ("Email", "LINE_ID", "Enabled"):
                    val_str = row.get(col, "").strip()
                    num_match = re.search(r"(\d+(?:\.\d+)?)", val_str)
                    if num_match:
                        try:
                            threshold_override = float(num_match.group(1))
                            print(f"【試算表設定】從試算表讀取到溫度閾值設定：{threshold_override}°C (將覆蓋本機設定)")
                            break
                        except ValueError:
                            pass
                continue
            
            # 判斷是否啟用（預設啟用）
            enabled = row.get("Enabled", "Y").upper()
            if enabled not in ("Y", "YES", "TRUE", "1", ""):
                continue
                
            email = row.get("Email", "")
            line_id = row.get("LINE_ID", "")
            
            if email and "@" in email:
                recipients["emails"].append(email)
            if line_id:
                prefix = line_id[0].upper()
                if prefix in ("U", "C", "R"):
                    recipients["line_ids"].append(line_id)
                
        print(f"從 Google 試算表載入成功：Email x {len(recipients['emails'])} 人, LINE ID x {len(recipients['line_ids'])} 人")
    except Exception as e:
        print(f"【警告】從 Google 試算表載入名單失敗: {e}", file=sys.stderr)
        
    return recipients, threshold_override

def check_weather(config):
    """透過 CWA Open Data API 抓取即時觀測的環境溫度"""
    api_key    = config.get("cwa_api_key", "")
    station_id = config.get("cwa_station_id", "C2G870") # 預設改為伸港站

    if not api_key:
        raise ValueError("請在 config.json 中設定 cwa_api_key。")

    # 改為 O-A0003-001 (自動氣象站)
    url = (
        f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001"
        f"?Authorization={api_key}&StationId={station_id}"
    )
    print(f"正在透過 CWA Open Data API 抓取觀測資料... (站點: {station_id})")
    content = fetch_url(url)
    data = json.loads(content)

    stations = data.get("records", {}).get("Station", [])
    if not stations:
        raise ValueError(f"CWA API 回傳空資料，StationId={station_id}")

    s        = stations[0]
    we       = s.get("WeatherElement", {})
    raw_obs_time = s.get("ObsTime", {}).get("DateTime", "")
    obs_time = raw_obs_time.replace("T", " ")[:19] if raw_obs_time else ""

    temp = float(we.get("AirTemperature", -99))

    if temp == -99:
        raise ValueError(f"站點 {station_id} 觀測環境溫度異常（-99），無法讀取。")

    print(f"觀測時間: {obs_time}, 環境溫度: {temp}°C")
    return temp, obs_time

def send_line_notifications(line_config, message, recipients):
    """發送 LINE 訊息通知（支援 Multicast API 一次推播多人）"""
    token = line_config.get("channel_access_token")
    if not token or "YOUR_LINE" in token:
        print("【警告】未設定有效的 LINE Token，跳過 LINE 發送。")
        return False
        
    if not recipients:
        print("【警告】LINE 收件者清單為空，跳過發送。")
        return False
        
    # 分離 User ID (U/u 開頭) 與 Group/Room ID (C/c 或 R/r 開頭)
    user_ids = [r for r in recipients if r.upper().startswith("U")]
    group_ids = [r for r in recipients if r.upper().startswith("C") or r.upper().startswith("R")]
    
    success = False
    
    # 1. 對個人 ID 使用 Multicast API (支援一次最多 500 位個人接收者)
    if user_ids:
        # 將收件者切分為每 500 人一組
        for chunk in [user_ids[i:i + 500] for i in range(0, len(user_ids), 500)]:
            url = "https://api.line.me/v2/bot/message/multicast"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            payload = {
                "to": chunk,
                "messages": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            }
            
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    print(f"LINE 訊息 Multicast 推播成功！(收件者數量: {len(chunk)} 人)")
                    success = True
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8")
                print(f"【LINE Multicast API 錯誤】狀態碼 {e.code}: {err_body}", file=sys.stderr)
            except Exception as e:
                print(f"【錯誤】發送 LINE Multicast 時發生異常: {e}", file=sys.stderr)
                
    # 2. 對群組/聊天室 ID 使用 Push API（群組不支援 Multicast，需單獨發送）
    for gid in group_ids:
        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        payload = {
            "to": gid,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                print(f"LINE 群組/聊天室推播成功！(ID: {gid})")
                success = True
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            print(f"【LINE Push API 錯誤】狀態碼 {e.code}: {err_body}", file=sys.stderr)
        except Exception as e:
            print(f"【錯誤】發送 LINE Push 時發生異常: {e}", file=sys.stderr)
            
    return success

def send_email_notifications(email_config, subject, body, recipients):
    """透過 SMTP 一次發送電子郵件通知給多個收件人"""
    smtp_server = email_config.get("smtp_server")
    smtp_port = email_config.get("smtp_port", 587)
    user = email_config.get("smtp_user")
    password = email_config.get("smtp_password")
    from_email = email_config.get("from_email", user)
    
    if not smtp_server or "YOUR_EMAIL" in user:
        print("【警告】未設定有效的 SMTP 帳號資訊，跳過郵件發送。")
        return False
        
    if not recipients:
        print("【警告】郵件收件者清單為空，跳過發送. ")
        return False
        
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = Header(from_email, "utf-8")
    msg["To"] = Header(", ".join(recipients), "utf-8")
    
    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
            
        if user and password:
            server.login(user, password)
            
        server.sendmail(from_email, recipients, msg.as_string())
        server.close()
        print(f"電子郵件發送成功！(收件者數量: {len(recipients)} 人)")
        return True
    except Exception as e:
        print(f"【錯誤】發送電子郵件時發生異常: {e}", file=sys.stderr)
        return False

def main():
    force_run = "--force" in sys.argv
    
    # 1. 檢查是否在監測時段 (07:00 - 24:00) 內，避免非工作時間打擾人員
    tz_taiwan = datetime.timezone(datetime.timedelta(hours=8))
    current_hour = datetime.datetime.now(tz_taiwan).hour
    if (current_hour < 7 or current_hour >= 24) and not force_run:
        print(f"目前時間為 {current_hour:02d}:00，不在監測時段 (07:00 - 24:00) 內，跳過監測。")
        sys.exit(0)
        
    config = load_config()
    state = load_state()
    frequency = config.get("frequency", 60)
    threshold = config.get("temperature_threshold", 28.0)
    
    # 2. 獲取 CWA 氣象數據 (無論是否節流都需要獲取即時數據)
    try:
        current_temp, display_time = check_weather(config)
    except Exception as e:
        print(f"【錯誤】獲取即時觀測數據失敗: {e}", file=sys.stderr)
        sys.exit(1)
        
    # 3. 將 10 分鐘即時觀測數據寫入 Firestore realtime_logs (供 HMI 即時 24H 趨勢圖呈現)
    try:
        add_realtime_log_to_firebase(current_temp, display_time)
    except Exception as e:
        print(f"【警告】寫入即時觀測紀錄失敗: {e}", file=sys.stderr)
        
    # 4. 更新即時狀態 (儀表板溫度計與在線心跳指標)
    try:
        send_heartbeat_firebase(
            current_temp=current_temp,
            threshold=threshold,
            obs_time=display_time,
            alert_state="正常 (未超標)" if current_temp <= threshold else "高溫超標警報",
            status_text="即時觀測更新"
        )
        # 同時發送即時心跳給 GAS，更新 GAS 介面的在線時間（不寫入試算表歷史，以防洗版）
        web_app_url = config.get("web_app_url", "")
        if web_app_url:
            send_heartbeat(web_app_url, sync_type="heartbeat")
    except Exception as e:
        print(f"【警告】更新即時心跳失敗: {e}", file=sys.stderr)
        
    # 5. 進行本機排程自動節流 (僅節流通知與試算表寫入)
    if not force_run:
        last_run_str = state.get("last_run_time")
        if last_run_str:
            try:
                last_run_time = datetime.datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz_taiwan)
                now_time = datetime.datetime.now(tz_taiwan)
                diff_minutes = (now_time - last_run_time).total_seconds() / 60.0
                if diff_minutes < (frequency - 2): # 減 2 分鐘做為微小時間差容錯
                    print(f"【節流跳過】距離上一次執行僅 {diff_minutes:.1f} 分鐘，未達設定頻率 {frequency} 分鐘。已成功更新即時溫度與 24H 趨勢圖。")
                    sys.exit(0)
            except Exception as e:
                print(f"【警告】解析上次執行時間失敗: {e}", file=sys.stderr)
    
    # 進行本機與雲端的狀態同步與心跳報告 (Sync status)
    web_app_url = config.get("web_app_url", "")
    if web_app_url:
        print("正在向雲端同步當前狀態與發送心跳...")
        cloud_state = send_heartbeat(web_app_url, state.get("last_state", "COOL"), sync_type="sync")
        if cloud_state:
            if cloud_state != state.get("last_state"):
                print(f"【同步完成】雲端狀態為 {cloud_state}，本機為 {state.get('last_state')}，已將本機同步為 {cloud_state}。")
                state["last_state"] = cloud_state
                save_state(cloud_state)
    
    # 取得今日日期字串
    tz_taiwan = datetime.timezone(datetime.timedelta(hours=8))
    
    print(f"=== 啟動天氣監控排程 ({datetime.datetime.now(tz_taiwan).strftime('%Y-%m-%d %H:%M:%S')}) ===")
        
    # 2. 獲取收件者名單與設定
    # A. 從本機 config 載入
    local_emails = config.get("email", {}).get("to_email", [])
    if isinstance(local_emails, str):
        local_emails = [local_emails]
        
    local_line_ids = config.get("line", {}).get("to", [])
    if isinstance(local_line_ids, str):
        local_line_ids = [local_line_ids]
        
    # B. 從 Google 試算表載入並與本機名單合併
    sheet_recipients, threshold_override = fetch_recipients_from_google_sheet(config.get("google_sheet_csv_url", ""))
    
    # 若試算表有設定溫度閾值，覆蓋本機設定
    if threshold_override is not None:
        config["temperature_threshold"] = threshold_override
        
    threshold = config.get("temperature_threshold", 28.0)
        
    # 合併並去除重複
    final_emails = list(set(local_emails + sheet_recipients["emails"]))
    final_line_ids = list(set(local_line_ids + sheet_recipients["line_ids"]))
    
    # 清理掉無效字串 (例如 placeholder 範例)
    final_emails = [e for e in final_emails if e and "RECIPIENT_EMAIL" not in e and "YOUR_EMAIL" not in e]
    final_line_ids = [l for l in final_line_ids if l and "YOUR_LINE" not in l]
    
    print(f"【聯絡人名單確認】電子郵件收件人: {final_emails} | LINE 推播收件人: {final_line_ids}")
    
    if not final_emails and not final_line_ids:
        print("【錯誤】未偵測到任何有效的 Email 或 LINE 收件者，無法通報。", file=sys.stderr)
        sys.exit(1)
        
    # 3. 已在開頭完成氣象數據抓取與即時日誌上傳
        
    # 4. 狀態機邏輯比對
    last_state = state.get("last_state", "COOL")
    is_hot = current_temp > threshold
    
    should_notify = False
    notify_subject = ""
    notify_body = ""
    town_name = config.get("town_name", "彰化縣線西鄉")
    formatted_time = datetime.datetime.now(tz_taiwan).strftime('%Y-%m-%d %H:%M:%S')
    
    if is_hot:
        if last_state != "HOT" or force_run:
            should_notify = True
            notify_subject = f"【高溫警報】{town_name}目前環境溫度已達 {current_temp}°C，超過設定溫度閾值！"
            
            notify_body = f"【環境高溫警報】\n"
            notify_body += f"當前環境溫度：{current_temp}°C ⚠️ (已超過設定閾值 {threshold}°C)\n"
            notify_body += f"氣象觀測時間：{display_time}\n"
            notify_body += f"通報時間：{formatted_time}\n\n"
            notify_body += "※ 請相關人員開啟灑水設備降溫循環過濾器。\n"
            notify_body += "※ 請相關人員注意防暑、多補充水分，並採取防範措施。"
        else:
            print(f"當前環境溫度 {current_temp}°C 超標，但前次已通報高溫，跳過重複通知。")
    else:
        if last_state == "HOT" or force_run:
            should_notify = True
            notify_subject = f"【高溫解除】{town_name}目前環境溫度已回落至 {current_temp}°C，低於設定溫度閾值。"
            
            notify_body = f"【環境溫度回落通知】\n"
            notify_body += f"當前環境溫度：{current_temp}°C ✅ (已降至設定閾值 {threshold}°C 以下)\n"
            notify_body += f"氣象觀測時間：{display_time}\n"
            notify_body += f"通報時間：{formatted_time}\n\n"
            notify_body += "※ 目前高溫警報已解除，氣溫已回落至安全範圍。"
        else:
            print(f"當前環境溫度 {current_temp}°C 正常，且前次狀態為正常，跳過通知。")
            
    if not should_notify:
        # 本機執行成功但未觸發通知，發送一般心跳給雲端，回報本機已完成觀測，並帶上當前數據
        alert_state_text = "高溫持續中" if is_hot else "正常 (未超標)"
        print("本機已完成本次溫度觀測，發送觀測成功心跳...")
        # 直接寫 Firebase（不依賴 GAS）
        send_heartbeat_firebase(
            current_temp=current_temp,
            threshold=threshold,
            obs_time=display_time,
            alert_state=alert_state_text,
            status_text="未發送 (重複或正常)"
        )
        # 同時嘗試舊的 GAS 路徑（若有設定 web_app_url）
        if web_app_url:
            send_heartbeat(web_app_url, sync_type="heartbeat",
                current_temp=current_temp, threshold=threshold,
                obs_time=display_time, alert_state=alert_state_text,
                status_text="未發送 (重複或正常)")
        save_state(last_state)
        sys.exit(0)
        
    print("\n--- 觸發通知內容 ---")
    print(notify_body)
    print("--------------------\n")
    
    # 5. 開始發送
    line_sent = False
    email_sent = False
    
    # 發送 LINE
    if config.get("line", {}).get("enabled", True) and final_line_ids:
        line_sent = send_line_notifications(config["line"], notify_body, final_line_ids)
        
    # 發送 Email
    if config.get("email", {}).get("enabled", True) and final_emails:
        email_sent = send_email_notifications(config["email"], notify_subject, notify_body, final_emails)
        
    # 若成功發送任一通知，更新狀態防止重複發送
    if line_sent or email_sent:
        new_state = "HOT" if is_hot else "COOL"
        save_state(new_state)
        print("狀態已更新，記錄前次狀態。")
        status_text_list = []
        if line_sent: status_text_list.append("LINE")
        if email_sent: status_text_list.append("Email")
        status_str = " & ".join(status_text_list) + " 已發送" if status_text_list else "發送失敗"
        alert_str = "高溫超標警報" if is_hot else "溫度回落正常"
        print("正在向 Firebase 同步更新後的警報狀態...")
        # 直接寫 Firebase
        send_heartbeat_firebase(
            current_temp=current_temp, threshold=threshold,
            obs_time=display_time, alert_state=alert_str,
            status_text=status_str
        )
        if web_app_url:
            send_heartbeat(web_app_url, new_state, sync_type="update",
                current_temp=current_temp, threshold=threshold,
                obs_time=display_time, alert_state=alert_str,
                status_text=status_str)
    else:
        print("未成功發送任何通知，不更新狀態，但記錄本次執行時間。")
        save_state(last_state)
        alert_str2 = "正常 (未超標)" if not is_hot else "高溫持續中"
        send_heartbeat_firebase(
            current_temp=current_temp, threshold=threshold,
            obs_time=display_time, alert_state=alert_str2,
            status_text="發送失敗"
        )
        if web_app_url:
            send_heartbeat(web_app_url, sync_type="heartbeat",
                current_temp=current_temp, threshold=threshold,
                obs_time=display_time, alert_state=alert_str2,
                status_text="發送失敗")

if __name__ == "__main__":
    main()
