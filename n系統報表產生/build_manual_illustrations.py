from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from build_training_video import app_screen, overlay_dialog

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "tutorial_assets" / "manual_illustrations"
OUT.mkdir(parents=True, exist_ok=True)
FONT = ImageFont.truetype(r"C:\Windows\Fonts\msjhbd.ttc", 20)
SMALL = ImageFont.truetype(r"C:\Windows\Fonts\msjhbd.ttc", 17)
RED = "#e53935"


def draw_arrow(draw, start, end):
    draw.line((start, end), fill=RED, width=5)
    import math
    a = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 16
    p1 = (end[0] - size * math.cos(a - 0.45), end[1] - size * math.sin(a - 0.45))
    p2 = (end[0] - size * math.cos(a + 0.45), end[1] - size * math.sin(a + 0.45))
    draw.polygon((end, p1, p2), fill=RED)


def annotate(name, screen, targets, legend):
    im = screen.convert("RGB")
    d = ImageDraw.Draw(im)
    for i, (box, label, badge) in enumerate(targets, 1):
        x1, y1, x2, y2 = box
        d.rounded_rectangle(box, radius=8, outline=RED, width=5)
        cx, cy = badge
        d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=RED, outline="white", width=3)
        txt = str(i)
        bb = d.textbbox((0, 0), txt, font=FONT)
        d.text((cx - (bb[2]-bb[0])/2, cy - (bb[3]-bb[1])/2 - 2), txt, font=FONT, fill="white")
        tx = (x1 + x2) // 2
        ty = (y1 + y2) // 2
        if abs(cx-tx) + abs(cy-ty) > 180:
            draw_arrow(d, (cx, cy + (22 if cy < ty else -22)), (tx, ty))
    # A persistent footer makes the meaning of the coloured marks clear when images are reused.
    footer_h = 62
    out = Image.new("RGB", (im.width, im.height + footer_h), "white")
    out.paste(im, (0, 0))
    fd = ImageDraw.Draw(out)
    fd.rectangle((0, im.height, out.width, out.height), fill="#fff4f3")
    text = "　　".join(f"{i}｜{item}" for i, item in enumerate(legend, 1))
    x = 24
    for chunk in text.split("　　"):
        fd.text((x, im.height + 16), chunk, font=SMALL, fill="#762622")
        x += fd.textbbox((0, 0), chunk, font=SMALL)[2] + 26
    out.save(OUT / name, optimize=True)


def main():
    annotate(
        "06_主介面操作區標示.png",
        app_screen("initial"),
        [
            ((18, 220, 556, 261), "工具列", (560, 210)),
            ((18, 273, 1262, 336), "輸出模式", (1230, 263)),
            ((18, 347, 1262, 553), "排程與核對", (1230, 340)),
            ((18, 711, 1262, 777), "產生報表", (1230, 701)),
        ],
        ["匯入與載入來源檔", "設定資料夾結構", "檢查各列資料", "開始批次產生"],
    )
    annotate(
        "01_排程預覽標示.png",
        overlay_dialog(app_screen("initial"), "import_preview"),
        [
            ((304, 249, 485, 280), "起始日", (293, 238)),
            ((510, 249, 691, 280), "結束日", (500, 291)),
            ((700, 249, 773, 280), "查詢", (790, 239)),
            ((197, 345, 1066, 482), "預覽", (173, 492)),
            ((781, 623, 925, 671), "確認匯入", (946, 605)),
        ],
        ["起始日／日曆", "結束日／日曆", "查詢日期區間", "核對資料後匯入"],
    )
    annotate(
        "07_單日查詢留白示範.png",
        overlay_dialog(app_screen("initial"), "import_single"),
        [
            ((304, 249, 485, 280), "起始日", (293, 238)),
            ((510, 249, 691, 280), "結束日留白", (500, 291)),
            ((700, 249, 773, 280), "查詢", (790, 239)),
            ((197, 345, 1066, 482), "單日結果", (173, 492)),
        ],
        ["起始日／日曆", "結束日留白", "按查詢", "核對結果"],
    )
    annotate(
        "02_履歷與COA載入標示.png",
        app_screen("review"),
        [
            ((217, 220, 390, 261), "載入生產履歷", (390, 207)),
            ((399, 220, 556, 261), "載入 COA", (564, 207)),
        ],
        ["選取 Chemical_Lorry 範本", "選取 CSV 或 XLSX COA 範本"],
    )
    annotate(
        "03_排程欄位核對標示.png",
        app_screen("review"),
        [
            ((89, 347, 181, 505), "批號 10 碼", (88, 332)),
            ((243, 347, 305, 505), "地點代號", (305, 332)),
            ((381, 347, 472, 505), "出貨日期", (470, 332)),
        ],
        ["每筆必填", "須有對照碼", "確認正確日期"],
    )
    annotate(
        "04_批次產生標示.png",
        app_screen("mode2"),
        [
            ((18, 273, 1262, 336), "輸出資料夾模式", (1224, 264)),
            ((18, 711, 1262, 777), "開始批次產生", (1224, 700)),
        ],
        ["先選模式 1 或 2", "完成核對後再按此按鈕"],
    )
    annotate(
        "05_完成結果標示.png",
        overlay_dialog(app_screen("output"), "results"),
        [
            ((252, 251, 752, 335), "成功筆數", (782, 252)),
            ((252, 359, 1025, 516), "輸出路徑與檔案", (1018, 350)),
        ],
        ["確認生產履歷及 COA 數量", "開啟路徑並抽查檔案"],
    )
    for p in sorted(OUT.glob("*.png")):
        print(f"created {p.name}: {p.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
