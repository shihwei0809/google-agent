import os
import sys
import io
import uuid
import json
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

app = FastAPI(title="AI 圖片/PDF 智慧判讀轉 Excel 系統 (雙重 OCR 引擎)")

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
print("  AI 圖片/PDF 智慧判讀轉 Excel 系統 (雙重 OCR 引擎架構)")
print("  優先 Google Gemini 雲端高精準度，離線/無金鑰自動本機備援")
print("=" * 60)
print("[*] 正在載入 EasyOCR 繁體中文與英文雙語模型 (約需 5-10 秒)...")
reader = easyocr.Reader(['ch_tra', 'en'], gpu=False)
print("[+] 本機 EasyOCR 備援引擎就緒！支援手機照片自動轉正與多頁 PDF 解析")

def get_system_gemini_key():
    """多管道動態取得系統預設的 Google Gemini API Key"""
    # 1. 優先檢查系統環境變數
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if k:
        return k
    
    # 2. 當前目錄 .env
    cur_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(cur_env):
        try:
            with open(cur_env, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GEMINI_API_KEY="):
                        val = line.strip().split("=", 1)[1].strip("\"' ")
                        if val:
                            return val
        except Exception:
            pass

    # 3. 專案其它 .env 備用
    fallback_envs = [
        r"C:\GOOGLE ANGET\第一類_核心網頁與互動系統\互動式網站\.env",
        r"C:\GOOGLE ANGET\教育訓練教材\backend\.env",
        r"C:\GOOGLE ANGET\.env"
    ]
    for env_path in fallback_envs:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("GEMINI_API_KEY="):
                            val = line.strip().split("=", 1)[1].strip("\"' ")
                            if val:
                                return val
            except Exception:
                pass
    return ""

def sanitize_numpy(obj):
    """遞迴清理所有 numpy 物件以確保 JSON 序列化 100% 成功"""
    if isinstance(obj, dict):
        return {str(k): sanitize_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_numpy(x) for x in obj]
    elif hasattr(obj, 'item'):  # 攔截 np.int32, np.int64, np.float32, np.ndarray scalar
        return obj.item()
    elif hasattr(obj, 'tolist'): # 攔截 np.ndarray
        return sanitize_numpy(obj.tolist())
    elif isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    return str(obj)

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
        image = Image.open(io.BytesIO(img_bytes))
        
        # 1. 根據 EXIF Orientation 自動旋轉還原
        image = ImageOps.exif_transpose(image)
        
        # 2. 轉為 RGB
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        # 3. 尺寸優化
        width, height = image.size
        max_edge = max(width, height)
        if max_edge > max_dim:
            scale = max_dim / float(max_edge)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        print(f"[!] 影像預處理警告: {e}，回退使用原始二進位資料")
        return img_bytes

def call_gemini_ocr(img_bytes, api_key):
    """
    使用 Google Gemini API 進行高精度多模態 OCR 與二維表格直接提取
    """
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        prompt = """你是一個極致專業的繁體中文光學字元識別 (OCR) 與二維表格還原引擎。
請仔細審視這張圖片或掃描文件，執行以下任務：
1. 完整辨識並還原所有表格結構與文字，嚴格保持行列對齊。
2. 若遇到手寫筆跡、勾選記號、備註、數字、英文代碼，請精準還原。
3. 表格每一列的欄位數請維持一致，空儲存格請填入空字串 ""。
4. 請直接輸出標準 JSON 格式（不得包含 markdown 說明），格式如下：
{
  "title": "表單名稱或標題",
  "table": [
    ["欄1", "欄2", "欄3"],
    ["數值1", "數值2", "數值3"]
  ],
  "raw_text": "本頁所有純文字內容摘要"
}"""
        
        # 依序嘗試可用模型
        candidate_models = ['gemini-2.5-flash', 'gemini-flash-latest', 'gemini-3.5-flash', 'gemini-2.5-pro']
        resp = None
        last_error = ""
        
        for model_name in candidate_models:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type='image/png'),
                        prompt
                    ]
                )
                if resp and resp.text:
                    break
            except Exception as me:
                last_error = str(me)
                continue
                
        if not resp or not resp.text:
            return None, [], "", False, f"Gemini 模型無回應: {last_error}"
            
        txt = resp.text.strip()
        if '```json' in txt:
            txt = txt.split('```json')[1].split('```')[0].strip()
        elif '```' in txt:
            txt = txt.split('```')[1].split('```')[0].strip()
            
        data = json.loads(txt)
        table = data.get('table', [])
        raw_text = data.get('raw_text', '')
        
        # 確保 table 格式為 list of lists of strings
        clean_table = []
        for row in table:
            if isinstance(row, list):
                clean_table.append([str(c) if c is not None else "" for c in row])
                
        # 模擬產生 items 讓 UI 顯示明細與下載
        items = []
        for r_idx, row in enumerate(clean_table):
            for c_idx, cell_val in enumerate(row):
                if str(cell_val).strip():
                    items.append({
                        'text': str(cell_val).strip(),
                        'left': int(c_idx * 100),
                        'top': int(r_idx * 30),
                        'right': int((c_idx + 1) * 100),
                        'bottom': int((r_idx + 1) * 30),
                        'center_x': float(c_idx * 100 + 50),
                        'center_y': float(r_idx * 30 + 15),
                        'width': 90,
                        'height': 25,
                        'conf': 0.98,
                        'box': [[int(c_idx * 100), int(r_idx * 30)], [int((c_idx + 1) * 100), int(r_idx * 30)], [int((c_idx + 1) * 100), int((r_idx + 1) * 30)], [int(c_idx * 100), int((r_idx + 1) * 30)]]
                    })
                    
        return clean_table, items, raw_text, True, ""
        
    except Exception as e:
        return None, [], "", False, str(e)

def cluster_and_align_table(ocr_results, y_threshold_ratio=0.6, col_threshold_ratio=0.5):
    """
    本機 EasyOCR 二維空間聚類重構演算法：
    將 OCR 散落的文字框，精確聚類成具有「列 (Row)」與「欄 (Column)」的對齊二維表格矩陣。
    """
    if not ocr_results:
        return [], [], ""

    items = []
    for item in ocr_results:
        box = [[int(pt[0]), int(pt[1])] for pt in item[0]]
        text = str(item[1]).strip()
        conf = float(item[2]) if len(item) > 2 else 1.0

        if not text:
            continue

        left = int(min(p[0] for p in box))
        top = int(min(p[1] for p in box))
        right = int(max(p[0] for p in box))
        bottom = int(max(p[1] for p in box))
        width = int(right - left)
        height = int(bottom - top)

        items.append({
            'text': str(text),
            'left': int(left),
            'top': int(top),
            'right': int(right),
            'bottom': int(bottom),
            'center_x': float((left + right) / 2.0),
            'center_y': float((top + bottom) / 2.0),
            'width': int(width),
            'height': int(height),
            'conf': float(conf),
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
                    row_cells[best_idx] += " " + it['text']
                else:
                    row_cells[best_idx] = it['text']
            table_matrix.append(row_cells)

    # 4. 去除多餘全空欄位
    if table_matrix and len(table_matrix[0]) > 0:
        num_cols = len(table_matrix[0])
        valid_col_indices = [c for c in range(num_cols) if any(table_matrix[r][c].strip() for r in range(len(table_matrix)))]
        if valid_col_indices:
            table_matrix = [[row[c] for c in valid_col_indices] for row in table_matrix]

    raw_text = "\n".join(["\t".join(r) for r in table_matrix])
    return table_matrix, items, raw_text

def format_cell_value(val):
    """判斷數值格式與自動轉型"""
    if val is None or str(val).strip() == "":
        return "", "left"
    s = str(val).strip().replace(",", "")
    try:
        if "." in s:
            f_val = float(s)
            return f_val, "right"
        else:
            i_val = int(s)
            return i_val, "right"
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
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    font_header = Font(name="微軟正黑體", size=11, bold=True, color="FFFFFF")
    font_data = Font(name="微軟正黑體", size=10, color="1E293B")
    font_bold = Font(name="微軟正黑體", size=10, bold=True, color="1E293B")
    fill_header = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    fill_high_conf = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    fill_mid_conf = PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid")
    fill_low_conf = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    border_thin = Border(left=Side(style="thin", color="CBD5E1"), right=Side(style="thin", color="CBD5E1"), top=Side(style="thin", color="CBD5E1"), bottom=Side(style="thin", color="CBD5E1"))
    border_header = Border(left=Side(style="thin", color="1E3A8A"), right=Side(style="thin", color="1E3A8A"), top=Side(style="medium", color="1E3A8A"), bottom=Side(style="medium", color="1E3A8A"))

    is_multi_page = len(pages_data) > 1

    if is_multi_page:
        # Sheet 1: 📋 全部頁面合併總表
        ws_all = wb.active
        ws_all.title = "📋 全部頁面合併總表"
        combined_matrix = []
        for p in pages_data:
            if not combined_matrix:
                combined_matrix.extend(p['table_matrix'])
            else:
                combined_matrix.append([f"=== 第 {p['page_num']} 頁開始 ==="])
                combined_matrix.extend(p['table_matrix'])

        write_table_to_sheet(
            ws_all, 
            combined_matrix, 
            f"📊 OCR 辨識總表 - {original_filename}",
            f"產生時間：{now_str}  |  解析頁數：{len(pages_data)} 頁  |  已自動跨頁對齊整合"
        )

        # 個別獨立頁面分頁
        for p in pages_data:
            ws_p = wb.create_sheet(title=f"📄 第 {p['page_num']} 頁")
            write_table_to_sheet(
                ws_p, 
                p['table_matrix'], 
                f"📄 第 {p['page_num']} 頁還原表格",
                f"頁碼：第 {p['page_num']} 頁  |  辨識項目數：{len(p['items'])} 個"
            )
    else:
        # 單張照片或單頁 PDF
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

        for i, item in enumerate(items, 1):
            box = item['box']
            conf = item['conf']
            if conf >= 0.85:
                color = (34, 197, 94)    # 綠色
            elif conf >= 0.60:
                color = (234, 179, 8)    # 黃色
            else:
                color = (239, 68, 68)    # 紅色

            pts = [(int(p[0]), int(p[1])) for p in box]
            if len(pts) >= 4:
                draw.polygon(pts, outline=color, width=2)
            left = int(item['left'])
            top = max(0, int(item['top']) - 12)
            draw.rectangle([left, top, left + 20, top + 12], fill=color)
            draw.text((left + 2, top), str(i), fill=(255, 255, 255))

        alpha = 0.85
        blended = Image.blend(image, overlay, alpha)
        
        # 限制預覽圖大小
        max_preview_dim = 1400
        w, h = blended.size
        if max(w, h) > max_preview_dim:
            scale = max_preview_dim / float(max(w, h))
            blended = blended.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        blended.save(buf, format="JPEG", quality=80)
        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        print(f"[!] 標註圖片產生異常: {e}")
        return ""

# ====================================================
# API 路由定義
# ====================================================
@app.get("/")
async def root():
    """首頁：直接返回整合版 web_index.html"""
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return JSONResponse(status_code=404, content={"message": "web_index.html 檔案不存在"})

@app.get("/api/config")
async def get_system_config():
    """查詢伺服器端環境與 API Key 狀態"""
    sys_key = get_system_gemini_key()
    return {
        "has_default_key": bool(sys_key),
        "key_hint": (sys_key[:6] + "..." + sys_key[-4:]) if sys_key else "",
        "default_mode": "gemini" if sys_key else "easyocr"
    }

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
    custom_pages: str = Form(""),
    api_key: str = Form(""),
    engine_choice: str = Form("auto")  # auto=優先雲端, easyocr=純本機
):
    """
    通用雙重 OCR 轉 Excel 接口：
    - 支援照片 (PNG, JPG, JPEG, WEBP, BMP)，自動 EXIF 轉正防歪
    - 支援 PDF 檔 (單頁/多頁)，支援自選頁數範圍並自動逐頁辨識
    - 雙重架構：有 KEY 優先調用 Google Gemini 2.5 雲端多模態 OCR，離線或失敗時自動切換至本機 EasyOCR！
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

        effective_key = (api_key or "").strip() or get_system_gemini_key()
        pages_results = []
        total_items_count = 0
        total_conf_sum = 0.0
        total_to_process = len(pages_to_process)

        for idx, p_info in enumerate(pages_to_process):
            page_num = p_info["page_num"]
            p_bytes = p_info["img_bytes"]
            print(f"[*] 正在辨識 第 {page_num} 頁 (進度: {idx+1}/{total_to_process})...")

            use_gemini = (engine_choice != "easyocr") and bool(effective_key)
            page_engine = "easyocr"
            table_matrix = []
            items = []
            raw_text = ""

            if use_gemini:
                print(f"[*] 第 {page_num} 頁：啟用 Google Gemini 雲端高精度辨識中...")
                g_table, g_items, g_text, g_ok, g_err = call_gemini_ocr(p_bytes, effective_key)
                if g_ok and g_table:
                    table_matrix = g_table
                    items = g_items
                    raw_text = g_text
                    page_engine = "gemini"
                    print(f"[+] 第 {page_num} 頁：Google Gemini 雲端辨識成功！取得 {len(table_matrix)} 列表格")
                else:
                    print(f"[提示] Google Gemini 連線失敗 ({g_err})，自動平滑切換至本機 EasyOCR 雙語引擎...")

            if not table_matrix:
                # 本機離線 EasyOCR 模式（或雲端失敗後自動備援降級）
                print(f"[*] 第 {page_num} 頁：使用本機 EasyOCR 雙語引擎辨識中...")
                results = reader.readtext(p_bytes, detail=1)
                table_matrix, items, raw_text = cluster_and_align_table(results)
                page_engine = "easyocr"

            annotated_img = generate_annotated_image(p_bytes, items)
            total_items_count += len(items)
            total_conf_sum += sum(it.get('conf', 1.0) for it in items)

            pages_results.append({
                "page_num": int(page_num),
                "table_matrix": table_matrix,
                "items": items,
                "raw_text": str(raw_text),
                "annotated_image": annotated_img,
                "rows_count": int(len(table_matrix)),
                "cols_count": int(max([len(r) for r in table_matrix])) if table_matrix else 0,
                "engine_used": page_engine
            })

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(filename)[0]
        excel_filename = f"{base_name}_OCR辨識表_{timestamp}.xlsx"
        unique_file_id = f"{uuid.uuid4().hex}.xlsx"
        output_filepath = os.path.join(OUTPUT_DIR, unique_file_id)

        generate_multi_page_excel(pages_results, output_filepath, original_filename=filename)

        avg_conf = (total_conf_sum / total_items_count * 100) if total_items_count > 0 else 0.0
        primary_page = pages_results[0]

        # 彙整使用引擎
        gemini_count = sum(1 for p in pages_results if p.get("engine_used") == "gemini")
        if gemini_count == len(pages_results) and gemini_count > 0:
            engine_summary = "Google Gemini 雲端超高精度引擎"
            engine_badge = "gemini"
        elif gemini_count > 0:
            engine_summary = f"混合模式 (Gemini: {gemini_count} 頁, 本機: {len(pages_results)-gemini_count} 頁)"
            engine_badge = "hybrid"
        else:
            engine_summary = "本機離線 EasyOCR 雙語引擎"
            engine_badge = "easyocr"

        res_data = {
            "success": True,
            "filename": str(excel_filename),
            "download_url": f"/download/{unique_file_id}?name={excel_filename}",
            "is_pdf": bool(is_pdf),
            "total_pages": int(len(pages_results)),
            "total_items": int(total_items_count),
            "avg_confidence": f"{avg_conf:.1f}%",
            "engine_used": engine_badge,
            "engine_summary": engine_summary,
            "pages": pages_results,
            "table_data": primary_page["table_matrix"],
            "rows_count": int(primary_page["rows_count"]),
            "cols_count": int(primary_page["cols_count"]),
            "annotated_image": primary_page["annotated_image"],
            "raw_text": "\n\n".join([f"=== 第 {p['page_num']} 頁 ===\n" + str(p["raw_text"]) for p in pages_results]),
            "timestamp": timestamp
        }

        # 遞迴清理 numpy 物件，確保 100% 序列化安全
        return JSONResponse(content=sanitize_numpy(res_data))

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
    print(f"🚀 AI 圖片/PDF 雙重 OCR 轉 Excel 系統已啟動！")
    print(f"👉 本機電腦請開：  http://localhost:{port}")
    print(f"👉 區域網路請開：  http://{local_ip}:{port}")
    print("=" * 60)

    import threading, time, webbrowser
    def auto_open_browser():
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{port}")
    threading.Thread(target=auto_open_browser, daemon=True).start()
    
    uvicorn.run(app, host="0.0.0.0", port=port)
