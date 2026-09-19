from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "manual_assets" / "current_main_ui.png"
OUT = ROOT / "manual_assets" / "v5_visuals"

try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 24)
except OSError:
    FONT = SMALL = ImageFont.load_default()


def visual(name, crop, boxes, label):
    image = Image.open(SRC).convert("RGB").crop(crop)
    draw = ImageDraw.Draw(image)
    for box in boxes:
        x1, y1, x2, y2 = (box[0] - crop[0], box[1] - crop[1], box[2] - crop[0], box[3] - crop[1])
        # Only frame the control. Explanations belong below the image so the UI remains readable.
        draw.rounded_rectangle((x1, y1, x2, y2), radius=4, outline="#E53935", width=4)
    caption_h = 54
    panel = Image.new("RGB", (image.width, image.height + caption_h), "#F4F8FC")
    panel.paste(image, (0, 0))
    pd = ImageDraw.Draw(panel)
    pd.text((18, image.height + 13), label, font=FONT, fill="#17365D")
    panel.save(OUT / f"{name}.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    visual("01_status", (10, 35, 1265, 170), [
        (380, 95, 500, 123),
        (598, 122, 718, 150),
    ], "步驟 1 先確認範本與對照表，再按需要載入 Chemical Lorry 來源檔")
    visual("02_import", (10, 160, 1265, 210), [
        (25, 169, 165, 198),
        (174, 169, 390, 198),
        (400, 169, 526, 198),
    ], "步驟 2 依工作選擇排程匯入、生產履歷或 COA 表單")
    visual("03_batch", (10, 205, 710, 265), [
        (36, 232, 126, 253),
        (244, 229, 357, 253),
        (363, 229, 430, 253),
    ], "步驟 3 設定批次出貨日期，並套用至已填寫的資料列")
    visual("04_rows", (15, 325, 860, 765), [
        (118, 375, 236, 397),
        (321, 375, 423, 397),
        (544, 375, 650, 397),
        (794, 375, 851, 397),
    ], "步驟 4 填寫並勾選要產生的資料；槽號與長代號會自動帶入")
    visual("05_reports", (15, 260, 1000, 325), [
        (40, 298, 318, 318),
        (352, 298, 749, 318),
    ], "步驟 5 勾選本次要輸出的報表；三合一單為必要選項")
    visual("06_generate", (15, 770, 1260, 835), [
        (24, 781, 1252, 826),
    ], "步驟 6 按開始產生，等待完成訊息並在開啟的資料夾驗收檔案")


if __name__ == "__main__":
    main()
