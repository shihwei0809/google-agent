import traceback
import os
import sys
import socket
import json
import zipfile
from io import BytesIO
from datetime import datetime, date
from copy import copy
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.utils.units import pixels_to_EMU
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.cell.rich_text import TextBlock, CellRichText
from openpyxl.cell.text import InlineFont
import qrcode
from PIL import Image
from fastapi import FastAPI, Form, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List
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


# ================= 1.5. 本機 Tesseract OCR 自動偵測 =================
import shutil as _shutil

def _auto_detect_tesseract():
    """自動偵測本機 tesseract.exe，回傳路徑或 None"""
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
        r"D:\Tesseract-OCR\tesseract.exe",
    ]
    from_path = _shutil.which("tesseract")
    if from_path:
        candidates.insert(0, from_path)
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None

TESSERACT_EXE = _auto_detect_tesseract()
TESSERACT_AVAILABLE = TESSERACT_EXE is not None

if TESSERACT_AVAILABLE:
    try:
        import pytesseract as _pytes
        _pytes.pytesseract.tesseract_cmd = TESSERACT_EXE
        print(f"[OCR] Local Tesseract found: {TESSERACT_EXE}")
    except ImportError:
        TESSERACT_AVAILABLE = False
        print("[OCR] tesseract.exe found but pytesseract not installed")
else:
    print("[OCR] No local Tesseract, using frontend OCR + geometric crop")

def backend_ocr_batch(img_pil):
    """用本機 Tesseract 辨識圖片，回傳字詞 list（含座標）"""
    if not TESSERACT_AVAILABLE:
        return []
    try:
        import pytesseract
        data = pytesseract.image_to_data(img_pil, lang="eng", config="--psm 6",
                                         output_type=pytesseract.Output.DICT)
        results = []
        for i, word in enumerate(data["text"]):
            word = word.strip()
            if word and data["conf"][i] > 30:
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                results.append({
                    "text": word.upper(), "left": x, "top": y,
                    "right": x + w, "bottom": y + h,
                })
        return results
    except Exception as e:
        print(f"[OCR] 後端 OCR 失敗: {e}")
        return []

# ================= 2. 核心業務邏輯 (批號解析與對照) =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "台積電槽車barcode三合一單-範本.xlsx")
MAPPING_PATH = os.path.join(BASE_DIR, "地點代號對照表.xlsx")

def get_all_mapping_file_paths():
    return [
        os.path.join(BASE_DIR, "地點代號對照表.xlsx"),
        os.path.abspath(os.path.join(BASE_DIR, "..", "三合一單自動產生器", "地點代號對照表.xlsx")),
        os.path.abspath(os.path.join(BASE_DIR, "..", "勝一三合一單產生系統", "地點代號對照表.xlsx")),
    ]

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
                    if any(kw in k for kw in ("地點", "代號", "SHORT", "LOCATION", "KEY", "簡稱")):
                        continue
                    mapping[k] = v
            wb.close()
        except Exception as e:
            print(f"警告: 讀取地點對照表失敗: {e}")
    return mapping

def save_location_mapping_to_excel(loc: str, code: str):
    loc = loc.strip().upper()
    code = code.strip().upper()
    paths = get_all_mapping_file_paths()
    saved_count = 0
    for file_path in paths:
        try:
            if os.path.exists(file_path):
                wb = openpyxl.load_workbook(file_path)
                ws = wb.active
                updated = False
                for r in range(2, ws.max_row + 1):
                    val = ws.cell(row=r, column=1).value
                    if val is not None and str(val).strip().upper() == loc:
                        ws.cell(row=r, column=2, value=code)
                        updated = True
                        break
                if not updated:
                    ws.append([loc, code])
                wb.save(file_path)
                wb.close()
                saved_count += 1
            else:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "工作表1"
                ws.append(["短地點", "長代號"])
                ws.append([loc, code])
                wb.save(file_path)
                wb.close()
                saved_count += 1
        except Exception as e:
            print(f"寫入地點對照表至 {file_path} 失敗: {e}")
    return saved_count

def delete_location_from_excel(loc: str):
    loc = loc.strip().upper()
    paths = get_all_mapping_file_paths()
    for file_path in paths:
        if os.path.exists(file_path):
            try:
                wb = openpyxl.load_workbook(file_path)
                ws = wb.active
                target_row = None
                for r in range(2, ws.max_row + 1):
                    val = ws.cell(row=r, column=1).value
                    if val is not None and str(val).strip().upper() == loc:
                        target_row = r
                        break
                if target_row:
                    ws.delete_rows(target_row, 1)
                    wb.save(file_path)
                wb.close()
            except Exception as e:
                print(f"自 {file_path} 刪除地點失敗: {e}")

def extract_tank_from_batch(batch_no: str) -> str:
    batch = batch_no.strip().upper()
    if len(batch) != 10:
        return ""
    if batch.endswith("J1"):
        return batch[5:8]
    return batch[5:9]

def normalize_time_str(raw):
    """
    將時間字串統一為 4 碼純數字 (如 0900, 1400, 1630)，排除日期與星期字串。
    """
    if raw is None or raw == "":
        return ""
    if hasattr(raw, "hour") and hasattr(raw, "minute"):
        return f"{raw.hour:02d}{raw.minute:02d}"
    s = str(raw).strip()
    if not s:
        return ""
    import re
    m = re.search(r'(\d{1,2}):(\d{2})', s)
    if m:
        return f"{int(m.group(1)):02d}{int(m.group(2)):02d}"
    if len(s) == 4 and s.isdigit():
        return s
    if len(s) == 3 and s.isdigit():
        return "0" + s
    return s

def build_single_row_lorry_workbook(src_ws, target_row, max_cols=30):
    new_wb = openpyxl.Workbook()
    new_ws = new_wb.active
    new_ws.title = src_ws.title
    
    # 複製欄寬
    for col_letter, col_dim in src_ws.column_dimensions.items():
        if col_dim.width:
            new_ws.column_dimensions[col_letter].width = col_dim.width
            
    def copy_cell(s_cell, d_cell):
        d_cell.value = s_cell.value
        if s_cell.has_style:
            d_cell.font = copy(s_cell.font)
            d_cell.border = copy(s_cell.border)
            d_cell.fill = copy(s_cell.fill)
            d_cell.number_format = copy(s_cell.number_format)
            d_cell.protection = copy(s_cell.protection)
            d_cell.alignment = copy(s_cell.alignment)

    # 複製列高 (保持第 6 列表頭與資料列原始高度)
    for r in range(1, 8):
        src_r = r if r <= 6 else target_row
        if src_ws.row_dimensions[src_r].height:
            new_ws.row_dimensions[r].height = src_ws.row_dimensions[src_r].height

    # 複製 1~6 列表頭
    for r in range(1, 7):
        for c in range(1, max_cols + 1):
            copy_cell(src_ws.cell(r, c), new_ws.cell(r, c))
            
    # 複製目標資料列至第 7 列
    for c in range(1, max_cols + 1):
        copy_cell(src_ws.cell(target_row, c), new_ws.cell(7, c))
        
    # 自動智慧調整欄寬，確保所有欄位表頭與資料完整顯示不被遮擋
    for col_idx in range(1, max_cols + 1):
        col_letter = get_column_letter(col_idx)
        max_len = 0
        for r in range(1, 8):
            val = new_ws.cell(r, col_idx).value
            if val is not None:
                if isinstance(val, (datetime, date)):
                    s = val.strftime('%Y/%m/%d')
                else:
                    s = str(val).strip()
                lines = s.split('\n')
                for line in lines:
                    line_len = sum(2.0 if ord(ch) > 127 else 1.15 for ch in line)
                    if line_len > max_len:
                        max_len = line_len
        if max_len > 0:
            # 依最長文字加上留白邊界 (+4.0)，至少 13.0
            adjusted_width = max(max_len + 4.0, 13.0)
            orig_w = new_ws.column_dimensions[col_letter].width
            if orig_w and orig_w > adjusted_width:
                adjusted_width = orig_w
            new_ws.column_dimensions[col_letter].width = round(adjusted_width, 1)

    # 確保第 6 列表頭高度 (28.0) 與第 7 列資料列高度 (22.0) 呼吸空間
    new_ws.row_dimensions[6].height = 28.0
    new_ws.row_dimensions[7].height = 22.0

    return new_wb

def parse_tsmc_query_table_accurate(im):
    """
    精確解析台積電 Query Result 表格結構：
    自動掃描圖片下半部的水平灰色邊界線 (標準表格分隔線)，
    返回 (表頭底線 Y, [(第1列top, 第1列bot), (第2列top, 第2列bot), ...])
    """
    w, h = im.size
    grey_lines = []
    # 掃描從 h*0.3 到 h 的水平線
    for y in range(int(h * 0.3), h):
        sample_xs = range(int(w * 0.1), int(w * 0.9), 10)
        pixels = [im.getpixel((x, y)) for x in sample_xs]
        if all(abs(p[0]-p[1]) < 8 and abs(p[1]-p[2]) < 8 and 170 < p[0] < 240 for p in pixels):
            grey_lines.append(y)
    
    merged_lines = []
    for y in grey_lines:
        if not merged_lines or y - merged_lines[-1] > 5:
            merged_lines.append(y)

    if len(merged_lines) >= 2:
        row_intervals = []
        for i in range(len(merged_lines)-1, 0, -1):
            diff = merged_lines[i] - merged_lines[i-1]
            if 20 <= diff <= 55:
                row_intervals.insert(0, (merged_lines[i-1], merged_lines[i]))
            else:
                break
        if row_intervals:
            header_bottom = row_intervals[0][0]
            return header_bottom, row_intervals
            
    return int(h * 0.85), []

# ================= 3. FastAPI Web 應用程式 =================

app = FastAPI(title="台積電槽車 Barcode 三合一單專用架機伺服器")

@app.get("/api/mapping")
def get_mapping():
    mapping = load_location_mapping()
    return JSONResponse({"status": "success", "count": len(mapping), "data": mapping})

@app.post("/api/save_location")
async def api_save_location(request: Request):
    try:
        data = await request.json()
        loc = str(data.get("loc", "")).strip().upper()
        code = str(data.get("code", "")).strip().upper()
        if not loc or not code:
            raise HTTPException(status_code=400, detail="地點簡稱與長代號均不得為空！")
        
        save_location_mapping_to_excel(loc, code)
        mapping = load_location_mapping()
        return JSONResponse({
            "status": "success",
            "message": f"地點「{loc}」對應代碼「{code}」已成功回寫儲存至主機端對照表！",
            "loc": loc,
            "code": code,
            "count": len(mapping),
            "data": mapping
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回寫地點至電腦端失敗: {e}")

@app.post("/api/delete_location")
async def api_delete_location(request: Request):
    try:
        data = await request.json()
        loc = str(data.get("loc", "")).strip().upper()
        if not loc:
            raise HTTPException(status_code=400, detail="請指定欲刪除的地點簡稱！")
        
        delete_location_from_excel(loc)
        mapping = load_location_mapping()
        return JSONResponse({
            "status": "success",
            "message": f"地點「{loc}」已成功自電腦端對照表移除！",
            "count": len(mapping),
            "data": mapping
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除地點失敗: {e}")

def generate_transport_workbook(items, mat_no="L12C53161"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "運輸通知表"
    ws.views.sheetView[0].showGridLines = True
    
    col_widths = {
        'A': 8, 'B': 18, 'C': 18, 'D': 16, 'E': 14, 'F': 16,
        'G': 4,
        'H': 8, 'I': 18, 'J': 18, 'K': 16, 'L': 14, 'M': 16
    }
    for col, width in col_widths.items():
        ws.column_dimensions[col].width = width
    
    thin_border = Border(
        left=Side(style='thin', color='000000'),
        right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'),
        bottom=Side(style='thin', color='000000')
    )
    
    fill_yellow = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    fill_green = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    fill_bright_yellow = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    
    openpyxl_font_dark_blue = Font(name="Microsoft JhengHei", color="002060", size=11)
    openpyxl_font_dark_blue_b13 = Font(name="Microsoft JhengHei", color="002060", size=13, bold=True)
    openpyxl_font_strike_blue_b13 = Font(name="Microsoft JhengHei", color="002060", size=13, bold=True, strike=True)
    openpyxl_font_red_b13 = Font(name="Microsoft JhengHei", color="C00000", size=13, bold=True)
    openpyxl_font_dark_blue_b14 = Font(name="Microsoft JhengHei", color="002060", size=14, bold=True)
    
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

    def render_notice_card(start_r, start_c, is_modified_card, item):
        r1 = start_r
        r2 = start_r + 1
        r3 = start_r + 2
        r4 = start_r + 3
        r5 = start_r + 4
        r6 = start_r + 5
        
        c1 = start_c
        c2 = start_c + 1
        c3 = start_c + 2
        c4 = start_c + 3
        c5 = start_c + 4
        c6 = start_c + 5
        
        for r in range(r1, r6 + 1):
            ws.row_dimensions[r].height = 24 if r >= r3 else 22
            for c in range(c1, c6 + 1):
                cell = ws.cell(row=r, column=c)
                cell.border = thin_border
                cell.font = openpyxl_font_dark_blue
                cell.alignment = align_center

        ws.merge_cells(start_row=r1, start_column=c1, end_row=r2, end_column=c3)
        title_suffix = "出貨排程修正通知" if is_modified_card else "出貨排程通知"
        title_rt = CellRichText([
            TextBlock(InlineFont(color="002060", b=True, sz=12, rFont="Microsoft JhengHei"), "Shiny IPA Lorry\n"),
            TextBlock(InlineFont(color="002060", sz=10, rFont="Microsoft JhengHei"), f"(料號：{mat_no}) {title_suffix}")
        ])
        cell_a1 = ws.cell(row=r1, column=c1)
        cell_a1.value = title_rt
        cell_a1.fill = fill_yellow
        cell_a1.alignment = align_center
        
        cell_d1 = ws.cell(row=r1, column=c4, value="廠區")
        cell_d1.fill = fill_yellow
        cell_d1.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)
        
        cell_e1 = ws.cell(row=r1, column=c5, value="槽號")
        cell_e1.fill = fill_yellow
        cell_e1.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)
        
        date_raw = item.get("date", "").strip() if item.get("date") else datetime.now().strftime("%Y-%m-%d")
        formatted_date = ""
        weekday_str = ""
        if date_raw:
            dt = None
            date_part = date_raw.split()[0]
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%m/%d/%Y", "%d/%m/%Y"):
                try:
                    dt = datetime.strptime(date_part, fmt)
                    break
                except ValueError:
                    pass
            if dt:
                weekday_str = weekdays[dt.weekday()]
                formatted_date = f"{dt.year}/{dt.month}/{dt.day}"
            else:
                formatted_date = date_raw
        
        cell_f1 = ws.cell(row=r1, column=c6, value=formatted_date)
        cell_f1.fill = fill_green
        cell_f1.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)
        
        cell_f2 = ws.cell(row=r2, column=c6, value=weekday_str)
        cell_f2.fill = fill_green
        cell_f2.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)

        ws.merge_cells(start_row=r3, start_column=c1, end_row=r6, end_column=c1)
        cell_a3 = ws.cell(row=r3, column=c1, value="IPA")
        cell_a3.font = openpyxl_font_dark_blue_b14
        
        time_val = normalize_time_str(item.get("time", ""))
        mod_time_val = normalize_time_str(item.get("modTime", ""))
        
        ws.merge_cells(start_row=r3, start_column=c2, end_row=r3, end_column=c3)
        ws.cell(row=r3, column=c2, value="預計到廠時間")
        cell_f3 = ws.cell(row=r3, column=c6, value=time_val)
        
        ws.merge_cells(start_row=r4, start_column=c2, end_row=r4, end_column=c3)
        ws.cell(row=r4, column=c2, value="修正到廠時間")
        cell_f4 = ws.cell(row=r4, column=c6)
        
        if is_modified_card:
            cell_f3.font = openpyxl_font_strike_blue_b13
            cell_f4.value = mod_time_val
            cell_f4.font = openpyxl_font_red_b13
        else:
            cell_f3.font = openpyxl_font_dark_blue_b13
            cell_f4.value = ""
        
        ws.merge_cells(start_row=r5, start_column=c2, end_row=r5, end_column=c3)
        ws.cell(row=r5, column=c2, value="充填數量(KG)")
        ws.cell(row=r5, column=c6, value="4300")
        
        ws.merge_cells(start_row=r2, start_column=c4, end_row=r5, end_column=c4)
        full_loc = item.get("loc", "").strip() if item.get("loc") else ""
        
        d_rt = CellRichText([
            TextBlock(InlineFont(color="002060", b=True, sz=14, rFont="Microsoft JhengHei"), "台積\n"),
            TextBlock(InlineFont(color="C00000", b=True, sz=14, rFont="Microsoft JhengHei"), full_loc)
        ])
        cell_d2 = ws.cell(row=r2, column=c4)
        cell_d2.value = d_rt
        
        ws.merge_cells(start_row=r2, start_column=c5, end_row=r5, end_column=c5)
        cell_e2 = ws.cell(row=r2, column=c5, value=item.get("tank", "").strip() if item.get("tank") else "")
        cell_e2.font = openpyxl_font_dark_blue_b14
        cell_e2.fill = fill_bright_yellow
        
        ws.merge_cells(start_row=r6, start_column=c2, end_row=r6, end_column=c5)
        cell_b6 = ws.cell(row=r6, column=c2)
        cell_b6.value = CellRichText([
            TextBlock(InlineFont(color="C00000", b=True, sz=11, rFont="Microsoft JhengHei"), "PFA 500ml"),
            TextBlock(InlineFont(color="002060", sz=11, rFont="Microsoft JhengHei"), " 取樣瓶裝原液 8 分滿放置工具箱內")
        ])
        
        cell_f6 = ws.cell(row=r6, column=c6, value="6 支")
        cell_f6.font = Font(name="Microsoft JhengHei", color="002060", size=11, bold=True)

    curr_row = 1
    for item in items:
        render_notice_card(curr_row, 1, False, item)
        if item.get("modTime", "").strip():
            render_notice_card(curr_row, 8, True, item)
        curr_row += 7

    return wb

def parse_tsmc_query_table_accurate(coa_raw):
    w, h = coa_raw.size
    img_rgb = coa_raw.convert('RGB')
    query_result_y = None
    for y in range(int(h * 0.3), int(h * 0.9)):
        sample = [img_rgb.getpixel((x, y)) for x in range(int(w * 0.1), int(w * 0.9), max(1, int(w * 0.05)))]
        if sum(1 for p in sample if p[0] < 100 and p[1] < 160 and p[2] > 200) > len(sample) * 0.7:
            query_result_y = y
            break
    start_y = query_result_y if query_result_y else int(h * 0.5)
    btn_y_list = []
    for y in range(start_y + 20, h):
        sample = [img_rgb.getpixel((x, y)) for x in range(15, 65, 2)]
        blue_cnt = sum(1 for p in sample if p[0] < 60 and p[2] > 180)
        if blue_cnt >= 8:
            btn_y_list.append(y)
    btn_clusters = []
    for y in btn_y_list:
        if not btn_clusters or y > btn_clusters[-1][-1] + 5:
            btn_clusters.append([y])
        else:
            btn_clusters[-1].append(y)
    def find_border_line(start_y, direction, max_search=40):
        for step in range(max_search):
            curr_y = start_y + step * direction
            if curr_y <= 0 or curr_y >= h:
                break
            sample_xs = range(int(w * 0.2), int(w * 0.8), max(1, int(w * 0.05)))
            pixels = [img_rgb.getpixel((x, curr_y)) for x in sample_xs]
            if all(abs(p[0] - p[1]) < 8 and abs(p[1] - p[2]) < 8 and 150 < p[0] < 235 for p in pixels):
                if step > 1:
                    return curr_y
        return None
    if not btn_clusters:
        return None, []
    first_btn_top = btn_clusters[0][0]
    header_bottom = find_border_line(first_btn_top, -1, max_search=50) or (first_btn_top - 6)
    data_rows = []
    for cluster in btn_clusters:
        mid_y = int(sum(cluster) / len(cluster))
        row_t = find_border_line(mid_y, -1, max_search=30) or (cluster[0] - 6)
        row_b = find_border_line(mid_y, +1, max_search=30) or (cluster[-1] + 8)
        data_rows.append((max(0, row_t), min(h, row_b + 1)))
    return header_bottom, data_rows

# 1. 一鍵打包產生所有報表 ZIP (與 BAT 產出完全相同)
@app.post("/api/generate_all_zip")
async def generate_all_zip(request: Request):
    try:
        data_json = await request.json()
        records = data_json.get("records", [])
        do_3in1 = data_json.get("do3in1", True)
        do_transport = data_json.get("doTransport", True)
        do_lorry = data_json.get("doLorry", True)

        if not records:
            raise HTTPException(status_code=400, detail="請至少提供一筆有效的排程資料。")

        mapping = load_location_mapping()
        zip_buffer = BytesIO()

        output_date_str = datetime.now().strftime('%Y%m%d')
        for item in records:
            d_raw = str(item.get("date", "")).strip()
            if d_raw:
                d_part = d_raw.split()[0]
                dt_found = None
                for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%m/%d/%Y", "%d/%m/%Y"):
                    try:
                        dt_found = datetime.strptime(d_part, fmt)
                        break
                    except ValueError:
                        pass
                if dt_found:
                    output_date_str = dt_found.strftime('%Y%m%d')
                    break
        folder_name = f"三合一單輸出_{output_date_str}" 

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 1. 產生三合一單 Excel 報表 (依具體短地點各自獨立資料夾，如 15P5/, 15P6/, 18P3B/)
            if do_3in1 and os.path.exists(TEMPLATE_PATH):
                used_filenames = set()
                for item_idx, item in enumerate(records):
                    batch = item.get("batch", "").strip().upper()
                    loc = item.get("loc", "").strip().upper()
                    if not batch or not loc or len(batch) != 10 or loc not in mapping:
                        continue

                    loc_code = mapping[loc]
                    custom_tank = item.get("tank", "").strip()
                    if custom_tank and custom_tank != "自動槽號":
                        tank_no = custom_tank
                    else:
                        tank_no = extract_tank_from_batch(batch)
                    tank_with_prefix = "5" + tank_no
                    batch_with_prefix = "6" + batch

                    wb = openpyxl.load_workbook(TEMPLATE_PATH)
                    ws = wb["barcode"] if "barcode" in wb.sheetnames else wb.worksheets[0]

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

                    offset_x, offset_y = 35, 45
                    img_qr = Image.new('RGBA', (raw_img.width + offset_x, raw_img.height + offset_y), (255, 255, 255, 0))
                    img_qr.paste(raw_img, (offset_x, offset_y))

                    img_io = BytesIO()
                    img_qr.save(img_io, format='PNG')
                    img_io.seek(0)

                    new_qr = OpenpyxlImage(img_io)
                    new_qr.anchor = 'F2'
                    ws.add_image(new_qr)

                    # COA 截圖自動裁切 - 三層降級策略：
                    # 1.後端Tesseract(有安裝才用) -> 2.前端tesseract.js -> 3.幾何排程順序
                    if "latest_coa" in COA_CACHE and COA_CACHE["latest_coa"]:
                         try:
                             coa_raw = Image.open(BytesIO(COA_CACHE["latest_coa"])).convert("RGB")
                             w, h = coa_raw.size
                             cropped_coa = None
                             hb_struct, rows_struct = parse_tsmc_query_table_accurate(coa_raw)
                             if hb_struct and rows_struct:
                                 img_top = coa_raw.crop((0, 0, w, hb_struct))
                                 target_row = None
                                 target_digits = "".join(c for c in batch if c.isdigit())
                                 # === Layer 1: Local Tesseract (if installed) ===
                                 if TESSERACT_AVAILABLE:
                                     for box in backend_ocr_batch(coa_raw):
                                         box_text = box.get("text", "").upper()
                                         box_digits = "".join(c for c in box_text if c.isdigit())
                                         if box_text == batch or (len(box_digits) >= 6 and (box_digits in target_digits or target_digits in box_digits)):
                                             text_y = int((box.get("top", 0) + box.get("bottom", 0)) / 2)
                                             for row in rows_struct:
                                                 if row[0] - 20 <= text_y <= row[1] + 20:
                                                     target_row = row
                                                     print(f"[COA] Tesseract hit: {batch}")
                                                     break
                                             if target_row:
                                                 break
                                 # === Layer 2: Frontend tesseract.js OCR result ===
                                 if not target_row:
                                     ocr_data = COA_CACHE.get("ocr_data")
                                     if ocr_data and "boxes" in ocr_data and ocr_data["boxes"]:
                                         for box in ocr_data["boxes"]:
                                             box_text = box.get("text", "").upper()
                                             box_digits = "".join(c for c in box_text if c.isdigit())
                                             if box_text == batch or (len(box_digits) >= 6 and (box_digits in target_digits or target_digits in box_digits)):
                                                 text_y = int((box.get("top", 0) + box.get("bottom", 0)) / 2)
                                                 for row in rows_struct:
                                                     if row[0] - 15 <= text_y <= row[1] + 15:
                                                         target_row = row
                                                         print(f"[COA] Frontend OCR hit: {batch}")
                                                         break
                                                 if target_row:
                                                     break
                                 # === Layer 3: Geometric order fallback (no OCR needed) ===
                                 if not target_row:
                                     idx3 = min(item_idx, len(rows_struct) - 1)
                                     if idx3 >= 0:
                                         target_row = rows_struct[idx3]
                                         print(f"[COA] Geometric fallback idx={idx3} for {batch}")
                                 if target_row:
                                     img_row = coa_raw.crop((0, target_row[0], w, target_row[1]))
                                     cropped_coa = Image.new("RGB", (w, img_top.height + img_row.height), "white")
                                     cropped_coa.paste(img_top, (0, 0))
                                     cropped_coa.paste(img_row, (0, img_top.height))
                             if not cropped_coa:
                                 cropped_coa = coa_raw.crop((0, 0, w, int(h * 0.98)))
                             # 提高解析度：將圖片放大2倍 (使用高品質 Lanczos 重新取樣)，這樣印出來會更清晰
                             try:
 
                                 resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
                                 cropped_coa = cropped_coa.resize((cropped_coa.width * 2, cropped_coa.height * 2), resample_filter)
                             except Exception as e:
                                 print(f'Upscaling failed: {e}')
                             coa_io = BytesIO()
                             cropped_coa.save(coa_io, format="PNG", dpi=(300, 300))
                             coa_io.seek(0)
                             coa_img = OpenpyxlImage(coa_io)
                             coa_img.width = int(round(27.1 * 96 / 2.54))
                             coa_img.height = int(round(11.51 * 96 / 2.54))
                             _from = AnchorMarker(col=5, colOff=pixels_to_EMU(15), row=4, rowOff=0)
                             size = XDRPositiveSize2D(pixels_to_EMU(coa_img.width), pixels_to_EMU(coa_img.height))
                             coa_img.anchor = OneCellAnchor(_from=_from, ext=size)
                             ws.add_image(coa_img)
                             print(f"[COA] Image inserted (w={coa_img.width}, h={coa_img.height})")
                         except Exception as coa_e:
                             traceback.print_exc()
                             print(f"[COA Error] {batch}: {coa_e}")

                    excel_io = BytesIO()
                    wb.save(excel_io)
                    wb.close()
                    excel_io.seek(0)

                    # 檔名公式：[出貨日期]. [槽號] [廠別]台積電槽車barcode三合一單.xlsx (例如: 2026.8.18. E44 18P3B台積電槽車barcode三合一單.xlsx)
                    date_raw = str(item.get("date", "")).strip()
                    dt_file = None
                    if date_raw:
                        date_part = date_raw.split()[0]
                        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%m/%d/%Y", "%d/%m/%Y"):
                            try:
                                dt_file = datetime.strptime(date_part, fmt)
                                break
                            except ValueError:
                                pass
                    if not dt_file:
                        dt_file = datetime.now()

                    mmdd_3in1 = f"{dt_file.month:02d}{dt_file.day:02d}"
                    date_prefix = f"{dt_file.year}.{dt_file.month}.{dt_file.day}. "
                    tank_part = f"{tank_no} " if tank_no else ""
                    tank_str = tank_no if tank_no else ""
                    sub_folder = f"{mmdd_3in1} {loc} {tank_str}".strip()
                    base_name = f"{date_prefix}{tank_part}{loc}台積電槽車barcode三合一單.xlsx"
                    test_name = base_name
                    counter = 1
                    while f"{folder_name}/{sub_folder}/{test_name}" in used_filenames:
                        test_name = f"{date_prefix}{tank_part}{loc}_{counter}台積電槽車barcode三合一單.xlsx"
                        counter += 1
                    file_name = test_name
                    used_filenames.add(f"{folder_name}/{sub_folder}/{file_name}")
                    zip_file.writestr(f"{folder_name}/{sub_folder}/{file_name}", excel_io.getvalue())

            # 2. 寫入 session.json 至 ZIP 根目錄，供本機 BAT 或網頁版載入時 100% 精準還原原始完整 10 碼批號
            try:
                session_payload = []
                for r in records:
                    session_payload.append({
                        "batch": r.get("batch", ""),
                        "tank": r.get("tank", ""),
                        "loc": r.get("loc", ""),
                        "date": r.get("date", ""),
                        "time": r.get("time", ""),
                        "mod_time": r.get("modTime", r.get("mod_time", "")),
                        "po": r.get("po", "")
                    })
            # zip_file.writestr(f"{folder_name}/session.json", json.dumps(session_payload, ensure_ascii=False, indent=2).encode('utf-8'))
            except Exception as se:
                print(f"[Session JSON Error] {se}")

            # 3. 產生單列生產履歷 Excel (Chemical_Lorry)，依短地點歸入對應子資料夾
            extra_file = EXTRA_FILE_CACHE.get("latest_file")
            if do_lorry and extra_file and extra_file["ext"].lower() in [".xlsx", ".xls"]:
                try:
                    src_wb = openpyxl.load_workbook(BytesIO(extra_file["content"]), data_only=False)
                    src_ws = src_wb.active
                    
                    # 建立批號到列號的快速索引字典
                    batch_row_map = {}
                    for r in range(7, src_ws.max_row + 1):
                        val = str(src_ws.cell(row=r, column=1).value or "").strip().upper()
                        if val and val not in batch_row_map:
                            batch_row_map[val] = r

                    orig_name = extra_file["filename"]
                    base_name = orig_name.rsplit('-', 1)[0] if '-' in orig_name else orig_name

                    for item in records:
                        batch = item.get("batch", "").strip().upper()
                        loc = item.get("loc", "").strip().upper()
                        if not batch or not loc or len(batch) != 10 or loc not in mapping:
                            continue
                        
                        matched_row_idx = batch_row_map.get(batch)
                        if matched_row_idx:
                            # 建立只包含表頭 1~6 列與目標單列的極速輕量化 Workbook
                            new_wb = build_single_row_lorry_workbook(src_ws, matched_row_idx)
                            
                            # 組合新檔名：[原檔名前半部]-[MMDD] [槽號] [Loc].[Ext]
                            date_raw = item.get("date", "").strip()
                            mmdd = "0000"
                            if date_raw:
                                for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%m/%d/%Y", "%d/%m/%Y"):
                                    try:
                                        dt = datetime.strptime(date_raw, fmt)
                                        mmdd = f"{dt.month:02d}{dt.day:02d}"
                                        break
                                    except ValueError:
                                        pass
                            custom_tank = item.get("tank", "").strip()
                            if custom_tank and custom_tank != "自動槽號":
                                tank_no = custom_tank
                            else:
                                tank_no = extract_tank_from_batch(batch)
                            tank_part = f"{tank_no} " if tank_no else ""
                            new_filename = f"{base_name}-{mmdd} {tank_part}{loc}{extra_file['ext']}"
                            tank_str = tank_no if tank_no else ""
                            sub_folder = f"{mmdd} {loc} {tank_str}".strip()
                            
                            # 儲存到 ZIP 中對應的短地點資料夾 (例如: folder_name/15P5/Chemical_Lorry_...xlsx)
                            out_buf = BytesIO()
                            new_wb.save(out_buf)
                            # 儲存到 ZIP 中對應的短地點資料夾 (例如: folder_name/15P5/Chemical_Lorry_...xlsx)
                            zip_file.writestr(f"{folder_name}/{sub_folder}/{new_filename}", out_buf.getvalue())
                    src_wb.close()
                except Exception as ex:
                    print(f"[Lorry Error] {ex}")

            # 4. 處理 COA 表單 (如果使用者有上傳)
            if COA_FILE_CACHE:
                try:
                    valid_records = {}
                    for r in records:
                        batch = r.get("batch", "").strip().upper()
                        if batch:
                            valid_records[batch] = r

                    lorry_data_map = {}
                    extra_file = EXTRA_FILE_CACHE.get("latest_file")
                    if extra_file and extra_file["ext"].lower() in [".xlsx", ".xls"]:
                        try:
                            src_wb_l = openpyxl.load_workbook(BytesIO(extra_file["content"]), data_only=True)
                            src_ws_l = src_wb_l.active
                            for r_idx in range(7, src_ws_l.max_row + 1):
                                val = str(src_ws_l.cell(row=r_idx, column=1).value or "").strip().upper()
                                if val:
                                    col_b = str(src_ws_l.cell(row=r_idx, column=2).value or "").strip()
                                    
                                    raw_c = src_ws_l.cell(row=r_idx, column=3).value
                                    col_c = ""
                                    if isinstance(raw_c, datetime):
                                        col_c = f"{raw_c.year}/{raw_c.month}/{raw_c.day}"
                                    elif raw_c:
                                        col_c = str(raw_c).strip().split()[0]
                                        
                                    col_g = str(src_ws_l.cell(row=r_idx, column=7).value or "").strip()
                                    
                                    lorry_data_map[val] = {
                                        "b": col_b,
                                        "c": col_c,
                                        "g": col_g
                                    }
                            src_wb_l.close()
                        except Exception as e:
                            print(f"[COA Lorry Extraction Error] {e}")

                    for coa_file in COA_FILE_CACHE:
                        base_name = coa_file["filename"]
                        ext = coa_file["ext"]
                        matched_batch = None
                        for b in valid_records:
                            if b in base_name.upper():
                                matched_batch = b
                                break
                        
                        if not matched_batch:
                            continue

                        r = valid_records[matched_batch]
                        loc = r.get("loc", "").strip().upper()
                        date_raw = r.get("date", "").strip()
                        po_no = r.get("po", "").strip()[:10]
                        factory_code = loc[1:5] if len(loc) >= 5 else loc
                        
                        lorry_info = lorry_data_map.get(matched_batch, {})
                        val_b = lorry_info.get("b") or factory_code
                        val_c = lorry_info.get("c") or date_raw
                        val_g = lorry_info.get("g") or ""

                        formatted_date = ""
                        mmdd = "0000"
                        if date_raw:
                            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%m/%d/%Y", "%d/%m/%Y"):
                                try:
                                    dt = datetime.strptime(date_raw, fmt)
                                    formatted_date = f"{dt.year}{dt.month:02d}{dt.day:02d}"
                                    mmdd = f"{dt.month:02d}{dt.day:02d}"
                                    break
                                except ValueError:
                                    pass

                        idx = base_name.upper().find(matched_batch)
                        prefix = base_name[:idx]
                        suffix = base_name[idx + len(matched_batch):]
                        
                        import re
                        date_pattern = r'\d{4}[-_]?\d{2}[-_]?\d{2}|\d{8}'
                        mmdd_pattern = r'\b\d{4}(?=[-_]$)'
                        if re.search(date_pattern, prefix) and formatted_date:
                            prefix = re.sub(date_pattern, formatted_date, prefix)
                        elif re.search(mmdd_pattern, prefix) and mmdd != "0000":
                            prefix = re.sub(mmdd_pattern, mmdd, prefix)
                        else:
                            if prefix.endswith("_") or prefix.endswith("-"):
                                prefix = formatted_date + prefix if formatted_date else prefix
                            else:
                                prefix = formatted_date + "_" + prefix if prefix and formatted_date else (formatted_date + "_" if formatted_date else "")

                        new_base = f"{prefix}{base_name[idx:idx+len(matched_batch)]}{suffix}"
                        
                        custom_tank = r.get("tank", "").strip()
                        if custom_tank and custom_tank != "自動槽號":
                            tank_no = custom_tank
                        else:
                            tank_no = extract_tank_from_batch(matched_batch)
                        tank_str = tank_no if tank_no else ""
                        sub_folder = f"{mmdd} {loc} {tank_str}".strip()

                        # Write modified COA to ZIP
                        out_buf = BytesIO()
                        if ext in ['.xlsx', '.xls']:
                            try:
                                wb = openpyxl.load_workbook(BytesIO(coa_file["content"]))
                                ws = wb.active
                                ws["B6"] = val_b
                                if val_g: ws["B7"] = val_g
                                ws["B11"] = val_c
                                if po_no: ws["B12"] = po_no
                                wb.save(out_buf)
                                wb.close()
                                zip_file.writestr(f"{folder_name}/{sub_folder}/{new_base}", out_buf.getvalue())
                            except Exception as e:
                                print(f"[COA Excel Error] {e}")
                        elif ext == '.csv':
                            try:
                                import csv
                                text_content = coa_file["content"].decode('utf-8-sig', errors='ignore')
                                reader = list(csv.reader(text_content.splitlines()))
                                while len(reader) <= 17: reader.append([])
                                for row in reader:
                                    while len(row) <= 11: row.append("")
                                reader[5][1] = val_b
                                if val_g: reader[6][1] = val_g
                                reader[10][1] = val_c
                                if po_no: reader[11][1] = po_no
                                
                                import io
                                str_io = io.StringIO()
                                writer = csv.writer(str_io)
                                writer.writerows(reader)
                                zip_file.writestr(f"{folder_name}/{sub_folder}/{new_base}", str_io.getvalue().encode('utf-8-sig'))
                            except Exception as e:
                                print(f"[COA CSV Error] {e}")

                except Exception as ex:
                    print(f"[COA processing error] {ex}")

        # 生成完成後，清空快取避免影響下一次
        # COA_CACHE.clear() 
        # EXTRA_FILE_CACHE.clear()

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

# 2. COA 截圖處理與 Excel 自動貼上 API (純 Python Pillow 零依賴 .exe 方案)
COA_CACHE = {}
EXTRA_FILE_CACHE = {}

@app.post("/api/upload_extra_file")
async def upload_extra_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        import os
        filename, ext = os.path.splitext(file.filename)
        
        EXTRA_FILE_CACHE["latest_file"] = {
            "content": content,
            "filename": filename,
            "ext": ext
        }

        return JSONResponse({
            "status": "success",
            "message": f"附加檔案 {file.filename} 上傳成功！產生報表時將自動依排程複製與命名。"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"附加檔案處理失敗: {e}")

@app.post("/api/upload_coa_image")
async def upload_coa_image(file: UploadFile = File(...), ocr_data: str = Form(None)):
    try:
        content = await file.read()
        img = Image.open(BytesIO(content)).convert("RGB")

        # 保留原始高畫質，不進行任何強制壓縮或縮放
        w, h = img.size

        img_io = BytesIO()
        img.save(img_io, format="PNG")
        img_bytes = img_io.getvalue()
        COA_CACHE["latest_coa"] = img_bytes
        if ocr_data:
            import json
            try:
                COA_CACHE["ocr_data"] = json.loads(ocr_data)
            except:
                COA_CACHE["ocr_data"] = None

        return JSONResponse({
            "status": "success",
            "message": "COA 截圖已成功接收並完成影像最佳化！產生三合一單時將自動嵌入 Excel。"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"COA 截圖處理失敗: {e}")

COA_FILE_CACHE = []

@app.post("/api/upload_coa_files")
async def upload_coa_files(files: List[UploadFile] = File(...)):
    try:
        COA_FILE_CACHE.clear()
        for file in files:
            content = await file.read()
            ext = os.path.splitext(file.filename)[1].lower()
            COA_FILE_CACHE.append({
                "filename": file.filename,
                "ext": ext,
                "content": content
            })
        return JSONResponse({
            "status": "success",
            "message": f"成功上傳 {len(files)} 份 COA 表單！產生三合一單時將自動比對批號並處理。"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"COA 表單上傳失敗: {e}")

static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    port = find_available_port(8002)
    local_ip = get_local_ip()
    print("============================================================")
    print(f"TSMC Lorry Barcode Server started successfully!")
    print(f"Local URL: http://localhost:{port}")
    print(f"LAN URL: http://{local_ip}:{port}")
    print("============================================================")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
