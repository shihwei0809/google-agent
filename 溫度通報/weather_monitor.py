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
RUN_STATE_PATH = os.path.join(SCRIPT_DIR, "last_run.json")

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

def save_state(state_name):
    """儲存發送狀態"""
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "last_state": state_name
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"【警告】儲存發送狀態失敗: {e}", file=sys.stderr)

def load_last_run_timestamp():
    """載入最後一次執行監測的時間戳"""
    if os.path.exists(RUN_STATE_PATH):
        try:
            with open(RUN_STATE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_run_timestamp", 0.0)
        except Exception:
            pass
    return 0.0

def save_last_run_timestamp(ts):
    """儲存最後一次執行監測的時間戳"""
    try:
        with open(RUN_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "last_run_timestamp": ts
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"【警告】儲存執行紀錄失敗: {e}", file=sys.stderr)

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

def send_heartbeat(url, state_name=None, sync_type="heartbeat", current_temp=None, obs_time=None, threshold=None, alert_state=None, status_text=None):
    """發送心跳與狀態同步給 Google Apps Script 雲端 Web App"""
    payload = {
        "action": "heartbeat",
        "type": sync_type
    }
    if state_name:
        payload["local_state"] = state_name
    if current_temp is not None:
        payload["current_temp"] = current_temp
    if obs_time is not None:
        payload["obs_time"] = obs_time
    if threshold is not None:
        payload["threshold"] = threshold
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

def get_sheet_urls(url):
    """
    根據使用者填寫的試算表網址，解析並產生「聯絡人名單」與「系統設定」兩個分頁的 CSV 下載網址。
    """
    contacts_url = url
    settings_url = None
    
    # 判斷是否為標準瀏覽器網址
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if match and "pub" not in url:
        spreadsheet_id = match.group(1)
        contacts_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=0"
        settings_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&sheet=系統設定"
    else:
        # 如果是已發布網址，若是包含 pub? 的格式，我們試著替換參數
        if "pub?" in url:
            base_url = url.split("?")[0]
            contacts_url = f"{base_url}?output=csv"
            settings_url = f"{base_url}?output=csv&sheet=系統設定"
            
    return contacts_url, settings_url

def fetch_recipients_from_google_sheet(csv_url):
    """從 Google 試算表載入收件者清單與設定"""
    recipients = {"emails": [], "line_ids": []}
    threshold_override = None
    start_hour_override = None
    end_hour_override = None
    frequency_override = None
    
    if not csv_url or "YOUR_GOOGLE_SHEET" in csv_url:
        return recipients, threshold_override, start_hour_override, end_hour_override, frequency_override
        
    contacts_url, settings_url = get_sheet_urls(csv_url)
    
    # 1. 嘗試下載並解析「系統設定」分頁
    has_settings_sheet = False
    if settings_url:
        try:
            print(f"正在從 Google 試算表下載【系統設定】分頁... ({settings_url})")
            settings_data = fetch_url(settings_url)
            f_settings = io.StringIO(settings_data)
            reader_settings = csv.reader(f_settings)
            rows = list(reader_settings)
            
            for row in rows[1:]: # 跳過表頭
                if len(row) < 2:
                    continue
                key = row[0].strip()
                val = row[1].strip()
                key_lower = key.lower()
                
                # 溫度閾值
                if any(k in key_lower for k in ("threshold", "溫度", "閥值", "閾值")):
                    num_match = re.search(r"(\d+(?:\.\d+)?)", val)
                    if num_match:
                        threshold_override = float(num_match.group(1))
                        print(f"【試算表設定】讀取溫度閾值：{threshold_override}°C")
                        has_settings_sheet = True
                
                # 開始時間
                elif any(k in key_lower for k in ("start", "開始", "啟動")):
                    num_match = re.search(r"(\d+)", val)
                    if num_match:
                        start_hour_override = int(num_match.group(1))
                        print(f"【試算表設定】讀取監測開始時間：{start_hour_override:02d}:00")
                        has_settings_sheet = True
                        
                # 結束時間
                elif any(k in key_lower for k in ("end", "結束", "停止")):
                    num_match = re.search(r"(\d+)", val)
                    if num_match:
                        end_hour_override = int(num_match.group(1))
                        print(f"【試算表設定】讀取監測結束時間：{end_hour_override:02d}:00")
                        has_settings_sheet = True
                        
                # 監測頻率
                elif any(k in key_lower for k in ("frequency", "頻率", "間隔")):
                    num_match = re.search(r"(\d+)", val)
                    if num_match:
                        frequency_override = int(num_match.group(1))
                        print(f"【試算表設定】讀取監測頻率：{frequency_override} 分鐘")
                        has_settings_sheet = True
        except Exception as e:
            # 分頁不存在或下載失敗，略過並降級到舊版相容模式
            print(f"【提示】無法從專屬「系統設定」分頁取得設定 (原因: {e})，將嘗試在聯絡人分頁中搜尋設定。")

    # 2. 下載並解析「聯絡人名單」分頁
    try:
        print(f"正在從 Google 試算表下載【聯絡人名單】... ({contacts_url})")
        csv_data = fetch_url(contacts_url)
        f_contacts = io.StringIO(csv_data)
        reader = csv.DictReader(f_contacts)
        
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items() if k}
            name = row.get("Name", "").strip()
            name_lower = name.lower()
            
            # 若無獨立設定分頁，使用相容模式解析混合在聯絡人名單中的設定列
            if not has_settings_sheet:
                if any(k in name_lower for k in ("threshold", "溫度", "閥值", "閾值")):
                    for col in ("Email", "LINE_ID", "Enabled"):
                        val_str = row.get(col, "").strip()
                        num_match = re.search(r"(\d+(?:\.\d+)?)", val_str)
                        if num_match:
                            threshold_override = float(num_match.group(1))
                            print(f"【相容舊設定】讀取溫度閾值：{threshold_override}°C")
                            break
                    continue
                if any(k in name_lower for k in ("start", "開始", "啟動")):
                    for col in ("Email", "LINE_ID", "Enabled"):
                        val_str = row.get(col, "").strip()
                        num_match = re.search(r"(\d+)", val_str)
                        if num_match:
                            start_hour_override = int(num_match.group(1))
                            print(f"【相容舊設定】讀取監測開始時間：{start_hour_override:02d}:00")
                            break
                    continue
                if any(k in name_lower for k in ("end", "結束", "停止")):
                    for col in ("Email", "LINE_ID", "Enabled"):
                        val_str = row.get(col, "").strip()
                        num_match = re.search(r"(\d+)", val_str)
                        if num_match:
                            end_hour_override = int(num_match.group(1))
                            print(f"【相容舊設定】讀取監測結束時間：{end_hour_override:02d}:00")
                            break
                    continue
            
            # 判斷是否啟用（預設啟用）
            enabled = row.get("Enabled", "Y").upper()
            if enabled not in ("Y", "YES", "TRUE", "1", ""):
                continue
                
            email = row.get("Email", "")
            line_id = row.get("LINE_ID", "")
            
            # 排除設定關鍵字列被誤判為聯絡人
            if any(k in name_lower for k in ("threshold", "溫度", "閥值", "閾值", "start", "開始", "啟動", "end", "結束", "停止", "frequency", "頻率", "間隔")):
                continue
                
            if email and "@" in email:
                recipients["emails"].append(email)
            if line_id:
                prefix = line_id[0].upper()
                if prefix in ("U", "C", "R"):
                    recipients["line_ids"].append(line_id)
                
        print(f"聯絡人名單解析成功：Email x {len(recipients['emails'])} 人, LINE ID x {len(recipients['line_ids'])} 人")
    except Exception as e:
        print(f"【警告】載入聯絡人名單失敗: {e}", file=sys.stderr)
        
    return recipients, threshold_override, start_hour_override, end_hour_override, frequency_override

def check_weather(config):
    """透過 CWA Open Data API 抓取線西站即時環境溫度"""
    api_key    = config.get("cwa_api_key", "")
    station_id = config.get("cwa_station_id", "C0G900")

    if not api_key:
        raise ValueError("請在 config.json 中設定 cwa_api_key。")

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
    obs_time = s.get("ObsTime", {}).get("DateTime", "")

    temp = float(we.get("AirTemperature", -99))

    if temp == -99:
        raise ValueError(f"站點 {station_id} 觀測資料異常（-99），無法取得環境溫度。")

    # 格式化時間，去除 "T" 與 "+08:00"
    if obs_time and "T" in obs_time:
        obs_time = obs_time.replace("T", " ")[:19]

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
    
    config = load_config()
    state = load_state()
    
    tz_taiwan = datetime.timezone(datetime.timedelta(hours=8))
    print(f"=== 啟動天氣監控排程 ({datetime.datetime.now(tz_taiwan).strftime('%Y-%m-%d %H:%M:%S')}) ===")
        
    # 1. 獲取收件者名單與設定 (合併試算表設定)
    local_emails = config.get("email", {}).get("to_email", [])
    if isinstance(local_emails, str):
        local_emails = [local_emails]
        
    local_line_ids = config.get("line", {}).get("to", [])
    if isinstance(local_line_ids, str):
        local_line_ids = [local_line_ids]
        
    # 從 Google 試算表下載收件者名單與配置參數 (包含獨立設定分頁)
    sheet_recipients, threshold_override, start_hour_override, end_hour_override, frequency_override = fetch_recipients_from_google_sheet(config.get("google_sheet_csv_url", ""))
    
    # 2. 進行監測頻率檢查與節流判定 (Throttling)
    frequency = frequency_override if frequency_override is not None else config.get("frequency", 60)
    
    if not force_run:
        last_run_ts = load_last_run_timestamp()
        current_ts = datetime.datetime.now(tz_taiwan).timestamp()
        elapsed_seconds = current_ts - last_run_ts
        required_seconds = frequency * 60 - 30  # 允許30秒的時間誤差
        
        if elapsed_seconds < required_seconds:
            elapsed_minutes = round(elapsed_seconds / 60.0, 1)
            print(f"【頻率限制】距離上次實際執行僅 {elapsed_minutes} 分鐘，未達設定監測頻率 {frequency} 分鐘，跳過本次執行。")
            sys.exit(0)
            
    # 3. 檢查監測時段是否相符
    start_hour = start_hour_override if start_hour_override is not None else config.get("start_hour", 8)
    end_hour = end_hour_override if end_hour_override is not None else config.get("end_hour", 24)
    
    current_hour = datetime.datetime.now(tz_taiwan).hour
    
    is_in_time_window = False
    if start_hour < end_hour:
        is_in_time_window = (start_hour <= current_hour < end_hour)
    else: # 跨夜時段，例如 22點至06點
        is_in_time_window = (current_hour >= start_hour or current_hour < end_hour)
        
    if not is_in_time_window and not force_run:
        print(f"目前時間為 {current_hour:02d}:00，不在監測時段 ({start_hour:02d}:00 - {end_hour:02d}:00) 內，跳過監測。")
        sys.exit(0)
        
    # 若試算表有設定溫度閾值，覆蓋本機設定
    if threshold_override is not None:
        config["temperature_threshold"] = threshold_override
        
    # 4. 若確認執行，才進行本機與雲端的狀態同步與心跳報告
    web_app_url = config.get("web_app_url", "")
    if web_app_url:
        print("正在向雲端同步當前狀態與發送心跳...")
        cloud_state = send_heartbeat(web_app_url, state.get("last_state", "COOL"), sync_type="sync")
        if cloud_state:
            if cloud_state != state.get("last_state"):
                print(f"【同步完成】雲端狀態為 {cloud_state}，本機為 {state.get('last_state')}，已將本機同步為 {cloud_state}。")
                state["last_state"] = cloud_state
                save_state(cloud_state)
        
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
        
    # 3. 檢查氣象數據
    try:
        current_temp, display_time = check_weather(config)
    except Exception as e:
        print(f"【錯誤】獲取即時觀測數據失敗: {e}", file=sys.stderr)
        sys.exit(1)
        
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
            notify_subject = f"【高溫警報】{town_name}目前環境溫度已達 {current_temp}°C，超過設定閾值！"
            
            notify_body = f"【{town_name} 環境高溫警報】\n"
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
            notify_subject = f"【高溫解除】{town_name}目前環境溫度已回落至 {current_temp}°C，低於設定閾值。"
            
            notify_body = f"【{town_name} 環境溫度回落通知】\n"
            notify_body += f"當前環境溫度：{current_temp}°C ✅ (已降至設定閾值 {threshold}°C 以下)\n"
            notify_body += f"氣象觀測時間：{display_time}\n"
            notify_body += f"通報時間：{formatted_time}\n\n"
            notify_body += "※ 目前高溫警報已解除，氣溫已回落至安全範圍。"
        else:
            print(f"當前環境溫度 {current_temp}°C 正常，且前次狀態為正常，跳過通知。")
            
    if not should_notify:
        # 本機執行成功但未觸發通知，發送一般心跳給雲端，回報本機已完成觀測
        if web_app_url:
            print("本機已完成本次溫度觀測，發送觀測成功心跳給雲端...")
            alert_state_text = "高溫持續中" if is_hot else "正常 (未超標)"
            status_text = "未發送 (重複或正常)"
            send_heartbeat(
                web_app_url, 
                sync_type="heartbeat",
                current_temp=current_temp,
                obs_time=display_time,
                threshold=threshold,
                alert_state=alert_state_text,
                status_text=status_text
            )
        # 儲存執行時間戳
        save_last_run_timestamp(datetime.datetime.now(tz_taiwan).timestamp())
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
        if web_app_url:
            print("正在向雲端同步更新後的警報狀態...")
            alert_state_text = "高溫超標警報" if is_hot else "溫度回落正常"
            status_arr = []
            if line_sent: status_arr.append("LINE")
            if email_sent: status_arr.append("Email")
            status_text = f"{' & '.join(status_arr)} 已發送" if status_arr else "發送失敗"
            send_heartbeat(
                web_app_url, 
                state_name=new_state, 
                sync_type="update",
                current_temp=current_temp,
                obs_time=display_time,
                threshold=threshold,
                alert_state=alert_state_text,
                status_text=status_text
            )
    else:
        print("未成功發送任何通知，不更新狀態。")
        if web_app_url:
            alert_state_text = "高溫超標警報" if is_hot else "溫度回落正常"
            status_text = "發送失敗"
            send_heartbeat(
                web_app_url, 
                sync_type="heartbeat",
                current_temp=current_temp,
                obs_time=display_time,
                threshold=threshold,
                alert_state=alert_state_text,
                status_text=status_text
            )
            
    # 儲存執行時間戳 (完成一次觀測與通報週期)
    save_last_run_timestamp(datetime.datetime.now(tz_taiwan).timestamp())

if __name__ == "__main__":
    main()
