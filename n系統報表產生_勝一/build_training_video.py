from __future__ import annotations

import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
ASSET_DIR = ROOT / "tutorial_assets"
VIDEO_DIR = ROOT / "操作影片"
FRAME_DIR = ASSET_DIR / "video_frames"
ASSET_DIR.mkdir(exist_ok=True)
FRAME_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1920, 1080
FONT_NORMAL = r"C:\Windows\Fonts\msjh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msjhbd.ttc"


def F(size: int, bold=False):
    p = FONT_BOLD if bold and Path(FONT_BOLD).exists() else FONT_NORMAL
    return ImageFont.truetype(p, size)


def fit_text(draw, xy, value, max_w, size, color, bold=False):
    size = int(size)
    while size > 12 and draw.textbbox((0, 0), value, font=F(size, bold))[2] > max_w:
        size -= 1
    draw.text(xy, value, font=F(size, bold), fill=color)


def rounded(draw, box, fill, outline=None, radius=12, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_calendar_icon(d, box, color="#1d4ed8"):
    x1, y1, x2, y2 = box
    d.rounded_rectangle((x1 + 8, y1 + 7, x2 - 8, y2 - 6), radius=3, outline=color, width=2)
    d.line((x1 + 8, y1 + 13, x2 - 8, y1 + 13), fill=color, width=2)
    d.line((x1 + 12, y1 + 4, x1 + 12, y1 + 10), fill=color, width=2)
    d.line((x2 - 12, y1 + 4, x2 - 12, y1 + 10), fill=color, width=2)
    for cx, cy in ((x1 + 13, y1 + 18), (x2 - 13, y1 + 18), (x1 + 13, y2 - 11), (x2 - 13, y2 - 11)):
        d.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill=color)


def app_screen(state="initial"):
    im = Image.new("RGB", (1280, 820), "#f0f1f3")
    d = ImageDraw.Draw(im)
    # Window chrome and system status panel
    d.rectangle((0, 0, 1279, 42), fill="#e6e6e6")
    d.text((18, 10), "生產履歷與 COA 自動產生器｜新版介面示意", font=F(17, True), fill="#202020")
    d.text((1205, 8), "—   □   ×", font=F(17), fill="#444")
    rounded(d, (16, 56, 1264, 204), "#ffffff", "#cfd8dc", 12)
    d.text((34, 67), "系統狀態", font=F(18, True), fill="#173b64")
    d.text((42, 100), "對照表檔案：", font=F(15, True), fill="#333")
    d.text((167, 100), "已找到（示範）", font=F(15, True), fill="#16803c")
    rounded(d, (351, 91, 518, 124), "#607d8b", None, 7)
    d.text((365, 98), "重新載入對照表", font=F(13, True), fill="white")
    d.text((42, 151), "生產履歷：", font=F(15, True), fill="#333")
    lorry_state = "已載入 1 份（示範）" if state in ("lorry", "coa", "review", "output", "error") else "尚未載入"
    d.text((167, 151), lorry_state, font=F(15, True), fill="#16803c" if state != "initial" else "#c05621")
    rounded(d, (351, 142, 520, 175), "#e65100", None, 7)
    d.text((365, 149), "選擇生產履歷檔", font=F(13, True), fill="white")

    # Toolbar
    buttons = [
        ("從 Excel 匯入排程", "#1976d2", 190),
        ("載入生產履歷", "#e65100", 173),
        ("載入 COA 表單", "#8e24aa", 157),
        ("清除已載入檔案", "#546e7a", 177),
    ]
    x = 18
    for label, color, width in buttons:
        rounded(d, (x, 220, x + width, 261), color, None, 7)
        fit_text(d, (x + 12, 230), label, width - 24, 15, "#ffffff", True)
        x += width + 9
    quick = [("帶入今天日期", 147), ("新增 10 列", 130), ("清除全部資料", 143)]
    x = 805
    for label, width in quick:
        rounded(d, (x, 220, x + width, 261), "#546e7a" if "清除" not in label else "#d32f2f", None, 7)
        fit_text(d, (x + 10, 230), label, width - 20, 14, "#fff", True)
        x += width + 8

    # Export folder mode controls
    rounded(d, (18, 273, 1262, 336), "#ffffff", "#b0bec5", 10)
    d.text((32, 281), "輸出資料夾模式", font=F(15, True), fill="#37474f")
    mode1 = "● 模式 1：出貨日 → 廠區 → 批號資料夾 → 檔案"
    mode2 = "○ 模式 2：出貨日 → 廠區 → 檔案"
    if state == "mode2":
        mode1, mode2 = "○ 模式 1：出貨日 → 廠區 → 批號資料夾 → 檔案", "● 模式 2：出貨日 → 廠區 → 檔案"
    d.text((341, 288), mode1, font=F(14), fill="#333")
    d.text((826, 288), mode2, font=F(14), fill="#333")

    # Schedule table with fictional values only
    d.rectangle((18, 347, 1262, 408), fill="#e8ebee", outline="#adb5bd", width=1)
    columns = [
        ("產生", 28), ("項次", 34), ("批號\n(10碼)", 90), ("數量", 58), ("地點", 58),
        ("長代號", 68), ("出貨日期", 84), ("到貨日期", 84), ("採購單號", 88), ("料號", 72),
        ("品名", 114), ("製造日", 75), ("保存期限", 75), ("剩餘\n天數", 56), ("清空", 45),
    ]
    x = 21
    starts = []
    for label, width in columns:
        starts.append((x, width))
        d.rectangle((x, 348, x + width, 407), outline="#c4c9ce", width=1)
        lines = label.split("\n")
        for idx, line in enumerate(lines):
            fit_text(d, (x + 3, 360 + idx * 20), line, width - 6, 12, "#333333", True)
        x += width
    rows = [
        ["☑", "1", "DEMO000001", "800", "15P5", "1500", "2026/10/07", "2026/10/08", "DEMO-PO-01", "DEMO-PART", "NSE DEMO A", "2026/10/01", "2027/10/01", "359", "清空"],
        ["☑", "2", "DEMO000002", "1200", "12P8", "1280", "2026/10/07", "2026/10/09", "DEMO-PO-02", "DEMO-PART", "NSE DEMO B", "2026/10/02", "2027/10/02", "360", "清空"],
    ]
    for ri, row in enumerate(rows):
        y1, y2 = 409 + ri * 48, 457 + ri * 48
        d.rectangle((18, y1, 1262, y2), fill="#ffffff" if ri == 0 else "#fafafa", outline="#d4d9de")
        for ci, ((cx, cw), value) in enumerate(zip(starts, row)):
            d.rectangle((cx, y1, cx + cw, y2), outline="#e0e4e8")
            color = "#216e39" if ci in (4, 5, 12) else "#29323a"
            fit_text(d, (cx + 3, y1 + 14), value, cw - 6, 11, color, ci in (2, 4))
    # One more blank row for editing
    for ri in range(2, 5):
        y1, y2 = 409 + ri * 48, 457 + ri * 48
        d.rectangle((18, y1, 1262, y2), fill="#ffffff", outline="#e0e4e8")
        for cx, cw in starts:
            d.rectangle((cx, y1, cx + cw, y2), outline="#e0e4e8")
        d.text((24, y1 + 16), "□", font=F(12), fill="#9aa3ab")

    # Generate button and COA load indicator
    if state in ("coa", "review", "output", "mode2", "error"):
        d.text((38, 666), "COA：已載入 2 份（示範）　｜　剩餘天數：由匯入欄位帶入", font=F(14, True), fill="#16803c")
    else:
        d.text((38, 666), "COA：尚未載入　｜　剩餘天數：由 Excel 欄位直接匯入", font=F(14, True), fill="#c05621")
    rounded(d, (18, 711, 1262, 777), "#43a047", None, 10)
    d.text((425, 727), "開始批次產生 Excel 報表", font=F(21, True), fill="white")
    if state in ("review", "output", "mode2", "error"):
        rounded(d, (601, 365, 1224, 450), "#eff6ff", "#93c5fd", 8)
        d.text((621, 380), "核對示範列：批號 10 碼｜地點代號已對照｜出貨日期有效", font=F(14, True), fill="#1e3a8a")
        d.text((621, 413), "確認左側勾選框，再執行批次產生。", font=F(13), fill="#334155")
    return im


def overlay_dialog(im, kind):
    im = im.convert("RGBA")
    shade = Image.new("RGBA", im.size, (25, 32, 42, 125))
    im = Image.alpha_composite(im, shade)
    d = ImageDraw.Draw(im)
    if kind == "file_schedule":
        box = (262, 138, 1016, 666)
        rounded(d, box, "#ffffff", "#aeb8c1", 14, 2)
        d.text((294, 162), "選擇要匯入的 Excel 或 CSV 檔案", font=F(22, True), fill="#1f2933")
        d.text((294, 216), "資料夾：NSE_範例資料", font=F(15), fill="#52606d")
        for i, (name, ext) in enumerate((("出貨排程_示範", ".xlsx"), ("出貨排程_示範備份", ".csv"), ("操作說明", ".txt"))):
            y = 264 + 53 * i
            if i == 0:
                d.rectangle((284, y - 4, 993, y + 42), fill="#dbeafe")
            d.text((315, y), "▦", font=F(18), fill="#16803c")
            d.text((354, y + 3), name + ext, font=F(16), fill="#27313a")
        rounded(d, (785, 582, 890, 628), "#1976d2", None, 6)
        d.text((815, 594), "開啟", font=F(16, True), fill="white")
        rounded(d, (902, 582, 993, 628), "#e9ecef", "#b8c0c8", 6)
        d.text((926, 594), "取消", font=F(15), fill="#374151")
    elif kind in ("import_preview", "import_single"):
        box = (165, 105, 1112, 707)
        rounded(d, box, "#ffffff", "#aeb8c1", 14, 2)
        d.text((197, 130), "排程匯入確認", font=F(23, True), fill="#173b64")
        d.text((197, 180), "檔案：出貨排程_示範.xlsx　｜　跨 2 個分頁偵測到 12 筆資料", font=F(15), fill="#4b5563")
        rounded(d, (197, 218, 1066, 340), "#eef6ff", "#c7dff6", 8)
        d.text((213, 224), "日期快速篩選： [近三日] [今天] [明天] [後天] [全部]", font=F(12, True), fill="#1e3a8a")
        d.text((213, 254), "指定區間：", font=F(12, True), fill="#334155")
        rounded(d, (304, 249, 450, 280), "#ffffff", "#93a4b5", 4)
        d.text((315, 255), "2026/10/06", font=F(13), fill="#334155")
        rounded(d, (453, 249, 485, 280), "#ffffff", "#93a4b5", 4)
        draw_calendar_icon(d, (453, 249, 485, 280))
        d.text((490, 254), "~", font=F(15, True), fill="#334155")
        end_value = "" if kind == "import_single" else "2026/10/10"
        rounded(d, (510, 249, 656, 280), "#ffffff", "#93a4b5", 4)
        d.text((520, 255), end_value, font=F(13), fill="#334155")
        rounded(d, (659, 249, 691, 280), "#ffffff", "#93a4b5", 4)
        draw_calendar_icon(d, (659, 249, 691, 280))
        rounded(d, (700, 249, 773, 280), "#009688", None, 5)
        d.text((715, 256), "查詢", font=F(12, True), fill="white")
        d.text((213, 289), "筆數：[5] [10] [20] [全部]　自訂 [10] 筆　｜　可逐列取消選取", font=F(12, True), fill="#334155")
        date_note = "起始日填 2026/10/06；結束日空白，查詢單日排程。" if kind == "import_single" else "起始日與結束日都填寫，即可查詢整段日期。"
        d.text((213, 316), date_note, font=F(12), fill="#334155")
        headers = [("選取", 62), ("分頁", 98), ("批號", 137), ("數量", 86), ("地點", 95), ("出貨日", 128), ("到貨日", 128), ("長代號", 125)]
        x = 197
        for label, width in headers:
            d.rectangle((x, 345, x + width, 391), fill="#e8edf3", outline="#c9d0d7")
            fit_text(d, (x + 6, 358), label, width - 12, 14, "#24313d", True)
            x += width
        data_rows = [
            ["☑", "115A", "DEMO000001", "800", "15P5", "2026/10/07", "2026/10/08", "1500"],
            ["☑", "1106A", "DEMO000002", "1200", "12P8", "2026/10/07", "2026/10/09", "1280"],
        ]
        for ri, row in enumerate(data_rows):
            x, y = 197, 392 + ri * 45
            for (label, width), value in zip(headers, row):
                d.rectangle((x, y, x + width, y + 45), fill="#fff" if ri % 2 == 0 else "#f8fafc", outline="#d7dde3")
                fit_text(d, (x + 7, y + 13), value, width - 14, 13, "#334155")
                x += width
        d.text((197, 515), "先檢查分頁、出貨日、到貨日、地點與長代號，逐列確認匯入勾選。", font=F(14, True), fill="#334155")
        rounded(d, (781, 623, 925, 671), "#1976d2", None, 8)
        d.text((806, 636), "確認匯入資料", font=F(14, True), fill="white")
        rounded(d, (941, 623, 1065, 671), "#eef0f2", "#c7cdd2", 8)
        d.text((980, 636), "取消", font=F(14), fill="#374151")
    elif kind == "match_status":
        box = (234, 228, 1040, 586)
        rounded(d, box, "#ffffff", "#9eacb7", 14, 2)
        d.text((272, 255), "檔案載入結果", font=F(24, True), fill="#173b64")
        d.text((272, 315), "✓ 累計已載入 1 份生產履歷（本次新增 1 份）", font=F(16, True), fill="#16803c")
        d.text((272, 360), "✓ DEMO000001 — 已找到對應資料", font=F(15), fill="#334155")
        d.text((272, 399), "✓ DEMO000002 — 已找到對應資料", font=F(15), fill="#334155")
        d.text((272, 427), "✓ 出貨日期／到貨日期：已確認兩個欄位分開帶入", font=F(14), fill="#334155")
        d.text((272, 466), "COA 表單：本次新增 2 份，累計 2 份", font=F(15, True), fill="#16803c")
        rounded(d, (859, 515, 1001, 562), "#1976d2", None, 8)
        d.text((895, 528), "確定", font=F(15, True), fill="white")
    elif kind == "working":
        box = (354, 272, 934, 546)
        rounded(d, box, "#ffffff", "#9eacb7", 14, 2)
        d.text((426, 316), "正在產生檔案，請稍候…", font=F(22, True), fill="#173b64")
        rounded(d, (420, 385, 868, 419), "#e7eef5", None, 16)
        rounded(d, (420, 385, 754, 419), "#2e86de", None, 16)
        d.text((514, 449), "請勿關閉系統視窗", font=F(15), fill="#5f6b76")
    elif kind == "results":
        box = (211, 169, 1064, 652)
        rounded(d, box, "#ffffff", "#9eacb7", 14, 2)
        d.text((252, 199), "批次產生完成", font=F(25, True), fill="#16803c")
        d.text((252, 259), "• 生產履歷：成功產生 2 份", font=F(16), fill="#263238")
        d.text((252, 304), "• COA 表單：成功產生 2 份", font=F(16), fill="#263238")
        d.text((252, 364), "輸出資料夾：N系小包報表輸出_20261007", font=F(15, True), fill="#173b64")
        rounded(d, (252, 410, 1025, 516), "#f1f5f9", "#d5dee7", 8)
        d.text((276, 427), "15P5  /  1007 15P5 DEMO000001  /  示範檔案", font=F(14), fill="#334155")
        d.text((276, 464), "12P8  /  1007 12P8 DEMO000002  /  示範檔案", font=F(14), fill="#334155")
        rounded(d, (885, 574, 1022, 620), "#1976d2", None, 8)
        d.text((922, 587), "確定", font=F(15, True), fill="white")
    return im.convert("RGB")


def wrap(d, value, max_width, fnt):
    lines, current = [], ""
    for char in value:
        candidate = current + char
        if current and d.textbbox((0, 0), candidate, font=fnt)[2] > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def slide(path: Path, screen: Image.Image, chapter: str, title: str,
          instructions: list[str], active: int, takeaway: str, footer="介面重製示意｜畫面內所有資料均為合成資料"):
    im = Image.new("RGB", (W, H), "#0b1220")
    d = ImageDraw.Draw(im)
    rounded(d, (22, 18, 1898, 1062), "#f8fafc", None, 24)
    d.rounded_rectangle((22, 18, 1898, 112), 22, fill="#10243b")
    d.rectangle((22, 88, 1898, 112), fill="#10243b")
    d.text((58, 36), "N 系小包生產履歷與 COA 產生器", font=F(30, True), fill="#ffffff")
    d.text((644, 48), "操作教學｜多情境", font=F(20), fill="#cbd5e1")
    rounded(d, (1561, 42, 1858, 87), "#164e63", None, 20)
    d.text((1590, 53), "本機示範・合成資料", font=F(16, True), fill="#cffafe")

    # left screen card
    rounded(d, (45, 137, 1325, 1006), "#ffffff", "#d5dce4", 16, 2)
    sw, sh = 1248, 800
    screen = screen.resize((sw, sh), Image.Resampling.LANCZOS)
    im.paste(screen, (61, 157))
    d = ImageDraw.Draw(im)
    # right instruction card
    rounded(d, (1351, 137, 1875, 1006), "#ffffff", "#d5dce4", 16, 2)
    rounded(d, (1380, 164, 1584, 208), "#dbeafe", None, 20)
    fit_text(d, (1402, 176), chapter, 165, 17, "#1d4ed8", True)
    size = 28
    while size > 19 and d.textbbox((0, 0), title, font=F(size, True))[2] > 454:
        size -= 1
    d.text((1380, 231), title, font=F(size, True), fill="#0f172a")
    d.line((1380, 281, 1845, 281), fill="#e2e8f0", width=2)
    y = 303
    for i, item in enumerate(instructions):
        bg = "#eff6ff" if i == active else "#f8fafc"
        fg = "#1d4ed8" if i == active else "#475569"
        rounded(d, (1379, y, 1846, y + 80), bg, None, 13)
        d.ellipse((1401, y + 17, 1447, y + 63), fill="#2563eb" if i == active else "#cbd5e1")
        count = str(i + 1)
        bb = d.textbbox((0, 0), count, font=F(20, True))
        d.text((1424 - (bb[2] - bb[0]) // 2, y + 28), count, font=F(20, True), fill="#ffffff")
        lines = wrap(d, item, 365, F(17, i == active))
        text_y = y + (20 if len(lines) <= 2 else 8)
        for li, line in enumerate(lines[:3]):
            d.text((1465, text_y + li * 25), line, font=F(17, i == active), fill=fg)
        y += 94
    rounded(d, (1379, 824, 1846, 958), "#f1f5f9", None, 12)
    d.text((1402, 842), "操作重點", font=F(17, True), fill="#475569")
    for li, line in enumerate(wrap(d, takeaway, 422, F(16))[:3]):
        d.text((1402, 877 + li * 23), line, font=F(16), fill="#334155")
    d.text((55, 1024), footer, font=F(14), fill="#64748b")
    im.save(path, optimize=True)


def to_video(outfile: Path, frames: list[Path], seconds=4.4):
    args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    for frame in frames:
        args += ["-loop", "1", "-t", str(seconds), "-i", str(frame)]
    filters = []
    for i in range(len(frames)):
        filters.append(f"[{i}:v]scale={W}:{H},fps=30,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[v{i}]")
    overlap = 0.35
    last = "v0"
    for i in range(1, len(frames)):
        nxt = "out" if i == len(frames) - 1 else f"x{i}"
        offset = seconds * i - overlap * i
        filters.append(f"[{last}][v{i}]xfade=transition=fade:duration={overlap}:offset={offset:.2f}[{nxt}]")
        last = nxt
    args += ["-filter_complex", ";".join(filters), "-map", f"[{last}]", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-movflags", "+faststart", str(outfile)]
    subprocess.run(args, check=True)


def main():
    base = app_screen("initial")
    base.save(ASSET_DIR / "main_interface_mock.png", optimize=True)
    scenarios = [
        ("01_排程匯入與核對.mp4", "01｜出貨排程", "匯入 Excel 排程並確認資料", [
            (app_screen("initial"), "啟動系統與確認狀態", ["雙擊「啟動本機視窗版.bat」", "確認地點對照表顯示已找到", "先核對今天要處理的排程"], 0, "對照表狀態應顯示已找到；若未找到，先確認對照表檔案在專案資料夾。"),
            (overlay_dialog(app_screen("initial"), "file_schedule"), "選擇排程檔案", ["按「從 Excel 匯入排程」", "選取排程 Excel 或 CSV 檔", "可一次選取多個檔案"], 1, "影片使用「出貨排程_示範」檔名，實際操作時請選擇當日正式排程。"),
            (overlay_dialog(app_screen("initial"), "import_preview"), "區間查詢與指定筆數", ["起始日填 2026/10/06，結束日填 2026/10/10", "按「查詢」；兩個日曆按鈕可用滑鼠選日期", "選 5／10／20／全部或自訂筆數；可逐列取消勾選"], 1, "日期區間依出貨日期篩選，包含起始日與結束日；跨分頁預覽可核對出貨日、到貨日與地點長代號。"),
            (overlay_dialog(app_screen("initial"), "import_single"), "只填起始日即可查單日", ["起始日填入日期，例如 2026/10/06", "結束日保持空白，不必重複輸入", "按「查詢」後確認預覽及勾選資料"], 1, "結束日留白時，系統以起始日作為查詢日期；日期篩選依出貨日期。"),
            (app_screen("review"), "確認出貨日與到貨日", ["核對批號為 10 碼及地點代號", "分別檢查出貨日期與到貨日期", "確認剩餘天數為匯入的欄位值"], 2, "出貨日期與到貨日期分開保留；剩餘天數必須從 Excel 對應欄位匯入，請勿依保存期限推算代替。"),
        ]),
        ("02_載入生產履歷與COA.mp4", "02｜範本資料", "載入並比對履歷與 COA", [
            (app_screen("review"), "載入生產履歷檔", ["按「載入生產履歷」", "選擇相對應系列的 Chemical_Lorry 範本", "可多選並分次累加載入"], 0, "載入後注意批號比對結果；不同系列的履歷可分批選取。"),
            (overlay_dialog(app_screen("lorry"), "match_status"), "確認履歷及雙日期資料", ["查看每筆批號的找到／找不到結果", "確認出貨日與到貨日分開帶入", "確認後再載入 COA"], 1, "清單顯示本次新增與累計檔數；輸出履歷採用到貨日期，若無到貨日期才使用出貨日期。"),
            (app_screen("lorry"), "載入 COA 表單", ["按「載入 COA 表單」", "選取相應產品系列的 CSV 或 XLSX 範本", "可多選、分批載入"], 1, "COA 以批號進行比對；此操作流程示範 CSV 與 XLSX 表單。"),
            (overlay_dialog(app_screen("coa"), "match_status"), "確認 COA 對應結果", ["檢查已載入檔案數量", "確認批號成功對應", "先處理找不到批號的檔案"], 2, "只有已勾選且可對應的排程資料會參與輸出。"),
        ]),
        ("03_批次產生與輸出檢查.mp4", "03｜批次輸出", "選擇資料夾結構並檢查結果", [
            (app_screen("review"), "執行前最後核對", ["核對批號、地點、數量及兩種日期", "確認剩餘天數是來源欄位值", "確認履歷／COA 已載入並勾選資料列"], 0, "本版批次產生生產履歷及 COA；三合一與運輸通知表目前未啟用。"),
            (app_screen("mode2"), "選擇輸出資料夾模式", ["模式 1：依批號建立子資料夾", "模式 2：直接集中在廠區資料夾", "確認後再按批次產生"], 1, "模式會套用到本次輸出的生產履歷與 COA。"),
            (overlay_dialog(app_screen("output"), "working"), "等待產生完成", ["按「開始批次產生 Excel 報表」", "等待系統顯示完成結果", "產生期間不要關閉程式"], 1, "系統依出貨日期分組建立輸出資料夾。"),
            (overlay_dialog(app_screen("output"), "results"), "檢查輸出結果", ["確認生產履歷與 COA 成功筆數", "按輸出路徑開啟出貨日資料夾", "抽查批號、出貨日、到貨日及剩餘天數"], 2, "履歷日期依到貨日優先、出貨日備援；COA 檢查剩餘天數是否與來源排程相符。"),
        ]),
        ("04_常見狀況處理.mp4", "04｜常見狀況", "排除匯入與輸出錯誤", [
            (app_screen("error"), "地點代號無法對應", ["查看錯誤訊息中的地點", "核對對照表是否包含該代號", "更新檔案後按「重新載入對照表」"], 0, "不建議為了繼續產生而猜填地點長代號。"),
            (overlay_dialog(app_screen("error"), "match_status"), "履歷或 COA 找不到批號", ["檢查排程批號是否完整且為 10 碼", "確認該列已勾選", "確認選到正確系列的來源檔"], 1, "從匯入結果找出未對應項目，再逐一比對來源範本。"),
            (app_screen("error"), "輸出檔案被 Excel 占用", ["關閉正在開啟的來源或輸出活頁簿", "重新確認輸出資料夾權限", "回到系統重新執行批次產生"], 1, "若檔案鎖定，系統會提示檔名；關閉 Excel 後再重新產生。"),
            (app_screen("initial"), "日期與欄位修正後重匯", ["出貨日、到貨日分別核對", "剩餘天數檢查來源欄位名稱", "重新匯入後確認勾選列與筆數"], 2, "日期篩選可指定 YYYY/MM/DD；剩餘天數讀取名稱含「剩餘天數」的來源欄位。"),
        ]),
    ]
    all_chapters = []
    for ix, (filename, chapter, title, scenes) in enumerate(scenarios, start=1):
        paths = []
        title_frame = FRAME_DIR / f"chapter{ix:02d}-title.png"
        slide(title_frame, app_screen("initial"), chapter, title,
              ["依序跟著畫面完成操作", "影片數據均為示範值", "正式產生前請核對來源與輸出路徑"], 0,
              "影片為介面重製示意，沒有讀取或修改正式出貨資料。")
        paths.append(title_frame)
        for jx, (screen, title_text, instructions, active, takeaway) in enumerate(scenes, start=1):
            frame = FRAME_DIR / f"chapter{ix:02d}-step{jx:02d}.png"
            slide(frame, screen, chapter, title_text, instructions, active, takeaway)
            paths.append(frame)
        outfile = VIDEO_DIR / filename
        to_video(outfile, paths)
        all_chapters.append(outfile)
        print(f"created {outfile.name}: {outfile.stat().st_size:,} bytes")

    concat = VIDEO_DIR / "chapters.txt"
    concat.write_text("\n".join(f"file '{p.name}'" for p in all_chapters) + "\n", encoding="utf-8")
    combined = VIDEO_DIR / "N系報表輸出系統_多情境操作影片.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(combined)], check=True)
    concat.unlink(missing_ok=True)
    (VIDEO_DIR / "README.md").write_text(
        "# N 系小包報表輸出系統操作影片\n\n"
        "依據 2026-10-07 的 main.py 版本更新：匯入預覽包含跨分頁、出貨日期區間查詢、起始日單獨查單日、兩個日曆按鈕、筆數選擇、逐列勾選、出貨日／到貨日並列；剩餘天數由 Excel 欄位匯入。影片畫面由程式重製，使用合成批號、品名與範例檔案，是字幕式教學動畫，非正式環境螢幕錄影；未讀取或修改正式出貨資料，也未產生實際報表。\n\n"
        "- `N系報表輸出系統_多情境操作影片.mp4`：四段合輯\n"
        "- `01_排程匯入與核對.mp4`：日期區間、結束日留白查單日、日曆按鈕、筆數篩選與逐列選取；出貨日／到貨日分開檢查\n"
        "- `02_載入生產履歷與COA.mp4`：履歷及 COA 範本載入、批號比對、雙日期確認\n"
        "- `03_批次產生與輸出檢查.mp4`：剩餘天數來源核對、輸出模式、批次產生及結果確認\n"
        "- `04_常見狀況處理.mp4`：地點對照、批號比對、來源欄位及日期修正\n\n"
        "影片右側逐步顯示操作提示，無旁白；所有說明字幕已燒錄在畫面中。\n",
        encoding="utf-8",
    )
    print(f"created {combined.name}: {combined.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
