import os
import sys
import socket
import json
import zipfile
from io import BytesIO
from datetime import datetime
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
import qrcode
from PIL import Image
from fastapi import FastAPI, Form, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# ================= 1. IP 與 Port 自動取得 (Rule 6 規範) =================

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port: int, max_attempts: int = 50) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port

# ================= 2. 核心業務邏輯 (批號解析與對照) =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "台積電槽車barcode三合一單-範本.xlsx")
MAPPING_PATH = os.path.join(BASE_DIR, "地點代號對照表.xlsx")

def load_location_mapping():
    mapping = {
        "15P5": "E1550155A",
        "15P6": "E1550156A",
        "18P3B": "EF180183B",
        "12P7": "E00700001"
    }
    if os.path.exists(MAPPING_PATH):
        try:
            wb = openpyxl.load_workbook(MAPPING_PATH, data_only=True)
            ws = wb.active
            for row in ws.iter_rows(values_only=True):
                if row and len(row) >= 2 and row[0] and row[1]:
                    k = str(row[0]).strip().upper()
                    v = str(row[1]).strip()
                    if "地點" in k or "代號" in k or "SHORT" in k:
                        continue
                    mapping[k] = v
            wb.close()
        except Exception as e:
            print(f"警告: 讀取地點對照表失敗: {e}")
    return mapping

def extract_tank_from_batch(batch_no: str) -> str:
    batch = batch_no.strip().upper()
    if len(batch) != 10:
        return ""
    if batch.endswith("J1"):
        return batch[5:8]
    return batch[5:9]

# ================= 3. FastAPI Web 應用程式 =================

app = FastAPI(title="台積電槽車 Barcode 三合一單專用架機伺服器")

@app.get("/api/mapping")
def get_mapping():
    mapping = load_location_mapping()
    return JSONResponse({"status": "success", "count": len(mapping), "data": mapping})

# 1. 一鍵打包產生所有報表 ZIP (與 BAT 產出完全相同)
@app.post("/api/generate_all_zip")
async def generate_all_zip(request: Request):
    try:
        data_json = await request.json()
        records = data_json.get("records", [])
        do_3in1 = data_json.get("do3in1", True)
        do_transport = data_json.get("doTransport", True)

        if not records:
            raise HTTPException(status_code=400, detail="請至少提供一筆有效的排程資料。")

        mapping = load_location_mapping()
        zip_buffer = BytesIO()

        today_str = datetime.now().strftime('%Y%m%d')
        folder_name = f"三合一單輸出_{today_str}"

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 1. 產生三合一單 Excel 報表
            if do_3in1 and os.path.exists(TEMPLATE_PATH):
                for item in records:
                    batch = item.get("batch", "").strip().upper()
                    loc = item.get("loc", "").strip().upper()
                    if not batch or not loc or len(batch) != 10 or loc not in mapping:
                        continue

                    loc_code = mapping[loc]
                    tank_no = extract_tank_from_batch(batch)
                    tank_with_prefix = "5" + tank_no
                    batch_with_prefix = "6" + batch

                    wb = openpyxl.load_workbook(TEMPLATE_PATH)
                    ws = wb.active

                    ws['C5'] = tank_with_prefix
                    ws['C7'] = batch_with_prefix
                    ws['C11'] = loc_code

                    mat_no = str(ws['C3'].value or "4L12C53161").strip()
                    sup_no = str(ws['C9'].value or "375970680").strip()
                    qr_str = f"||{mat_no}||{tank_with_prefix}||{batch_with_prefix}||{sup_no}||{loc_code}"
                    ws['B20'] = qr_str

                    # 清除舊圖片
                    images_to_keep = [img for img in ws._images if not (0.8 < (img.width/img.height if img.height>0 else 1) < 1.2 and img.width < 300)]
                    ws._images = images_to_keep

                    # 生成 QR Code PNG
                    qr = qrcode.QRCode(box_size=4, border=2)
                    qr.add_data(qr_str)
                    qr.make(fit=True)
                    raw_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

                    offset_x, offset_y = 35, 25
                    img_qr = Image.new('RGB', (raw_img.width + offset_x, raw_img.height + offset_y), 'white')
                    img_qr.paste(raw_img, (offset_x, offset_y))

                    img_io = BytesIO()
                    img_qr.save(img_io, format='PNG')
                    img_io.seek(0)

                    new_qr = OpenpyxlImage(img_io)
                    new_qr.anchor = 'F2'
                    ws.add_image(new_qr)

                    excel_io = BytesIO()
                    wb.save(excel_io)
                    wb.close()
                    excel_io.seek(0)

                    # 檔名公式：[出貨日期]. [地點]_[槽號]_台積電槽車barcode三合一單.xlsx
                    date_prefix = f"{datetime.now().year}.{datetime.now().month}.{datetime.now().day}. "
                    file_name = f"{date_prefix}{loc}_{tank_no}_台積電槽車barcode三合一單.xlsx"
                    zip_file.writestr(f"{folder_name}/{file_name}", excel_io.getvalue())

            # 2. 產生獨立運輸通知表 Excel
            if do_transport:
                wb_t = openpyxl.Workbook()
                ws_t = wb_t.active
                ws_t.title = "運輸通知"
                r = 1
                weekdays = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]

                for item in records:
                    batch = item.get("batch", "")
                    loc = item.get("loc", "")
                    tank = item.get("tank", "")
                    date_str = item.get("date") or datetime.now().strftime("%Y-%m-%d")
                    time_str = item.get("time", "")
                    mod_time_str = item.get("modTime", "")
                    has_mod = bool(mod_time_str)

                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        w_str = weekdays[dt.weekday() + 1 if dt.weekday() < 6 else 0]
                    except Exception:
                        w_str = ""

                    title_text = "Shiny IPA Lorry\n(料號：L12C53161) 出貨排程通知"
                    mod_title_text = "Shiny IPA Lorry\n(料號：L12C53161) 出貨排程修正通知"

                    ws_t.cell(row=r, column=1, value=title_text)
                    ws_t.cell(row=r, column=4, value="廠區")
                    ws_t.cell(row=r, column=5, value="槽號")
                    ws_t.cell(row=r, column=6, value=date_str)

                    ws_t.cell(row=r+1, column=1, value="IPA")
                    ws_t.cell(row=r+1, column=4, value=f"台積\n{loc}")
                    ws_t.cell(row=r+1, column=5, value=tank)
                    ws_t.cell(row=r+1, column=6, value=w_str)

                    ws_t.cell(row=r+2, column=1, value="IPA")
                    ws_t.cell(row=r+2, column=2, value="預計到廠時間")
                    ws_t.cell(row=r+2, column=4, value=f"台積\n{loc}")
                    ws_t.cell(row=r+2, column=5, value=tank)
                    ws_t.cell(row=r+2, column=6, value=f"~{time_str}~" if has_mod else time_str)

                    ws_t.cell(row=r+3, column=1, value="IPA")
                    ws_t.cell(row=r+3, column=2, value="修正到廠時間")
                    ws_t.cell(row=r+3, column=4, value=f"台積\n{loc}")
                    ws_t.cell(row=r+3, column=5, value=tank)
                    ws_t.cell(row=r+3, column=6, value=mod_time_str if has_mod else "")

                    ws_t.cell(row=r+4, column=1, value="IPA")
                    ws_t.cell(row=r+4, column=2, value="充填數量(KG)")
                    ws_t.cell(row=r+4, column=4, value=f"台積\n{loc}")
                    ws_t.cell(row=r+4, column=5, value=tank)
                    ws_t.cell(row=r+4, column=6, value="4300")

                    ws_t.cell(row=r+5, column=1, value="IPA")
                    ws_t.cell(row=r+5, column=2, value="PFA 500ml 取樣瓶裝原液 8 分滿放置工具箱內")
                    ws_t.cell(row=r+5, column=6, value="6 支")

                    ws_t.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
                    ws_t.merge_cells(start_row=r+1, start_column=1, end_row=r+4, end_column=1)
                    ws_t.merge_cells(start_row=r+2, start_column=2, end_row=r+2, end_column=3)
                    ws_t.merge_cells(start_row=r+3, start_column=2, end_row=r+3, end_column=3)
                    ws_t.merge_cells(start_row=r+4, start_column=2, end_row=r+4, end_column=3)
                    ws_t.merge_cells(start_row=r+1, start_column=4, end_row=r+4, end_column=4)
                    ws_t.merge_cells(start_row=r+1, start_column=5, end_row=r+4, end_column=5)
                    ws_t.merge_cells(start_row=r+5, start_column=2, end_row=r+5, end_column=5)

                    if has_mod:
                        ws_t.cell(row=r, column=8, value=mod_title_text)
                        ws_t.cell(row=r, column=11, value="廠區")
                        ws_t.cell(row=r, column=12, value="槽號")
                        ws_t.cell(row=r, column=13, value=date_str)

                        ws_t.cell(row=r+1, column=8, value="IPA")
                        ws_t.cell(row=r+1, column=11, value=f"台積\n{loc}")
                        ws_t.cell(row=r+1, column=12, value=tank)
                        ws_t.cell(row=r+1, column=13, value=w_str)

                        ws_t.cell(row=r+2, column=8, value="IPA")
                        ws_t.cell(row=r+2, column=9, value="預計到廠時間")
                        ws_t.cell(row=r+2, column=11, value=f"台積\n{loc}")
                        ws_t.cell(row=r+2, column=12, value=tank)
                        ws_t.cell(row=r+2, column=13, value=f"~{time_str}~")

                        ws_t.cell(row=r+3, column=8, value="IPA")
                        ws_t.cell(row=r+3, column=9, value="修正到廠時間")
                        ws_t.cell(row=r+3, column=11, value=f"台積\n{loc}")
                        ws_t.cell(row=r+3, column=12, value=tank)
                        ws_t.cell(row=r+3, column=13, value=mod_time_str)

                        ws_t.cell(row=r+4, column=8, value="IPA")
                        ws_t.cell(row=r+4, column=9, value="充填數量(KG)")
                        ws_t.cell(row=r+4, column=11, value=f"台積\n{loc}")
                        ws_t.cell(row=r+4, column=12, value=tank)
                        ws_t.cell(row=r+4, column=13, value="4300")

                        ws_t.cell(row=r+5, column=8, value="IPA")
                        ws_t.cell(row=r+5, column=9, value="PFA 500ml 取樣瓶裝原液 8 分滿放置工具箱內")
                        ws_t.cell(row=r+5, column=13, value="6 支")

                        ws_t.merge_cells(start_row=r, start_column=8, end_row=r, end_column=10)
                        ws_t.merge_cells(start_row=r+1, start_column=8, end_row=r+4, end_column=8)
                        ws_t.merge_cells(start_row=r+2, start_column=9, end_row=r+2, end_column=10)
                        ws_t.merge_cells(start_row=r+3, start_column=9, end_row=r+3, end_column=10)
                        ws_t.merge_cells(start_row=r+4, start_column=9, end_row=r+4, end_column=10)
                        ws_t.merge_cells(start_row=r+1, start_column=11, end_row=r+4, end_column=11)
                        ws_t.merge_cells(start_row=r+1, start_column=12, end_row=r+4, end_column=12)
                        ws_t.merge_cells(start_row=r+5, start_column=9, end_row=r+5, end_column=12)

                    r += 7

                t_io = BytesIO()
                wb_t.save(t_io)
                wb_t.close()
                t_io.seek(0)
                zip_file.writestr(f"{folder_name}/運輸通知表.xlsx", t_io.getvalue())

        zip_buffer.seek(0)
        zip_filename = f"{folder_name}.zip"

        from urllib.parse import quote
        encoded_filename = quote(zip_filename)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"一鍵打包產生失敗: {e}")

# 2. 智慧 OCR 辨識與文字解析 API
@app.post("/api/ocr_parse")
async def ocr_parse(file: UploadFile = File(...)):
    try:
        content = await file.read()
        extracted_records = []

        # 嘗試簡單文字與批號地點正規表示法解析
        text = ""
        try:
            text = content.decode("utf-8", "ignore")
        except Exception:
            text = str(content)

        import re
        # 尋找 10 碼批號模式與地點
        batches = re.findall(r'\b[0-9A-Z]{10}\b', text.upper())
        mapping = load_location_mapping()

        found_locs = []
        for word in text.upper().split():
            clean_w = re.sub(r'[^A-Z0-9]', '', word)
            if clean_w in mapping:
                found_locs.append(clean_w)

        for i, b in enumerate(batches):
            loc_val = found_locs[i] if i < len(found_locs) else "18P3B"
            tank_val = extract_tank_from_batch(b)
            extracted_records.append({
                "batch": b,
                "tank": tank_val,
                "loc": loc_val
            })

        return JSONResponse({
            "status": "success",
            "count": len(extracted_records),
            "records": extracted_records
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 解析失敗: {e}")

static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    port = find_available_port(8002)
    local_ip = get_local_ip()
    print("=" * 60)
    print(f"🚀 台積電槽車 Barcode 專用架機伺服器已成功啟動！")
    print(f"👉 本機連線網址：http://localhost:{port}")
    print(f"👉 區域網路網址 (提供同仁免裝 Python 開啟)：http://{local_ip}:{port}")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
