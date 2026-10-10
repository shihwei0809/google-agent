from __future__ import annotations

import asyncio
import math
import subprocess
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "COA test"
OUT = ROOT / "教學影片_輸出"
FRAMES = OUT / "frames"
AUDIO = OUT / "voice"
W, H = 1280, 720
BG = "#f3f5f8"
INK = "#17212f"
BLUE = "#1976d2"
GREEN = "#278449"
PURPLE = "#7b3fa1"
ORANGE = "#c45b16"
FONT_PATH = r"C:\Windows\Fonts\msjh.ttc"
FONT_BOLD_PATH = r"C:\Windows\Fonts\msjhbd.ttc"

scenes = [
    ("01 開場｜一次整理兩種報表",
     "這是三合一單自動產生器。它能依排程資料，批次產生三合一單 Excel，並可同時輸出生產履歷 Excel，減少逐筆手動製作。接下來依序示範系統檢查、匯入資料與報表輸出。",
     "home", None),
    ("02 系統狀態｜先確認檔案",
     "先看最上方的系統狀態。範本與地點代號對照表都已找到，對照表目前載入三十二筆代號；有更新時，可按重新載入對照表。紅色狀態表示生產履歷尚未載入，等一下會選擇檔案。",
     "status", "status"),
    ("03 載入生產履歷｜選擇 Chemical_Lorry",
     "按載入生產履歷，選取 Chemical_Lorry Excel。成功選取後，狀態顯示已就緒，系統也會自動勾選單列生產履歷報表。這次示範使用你提供的測試檔；載入狀態表示檔案已選取，仍需留意程式提示的批號比對結果。",
     "lorry", "lorry"),
    ("04 匯入排程｜Ctrl 可多選",
     "按從 Excel 匯入排程，再按住 Ctrl 選取多個排程檔。匯入後，批號、地點與出貨日期等欄位會帶入表格；程式也會依地點代號對照表填入槽號、長代號與料號。請確認匯入內容符合當日排程。",
     "import", "import"),
    ("05 手動輸入｜日期與列數工具",
     "沒有排程檔時，也可以直接在表格輸入。批號依欄位提示輸入十碼，地點例如十五 P 五。出貨日期可用日曆挑選，也能按帶入今天日期。資料列不夠時新增十列；單筆可清空，全部重填則使用清除全部資料。",
     "manual", "manual"),
    ("06 載入 COA｜依批號對應",
     "接著按載入 COA 表單，選取當天的 COA CSV。這次測試素材中的 RawLotId 是 26916E3181，與排程中的批號相符，系統便能依批號對應資料。選檔前請確認日期、地點與批號都是本次要產生的資料。",
     "coa", "coa"),
    ("07 報表選擇｜勾選需要的輸出",
     "在欲產生的報表勾選區，可選三合一單 Excel，內容包含 Barcode 與 COA；也可選單列生產履歷 Excel，或兩項一起產生。表格最左側的產生欄，則能取消個別不需處理的資料列。",
     "reports", "reports"),
    ("08 開始產生｜檢查後批次輸出",
     "資料與報表選項確認無誤後，按下開始批次產生 Excel 報表。系統會依已勾選的報表與排程資料執行輸出，完成時顯示結果與儲存位置，並開啟輸出資料夾。此處展示的是操作流程示意。",
     "generate", "generate"),
    ("09 檢視成果｜核對欄位與附件",
     "開啟輸出的三合一單，檢查槽號、料號、長代號，以及 Barcode 和 COA 是否正確；再開啟生產履歷 Excel，確認資料列與槽車充填表內容相符。請依實際檔案逐筆核對。畫面中的成果檔為示意。",
     "results", "results"),
    ("10 結尾｜完成操作流程",
     "以上就是三合一單自動產生器的操作流程：確認系統狀態、載入資料、匯入或輸入排程、選擇報表，最後批次產生並檢視成果。謝謝觀看。",
     "home", None),
]


def font(size: int, bold: bool = False):
    path = FONT_BOLD_PATH if bold and Path(FONT_BOLD_PATH).exists() else FONT_PATH
    return ImageFont.truetype(path, size)


def rr(draw, box, radius=8, fill="white", outline=None, width=1):
    draw.rounded_rectangle(box, radius, fill=fill, outline=outline, width=width)


def fit_text(draw, text, fnt, max_width):
    out, line = [], ""
    for char in text:
        if draw.textbbox((0, 0), line + char, font=fnt)[2] > max_width and line:
            out.append(line)
            line = char
        else:
            line += char
    if line:
        out.append(line)
    return out


def draw_button(d, x, y, label, color, width=150, height=32):
    rr(d, (x, y, x + width, y + height), 5, color)
    d.text((x + 9, y + 6), label, font=font(14, True), fill="white")


def draw_checkbox(d, x, y, label, color=GREEN):
    d.rounded_rectangle((x, y + 1, x + 14, y + 15), radius=2, fill="white", outline=color, width=2)
    d.line((x + 3, y + 8, x + 6, y + 11, x + 11, y + 4), fill=color, width=2)
    d.text((x + 21, y), label, font=font(13), fill=color)


def draw_scene(scene, index):
    title, narration, mode, highlight = scene
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # Header strip
    d.rectangle((0, 0, W, 74), fill="#0e2340")
    d.text((46, 18), "三合一單自動產生器", font=font(27, True), fill="white")
    d.text((W - 380, 26), f"介面重繪示意  ·  {index:02d} / 10", font=font(15), fill="#c6d5ea")
    # Simulated desktop app window
    x0, y0, x1, y1 = 42, 94, 1238, 565
    rr(d, (x0, y0, x1, y1), 10, "white", "#ccd4df", 2)
    d.rectangle((x0 + 2, y0 + 2, x1 - 2, y0 + 38), fill="#e9edf2")
    d.text((x0 + 18, y0 + 10), "三合一單自動產生器", font=font(16, True), fill=INK)
    for i, c in enumerate(("#eb6a5b", "#e9bd45", "#62bd69")):
        d.ellipse((x1 - 72 + i * 18, y0 + 14, x1 - 60 + i * 18, y0 + 26), fill=c)

    # Status panel
    rr(d, (62, 145, 1218, 266), 7, "#fbfcfe", "#c8d0db", 1)
    d.text((78, 151), "系統狀態", font=font(16, True), fill=INK)
    d.text((82, 179), "範本檔案 (台積電槽車barcode三合一單-範本.xlsx):  ✅ 已找到", font=font(13), fill=GREEN)
    d.text((82, 202), "對照表檔案 (地點代號對照表.xlsx):  ✅ 已找到 (載入 32 筆代號)", font=font(13), fill=GREEN)
    lorry_ready = index >= 3
    lorry_name = "✅ 已就緒 (Chemical_Lorry 測試檔)" if lorry_ready else "⚠ 尚未載入"
    lorry_color = GREEN if lorry_ready else "#b53232"
    d.text((82, 225), f"生產履歷檔案 (Chemical_Lorry*.xlsx):  {lorry_name}", font=font(13), fill=lorry_color)
    draw_button(d, 770, 190, "重新載入對照表", "#607d8b", 150, 29)
    draw_button(d, 930, 220, "選擇生產履歷檔", ORANGE, 176, 29)

    # Toolbar
    draw_button(d, 66, 278, "從 Excel 匯入排程", BLUE, 158)
    draw_button(d, 234, 278, "載入生產履歷", ORANGE, 142)
    draw_button(d, 386, 278, "載入 COA 表單", PURPLE, 135)
    draw_button(d, 720, 278, "帶入今天日期", "#546e7a", 130)
    draw_button(d, 858, 278, "新增 10 列", "#00897b", 120)
    draw_button(d, 986, 278, "清除全部資料", "#d32f2f", 140)

    # Report controls
    rr(d, (62, 320, 1218, 375), 6, "#fcfcfd", "#c8d0db")
    d.text((77, 325), "欲產生的報表勾選", font=font(14, True), fill=INK)
    draw_checkbox(d, 80, 348, "產生三合一單 Excel (含 Barcode 與 COA)", GREEN)
    draw_checkbox(d, 495, 348, "產生單列生產履歷 Excel (Chemical_Lorry 槽車充填表)", ORANGE)

    # Table
    left, top = 63, 385
    cols = [(54, "產生"), (58, "項次"), (180, "批號 (10碼)"), (120, "槽號 (自動)"), (132, "地點"), (190, "長代號 (自動)"), (150, "料號 (自動)"), (145, "出貨日期")]
    xx = left
    for cw, label in cols:
        d.rectangle((xx, top, xx + cw, top + 30), fill="#e8eef6", outline="#cdd5df")
        d.text((xx + 6, top + 7), label, font=font(12, True), fill="#26374d")
        xx += cw
    rows = [("", "1", "26916E3181", "E318", "15P5", "E1550L155", "L12C53161", "2026/09/18"),
            ("", "2", "26916E3191", "E319", "15P5", "E1550L155", "L12C53161", "2026/09/18"),
            ("", "3", "", "", "", "", "", "")]
    for ri, row in enumerate(rows):
        yy, xx = top + 30 + ri * 31, left
        for (cw, _), value in zip(cols, row):
            d.rectangle((xx, yy, xx + cw, yy + 31), fill="white", outline="#dce2e9")
            if xx == left:
                draw_checkbox(d, xx + 9, yy + 8, "", GREEN)
            else:
                d.text((xx + 7, yy + 8), value, font=font(12), fill="#485566")
            xx += cw
    d.rectangle((1201, top + 32, 1211, top + 115), fill="#e2e7ee")
    d.rectangle((1202, top + 39, 1210, top + 80), fill="#aab5c3")
    draw_button(d, 900, 510, "開始批次產生 Excel 報表", "#43a047", 296, 39)

    # Per-scene callout focus
    focus_boxes = {
        "status": (66, 143, 1215, 266), "lorry": (926, 215, 1110, 254),
        "import": (64, 276, 230, 315), "manual": (720, 275, 1130, 317),
        "coa": (383, 276, 525, 315), "reports": (66, 320, 1215, 375),
        "generate": (894, 506, 1203, 554),
    }
    if mode == "results":
        # Sample output preview cards
        d.rectangle((65, 147, 625, 500), fill="white", outline="#b8c4d1", width=2)
        d.text((88, 165), "三合一單 Excel  ·  成果檢視示意", font=font(18, True), fill=INK)
        d.text((90, 209), "批號　 26916E3181　｜　槽號　 E318", font=font(17), fill=INK)
        d.text((90, 245), "料號　 L12C53161", font=font(17), fill=INK)
        d.text((90, 281), "長代號　 E1550L155　｜　地點　 15P5", font=font(17), fill=INK)
        # QR-like visual placeholder
        for yy in range(0, 9):
            for xx in range(0, 9):
                if (xx * yy + xx + yy) % 3:
                    d.rectangle((430 + xx * 12, 205 + yy * 12, 439 + xx * 12, 214 + yy * 12), fill="#162638")
        d.text((438, 322), "QR 示意", font=font(12), fill="#637083")
        d.rectangle((650, 147, 1214, 500), fill="white", outline="#b8c4d1", width=2)
        d.text((673, 165), "生產履歷 Excel  ·  欄位檢視示意", font=font(18, True), fill=INK)
        for i, label in enumerate(("批號", "廠區", "槽車充填資料", "出貨日期")):
            d.rectangle((680, 213 + i * 53, 1180, 256 + i * 53), fill="#f8fafc", outline="#d6dee7")
            d.text((695, 226 + i * 53), f"{label}　　 依實際輸出檔核對", font=font(14), fill="#425168")
        d.text((672, 445), "以上為介面重繪與測試資料預覽，影片未執行報表產生。", font=font(13), fill="#a24c22")

    if mode == "coa":
        # Actual file names from the provided COA test folder, shown as a file-picker illustration.
        rr(d, (409, 143, 1116, 496), 8, "#ffffff", "#9eabba", 2)
        d.rectangle((411, 145, 1114, 184), fill="#edf1f6")
        d.text((430, 155), "選擇要載入的 COA 表單 (可多選)", font=font(16, True), fill=INK)
        d.text((432, 195), "名稱", font=font(13, True), fill="#4b5a6d")
        csv_files = sorted(DATA.glob("*.CSV"))
        for i, f in enumerate(csv_files[:6]):
            yy = 222 + i * 32
            if "0916 15P5.CSV" in f.name:
                d.rectangle((425, yy - 3, 1098, yy + 26), fill="#dcecff")
            d.text((438, yy), f.name, font=font(12), fill="#26384e")
        d.text((432, 439), "RawLotId：26916E3181  ·  DeliverDate：2026/9/18", font=font(14, True), fill=PURPLE)
        d.text((432, 466), "選取與排程批號相符的 COA CSV", font=font(13), fill="#526177")
        draw_button(d, 950, 455, "開啟", BLUE, 66, 29)

    if highlight in focus_boxes:
        b = focus_boxes[highlight]
        d.rounded_rectangle(b, radius=7, outline="#ffb000", width=4)
    # Title and subtitle area
    d.text((48, 588), title, font=font(24, True), fill="#0e2340")
    d.text((49, 625), f"第 {index:02d} 段 / 10 段", font=font(14), fill="#607087")
    sub_lines = fit_text(d, narration, font(19), 1160)
    for j, line in enumerate(sub_lines[:2]):
        d.text((48, 654 + j * 25), line, font=font(18), fill="#29364a")
    return im


async def make_audio(path: Path, text: str):
    communicator = edge_tts.Communicate(text, "zh-TW-HsiaoChenNeural", rate="+25%", volume="+0%", pitch="+0Hz")
    await communicator.save(str(path))


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


async def main():
    OUT.mkdir(exist_ok=True)
    FRAMES.mkdir(exist_ok=True)
    AUDIO.mkdir(exist_ok=True)
    segs = []
    for i, scene in enumerate(scenes, 1):
        title, narration, mode, highlight = scene
        frame = FRAMES / f"scene_{i:02d}.png"
        voice = AUDIO / f"scene_{i:02d}.mp3"
        clip = OUT / f"clip_{i:02d}.mp4"
        draw_scene(scene, i).save(frame)
        await make_audio(voice, narration)
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(voice)], capture_output=True, text=True, check=True)
        duration = float(probe.stdout.strip()) + 0.8
        run(["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(frame), "-i", str(voice),
             "-t", f"{duration:.3f}", "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(clip)])
        segs.append(clip)
    listfile = OUT / "concat.txt"
    listfile.write_text("\n".join(f"file '{p.as_posix()}'" for p in segs), encoding="utf-8")
    final = OUT / "三合一單自動產生器_操作教學.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile), "-c", "copy", "-movflags", "+faststart", str(final)])
    (OUT / "旁白稿.txt").write_text("\n\n".join(f"{s[0]}\n{s[1]}" for s in scenes), encoding="utf-8")
    print(final)
    print(f"Voice: zh-TW-HsiaoChenNeural, Female, rate +25% (1.25x). Scenes: {len(scenes)}")


if __name__ == "__main__":
    asyncio.run(main())
