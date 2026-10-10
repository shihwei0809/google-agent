import os
import shutil
import sqlite3
import socket
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import openpyxl

app = FastAPI(title="回收液入料記錄系統")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "data"
PHOTOS_DIR = os.path.join(DATA_DIR, "photos")
DB_PATH = os.path.join(DATA_DIR, "records.db")

os.makedirs(PHOTOS_DIR, exist_ok=True)

# 靜態檔案
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/photos", StaticFiles(directory=PHOTOS_DIR), name="photos")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            license_plate TEXT NOT NULL,
            tank_level_before_photo TEXT,
            vehicle_photo TEXT,
            tank_level_after_photo TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, license_plate)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_gdrive_path():
    import string
    available_drives = ['%s:' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]
    for drive in available_drives:
        for folder_name in ["我的雲端硬碟", "My Drive"]:
            test_path = os.path.join(drive, folder_name)
            if os.path.exists(test_path):
                return test_path
    return None

def upload_to_gdrive(record_id: int):
    """
    自動判斷：
    1. 如果有 `service_account.json`，則使用 Google API 上傳到線上雲端硬碟與 Google Sheets (適合線上伺服器)
    2. 如果沒有，則退回使用本機掛載路徑複製檔案 (適合本機伺服器)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return
        
    date, license_plate = row[1], row[2]
    photos = [row[3], row[4], row[5]]
    
    # 模式 1: 線上伺服器 API 模式 (需要 service_account.json)
    if os.path.exists("service_account.json"):
        try:
            print("偵測到 service_account.json，使用 Google API 上傳模式...")
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            import gspread

            SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
            
            # 1. 寫入 Google Sheets (請將下方的試算表 ID 換成您真實的 ID)
            # SHEET_ID = "您的_GOOGLE_SHEET_ID"
            # gc = gspread.authorize(creds)
            # sh = gc.open_by_key(SHEET_ID)
            # worksheet = sh.sheet1
            # worksheet.append_row([row[0], row[1], row[2], row[3], row[4], row[5], row[7]])
            
            # 2. 上傳照片到 Google Drive (請將下方的資料夾 ID 換成您真實的 ID)
            # DRIVE_FOLDER_ID = "您的_GOOGLE_DRIVE_資料夾_ID"
            drive_service = build('drive', 'v3', credentials=creds)
            
            for p in photos:
                if p and os.path.exists(os.path.join(PHOTOS_DIR, p)):
                    file_metadata = {'name': p} # , 'parents': [DRIVE_FOLDER_ID]
                    media = MediaFileUpload(os.path.join(PHOTOS_DIR, p), mimetype='image/jpeg')
                    # drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            
            print(f"紀錄 {record_id} 已透過 API 上傳完成！(請記得解除註解並填入 ID)")
            return
        except Exception as e:
            print(f"API 上傳發生錯誤: {e}")

    # 模式 2: 本機伺服器模式 (複製到 Google Drive Desktop)
    print("未偵測到 service_account.json，嘗試使用本機掛載路徑備份...")
    try:
        gdrive_root = get_gdrive_path()
        if not gdrive_root:
            print("找不到本機 Google Drive 掛載路徑，取消上傳")
            return
            
        target_dir = os.path.join(gdrive_root, "GOOGLE ANGET", "回收液入料記錄_上傳區")
        photos_target_dir = os.path.join(target_dir, "photos")
        os.makedirs(photos_target_dir, exist_ok=True)
        
        for p in photos:
            if p:
                src = os.path.join(PHOTOS_DIR, p)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(photos_target_dir, p))
                    
        excel_path = os.path.join(target_dir, "入料記錄總表.xlsx")
        if not os.path.exists(excel_path):
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["ID", "日期", "車號", "入料前照片", "車輛照片", "入料後照片", "建立時間"])
        else:
            wb = openpyxl.load_workbook(excel_path)
            ws = wb.active
            
        ws.append([row[0], row[1], row[2], row[3], row[4], row[5], row[7]])
        wb.save(excel_path)
        print(f"紀錄 {record_id} ({license_plate}) 已自動上傳至本機 Google Drive！")
        
    except Exception as e:
        print(f"本機上傳 Google Drive 發生錯誤: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/before_feed")
async def before_feed(
    date: str = Form(...),
    license_plate: str = Form(...),
    tank_level_before: UploadFile = File(...),
    vehicle_photo: UploadFile = File(...)
):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM records WHERE date = ? AND license_plate = ?", (date, license_plate))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="此日期與車號已登錄過！")

        timestamp = datetime.now().strftime("%Y%md%H%M%S")
        tl_filename = f"before_{date}_{license_plate}_{timestamp}_{tank_level_before.filename}"
        v_filename = f"vehicle_{date}_{license_plate}_{timestamp}_{vehicle_photo.filename}"
        
        with open(os.path.join(PHOTOS_DIR, tl_filename), "wb") as buffer:
            shutil.copyfileobj(tank_level_before.file, buffer)
            
        with open(os.path.join(PHOTOS_DIR, v_filename), "wb") as buffer:
            shutil.copyfileobj(vehicle_photo.file, buffer)

        cursor.execute('''
            INSERT INTO records (date, license_plate, tank_level_before_photo, vehicle_photo, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (date, license_plate, tl_filename, v_filename))
        conn.commit()
        conn.close()
        return {"success": True, "message": "入料前資料已暫存"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pending_records")
async def get_pending_records():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM records WHERE status = 'pending' ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return {"records": [dict(row) for row in rows]}

@app.post("/api/after_feed/{record_id}")
async def after_feed(
    record_id: int, 
    background_tasks: BackgroundTasks,
    tank_level_after: UploadFile = File(...)
):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT date, license_plate FROM records WHERE id = ? AND status = 'pending'", (record_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="找不到該筆待入料紀錄")
        
        date, license_plate = row
        timestamp = datetime.now().strftime("%Y%md%H%M%S")
        after_filename = f"after_{date}_{license_plate}_{timestamp}_{tank_level_after.filename}"
        
        with open(os.path.join(PHOTOS_DIR, after_filename), "wb") as buffer:
            shutil.copyfileobj(tank_level_after.file, buffer)

        cursor.execute('''
            UPDATE records 
            SET tank_level_after_photo = ?, status = 'completed'
            WHERE id = ?
        ''', (after_filename, record_id))
        conn.commit()
        conn.close()
        
        # 背景執行 Google Drive 上傳，避免前端卡住
        background_tasks.add_task(upload_to_gdrive, record_id)
        
        return {"success": True, "message": "入料後資料已儲存並背景上傳中"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == "__main__":
    import uvicorn
    import socket
    port = 8000
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
            break
        except OSError:
            print(f"預設 Port {port} 已被佔用，切換至 {port+1}")
            port += 1
            
    ip = get_ip()
    print(f"==================================================")
    print(f"啟動成功！請在瀏覽器或手機開啟: http://{ip}:{port}")
    print(f"==================================================")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
