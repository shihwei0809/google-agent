import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ACTORS_JSON = ROOT / "actors.json"
OUT_PNG = ROOT / "固定演員班底總覽圖.png"


def load_font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/msjhbd.ttc" if bold else "C:/Windows/Fonts/msjh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def build_roster():
    data = json.loads(ACTORS_JSON.read_text(encoding="utf-8"))
    actors = data["actors"]

    # 3 rows (25 / 35 / 45) x 2 cols (Female left, Male right)
    cols = 2
    rows = (len(actors) + cols - 1) // cols
    card_w, card_h = 960, 540
    header_h = 110
    caption_h = 96
    pad = 28
    bg_color = (18, 22, 30)
    card_bg = (28, 34, 46)

    total_w = pad + cols * (card_w + pad)
    total_h = header_h + pad + rows * (card_h + caption_h + pad)
    canvas = Image.new("RGB", (total_w, total_h), bg_color)
    draw = ImageDraw.Draw(canvas)

    f_title = load_font(38, bold=True)
    f_sub = load_font(22, bold=False)
    f_name = load_font(28, bold=True)
    f_desc = load_font(20, bold=False)

    draw.text(
        (pad, 24),
        "固定 AI 演員班底總覽（25 / 35 / 45 歲 萬用定裝照）",
        fill=(245, 248, 255),
        font=f_title,
    )
    draw.text(
        (pad, 72),
        "女角 172cm 長髮清秀  |  男角 178cm 短髮幹練（25/35 歲無鬍子，45 歲極淡成熟短鬚）  |  正面＋微側臉雙角度鎖臉",
        fill=(168, 182, 205),
        font=f_sub,
    )

    for idx, actor in enumerate(actors):
        r = idx // cols
        c = idx % cols
        x0 = pad + c * (card_w + pad)
        y0 = header_h + pad + r * (card_h + caption_h + pad)

        draw.rounded_rectangle(
            [x0, y0, x0 + card_w, y0 + card_h + caption_h],
            radius=16,
            fill=card_bg,
            outline=(56, 68, 92),
            width=2,
        )

        img_path = ROOT / actor["ref_image"]
        if img_path.exists():
            im = Image.open(img_path).convert("RGB")
            # Cover-crop to exact 16:9 card_w x card_h
            tw, th = card_w, card_h
            iw, ih = im.size
            scale = max(tw / iw, th / ih)
            nw, nh = int(round(iw * scale)), int(round(ih * scale))
            im = im.resize((nw, nh), Image.Resampling.LANCZOS)
            left = (nw - tw) // 2
            top = (nh - th) // 2
            im = im.crop((left, top, left + tw, top + th))
            canvas.paste(im, (x0, y0))
        else:
            draw.text((x0 + 40, y0 + 240), f"Missing: {actor['ref_image']}", fill=(255, 110, 110), font=f_name)

        badge = f"[{actor['id']}] {actor['name_zh']} ({actor['name_en']})  ·  {actor['age']} 歲  ·  {actor['height_cm']}cm"
        draw.text((x0 + 20, y0 + card_h + 14), badge, fill=(255, 224, 140), font=f_name)
        uses = " / ".join(actor["use_cases"])
        draw.text((x0 + 20, y0 + card_h + 54), f"適用：{uses}", fill=(205, 214, 228), font=f_desc)

    canvas.save(OUT_PNG, optimize=True)
    print(f"Saved roster image: {OUT_PNG} ({canvas.size[0]}x{canvas.size[1]})")


if __name__ == "__main__":
    build_roster()
