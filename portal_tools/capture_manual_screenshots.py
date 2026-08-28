import os
import sys
import subprocess
import time
from PIL import Image, ImageDraw, ImageFont

img_dir = r"C:\GOOGLE ANGET\三合一單網頁架機伺服器\images"
os.makedirs(img_dir, exist_ok=True)

# 1. Capture Web UI with demo data loaded
html_with_demo_path = r"C:\GOOGLE ANGET\三合一單網頁架機伺服器\static\index_demo_capture.html"
orig_html_path = r"C:\GOOGLE ANGET\三合一單網頁架機伺服器\static\index.html"

with open(orig_html_path, "r", encoding="utf-8") as f:
    html_code = f.read()

# Inject demo data script into index.html
demo_script = """
<script>
window.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        tableData = [
            { selected: true, batch: "26814E3181", arrivalDate: "2026/08/28", location: "18P3B", longCode: "EF180183B", tank: "E318", time: "1000", modifiedTime: "", coaImage: "" },
            { selected: true, batch: "26814E3191", arrivalDate: "2026/08/28", location: "18P3B", longCode: "EF180183B", tank: "E319", time: "1400", modifiedTime: "1630", coaImage: "" },
            { selected: true, batch: "26814E3201", arrivalDate: "2026/08/28", location: "18P4", longCode: "EF180184A", tank: "E320", time: "1600", modifiedTime: "", coaImage: "" }
        ];
        renderTable();
    }, 200);
});
</script>
"""
demo_html = html_code.replace("</body>", demo_script + "\n</body>")
with open(html_with_demo_path, "w", encoding="utf-8") as f:
    f.write(demo_html)

# Capture Main UI Screenshot
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
screenshot_ui = os.path.join(img_dir, "ui_main_interface.png")

cmd = [
    edge_path,
    "--headless=new",
    f"--screenshot={screenshot_ui}",
    "--window-size=1200,750",
    f"file:///{html_with_demo_path.replace(os.sep, '/')}"
]
subprocess.run(cmd, check=True)
print(f"[OK] Captured: {screenshot_ui}")

# 2. Generate Professional Graphic: System Architecture
def create_system_architecture_img(out_path):
    w, h = 1000, 480
    im = Image.new("RGB", (w, h), "#0F172A") # Dark Navy Slate
    draw = ImageDraw.Draw(im)

    try:
        font_title = ImageFont.truetype("msjhbd.ttc", 22)
        font_box = ImageFont.truetype("msjhbd.ttc", 16)
        font_sub = ImageFont.truetype("msjh.ttc", 13)
        font_arrow = ImageFont.truetype("arial.ttf", 24)
    except:
        font_title = font_box = font_sub = font_arrow = ImageFont.load_default()

    # Draw Header Box
    draw.rounded_rectangle([(30, 20), (970, 70)], radius=10, fill="#1E293B", outline="#38BDF8", width=2)
    draw.text((w // 2, 45), "台積電槽車 Barcode 三合一單專用架機伺服器 — 全流程架構", fill="#38BDF8", font=font_title, anchor="mm")

    # Step 1 Box: Input
    draw.rounded_rectangle([(40, 110), (300, 360)], radius=12, fill="#1E293B", outline="#3B82F6", width=2)
    draw.rectangle([(40, 110), (300, 155)], fill="#2563EB")
    draw.text((170, 132), "【資料輸入端】", fill="#FFFFFF", font=font_box, anchor="mm")
    draw.text((60, 175), "1. Excel 排程多工作表匯入", fill="#E2E8F0", font=font_sub)
    draw.text((60, 205), "   (自動遍歷南科/竹科等分頁)", fill="#94A3B8", font=font_sub)
    draw.text((60, 240), "2. 載入既有運輸通知表", fill="#E2E8F0", font=font_sub)
    draw.text((60, 270), "   (修訂到廠時間專用)", fill="#94A3B8", font=font_sub)
    draw.text((60, 305), "3. 手動快速貼上與鍵盤導航", fill="#E2E8F0", font=font_sub)

    # Arrow 1 -> 2
    draw.text((335, 230), "==>", fill="#38BDF8", font=font_arrow, anchor="mm")

    # Step 2 Box: Processing & OCR
    draw.rounded_rectangle([(370, 110), (630, 360)], radius=12, fill="#1E293B", outline="#10B981", width=2)
    draw.rectangle([(370, 110), (630, 155)], fill="#059669")
    draw.text((500, 132), "【核心處理與 OCR】", fill="#FFFFFF", font=font_box, anchor="mm")
    draw.text((390, 175), "1. Tesseract.js 純前端辨識", fill="#E2E8F0", font=font_sub)
    draw.text((390, 205), "   (免裝 exe，瀏覽器直接 OCR)", fill="#94A3B8", font=font_sub)
    draw.text((390, 240), "2. COA 檢驗報告智慧裁切", fill="#E2E8F0", font=font_sub)
    draw.text((390, 270), "   (只保留單行表頭與目標批號)", fill="#94A3B8", font=font_sub)
    draw.text((390, 305), "3. 廠區代號自動反查映射", fill="#E2E8F0", font=font_sub)

    # Arrow 2 -> 3
    draw.text((665, 230), "==>", fill="#38BDF8", font=font_arrow, anchor="mm")

    # Step 3 Box: Output
    draw.rounded_rectangle([(700, 110), (960, 360)], radius=12, fill="#1E293B", outline="#F59E0B", width=2)
    draw.rectangle([(700, 110), (960, 155)], fill="#D97706")
    draw.text((830, 132), "【標準報表生成】", fill="#FFFFFF", font=font_box, anchor="mm")
    draw.text((720, 175), "1. 三合一單 Excel (.xlsx)", fill="#E2E8F0", font=font_sub)
    draw.text((720, 205), "   (嵌入 QR Code 與 COA 圖)", fill="#94A3B8", font=font_sub)
    draw.text((720, 240), "2. 雙色排版運輸通知表", fill="#E2E8F0", font=font_sub)
    draw.text((720, 270), "   (左側通知 + 右側紅字修正)", fill="#94A3B8", font=font_sub)
    draw.text((720, 305), "3. 一鍵 ZIP 批次打包下載", fill="#E2E8F0", font=font_sub)

    # Footer note
    draw.text((w // 2, 420), "FastAPI 後端引擎 + Pillow 精準裁切 + openpyxl 官方範本渲染", fill="#64748B", font=font_sub, anchor="mm")

    im.save(out_path, quality=95)
    print(f"[OK] Generated: {out_path}")

create_system_architecture_img(os.path.join(img_dir, "diagram_architecture.png"))

# 3. Generate Diagram: COA Smart Crop Diagram
def create_coa_crop_diagram(out_path):
    w, h = 960, 420
    im = Image.new("RGB", (w, h), "#FFFFFF")
    draw = ImageDraw.Draw(im)

    try:
        font_title = ImageFont.truetype("msjhbd.ttc", 18)
        font_head = ImageFont.truetype("msjhbd.ttc", 13)
        font_cell = ImageFont.truetype("msjh.ttc", 12)
        font_tag = ImageFont.truetype("msjhbd.ttc", 11)
    except:
        font_title = font_head = font_cell = font_tag = ImageFont.load_default()

    # Title
    draw.text((w // 2, 25), "COA 檢驗報告智慧影像辨識與自動裁切流程", fill="#1E293B", font=font_title, anchor="mm")

    # Left Box: Original COA (Multi rows)
    draw.rounded_rectangle([(30, 60), (450, 380)], radius=8, fill="#F8FAFC", outline="#94A3B8", width=1)
    draw.text((240, 80), "原始上傳之完整 COA 截圖 (含多批號)", fill="#0F172A", font=font_head, anchor="mm")

    # Table 1 Header
    draw.rectangle([(50, 110), (430, 140)], fill="#3B82F6")
    draw.text((240, 125), "檢驗項目 | 規格值 | 檢驗結果 (COA 表頭)", fill="#FFFFFF", font=font_cell, anchor="mm")

    # Batch 1 (Red / Filtered)
    draw.rectangle([(50, 150), (430, 185)], fill="#FEE2E2", outline="#EF4444", width=1)
    draw.text((240, 167), "批號: 26814E3181 檢驗數據 (非目標批號 - 自動去除)", fill="#991B1B", font=font_cell, anchor="mm")

    # Batch 2 (Green / Target)
    draw.rectangle([(50, 195), (430, 235)], fill="#DCFCE7", outline="#10B981", width=2)
    draw.text((240, 215), "★ 批號: 26814E3191 檢驗數據 (目標批號 - 精準鎖定)", fill="#065F46", font=font_head, anchor="mm")

    # Batch 3 (Red / Filtered)
    draw.rectangle([(50, 245), (430, 280)], fill="#FEE2E2", outline="#EF4444", width=1)
    draw.text((240, 262), "批號: 26814E3201 檢驗數據 (非目標批號 - 自動去除)", fill="#991B1B", font=font_cell, anchor="mm")

    # Batch 4 (Red / Filtered)
    draw.rectangle([(50, 290), (430, 325)], fill="#FEE2E2", outline="#EF4444", width=1)
    draw.text((240, 307), "批號: 26814E3211 檢驗數據 (非目標批號 - 自動去除)", fill="#991B1B", font=font_cell, anchor="mm")

    draw.text((240, 355), "Tesseract.js 前端 OCR 快速辨識批號座標", fill="#64748B", font=font_tag, anchor="mm")

    # Middle Arrow
    draw.text((505, 220), "==>", fill="#2563EB", font=ImageFont.truetype("arial.ttf", 26), anchor="mm")
    draw.text((505, 250), "智慧裁切", fill="#2563EB", font=font_tag, anchor="mm")

    # Right Box: Cropped Output
    draw.rounded_rectangle([(560, 60), (930, 380)], radius=8, fill="#F8FAFC", outline="#10B981", width=2)
    draw.text((745, 80), "嵌入 Excel F5 之單列高解析影像", fill="#065F46", font=font_head, anchor="mm")

    # Result Table Header
    draw.rectangle([(580, 130), (910, 170)], fill="#1E3A8A")
    draw.text((745, 150), "檢驗項目 | 規格值 | 檢驗結果 (單行表頭)", fill="#FFFFFF", font=font_cell, anchor="mm")

    # Result Target Row
    draw.rectangle([(580, 175), (910, 225)], fill="#DCFCE7", outline="#10B981", width=2)
    draw.text((745, 200), "批號: 26814E3191 檢驗數據 (單列精準保留)", fill="#065F46", font=font_head, anchor="mm")

    draw.rounded_rectangle([(580, 260), (910, 340)], radius=6, fill="#EFF6FF", outline="#60A5FA", width=1)
    draw.text((745, 285), "Excel 輸出尺寸自動鎖定：", fill="#1E40AF", font=font_tag, anchor="mm")
    draw.text((745, 312), "寬 23.7 公分 × 高 11.5 公分 (完美貼合格線)", fill="#1E40AF", font=font_head, anchor="mm")

    im.save(out_path, quality=95)
    print(f"[OK] Generated: {out_path}")

create_coa_crop_diagram(os.path.join(img_dir, "diagram_coa_crop.png"))

# 4. Generate Diagram: Transport Notice Dual Card
def create_transport_notice_diagram(out_path):
    w, h = 960, 400
    im = Image.new("RGB", (w, h), "#FFFFFF")
    draw = ImageDraw.Draw(im)

    try:
        font_title = ImageFont.truetype("msjhbd.ttc", 18)
        font_head = ImageFont.truetype("msjhbd.ttc", 14)
        font_cell = ImageFont.truetype("msjh.ttc", 12)
        font_bold = ImageFont.truetype("msjhbd.ttc", 12)
    except:
        font_title = font_head = font_cell = font_bold = ImageFont.load_default()

    draw.text((w // 2, 25), "運輸通知表 Excel 雙色左右併排卡片版型", fill="#1E293B", font=font_title, anchor="mm")

    # Left Card (A~F): Original Notification
    draw.rounded_rectangle([(40, 65), (460, 360)], radius=8, fill="#F8FAFC", outline="#3B82F6", width=2)
    draw.rectangle([(40, 65), (460, 105)], fill="#1D4ED8")
    draw.text((250, 85), "左側 (A~F 欄)：出貨排程通知表 (黑字/藍底)", fill="#FFFFFF", font=font_head, anchor="mm")

    draw.text((70, 130), "出貨通知日期：2026/08/28", fill="#1E293B", font=font_cell)
    draw.text((70, 165), "到廠廠區：台積電 18P3B 廠", fill="#1E293B", font=font_cell)
    draw.text((70, 200), "指定槽號：E319", fill="#1E293B", font=font_cell)
    draw.text((70, 235), "預估到廠時間：14:00", fill="#1E293B", font=font_bold)
    draw.text((70, 270), "產品品名：超高純度 IPA (IPAHQ)", fill="#1E293B", font=font_cell)
    draw.text((70, 310), "※ 週期長度：6 列資料 + 1 列空白分隔 (共7列循環)", fill="#64748B", font=font_cell)

    # Right Card (H~M): Modified Notification (Red)
    draw.rounded_rectangle([(500, 65), (920, 360)], radius=8, fill="#FEF2F2", outline="#EF4444", width=2)
    draw.rectangle([(500, 65), (920, 105)], fill="#B91C1C")
    draw.text((710, 85), "右側 (H~M 欄)：出貨排程修正通知 (紅字醒目)", fill="#FFFFFF", font=font_head, anchor="mm")

    draw.text((530, 130), "修正通知日期：2026/08/28", fill="#991B1B", font=font_cell)
    draw.text((530, 165), "到廠廠區：台積電 18P3B 廠", fill="#991B1B", font=font_cell)
    draw.text((530, 200), "指定槽號：E319", fill="#991B1B", font=font_cell)
    draw.text((530, 235), "修正到廠時間：16:30  ★ (紅字醒目標示)", fill="#DC2626", font=font_bold)
    draw.text((530, 270), "產品品名：超高純度 IPA (IPAHQ)", fill="#991B1B", font=font_cell)
    draw.text((530, 310), "※ 當有填入修正時間時，系統自動並排產生右側卡片", fill="#B91C1C", font=font_cell)

    im.save(out_path, quality=95)
    print(f"[OK] Generated: {out_path}")

create_transport_notice_diagram(os.path.join(img_dir, "diagram_transport_notice.png"))

if os.path.exists(html_with_demo_path):
    os.remove(html_with_demo_path)
