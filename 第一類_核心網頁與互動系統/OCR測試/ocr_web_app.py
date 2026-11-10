import os
import sys
import io
import uuid
import base64
import socket
import warnings

# 壓制 PyTorch / torchvision / OpenPyXL 非重大提示與警告，保持終端畫面乾淨
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import easyocr
import fitz  # PyMuPDF
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

app = FastAPI(title="AI 圖片/PDF 智慧判讀轉 Excel 系統 (OCR to Excel)")

# 啟用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 建立暫存輸出資料夾
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# 初始化 EasyOCR 模型 (繁體中文 + 英文)
print("=" * 60)
print("  AI 圖片/PDF 智慧判讀轉 Excel 系統 (OCR to Excel)")
print("  正在啟動本機伺服器中，請稍候...")
print("=" * 60)
print("[*] 正在載入 EasyOCR 繁體中文與英文雙語模型 (約需 5-10 秒)...")
reader = easyocr.Reader(['ch_tra', 'en'], gpu=False)
print("[+] OCR 模型就緒！支援手機照片自動轉正與多頁 PDF 解析")

def get_local_ip():
    """獲取本機區域網路 IP 位址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def preprocess_image_bytes(img_bytes, max_dim=2200):
    """
    處理照片專用：
    1. EXIF 陀螺儀自動轉正 (修復手機直拍橫躺、倒置問題)
    2. 自動縮放超大相片尺寸 (兼顧文字細節與運算效能)
    """
    try:
        pil_img = Image.open(io.BytesIO(img_bytes))
        pil_img = ImageOps.exif_transpose(pil_img)
        
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
            
        w, h = pil_img.size
        if max(w, h) > max_dim:
            scale = max_dim / float(max(w, h))
            new_w = max(10, int(w * scale))
            new_h = max(10, int(h * scale))
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=92)
        return buf.getvalue()
    except Exception as e:
        print(f"[-] 影像預處理警告: {e}")
        return img_bytes

def cluster_and_align_table(ocr_results, y_threshold_ratio=0.5, col_threshold_ratio=0.5):
    """
    將 OCR 辨識出來的文字座標框聚類為視覺二維表格 (Rows & Columns)
    """
    if not ocr_results:
        return [], [], ""

    items = []
    for item in ocr_results:
        box = item[0]
        text = str(item[1]).strip()
        conf = float(item[2]) if len(item) > 2 else 1.0

        if not text:
            continue

        left = min(p[0] for p in box)
        top = min(p[1] for p in box)
        right = max(p[0] for p in box)
        bottom = max(p[1] for p in box)
        width = right - left
        height = bottom - top

        items.append({
            'text': text,
            'left': left,
            'top': top,
            'right': right,
            'bottom': bottom,
            'center_x': (left + right) / 2.0,
            'center_y': (top + bottom) / 2.0,
            'width': width,
            'height': height,
            'conf': conf,
            'box': box
        })

    if not items:
        return [], [], ""

    # 1. 動態計算列距容差 (Row Y-threshold)
    heights = sorted([it['height'] for it in items if it['height'] > 4])
    med_height = heights[len(heights) // 2] if heights else 20
    y_threshold = max(8, med_height * y_threshold_ratio)

    # 2. 聚類成列 (Rows)
    items.sort(key=lambda x: (x['top'], x['left']))
    rows = []
    for it in items:
        placed = False
        for r in rows:
            avg_y = sum(x['center_y'] for x in r) / len(r)
            if abs(it['center_y'] - avg_y) <= y_threshold or (it['top'] <= avg_y <= it['bottom']):
                r.append(it)
                placed = True
                break
        if not placed:
            rows.append([it])

    # 依 Y 座標由上至下排序列
    rows.sort(key=lambda r: sum(x['top'] for x in r) / len(r))

    # 各列內依 X 座標由左至右排序
    for r in rows:
        r.sort(key=lambda x: x['left'])

    # 3. 欄位聚類 (Column Alignment)
    widths = sorted([it['width'] for it in items if it['width'] > 4])
    med_width = widths[len(widths) // 2] if widths else 40
    col_threshold = max(20, med_width * col_threshold_ratio)

    all_lefts = sorted([it['left'] for it in items])
    col_anchors = []
    for lx in all_lefts:
        if not col_anchors:
            col_anchors.append([lx])
        else:
            avg_lx = sum(col_anchors[-1]) / len(col_anchors[-1])
            if abs(lx - avg_lx) <= col_threshold:
                col_anchors[-1].append(lx)
            else:
                col_anchors.append([lx])

    cols_x = [sum(c) / len(c) for c in col_anchors]
    cols_x.sort()

    if len(cols_x) > 22:
        table_matrix = [[x['text'] for x in r] for r in rows]
    else:
        table_matrix = []
        for r in rows:
            row_cells = [''] * len(cols_x)
            for it in r:
                best_idx = 0
                best_dist = float('inf')
                for c_idx, cx in enumerate(cols_x):
                    dist = abs(it['left'] - cx)
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = c_idx
                if row_cells[best_idx]:
                    row_cells[best_idx] += ' ' + it['text']
                else:
                    row_cells[best_idx] = it['text']
            while row_cells and row_cells[-1] == '':
                row_cells.pop()
            table_matrix.append(row_cells if row_cells else [''])

    raw_text = "\n".join(["\t".join(r) for r in table_matrix])
    return table_matrix, items, raw_text

def format_cell_value(val):
    """嘗試轉換為整數或浮點數數值型別"""
    try:
        clean_num = str(val).replace(",", "").strip()
        if clean_num.isdigit():
            return int(clean_num), "right"
        elif clean_num.replace(".", "", 1).isdigit() and clean_num.count(".") == 1:
            return float(clean_num), "right"
        else:
            return str(val), "left"
    except Exception:
        return str(val), "left"

def write_table_to_sheet(ws, table_matrix, title_text, meta_text):
    """將二維表格矩陣美化寫入工作表"""
    font_title = Font(name="微軟正黑體", size=13, bold=True, color="1E3A8A")
    font_header = Font(name="微軟正黑體", size=11, bold=True, color="FFFFFF")
    font_data = Font(name="微軟正黑體", size=10, color="1E293B")
    font_meta = Font(name="微軟正黑體", size=9, italic=True, color="64748B")

    fill_header = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    align_right = Alignment(horizontal="right", vertical="center")

    border_thin = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )
    border_header = Border(
        left=Side(style="thin", color="1E3A8A"),
        right=Side(style="thin", color="1E3A8A"),
        top=Side(style="medium", color="1E3A8A"),
        bottom=Side(style="medium", color="1E3A8A")
    )

    ws.views.sheetView[0].showGridLines = True
    ws["A1"] = title_text
    ws["A1"].font = font_title
    ws["A2"] = meta_text
    ws["A2"].font = font_meta

    start_row = 4
    max_cols = max([len(r) for r in table_matrix]) if table_matrix else 1

    for col_i in range(1, max_cols + 1):
        cell = ws.cell(row=start_row, column=col_i)
        cell.value = f"欄 {col_i}"
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = border_header
    ws.row_dimensions[start_row].height = 24

    for r_idx, row_data in enumerate(table_matrix):
        cur_row = start_row + 1 + r_idx
        ws.row_dimensions[cur_row].height = 20
        fill_cur = fill_zebra if r_idx % 2 == 1 else fill_white

        for c_idx in range(max_cols):
            raw_v = row_data[c_idx] if c_idx < len(row_data) else ""
            cell = ws.cell(row=cur_row, column=c_idx + 1)
            parsed_v, align_type = format_cell_value(raw_v)
            cell.value = parsed_v
            cell.alignment = align_right if align_type == "right" else align_left
            cell.font = font_data
            cell.fill = fill_cur
            cell.border = border_thin

    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            if cell.row < start_row:
                continue
            v_str = str(cell.value or "")
            ch_count = sum(1 for ch in v_str if ord(ch) > 127)
            length = len(v_str) + ch_count
            if length > max_len:
                max_len = length
        ws.column_dimensions[col_letter].width = max(12, min(max_len + 3, 40))

def generate_multi_page_excel(pages_data, output_path, original_filename=""):
    """
    生成支援多頁 PDF 或單張照片的專業 Excel 活頁簿
    """
    wb = openpyxl.Workbook()
    total_pages = len(pages_data)

    font_header = Font(name="微軟正黑體", size=11, bold=True, color="FFFFFF")
    font_data = Font(name="微軟正黑體", size=10, color="1E293B")
    font_bold = Font(name="微軟正黑體", size=10, bold=True, color="1E293B")
    fill_header = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    fill_high_conf = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    fill_mid_conf = PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid")
    fill_low_conf = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    align_right = Alignment(horizontal="right", vertical="center")
    border_thin = Border(left=Side(style="thin", color="CBD5E1"), right=Side(style="thin", color="CBD5E1"), top=Side(style="thin", color="CBD5E1"), bottom=Side(style="thin", color="CBD5E1"))
    border_header = Border(left=Side(style="thin", color="1E3A8A"), right=Side(style="thin", color="1E3A8A"), top=Side(style="medium", color="1E3A8A"), bottom=Side(style="medium", color="1E3A8A"))

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if total_pages > 1:
        ws_all = wb.active
        ws_all.title = "📋 全部頁面合併總表"
        
        merged_table = []
        for p in pages_data:
            merged_table.append([f"--- 📄 第 {p['page_num']} 頁 ---"])
            for row in p['table_matrix']:
                merged_table.append(row)
            merged_table.append([])
            
        write_table_to_sheet(
            ws_all, 
            merged_table, 
            f"📊 多頁 PDF OCR 辨識總表 - {original_filename} (共 {total_pages} 頁)",
            f"產生時間：{now_str}  |  已整合全檔 {total_pages} 頁表格內容"
        )

        for p in pages_data:
            ws_page = wb.create_sheet(title=f"📄 第 {p['page_num']} 頁")
            write_table_to_sheet(
                ws_page, 
                p['table_matrix'], 
                f"第 {p['page_num']} 頁表格還原",
                f"檔案：{original_filename}  |  字塊數：{len(p['items'])}"
            )

    else:
        ws_single = wb.active
        ws_single.title = "📋 表格智慧還原"
        p0 = pages_data[0]
        write_table_to_sheet(
            ws_single, 
            p0['table_matrix'], 
            f"📊 OCR 辨識成果 - {original_filename}",
            f"產生時間：{now_str}  |  總辨識項目：{len(p0['items'])} 個字塊  |  已自動完成二維空間重構"
        )

    # 附錄：📝 辨識明細清單
    ws_detail = wb.create_sheet(title="📝 辨識明細清單")
    ws_detail.views.sheetView[0].showGridLines = True
    headers_detail = ["頁次", "項次", "辨識文字", "可信度", "X (px)", "Y (px)", "寬度", "高度"]
    ws_detail.row_dimensions[1].height = 24
    for c_idx, h in enumerate(headers_detail, 1):
        cell = ws_detail.cell(row=1, column=c_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = border_header

    detail_row = 2
    item_counter = 1
    for p in pages_data:
        for it in p['items']:
            ws_detail.row_dimensions[detail_row].height = 19
            fill_cur = fill_zebra if item_counter % 2 == 1 else fill_white

            ws_detail.cell(row=detail_row, column=1, value=f"P.{p['page_num']}").alignment = align_center
            ws_detail.cell(row=detail_row, column=2, value=item_counter).alignment = align_center
            
            c_txt = ws_detail.cell(row=detail_row, column=3, value=it['text'])
            c_txt.font = font_bold
            c_txt.alignment = align_left

            conf_pct = round(it['conf'] * 100, 1)
            c_conf = ws_detail.cell(row=detail_row, column=4, value=f"{conf_pct}%")
            c_conf.alignment = align_center
            c_conf.font = font_bold
            c_conf.fill = fill_high_conf if conf_pct >= 85 else (fill_mid_conf if conf_pct >= 60 else fill_low_conf)

            for col_i, val in enumerate([int(it['left']), int(it['top']), int(it['width']), int(it['height'])], 5):
                ws_detail.cell(row=detail_row, column=col_i, value=val).alignment = align_right

            for c in range(1, 9):
                cell = ws_detail.cell(row=detail_row, column=c)
                if c != 3 and c != 4:
                    cell.font = font_data
                cell.border = border_thin
                if c != 4:
                    cell.fill = fill_cur

            detail_row += 1
            item_counter += 1

    for col in ws_detail.columns:
        col_letter = get_column_letter(col[0].column)
        ws_detail.column_dimensions[col_letter].width = 14

    wb.save(output_path)

def generate_annotated_image(img_bytes, items):
    """
    在影像上繪製半透明文字辨識框與項次編號
    """
    try:
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        overlay = image.copy()
        draw = ImageDraw.Draw(overlay)

        for i, it in enumerate(items, 1):
            box = it['box']
            pts = [(int(p[0]), int(p[1])) for p in box]
            
            if it['conf'] >= 0.85:
                color = (34, 197, 94)    # 綠色
            elif it['conf'] >= 0.60:
                color = (234, 179, 8)    # 黃色
            else:
                color = (239, 68, 68)    # 紅色
                
            draw.polygon(pts, outline=color, width=2)
            left = min(p[0] for p in box)
            top = max(0, min(p[1] for p in box) - 12)
            draw.rectangle([left, top, left + 20, top + 12], fill=color)
            draw.text((left + 2, top), str(i), fill=(255, 255, 255))

        blended = Image.blend(image, overlay, alpha=0.9)
        max_dim = 1200
        if blended.width > max_dim or blended.height > max_dim:
            blended.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        blended.save(buf, format="JPEG", quality=85)
        b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        print(f"[-] 繪製標註圖警告: {e}")
        return ""

# ====================================================
# API 路由
# ====================================================

@app.get("/")
async def get_index():
    """提供前端網頁"""
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return JSONResponse(status_code=404, content={"message": "web_index.html 檔案不存在"})

@app.get("/download/{file_name}")
async def download_file(file_name: str, name: str = None):
    """下載生成的 Excel 報表"""
    file_path = os.path.join(OUTPUT_DIR, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="檔案不存在或已過期")
    
    download_filename = name if name else file_name
    return FileResponse(
        file_path, 
        filename=download_filename, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.post("/convert")
@app.post("/api/ocr-to-excel")
async def convert_image_or_pdf_to_excel(
    file: UploadFile = File(...),
    page_mode: str = Form("first_page"),
    custom_pages: str = Form("")
):
    """
    通用 OCR 轉 Excel 接口：
    - 支援照片 (PNG, JPG, JPEG, WEBP, BMP)，自動 EXIF 轉正防歪
    - 支援 PDF 檔 (單頁/多頁)，支援自選頁數範圍並自動逐頁辨識
    """
    try:
        filename = file.filename
        file_bytes = await file.read()
        
        if not file_bytes:
            raise HTTPException(status_code=400, detail="上傳檔案為空，請確認選取的檔案")

        is_pdf = filename.lower().endswith(".pdf")
        pages_to_process = []

        if is_pdf:
            print(f"[*] 收到 PDF 檔案: {filename}，正在解析頁面 (模式: {page_mode})...")
            pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
            total_pdf_pages = len(pdf_doc)
            if total_pdf_pages == 0:
                raise HTTPException(status_code=400, detail="PDF 檔案無有效頁面")

            target_page_indices = []
            if page_mode == "first_page":
                target_page_indices = [0]
            elif page_mode == "first_3":
                target_page_indices = list(range(min(3, total_pdf_pages)))
            elif page_mode == "all":
                target_page_indices = list(range(min(20, total_pdf_pages)))
            elif page_mode == "custom" and custom_pages.strip():
                raw_parts = custom_pages.replace("，", ",").split(",")
                for p in raw_parts:
                    p = p.strip()
                    if "-" in p:
                        bounds = p.split("-")
                        if len(bounds) == 2 and bounds[0].isdigit() and bounds[1].isdigit():
                            start_p = max(1, int(bounds[0]))
                            end_p = min(total_pdf_pages, int(bounds[1]))
                            target_page_indices.extend(range(start_p - 1, end_p))
                    elif p.isdigit():
                        p_num = int(p)
                        if 1 <= p_num <= total_pdf_pages:
                            target_page_indices.append(p_num - 1)
                target_page_indices = sorted(list(set(target_page_indices)))

            if not target_page_indices:
                target_page_indices = [0]

            print(f"[*] 預計解析頁面清單: {[i+1 for i in target_page_indices]} (共 {len(target_page_indices)} 頁)")

            for page_idx in target_page_indices:
                page = pdf_doc[page_idx]
                pix = page.get_pixmap(dpi=150)
                page_bytes = pix.tobytes("png")
                pages_to_process.append({
                    "page_num": page_idx + 1,
                    "img_bytes": page_bytes
                })
        else:
            print(f"[*] 收到照片檔案: {filename}，正在進行 EXIF 轉正與最佳化...")
            cleaned_img_bytes = preprocess_image_bytes(file_bytes)
            pages_to_process.append({
                "page_num": 1,
                "img_bytes": cleaned_img_bytes
            })

        pages_results = []
        total_items_count = 0
        total_conf_sum = 0.0
        total_to_process = len(pages_to_process)

        for idx, p_info in enumerate(pages_to_process):
            page_num = p_info["page_num"]
            p_bytes = p_info["img_bytes"]
            print(f"[*] 正在辨識 第 {page_num} 頁 (進度: {idx+1}/{total_to_process})...")

            results = reader.readtext(p_bytes, detail=1)
            table_matrix, items, raw_text = cluster_and_align_table(results)
            annotated_img = generate_annotated_image(p_bytes, items)

            total_items_count += len(items)
            total_conf_sum += sum(it['conf'] for it in items)

            pages_results.append({
                "page_num": page_num,
                "table_matrix": table_matrix,
                "items": items,
                "raw_text": raw_text,
                "annotated_image": annotated_img,
                "rows_count": len(table_matrix),
                "cols_count": max([len(r) for r in table_matrix]) if table_matrix else 0
            })

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(filename)[0]
        excel_filename = f"{base_name}_OCR辨識表_{timestamp}.xlsx"
        unique_file_id = f"{uuid.uuid4().hex}.xlsx"
        output_filepath = os.path.join(OUTPUT_DIR, unique_file_id)

        generate_multi_page_excel(pages_results, output_filepath, original_filename=filename)

        avg_conf = (total_conf_sum / total_items_count * 100) if total_items_count > 0 else 0.0
        primary_page = pages_results[0]

        return {
            "success": True,
            "filename": excel_filename,
            "download_url": f"/download/{unique_file_id}?name={excel_filename}",
            "is_pdf": is_pdf,
            "total_pages": len(pages_results),
            "total_items": total_items_count,
            "avg_confidence": f"{avg_conf:.1f}%",
            "pages": pages_results,
            "table_data": primary_page["table_matrix"],
            "rows_count": primary_page["rows_count"],
            "cols_count": primary_page["cols_count"],
            "annotated_image": primary_page["annotated_image"],
            "raw_text": "\n\n".join([f"=== 第 {p['page_num']} 頁 ===\n" + p["raw_text"] for p in pages_results]),
            "timestamp": timestamp
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"success": False, "message": f"處理發生錯誤: {str(e)}"})

# ====================================================
# 主程式入口
# ====================================================
if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 8000
    
    for test_port in range(8000, 8050):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', test_port)) != 0:
                port = test_port
                break
                
    if port != 8000:
        print(f"[提示] 預設 Port 8000 已被佔用，已自動切換至可用 Port: {port}")

    print("=" * 60)
    print(f"🚀 AI 圖片/PDF 辨識轉 Excel 系統已啟動！")
    print(f"👉 本機電腦請開：  http://localhost:{port}")
    print(f"👉 區域網路請開：  http://{local_ip}:{port}")
    print("=" * 60)

    import threading, time, webbrowser
    def auto_open_browser():
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{port}")
    threading.Thread(target=auto_open_browser, daemon=True).start()
    
    uvicorn.run(app, host="0.0.0.0", port=port)
