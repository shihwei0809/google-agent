# Source Code Backup - 溫度通報 - weather_monitor.py

> [!NOTE]
> *   **原始本機路徑**: [weather_monitor.py](file:///D:/GOOGLE%20ANGET/溫度通報/weather_monitor.py)
> *   **自動備份時間**: `2026-07-15 13:39:13`
> *   **語言類型**: `python`

``` python
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

# 本機 CSV & XLSX 備份路徑 (分開為歷史通報與心跳明細)
LOCAL_NOTIFY_CSV = os.path.join(SCRIPT_DIR, "本地歷史紀錄_歷史通報.csv")
LOCAL_HEARTBEAT_CSV = os.path.join(SCRIPT_DIR, "本地歷史紀錄_心跳明細.csv")
LOCAL_NOTIFY_XLSX = os.path.join(SCRIPT_DIR, "本地歷史紀錄_歷史通報.xlsx")
LOCAL_HEARTBEAT_XLSX = os.path.join(SCRIPT_DIR, "本地歷史紀錄_心跳明細.xlsx")

def get_realtime_backup_paths():
    """取得 24 小時趨勢備份的本機/雲端硬碟儲存路徑，支援自動建立資料夾，返回月度 CSV 與年度 XLSX 及月份 Sheet 名"""
    tz_taiwan = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz_taiwan)
    year_str = now.strftime('%Y')
    month_str = now.strftime('%Y-%m') # 例如 "2026-06"
    sheet_name = f"{now.month}月" # 例如 "6月"
    
    csv_file = f"{month_str}_24小時趨勢備份.csv"
    xlsx_file = f"{year_str}年_24小時趨勢備份.xlsx"
    
    # 優先嘗試寫入 Google Drive 虛擬硬碟 G:\
    g_drive_dir = r"G:\我的雲端硬碟\GOOGLE ANGET\溫度通報\24 小時趨勢備份"
    try:
        os.makedirs(g_drive_dir, exist_ok=True)
        return os.path.join(g_drive_dir, csv_file), os.path.join(g_drive_dir, xlsx_file), sheet_name
    except Exception:
        # 若 G 槽未掛載或無寫入權限，回退到本地目錄下
        local_dir = os.path.join(SCRIPT_DIR, "24 小時趨勢備份")
        os.makedirs(local_dir, exist_ok=True)
        return os.path.join(local_dir, csv_file), os.path.join(local_dir, xlsx_file), sheet_name

def append_to_monthly_xlsx(file_path, sheet_name, headers, row_data):
    """將資料寫入指定年份 XLSX 檔案的指定月份工作表 (sheet_name)"""
    try:
        import openpyxl
        from openpyxl.utils import get_column_letter
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        return

    try:
        file_exists = os.path.exists(file_path)
        if file_exists:
            try:
                wb = openpyxl.load_workbook(file_path)
            except Exception:
                wb = openpyxl.Workbook()
        else:
            wb = openpyxl.Workbook()

        # 獲取或建立指定工作表
        if sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
        else:
            ws = wb.create_sheet(title=sheet_name)
            # 如果新建的工作表是第一個（且預設工作表存在且為空），可以刪除預設的 "Sheet"
            if "Sheet" in wb.sheetnames and len(wb.sheetnames) > 1:
                default_sheet = wb["Sheet"]
                if default_sheet.max_row == 1 and default_sheet.cell(row=1, column=1).value is None:
                    wb.remove(default_sheet)
            ws.append(headers)

        ws.append(row_data)

        # 設定字型、背景填充與對齊
        header_font = Font(name="微軟正黑體", size=11, bold=True)
        header_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        header_align = Alignment(horizontal="center", vertical="center")
        data_font = Font(name="微軟正黑體", size=11)
        data_align = Alignment(horizontal="center", vertical="center")

        # 格式化所有儲存格的樣式
        for r_idx in range(1, ws.max_row + 1):
            is_header = (r_idx == 1)
            for c_idx in range(1, ws.max_column + 1):
                cell = ws.cell(row=r_idx, column=c_idx)
                if is_header:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = header_align
                else:
                    cell.font = data_font
                    if isinstance(cell.value, (int, float)):
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    else:
                        cell.alignment = data_align

        # 自動調整欄寬
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.value is not None:
                    val_str = str(cell.value)
                    width = 0
                    for char in val_str:
                        if ord(char) > 127:  # 中文與全形字元
                            width += 2
                        else:
                            width += 1.1
                    if width > max_len:
                        max_len = width
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        wb.save(file_path)
    except Exception as e:
        print(f"【本機備份警告】寫入 {os.path.basename(file_path)} 工作表 {sheet_name} 失敗: {e}", file=sys.stderr)

def append_to_local_csv(file_path, headers, row_data):
    """將資料寫入本機 CSV 檔案，若檔案不存在則自動建立並寫入表頭"""
    import csv
    file_exists = os.path.exists(file_path)
    try:
        # 使用 utf-8-sig 以便 Excel 開啟時不亂碼 (BOM)
        with open(file_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(headers)
            writer.writerow(row_data)
    except Exception as e:
        print(f"【本機備份警告】寫入 {os.path.basename(file_path)} 失敗: {e}", file=sys.stderr)

def append_to_local_xlsx(file_path, headers, row_data):
    """將資料寫入本機 XLSX 檔案，若檔案不存在則自動從 CSV 載入歷史資料或建立新工作表，並自動調整欄寬與格式"""
    try:
        import openpyxl
        from openpyxl.utils import get_column_letter
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        # 若沒有安裝 openpyxl，則優雅地跳過以保持相容性
        return

    try:
        file_exists = os.path.exists(file_path)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "歷史紀錄"

        # 如果 XLSX 不存在，但對應的 CSV 存在，則自動匯入舊資料
        csv_path = file_path.replace(".xlsx", ".csv")
        imported_from_csv = False
        
        if not file_exists and os.path.exists(csv_path):
            try:
                import csv
                with open(csv_path, "r", encoding="utf-8-sig") as csv_f:
                    reader = csv.reader(csv_f)
                    rows = list(reader)
                    if rows:
                        for r in rows:
                            converted_row = []
                            for cell_val in r:
                                try:
                                    if "." in cell_val:
                                        converted_row.append(float(cell_val))
                                    else:
                                        converted_row.append(int(cell_val))
                                except ValueError:
                                    converted_row.append(cell_val)
                            ws.append(converted_row)
                        imported_from_csv = True
            except Exception as csv_e:
                print(f"【匯入 CSV 警告】從 {os.path.basename(csv_path)} 匯入舊資料失敗: {csv_e}", file=sys.stderr)

        if not file_exists and not imported_from_csv:
            # 檔案與 CSV 都不存在，建立全新工作表並寫入表頭與當前列
            ws.append(headers)
            ws.append(row_data)
        elif file_exists:
            # 檔案已存在，載入並附加新資料
            try:
                wb = openpyxl.load_workbook(file_path)
                ws = wb.active
                ws.append(row_data)
            except Exception:
                # 檔案損壞則重新建立
                ws.append(headers)
                ws.append(row_data)
        else:
            # 已從 CSV 匯入舊資料，附加新資料（若新資料尚未寫入）
            last_row_vals = [ws.cell(row=ws.max_row, column=c).value for c in range(1, len(row_data) + 1)]
            csv_last_time = str(last_row_vals[0]) if last_row_vals and last_row_vals[0] else ""
            new_time = str(row_data[0])
            if csv_last_time != new_time:
                ws.append(row_data)

        # 設定字型、背景填充與對齊
        header_font = Font(name="微軟正黑體", size=11, bold=True)
        header_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        header_align = Alignment(horizontal="center", vertical="center")
        data_font = Font(name="微軟正黑體", size=11)
        data_align = Alignment(horizontal="center", vertical="center")

        # 格式化所有儲存格的樣式
        for r_idx in range(1, ws.max_row + 1):
            is_header = (r_idx == 1)
            for c_idx in range(1, ws.max_column + 1):
                cell = ws.cell(row=r_idx, column=c_idx)
                if is_header:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = header_align
                else:
                    cell.font = data_font
                    if isinstance(cell.value, (int, float)):
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    else:
                        cell.alignment = data_align

        # 自動調整欄寬
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.value is not None:
                    val_str = str(cell.value)
                    width = 0
                    for char in val_str:
                        if ord(char) > 127:  # 中文與全形字元
                            width += 2
                        else:  # 英文與半形字元
                            width += 1.1
                    if width > max_len:
                        max_len = width
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        wb.save(file_path)
    except Exception as e:
        print(f"【本機備份警告】寫入 {os.path.basename(file_path)} 失敗: {e}", file=sys.stderr)

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
    """儲存發送狀態與最後執行時間，如果為手動強制執行則不更新執行時間以防干擾排程"""
    try:
        existing_data = {}
        if os.path.exists(STATE_PATH):
            try:
                with open(STATE_PATH, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception:
                pass

        data = {"last_state": state_name}
        is_force = "--force" in sys.argv

        if is_force:
            # 手動測試不更新執行時間，優先保留原本檔案內的執行時間
            if "last_run_time" in existing_data:
                data["last_run_time"] = existing_data["last_run_time"]
            elif last_run_time_str:
                data["last_run_time"] = last_run_time_str
            else:
                tz_taiwan = datetime.timezone(datetime.timedelta(hours=8))
                data["last_run_time"] = datetime.datetime.now(tz_taiwan).strftime('%Y-%m-%d %H:%M:%S')
        else:
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
            scopes=[
                "https://www.googleapis.com/auth/datastore",
                "https://www.googleapis.com/auth/spreadsheets.readonly"
            ]
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

def get_first_sheet_name(token, spreadsheet_id):
    """透過 Google Sheets API 取得試算表中第一個分頁的名稱"""
    import urllib.parse
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?fields=sheets(properties(title))"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=_fb_ssl_ctx) as response:
            meta = json.loads(response.read().decode("utf-8"))
            sheets = meta.get("sheets", [])
            if sheets:
                return sheets[0].get("properties", {}).get("title")
    except Exception as e:
        print(f"【警告】動態取得分頁名稱失敗: {e}", file=sys.stderr)
    return "工作表1"

def fetch_recipients_from_google_sheet_api(token, spreadsheet_id):
    """透過 Google Sheets API (使用 service account token) 載入收件者清單與設定"""
    import urllib.parse
    recipients = {"emails": [], "line_ids": []}
    threshold_override = None
    if not spreadsheet_id:
        return recipients, threshold_override
        
    try:
        sheet_name = get_first_sheet_name(token, spreadsheet_id)
        print(f"正在透過 Google Sheets API 載入聯絡人資料... (試算表 ID: {spreadsheet_id}, 分頁: {sheet_name})")
        
        # 讀取 A 到 D 欄
        range_notation = "A:D"
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{urllib.parse.quote(sheet_name + '!' + range_notation)}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req, timeout=15, context=_fb_ssl_ctx) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            values = res_data.get("values", [])
            
        if not values:
            print("【警告】Google Sheets 回傳空資料")
            return recipients, threshold_override
            
        # 第一列為表頭
        headers = [h.strip() for h in values[0]]
        
        # 將其後的列轉換為 Dictionary 以利比對
        for row in values[1:]:
            row_dict = {}
            for idx, header in enumerate(headers):
                if idx < len(row):
                    row_dict[header] = row[idx].strip()
                else:
                    row_dict[header] = ""
                    
            name = row_dict.get("Name", "").strip()
            name_lower = name.lower()
            
            # 檢查是否為溫度閾值設定列
            if any(k in name_lower for k in ("threshold", "溫度", "閥值", "閾值")):
                for col in ("Email", "LINE_ID", "Enabled"):
                    val_str = row_dict.get(col, "").strip()
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
            enabled = row_dict.get("Enabled", "Y").upper()
            if enabled not in ("Y", "YES", "TRUE", "1", ""):
                continue
                
            email = row_dict.get("Email", "")
            line_id = row_dict.get("LINE_ID", "")
            
            if email and "@" in email:
                recipients["emails"].append(email)
            if line_id:
                prefix = line_id[0].upper()
                if prefix in ("U", "C", "R"):
                    recipients["line_ids"].append(line_id)
                    
        print(f"從 Google 試算表 (API) 載入成功：Email x {len(recipients['emails'])} 人, LINE ID x {len(recipients['line_ids'])} 人")
    except Exception as e:
        print(f"【警告】透過 Google Sheets API 載入名單失敗: {e}", file=sys.stderr)
        
    return recipients, threshold_override

def fetch_system_config_from_google_sheet_api(token, spreadsheet_id):
    """透過 Google Sheets API (使用 service account token) 載入系統設定分頁中的設定參數"""
    import urllib.parse
    config_overrides = {}
    if not spreadsheet_id:
        return config_overrides
        
    try:
        sheet_name = "系統設定"
        print(f"正在透過 Google Sheets API 載入系統設定... (分頁: {sheet_name})")
        
        # 讀取 A 到 B 欄
        range_notation = "A:B"
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{urllib.parse.quote(sheet_name + '!' + range_notation)}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req, timeout=15, context=_fb_ssl_ctx) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            values = res_data.get("values", [])
            
        if not values:
            return config_overrides
            
        # 表頭在第一列
        for row in values[1:]:
            if len(row) >= 2:
                key = str(row[0]).strip()
                val = str(row[1]).strip()
                key_lower = key.lower()
                
                if any(k in key_lower for k in ("start", "開始", "啟動")):
                    try:
                        config_overrides["start_hour"] = int(val)
                    except ValueError:
                        pass
                elif any(k in key_lower for k in ("end", "結束", "停止")):
                    try:
                        config_overrides["end_hour"] = int(val)
                    except ValueError:
                        pass
                elif any(k in key_lower for k in ("frequency", "頻率", "間隔")):
                    try:
                        config_overrides["frequency"] = int(val)
                    except ValueError:
                        pass
                        
        print(f"從 Google 試算表 (API) 載入系統設定成功: {config_overrides}")
    except Exception as e:
        print(f"【警告】透過 Google Sheets API 載入系統設定失敗: {e}", file=sys.stderr)
        
    return config_overrides

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
    msg["From"] = from_email
    msg["To"] = ", ".join(recipients)
    
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

def send_teams_notifications(teams_config, subject, message):
    """發送 Microsoft Teams Webhook 通知"""
    webhook_url = teams_config.get("webhook_url")
    if not webhook_url or "YOUR_TEAMS" in webhook_url:
        print("【警告】未設定有效的 Teams Webhook URL，跳過 Teams 發送。")
        return False
        
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "D9534F" if "警報" in subject else "5CB85C",
        "summary": subject,
        "title": subject,
        "text": message.replace("\n", "\n\n")
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url, 
        data=data, 
        headers={"Content-Type": "application/json"}, 
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            if status_code in [200, 202]:
                print("Teams 訊息推播成功！")
                return True
            else:
                print(f"【Teams API 錯誤】狀態碼 {status_code}", file=sys.stderr)
                return False
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"【Teams API 錯誤】狀態碼 {e.code}: {err_body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"【錯誤】發送 Teams 時發生異常: {e}", file=sys.stderr)
        return False

def main():
    force_run = "--force" in sys.argv
    config = load_config()
    state = load_state()
    
    # 預設監控時段與設定
    start_hour = config.get("start_hour", 0)
    end_hour = config.get("end_hour", 24)
    frequency = config.get("frequency", 60)
    threshold = config.get("temperature_threshold", 28.0)
    
    # 1. 嘗試從 Google 試算表載入最新聯絡人名冊與系統參數設定
    spreadsheet_id = config.get("spreadsheet_id", "")
    sheet_recipients = {"emails": [], "line_ids": []}
    threshold_override = None
    config_overrides = {}
    
    if spreadsheet_id:
        token, _ = _get_firebase_token()
        if token:
            try:
                sheet_recipients, threshold_override = fetch_recipients_from_google_sheet_api(token, spreadsheet_id)
                config_overrides = fetch_system_config_from_google_sheet_api(token, spreadsheet_id)
            except Exception as e:
                print(f"【警告】動態載入雲端設定失敗: {e}", file=sys.stderr)
        else:
            print("【警告】找不到憑證 Token，無法使用 Google Sheets API，嘗試備用 CSV 機制...")
            sheet_recipients, threshold_override = fetch_recipients_from_google_sheet(config.get("google_sheet_csv_url", ""))
    else:
        sheet_recipients, threshold_override = fetch_recipients_from_google_sheet(config.get("google_sheet_csv_url", ""))
        
    # 套用雲端覆蓋參數設定
    if threshold_override is not None:
        config["temperature_threshold"] = threshold_override
        threshold = threshold_override
    if "start_hour" in config_overrides:
        config["start_hour"] = config_overrides["start_hour"]
        start_hour = config_overrides["start_hour"]
    if "end_hour" in config_overrides:
        config["end_hour"] = config_overrides["end_hour"]
        end_hour = config_overrides["end_hour"]
    if "frequency" in config_overrides:
        config["frequency"] = config_overrides["frequency"]
        frequency = config_overrides["frequency"]

    # 2. 檢查目前是否在監測時段內 (支援跨日排程，例如 08:00 - 24:00 或 22:00 - 06:00)
    tz_taiwan = datetime.timezone(datetime.timedelta(hours=8))
    current_hour = datetime.datetime.now(tz_taiwan).hour
    
    is_in_time_window = False
    if start_hour < end_hour:
        is_in_time_window = (start_hour <= current_hour < end_hour)
    else:
        is_in_time_window = (current_hour >= start_hour or current_hour < end_hour)
        
    if not is_in_time_window and not force_run:
        print(f"目前時間為 {current_hour:02d}:00，不在監測時段 ({start_hour:02d}:00 - {end_hour:02d}:00) 內，跳過監測。")
        sys.exit(0)
    
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
        
    # 同時備份寫入 Google Drive 雲端同步目錄（自動以日期分檔，若失敗則退回本機目錄）
    try:
        realtime_csv_path, realtime_xlsx_path, sheet_name = get_realtime_backup_paths()
        now_time_str = datetime.datetime.now(tz_taiwan).strftime('%Y-%m-%d %H:%M:%S')
        headers = ["記錄時間", "環境溫度 (°C)", "氣象觀測時間", "時間戳 (ms)"]
        now_ms = int(time.time() * 1000)
        append_to_local_csv(realtime_csv_path, headers, [now_time_str, current_temp, display_time, now_ms])
        append_to_monthly_xlsx(realtime_xlsx_path, sheet_name, headers, [now_time_str, current_temp, display_time, now_ms])
    except Exception as e:
        print(f"【本機備份警告】寫入即時溫度備份失敗: {e}", file=sys.stderr)
        
    # 4. 更新即時狀態 (儀表板溫度計與在線心跳指標)
    try:
        send_heartbeat_firebase(
            current_temp=current_temp,
            threshold=threshold,
            obs_time=display_time,
            alert_state="正常 (未超標)" if current_temp <= threshold else "高溫超標警報",
            status_text="即時觀測更新"
        )
        # 寫入本機心跳明細紀錄 (10分鐘頻率，與 24小時紀錄同步)
        try:
            now_time_str = datetime.datetime.now(tz_taiwan).strftime('%Y-%m-%d %H:%M:%S')
            headers = ["通報時間", "溫度設定 (°C)", "通報環境溫度 (°C)", "氣象觀測時間", "警報狀態", "通知狀態"]
            append_to_local_csv(LOCAL_HEARTBEAT_CSV, headers, 
                [now_time_str, threshold, current_temp, display_time, 
                 "正常 (未超標)" if current_temp <= threshold else "高溫超標警報", "即時觀測更新"])
            append_to_local_xlsx(LOCAL_HEARTBEAT_XLSX, headers, 
                [now_time_str, threshold, current_temp, display_time, 
                 "正常 (未超標)" if current_temp <= threshold else "高溫超標警報", "即時觀測更新"])
        except Exception as e:
            print(f"【本機備份警告】寫入本地心跳明細紀錄失敗: {e}", file=sys.stderr)

        # 同時發送即時心跳與觀測數據給 GAS，更新 GAS 在線時間並由 GAS 寫入 24 小時紀錄
        web_app_url = config.get("web_app_url", "")
        if web_app_url:
            send_heartbeat(web_app_url, sync_type="heartbeat",
                current_temp=current_temp, threshold=threshold,
                obs_time=display_time, alert_state="正常 (未超標)" if current_temp <= threshold else "高溫超標警報",
                status_text="即時觀測更新")
    except Exception as e:
        print(f"【警告】更新即時心跳失敗: {e}", file=sys.stderr)
        
    # 5. 進行本機排程自動節流 (僅節流通知與試算表寫入)
    if not force_run:
        now_time = datetime.datetime.now(tz_taiwan)
        # 如果設定為每小時 (60 分鐘) 執行，且當前分鐘不在 58 分附近，直接節流跳過主流程
        if frequency == 60 and not (55 <= now_time.minute <= 59):
            print(f"【時間未到】每小時排程設定於 58 分執行。當前為 {now_time.minute} 分，跳過主通報流程。已更新即時溫度。")
            sys.exit(0)
            
        last_run_str = state.get("last_run_time")
        if last_run_str:
            try:
                last_run_time = datetime.datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz_taiwan)
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
    # 已於 main() 開頭完成載入，此處直接使用已下載的 sheet_recipients 與 threshold
    
    # 合併並去除重複 (新增自動分割逗號、提取 Name <email> 中乾淨 Email 的防錯機制)
    import email.utils
    cleaned_emails = []
    raw_emails_pool = local_emails + sheet_recipients["emails"]
    for raw_item in raw_emails_pool:
        if not raw_item:
            continue
        # 如果單一字串中含有多個逗號隔開的 Email，自動分割
        parts = raw_item.split(",") if isinstance(raw_item, str) else [raw_item]
        for part in parts:
            part_str = str(part).strip()
            if part_str:
                _, addr = email.utils.parseaddr(part_str)
                # 如果 parseaddr 成功解析出 @，則使用解析出的乾淨 Email；否則當作普通字串處理
                addr = addr.strip() if (addr and "@" in addr) else part_str
                if addr and "@" in addr and "RECIPIENT_EMAIL" not in addr and "YOUR_EMAIL" not in addr:
                    cleaned_emails.append(addr)
                    
    final_emails = list(set(cleaned_emails))
    final_line_ids = list(set(local_line_ids + sheet_recipients["line_ids"]))
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
        # 已於 10 分鐘即時更新處同步寫入本地心跳明細，此處不再重複寫入
        pass
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
    teams_sent = False
    
    # 發送 LINE
    if config.get("line", {}).get("enabled", True) and final_line_ids:
        line_sent = send_line_notifications(config["line"], notify_body, final_line_ids)
        
    # 發送 Email
    if config.get("email", {}).get("enabled", True) and final_emails:
        email_sent = send_email_notifications(config["email"], notify_subject, notify_body, final_emails)
        
    # 發送 Teams
    if config.get("teams", {}).get("enabled", True) and config.get("teams", {}).get("webhook_url"):
        teams_sent = send_teams_notifications(config["teams"], notify_subject, notify_body)
        
    # 若成功發送任一通知，更新狀態防止重複發送
    if line_sent or email_sent or teams_sent:
        new_state = "HOT" if is_hot else "COOL"
        save_state(new_state)
        print("狀態已更新，記錄前次狀態。")
        status_text_list = []
        if line_sent: status_text_list.append("LINE")
        if email_sent: status_text_list.append("Email")
        if teams_sent: status_text_list.append("Teams")
        status_str = " & ".join(status_text_list) + " 已發送" if status_text_list else "發送失敗"
        alert_str = "高溫超標警報" if is_hot else "溫度回落正常"
        print("正在向 Firebase 同步更新後的警報狀態...")
        # 直接寫 Firebase
        send_heartbeat_firebase(
            current_temp=current_temp, threshold=threshold,
            obs_time=display_time, alert_state=alert_str,
            status_text=status_str
        )
        # 寫入本機歷史通報紀錄
        try:
            headers = ["通報時間", "溫度設定 (°C)", "通報環境溫度 (°C)", "氣象觀測時間", "警報狀態", "通知狀態"]
            append_to_local_csv(LOCAL_NOTIFY_CSV, headers, 
                [formatted_time, threshold, current_temp, display_time, alert_str, status_str])
            append_to_local_xlsx(LOCAL_NOTIFY_XLSX, headers, 
                [formatted_time, threshold, current_temp, display_time, alert_str, status_str])
        except Exception as e:
            print(f"【本機備份警告】寫入本地通報歷史紀錄失敗: {e}", file=sys.stderr)
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
        # 寫入本機歷史通報紀錄
        try:
            headers = ["通報時間", "溫度設定 (°C)", "通報環境溫度 (°C)", "氣象觀測時間", "警報狀態", "通知狀態"]
            append_to_local_csv(LOCAL_NOTIFY_CSV, headers, 
                [formatted_time, threshold, current_temp, display_time, alert_str2, "發送失敗"])
            append_to_local_xlsx(LOCAL_NOTIFY_XLSX, headers, 
                [formatted_time, threshold, current_temp, display_time, alert_str2, "發送失敗"])
        except Exception as e:
            print(f"【本機備份警告】寫入本地通報歷史紀錄失敗: {e}", file=sys.stderr)
        if web_app_url:
            send_heartbeat(web_app_url, sync_type="heartbeat",
                current_temp=current_temp, threshold=threshold,
                obs_time=display_time, alert_state=alert_str2,
                status_text="發送失敗")

if __name__ == "__main__":
    main()

```
