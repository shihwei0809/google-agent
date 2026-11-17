"""
BPM 一般費用報銷單（私車公用）混合雙軌分鏡生成器 & 1080p 有聲教學影片管線
===========================================================================
功能：
1. 自動從 C:\\GOOGLE ANGET\\BPM一般費用報銷單_私車公用操作流程.docx 抽取 11 張高清操作截圖
2. 自動生成 Google Flow (Frames to Video) 專用之 3 組 1280x720 情境首尾幀圖檔 (Shot 01 / 05 / 08)
3. 使用 edge-tts (zh-TW-HsiaoChenNeural) 合成 8 段台灣女聲旁白 MP3（離線時自動降級 Windows SAPI5）
4. 以 Pillow + FFmpeg 渲染 8 段 1920x1080 24fps 分鏡影片：
   - UI 導覽鏡 (Shot 02, 03, 04, 06, 07)：原圖高清呈現 + 動態紅框聚焦 + 放大提示 + 字幕
   - Flow 情境鏡 (Shot 01, 05, 08)：優先嵌入 bpm_sop/flow_clips/shotXX_flow.mp4；未匯入時自動以首尾幀與佐證圖合成動態轉場
5. 無縫串接為總片 bpm_sop/BPM_一般費用報銷單_私車公用教學總片.mp4 並輸出 storyboard_manifest.json
"""

import argparse
import asyncio
import io
import json
import math
import os
import shutil
import ssl
import subprocess
import sys
import wave
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE_DIR = Path(__file__).resolve().parent
SOP_DOCX = BASE_DIR.parent / "BPM一般費用報銷單_私車公用操作流程.docx"
OUT_ROOT = BASE_DIR / "bpm_sop"
FIG_DIR = OUT_ROOT / "figures"
FLOW_FRAMES_DIR = OUT_ROOT / "flow_frames"
FLOW_CLIPS_DIR = OUT_ROOT / "flow_clips"
AUDIO_DIR = OUT_ROOT / "audio"
CLIPS_DIR = OUT_ROOT / "clips"
MANIFEST_PATH = OUT_ROOT / "storyboard_manifest.json"
FINAL_VIDEO_PATH = OUT_ROOT / "BPM_一般費用報銷單_私車公用教學總片.mp4"

VIDEO_W, VIDEO_H = 1920, 1080
FLOW_W, FLOW_H = 1280, 720
FPS = 24

FIGURE_FILENAMES = [
    "fig01_entry_epm.png",
    "fig02_trip_selector.jpg",
    "fig03_a05_mileage.jpg",
    "fig04_a05_list_check.jpg",
    "fig05_a07_etag.jpg",
    "fig06_etag_record.jpg",
    "fig07_route_go.jpg",
    "fig08_route_back.jpg",
    "fig09_multi_list.jpg",
    "fig10_a01_hsr.png",
    "fig11_a06_parking.png",
]

FIGURE_CAPTIONS = {
    "fig01_entry_epm.png": "圖 1　由流程處理頁進入 EPM 的一般費用報銷單",
    "fig02_trip_selector.jpg": "圖 2　出差登記單號資料選取與帶入欄位",
    "fig03_a05_mileage.jpg": "圖 3　A05 私車公用費用明細欄位",
    "fig04_a05_list_check.jpg": "圖 4　A07 eTag 明細輸入與下方 A05 列表對照",
    "fig05_a07_etag.jpg": "圖 5　其他出差費用明細欄位示例",
    "fig06_etag_record.jpg": "圖 6　遠通電收 ETag 通行費明細紀錄示例",
    "fig07_route_go.jpg": "圖 7　去程路線與里程示例（約 188 公里）",
    "fig08_route_back.jpg": "圖 8　回程路線與里程示例（約 195 公里）",
    "fig09_multi_list.jpg": "圖 9　多筆費用明細完成後的列表檢查",
    "fig10_a01_hsr.png": "圖 10　A01 高鐵費用明細示例",
    "fig11_a06_parking.png": "圖 11　A06 停車費明細示例",
}


# ---------------------------------------------------------------------------
# 字型與 FFmpeg 偵測
# ---------------------------------------------------------------------------

def find_font_path(bold: bool = False) -> str:
    candidates = (
        [
            r"C:\Windows\Fonts\msjhbd.ttc",
            r"C:\Windows\Fonts\NotoSansTC-VF.ttf",
            r"C:\Windows\Fonts\msjh.ttc",
        ]
        if bold
        else [
            r"C:\Windows\Fonts\msjh.ttc",
            r"C:\Windows\Fonts\NotoSansTC-VF.ttf",
            r"C:\Windows\Fonts\mingliu.ttc",
        ]
    )
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("找不到可用的繁體中文字型 (msjh.ttc / NotoSansTC-VF.ttf)")


FONT_REGULAR_PATH = find_font_path(bold=False)
FONT_BOLD_PATH = find_font_path(bold=True)
_FONT_CACHE: Dict[Tuple[bool, int], ImageFont.FreeTypeFont] = {}


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (bold, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(FONT_BOLD_PATH if bold else FONT_REGULAR_PATH, size)
    return _FONT_CACHE[key]


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    raise FileNotFoundError("找不到 ffmpeg，請先執行 winget install Gyan.FFmpeg 或 pip install imageio-ffmpeg")


def find_ffprobe(ffmpeg_exe: str) -> Optional[str]:
    probe = shutil.which("ffprobe")
    if probe:
        return probe
    candidate = Path(ffmpeg_exe).with_name("ffprobe.exe")
    return str(candidate) if candidate.exists() else None


def get_media_duration(ffmpeg_exe: str, media_path: Path) -> float:
    ffprobe = find_ffprobe(ffmpeg_exe)
    if ffprobe:
        out = subprocess.check_output(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(media_path),
            ],
            text=True,
        ).strip()
        if out:
            return max(3.0, float(out))
    return 10.0


# ---------------------------------------------------------------------------
# 1. 從 SOP Word 檔抽取 11 張高清圖
# ---------------------------------------------------------------------------

def extract_figures_from_docx() -> List[Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    if not SOP_DOCX.exists():
        existing = [FIG_DIR / name for name in FIGURE_FILENAMES if (FIG_DIR / name).exists()]
        if len(existing) == len(FIGURE_FILENAMES):
            print(f"[略過抽圖] 找不到 {SOP_DOCX.name}，沿用既有的 11 張圖片。")
            return existing
        raise FileNotFoundError(f"找不到 SOP Word 檔案：{SOP_DOCX}")

    extracted: List[Path] = []
    with zipfile.ZipFile(SOP_DOCX, "r") as zf:
        rels = ET.fromstring(zf.read("word/_rels/document.xml.rels"))
        rid_map = {
            r.attrib["Id"]: r.attrib["Target"]
            for r in rels
            if "image" in r.attrib.get("Type", "")
        }
        doc = ET.fromstring(zf.read("word/document.xml"))
        idx = 0
        for p in doc.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
            for blip in p.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}blip"):
                if idx >= len(FIGURE_FILENAMES):
                    break
                rid = blip.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                target = rid_map.get(rid)
                if not target:
                    continue
                out_path = FIG_DIR / FIGURE_FILENAMES[idx]
                out_path.write_bytes(zf.read("word/" + target))
                extracted.append(out_path)
                idx += 1
    print(f"[1/5] 已從 {SOP_DOCX.name} 抽取 {len(extracted)} 張圖片至 {FIG_DIR}")
    apply_figure_privacy_and_official_assets()
    return extracted


def apply_figure_privacy_and_official_assets():
    """確保個資打碼（住家地址）與使用含專用章之 ETC 官方紀錄 PDF。"""
    # 1. 路線圖住家地址馬賽克遮蔽
    for fname, (x1, y1, x2, y2) in [
        ("fig07_route_go.jpg", (70, 93, 340, 126)),
        ("fig08_route_back.jpg", (70, 227, 340, 260)),
    ]:
        p = FIG_DIR / fname
        if p.exists():
            im = Image.open(p).convert("RGB")
            reg = im.crop((x1, y1, x2, y2))
            small = reg.resize(((x2 - x1) // 8, (y2 - y1) // 4), Image.Resampling.NEAREST)
            pix = small.resize((x2 - x1, y2 - y1), Image.Resampling.NEAREST)
            im.paste(pix, (x1, y1))
            d = ImageDraw.Draw(im)
            d.rectangle([x1, y1, x2, y2], outline=(180, 180, 180), width=1)
            im.save(p)

    # 2. 官方含專用章之 ETC 憑證切圖覆蓋
    pdf_candidates = [
        Path(r"C:\Users\C606\.gemini\antigravity\brain\a974002d-4878-4028-b8dd-8fbcb92fccb4\.user_uploaded\media_1794909786197_25bad80c.pdf"),
        FIG_DIR / "fig06_etag_official_pdf.png",
    ]
    for cand in pdf_candidates:
        if cand.suffix.lower() == ".pdf" and cand.exists():
            try:
                import fitz
                doc = fitz.open(str(cand))
                pix = doc[0].get_pixmap(dpi=200)
                full_im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                crop_etc = full_im.crop((120, 220, 1540, 1400))
                crop_etc.save(FIG_DIR / "fig06_etag_record.jpg")
                crop_etc.save(FIG_DIR / "fig06_etag_official_pdf.png")
                break
            except Exception:
                pass
        elif cand.suffix.lower() == ".png" and cand.exists():
            im = Image.open(cand)
            im.save(FIG_DIR / "fig06_etag_record.jpg")
            break


# ---------------------------------------------------------------------------
# 2. 生成 Google Flow 3 個情境分鏡的首尾幀 (1280x720 PNG)
# ---------------------------------------------------------------------------

def draw_vertical_gradient(img: Image.Image, top_rgb: Tuple[int, int, int], bot_rgb: Tuple[int, int, int]):
    w, h = img.size
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top_rgb[0] * (1 - t) + bot_rgb[0] * t)
        g = int(top_rgb[1] * (1 - t) + bot_rgb[1] * t)
        b = int(top_rgb[2] * (1 - t) + bot_rgb[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def draw_car(draw: ImageDraw.Draw, cx: int, cy: int, scale: float = 1.0, body=(226, 232, 240)):
    s = scale
    # Shadow
    draw.ellipse([cx - 110 * s, cy + 28 * s, cx + 110 * s, cy + 52 * s], fill=(15, 23, 42))
    # Lower body
    draw.rounded_rectangle(
        [cx - 96 * s, cy - 12 * s, cx + 96 * s, cy + 34 * s],
        radius=int(18 * s),
        fill=body,
        outline=(148, 163, 184),
        width=max(2, int(2 * s)),
    )
    # Cabin
    draw.polygon(
        [
            (cx - 58 * s, cy - 10 * s),
            (cx - 34 * s, cy - 48 * s),
            (cx + 36 * s, cy - 48 * s),
            (cx + 62 * s, cy - 10 * s),
        ],
        fill=(30, 41, 59),
        outline=(148, 163, 184),
    )
    # Windshield highlight
    draw.polygon(
        [
            (cx - 46 * s, cy - 13 * s),
            (cx - 28 * s, cy - 42 * s),
            (cx + 28 * s, cy - 42 * s),
            (cx + 46 * s, cy - 13 * s),
        ],
        fill=(56, 189, 248),
    )
    # Headlights
    draw.rounded_rectangle([cx - 86 * s, cy + 2 * s, cx - 56 * s, cy + 16 * s], radius=4, fill=(254, 240, 138))
    draw.rounded_rectangle([cx + 56 * s, cy + 2 * s, cx + 86 * s, cy + 16 * s], radius=4, fill=(254, 240, 138))
    # Grille & license plate hint
    draw.rounded_rectangle([cx - 28 * s, cy + 12 * s, cx + 28 * s, cy + 27 * s], radius=4, fill=(15, 23, 42))
    # Wheels
    draw.rounded_rectangle([cx - 84 * s, cy + 26 * s, cx - 52 * s, cy + 46 * s], radius=6, fill=(15, 23, 42))
    draw.rounded_rectangle([cx + 52 * s, cy + 26 * s, cx + 84 * s, cy + 46 * s], radius=6, fill=(15, 23, 42))


def generate_flow_keyframes() -> Dict[str, Tuple[Path, Path]]:
    FLOW_FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, Tuple[Path, Path]] = {}

    # --- Shot 01 First: Highway + eTag Gantry + Sedan ---
    s1_first = Image.new("RGB", (FLOW_W, FLOW_H))
    draw_vertical_gradient(s1_first, (12, 32, 68), (56, 128, 196))
    d = ImageDraw.Draw(s1_first)
    # Sun glow & distant hills
    d.ellipse([900, 70, 1120, 290], fill=(253, 224, 140))
    d.polygon([(0, 410), (260, 320), (540, 375), (840, 305), (1280, 390), (1280, 440), (0, 440)], fill=(30, 64, 92))
    # Ground & Highway perspective
    d.rectangle([0, 420, FLOW_W, FLOW_H], fill=(22, 58, 52))
    d.polygon([(520, 420), (760, 420), (1180, 720), (100, 720)], fill=(51, 65, 85))
    d.polygon([(540, 420), (552, 420), (170, 720), (140, 720)], fill=(250, 204, 21))
    d.polygon([(728, 420), (740, 420), (1140, 720), (1110, 720)], fill=(250, 204, 21))
    for i in range(6):
        y1 = 440 + i * 44
        y2 = y1 + 22
        w1 = 4 + i * 2
        d.polygon([(640 - w1, y1), (640 + w1, y1), (640 + w1 + 2, y2), (640 - w1 - 2, y2)], fill=(241, 245, 249))
    # eTag Gantry
    d.rectangle([250, 190, 276, 560], fill=(203, 213, 225), outline=(100, 116, 139))
    d.rectangle([1004, 190, 1030, 560], fill=(203, 213, 225), outline=(100, 116, 139))
    d.rounded_rectangle([220, 165, 1060, 238], radius=14, fill=(14, 116, 144), outline=(56, 189, 248), width=4)
    d.text((545, 184), "eTag", fill=(255, 255, 255), font=get_font(36, bold=True))
    # Glowing cyan route wave
    d.arc([470, 238, 810, 390], start=20, end=160, fill=(56, 189, 248), width=5)
    draw_car(d, 640, 575, scale=1.35)
    p1_f = FLOW_FRAMES_DIR / "bpm_shot01_first.png"
    s1_first.save(p1_f)

    # --- Shot 01 Last: Arrival at Modern Steel Plant Gate ---
    s1_last = Image.new("RGB", (FLOW_W, FLOW_H))
    draw_vertical_gradient(s1_last, (24, 48, 88), (125, 178, 218))
    d = ImageDraw.Draw(s1_last)
    d.rectangle([0, 440, FLOW_W, FLOW_H], fill=(71, 85, 105))
    d.polygon([(0, 520), (1280, 520), (1280, 720), (0, 720)], fill=(51, 65, 85))
    # Industrial plant buildings
    d.rounded_rectangle([140, 180, 820, 460], radius=12, fill=(30, 41, 59), outline=(100, 116, 139), width=3)
    for gx in range(180, 790, 95):
        d.rectangle([gx, 240, gx + 65, 390], fill=(56, 189, 248), outline=(148, 163, 184), width=2)
    # Plant banner
    d.rounded_rectangle([240, 130, 720, 195], radius=10, fill=(15, 23, 42), outline=(56, 189, 248), width=3)
    d.text((310, 146), "IPA 鋼板材料廠", fill=(248, 250, 252), font=get_font(30, bold=True))
    # Gate arm & car parked
    d.rectangle([860, 290, 960, 460], fill=(226, 232, 240))
    d.rectangle([760, 340, 880, 355], fill=(16, 185, 129))
    draw_car(d, 560, 585, scale=1.45, body=(241, 245, 249))
    # Clean phone map card on right
    d.rounded_rectangle([960, 140, 1210, 450], radius=24, fill=(15, 23, 42), outline=(148, 163, 184), width=4)
    d.rounded_rectangle([978, 170, 1192, 420], radius=14, fill=(248, 250, 252))
    d.line([(1030, 220), (1120, 290), (1080, 370)], fill=(37, 99, 235), width=8)
    d.ellipse([1018, 208, 1042, 232], fill=(16, 185, 129))
    d.ellipse([1068, 358, 1092, 382], fill=(239, 68, 68))
    p1_l = FLOW_FRAMES_DIR / "bpm_shot01_last.png"
    s1_last.save(p1_l)
    paths["bpm_shot01"] = (p1_f, p1_l)

    # --- Shot 05 First: High Speed Rail Station Platform ---
    s5_first = Image.new("RGB", (FLOW_W, FLOW_H))
    draw_vertical_gradient(s5_first, (15, 23, 42), (51, 65, 85))
    d = ImageDraw.Draw(s5_first)
    # Glass canopy ribs
    for x in range(100, 1250, 180):
        d.line([(x, 0), (x + 80, 320)], fill=(100, 116, 139), width=4)
    d.rectangle([0, 480, FLOW_W, FLOW_H], fill=(71, 85, 105))
    d.rectangle([0, 474, FLOW_W, 488], fill=(250, 204, 21))
    # Streamlined HSR train body
    d.polygon([(80, 280), (880, 280), (1120, 385), (1090, 470), (80, 470)], fill=(248, 250, 252), outline=(148, 163, 184))
    d.polygon([(80, 405), (1110, 405), (1096, 442), (80, 442)], fill=(234, 88, 12))
    d.polygon([(860, 295), (1020, 355), (900, 365)], fill=(15, 23, 42))
    for wx in range(140, 820, 110):
        d.rounded_rectangle([wx, 315, wx + 78, 370], radius=10, fill=(30, 58, 138))
    p5_f = FLOW_FRAMES_DIR / "bpm_shot05_first.png"
    s5_first.save(p5_f)

    # --- Shot 05 Last: Modern Parking Garage Gate & Ticket Kiosk ---
    s5_last = Image.new("RGB", (FLOW_W, FLOW_H))
    draw_vertical_gradient(s5_last, (30, 41, 59), (71, 85, 105))
    d = ImageDraw.Draw(s5_last)
    d.rectangle([0, 470, FLOW_W, FLOW_H], fill=(51, 65, 85))
    # Parking ceiling lights
    for lx in range(160, 1160, 260):
        d.rounded_rectangle([lx, 60, lx + 160, 82], radius=8, fill=(224, 242, 254))
    # Kiosk + rising barrier arm
    d.rounded_rectangle([240, 210, 430, 540], radius=16, fill=(15, 23, 42), outline=(56, 189, 248), width=4)
    d.rounded_rectangle([268, 245, 402, 345], radius=10, fill=(16, 185, 129))
    d.text((310, 276), "P", fill=(255, 255, 255), font=get_font(44, bold=True))
    d.polygon([(430, 355), (1060, 180), (1070, 212), (430, 388)], fill=(239, 68, 68))
    # Crisp parking receipt card on right
    d.rounded_rectangle([740, 210, 1080, 560], radius=18, fill=(248, 250, 252), outline=(203, 213, 225), width=4)
    d.text((805, 248), "統一發票", fill=(15, 23, 42), font=get_font(34, bold=True))
    d.line([(780, 305), (1040, 305)], fill=(148, 163, 184), width=3)
    d.text((795, 340), "停車費用明細", fill=(51, 65, 85), font=get_font(26))
    d.text((795, 410), "NT$ 152 + 稅", fill=(220, 38, 38), font=get_font(32, bold=True))
    p5_l = FLOW_FRAMES_DIR / "bpm_shot05_last.png"
    s5_last.save(p5_l)
    paths["bpm_shot05"] = (p5_f, p5_l)

    # --- Shot 08 First: Applicant Desk Organizing Originals ---
    s8_first = Image.new("RGB", (FLOW_W, FLOW_H))
    draw_vertical_gradient(s8_first, (241, 245, 249), (203, 213, 225))
    d = ImageDraw.Draw(s8_first)
    d.rectangle([0, 420, FLOW_W, FLOW_H], fill=(180, 138, 96))
    # Printed BPM folder
    d.rounded_rectangle([240, 180, 680, 560], radius=16, fill=(255, 255, 255), outline=(59, 130, 246), width=5)
    d.rectangle([240, 180, 680, 245], fill=(37, 99, 235))
    d.text((310, 195), "BPM 報銷單正本", fill=(255, 255, 255), font=get_font(32, bold=True))
    for ly in range(280, 500, 48):
        d.rounded_rectangle([285, ly, 635, ly + 18], radius=6, fill=(226, 232, 240))
    # Stapled receipts on right
    d.rounded_rectangle([740, 220, 1020, 520], radius=12, fill=(254, 249, 195), outline=(234, 179, 8), width=4)
    d.text((795, 255), "發票 / 收據", fill=(113, 63, 18), font=get_font(30, bold=True))
    d.text((810, 330), "正本附件", fill=(161, 98, 7), font=get_font(28))
    p8_f = FLOW_FRAMES_DIR / "bpm_shot08_first.png"
    s8_first.save(p8_f)

    # --- Shot 08 Last: HR Verified -> Accounting Approval ---
    s8_last = Image.new("RGB", (FLOW_W, FLOW_H))
    draw_vertical_gradient(s8_last, (15, 23, 42), (30, 58, 95))
    d = ImageDraw.Draw(s8_last)
    cards = [
        (110, (56, 189, 248), "1. 申請人", "整理正本交件"),
        (470, (16, 185, 129), "2. 人事核對", "確認金額與附件"),
        (830, (245, 158, 11), "3. 會計審核", "入帳與核銷完成"),
    ]
    for idx, (x, col, title, desc) in enumerate(cards):
        d.rounded_rectangle([x, 210, x + 330, 490], radius=24, fill=(30, 41, 59), outline=col, width=5)
        d.rounded_rectangle([x + 28, 245, x + 302, 315], radius=14, fill=col)
        d.text((x + 64, 260), title, fill=(15, 23, 42), font=get_font(32, bold=True))
        d.text((x + 56, 375), desc, fill=(241, 245, 249), font=get_font(28, bold=True))
        if idx < 2:
            ax = x + 338
            d.polygon([(ax, 340), (ax + 16, 355), (ax, 370)], fill=(248, 250, 252))
    p8_l = FLOW_FRAMES_DIR / "bpm_shot08_last.png"
    s8_last.save(p8_l)
    paths["bpm_shot08"] = (p8_f, p8_l)

    print(f"[2/5] 已生成 3 組 Google Flow 情境首尾幀 (1280x720) 至 {FLOW_FRAMES_DIR}")
    return paths


# ---------------------------------------------------------------------------
# 3. 定義 8 大分鏡劇本與 UI 高清紅框座標
# ---------------------------------------------------------------------------

SHOTS: List[dict] = [
    {
        "id": "shot01",
        "index": 1,
        "title": "行前準備：核准出差單、實際路線圖與 eTag 明細",
        "chapter": "一～二、流程總覽與申請前實務準備",
        "engine": "ui",
        "kind": "prep_three",
        "figures": ["fig07_route_go.jpg", "fig08_route_back.jpg", "fig06_etag_record.jpg"],
        "narration": (
            "要報銷開車出差的費用，出發前先準備好三項實際佐證資料："
            "第一是本人已經核准的出差登記單；"
            "第二是用 Google 地圖截下當次實際去程與回程的路線里程圖，每個人的距離都不同，依實際跑多少公里計算；"
            "第三則是遠通 eTag 官方下載的通行費紀錄列印單，記得一定要有遠通電收的電子憑證專用章，不能只用線上即時截圖喔！"
        ),
        "subtitle": "出差三寶：本人核准出差單 ＋ 實際去回程路線截圖 ＋ 含專用章之 eTag 官方紀錄",
        "key_points": ["本人核准出差單", "依個人實距截圖計算", "含專用章之 eTag 官方紀錄"],
    },
    {
        "id": "shot02",
        "index": 2,
        "title": "開啟 BPM 報銷單並選取本人當次出差單號",
        "chapter": "三～四、進入一般費用報銷單與帶入出差單",
        "engine": "ui",
        "figures": ["fig01_entry_epm.png", "fig02_trip_selector.jpg"],
        "beats": [
            {
                "figure": "fig01_entry_epm.png",
                "zoom": 1.08,
                "boxes": [
                    {
                        "box": (0.26, 0.20, 0.75, 0.46),
                        "label": "步驟 1：進入 EPM → 點選「一般費用報銷單」",
                        "color": "gold",
                        "label_pos": "top",
                    },
                ],
                "caption": "確認表頭：依實際所屬公司別、申請人／部門、申請日期與幣別核對填寫",
            },
            {
                "figure": "fig02_trip_selector.jpg",
                "zoom": 1.06,
                "boxes": [
                    {
                        "box": (0.02, 0.28, 0.92, 0.81),
                        "label": "步驟 2：點查詢鈕，選擇你這趟實際出差的單號（畫面僅為範例）",
                        "color": "cyan",
                        "label_pos": "top",
                    },
                ],
                "caption": "請務必選擇本人當次出差單號，不可照抄範例；核對出差日期、地點與事由皆正確",
            },
        ],
        "narration": (
            "進到鼎新 BPM 系統後，點選 EPM 裡面的『一般費用報銷單』，"
            "先確認表頭的公司別、部門跟申請日期。接著到下方費用明細，"
            "點『出差登記單號』旁邊的查詢鈕，選擇你這趟實際出差的單號，不要選錯張，"
            "再核對帶入的日期、地點跟出差事由都與本人實際行程一致。"
        ),
        "subtitle": "進入 EPM 一般費用報銷單 → 查詢並選取你所出差的登記單號（勿照抄範例）",
        "key_points": ["EPM 一般費用報銷單", "選取本人當次出差單號", "核對實際日期與地點"],
    },
    {
        "id": "shot03",
        "index": 3,
        "title": "私車公用 A05：務必修改「憑證日期」並依實距填寫",
        "chapter": "五、新增私車公用費用明細（含憑證日期修改提醒）",
        "engine": "ui",
        "figures": ["fig03_a05_mileage.jpg"],
        "beats": [
            {
                "figure": "fig03_a05_mileage.jpg",
                "zoom": 1.02,
                "boxes": [
                    {
                        "box": (0.505, 0.048, 0.992, 0.136),
                        "label": "1. 憑證日期：務必改為實際出差／憑證日期",
                        "color": "cyan",
                        "label_pos": "left",
                    },
                    {
                        "box": (0.015, 0.132, 0.880, 0.292),
                        "label": "2. 選 A05 私車公用｜依個人實際里程與公司單價計算金額（T05 免稅）",
                        "color": "gold",
                        "label_pos": "bottom",
                    },
                ],
                "caption": "會計重點提醒：右上角「憑證日期」須改為實際日期！金額依個人實際公里數計算（圖僅範例）",
            },
            {
                "figure": "fig03_a05_mileage.jpg",
                "zoom": 1.08,
                "boxes": [
                    {
                        "box": (0.015, 0.665, 0.985, 0.885),
                        "label": "3. 選實際費用地區、於費用說明填入本人車號或去回程 → 按「新增」",
                        "color": "gold",
                        "label_pos": "top",
                    },
                ],
                "caption": "費用地區須與實際出差地點一致，費用說明務必註明實際自用車車牌號碼再按新增",
            },
        ],
        "narration": (
            "接下來新增私車公用里程費。請先注意右上角的『憑證日期』，"
            "記得一定要修改為這筆費用的實際發生或憑證日期，不要漏掉喔！"
            "接著費用類別選 A05『國內出差私車公用』，金額依照你自己實際跑了幾公里、"
            "按公司核定單價計算後再填寫，稅別碼選 T05 免稅；最後選實際費用地區，並在費用說明寫上本人車牌號碼後按『新增』。"
        ),
        "subtitle": "重點：右上角「憑證日期」必改為實際日期！A05 依個人實距計費並註明車號 → 按「新增」",
        "key_points": ["憑證日期須改為實際日期", "A05 依個人實距計費", "說明填本人車牌號碼"],
    },
    {
        "id": "shot04",
        "index": 4,
        "title": "ETag 通行費獨立列示（費用類別 A07）",
        "chapter": "六～七、新增通行費與 eTag 費用明細",
        "engine": "ui",
        "figures": ["fig06_etag_record.jpg", "fig04_a05_list_check.jpg"],
        "beats": [
            {
                "figure": "fig06_etag_record.jpg",
                "zoom": 1.02,
                "boxes": [
                    {
                        "box": (0.040, 0.590, 0.960, 0.720),
                        "label": "1. 須下載含專用章之官方紀錄 PDF，依實扣 18 元登打",
                        "color": "gold",
                        "label_pos": "top",
                    },
                    {
                        "box": (0.590, 0.760, 0.960, 0.940),
                        "label": "2. 遠通電收電子憑證專用章（不可僅用未出帳線上截圖）",
                        "color": "cyan",
                        "label_pos": "left",
                    },
                ],
                "info_card": {
                    "title": "【會計實務提醒｜eTag 通行費憑證規範】",
                    "border": "gold",
                    "lines": [
                        "1. 高速公路通行費佐證，請至遠通網站下載含「電子憑證專用章」之官方紀錄 PDF 列印。",
                        "2. 不可僅使用未出帳或即時扣款的網頁線上截圖，須具備遠通專用章始符合稅務報銷規定。",
                        "3. 請依單據上實際扣款金額登打，並獨立新增費用類別 A07，嚴禁併入 A05 私車里程費。",
                    ],
                },
                "caption": "通行費憑證必備：下載含「電子憑證專用章」之官方紀錄 PDF，依實扣金額登打",
            },
            {
                "figure": "fig04_a05_list_check.jpg",
                "zoom": 1.02,
                "boxes": [
                    {
                        "box": (0.015, 0.040, 0.990, 0.185),
                        "label": "1. 另增 A07 國內出差-交通-eTag｜依實扣金額與規定稅別登打",
                        "color": "gold",
                        "label_pos": "bottom",
                    },
                    {
                        "box": (0.015, 0.720, 0.990, 0.945),
                        "label": "2. 明細清單須分列 A05 與 A07，並確認每筆憑證日期皆為實際日期",
                        "color": "green",
                        "label_pos": "top",
                    },
                ],
                "caption": "通行費不可併入 A05 私車里程費！請依實際 eTag 扣款金額獨立新增 A07 並確認憑證日期",
            },
        ],
        "narration": (
            "這裡要特別注意，高速公路的 eTag 通行費不能跟里程費算在同一筆！"
            "而且會計規定，通行費佐證必須下載含有『遠通電收電子憑證專用章』的官方紀錄列印單，不能只用網站上的未出帳截圖。"
            "確認本筆憑證日期後，依照單據上的實際扣款金額，另外新增一筆 A07『國內出差交通 eTag』，照實登打並與下方 A05 分開列示。"
        ),
        "subtitle": "eTag 通行費須附含專用章之官方紀錄 PDF 並另列 A07，嚴禁併入 A05 里程費",
        "key_points": ["下載含專用章之官方 PDF", "依實際扣款金額登打", "與 A05 里程費分開列示"],
    },
    {
        "id": "shot05",
        "index": 5,
        "title": "A01 高鐵車資：13 碼票號與 T02 含稅金額登打",
        "chapter": "十一之一、高鐵票（A01）憑證日期、特殊票號與稅別",
        "engine": "ui",
        "figures": ["fig10_a01_hsr.png"],
        "beats": [
            {
                "figure": "fig10_a01_hsr.png",
                "zoom": 1.01,
                "boxes": [
                    {
                        "box": (0.505, 0.002, 0.995, 0.056),
                        "label": "1. 憑證日期：務必改為高鐵乘車／購票實際日期",
                        "color": "cyan",
                        "label_pos": "left",
                    },
                    {
                        "box": (0.502, 0.365, 0.995, 0.460),
                        "label": "2. 高鐵發票號碼特殊：無英文兩碼字軌，請輸入車票上的 13 碼票號",
                        "color": "gold",
                        "label_pos": "bottom",
                    },
                ],
                "info_card": {
                    "title": "【會計實務提醒｜高鐵票（A01）發票號碼怎麼填？】",
                    "border": "gold",
                    "lines": [
                        "1. 高鐵車票沒有一般電子發票的 2 碼英文字軌（例如 AB），請勿留白或亂補英文。",
                        "2. 「發票號碼」欄請直接輸入高鐵車票正本上印製的 13 碼純數字票號（圖中 2904312521681 為範例）。",
                        "3. 右上角「憑證日期」請同步改為實際乘車／發票日期，切勿直接套用系統預設日期。",
                    ],
                },
                "caption": "高鐵 A01 重點：憑證日期改為實際日期，發票號碼輸入車票上 13 碼票號（圖僅範例）",
            },
            {
                "figure": "fig10_a01_hsr.png",
                "zoom": 1.01,
                "boxes": [
                    {
                        "box": (0.010, 0.056, 0.992, 0.250),
                        "label": "3. 選 A01 高鐵、稅別碼 T02（內含 5%）→ 報銷金額直接 Key 含稅總額",
                        "color": "gold",
                        "label_pos": "bottom",
                    },
                    {
                        "box": (0.010, 0.560, 0.995, 0.662),
                        "label": "4. 送出前核對「原幣未稅 ＋ 原幣稅額 ＝ 原幣含稅」與票據完全一致",
                        "color": "cyan",
                        "label_pos": "top",
                    },
                ],
                "info_card": {
                    "title": "【金額 Key 未稅還是含稅？｜高鐵 A01 ＋ 稅別碼 T02】",
                    "border": "cyan",
                    "lines": [
                        "● 稅別碼選 T02（應稅內含 5%）：報銷金額欄請直接輸入「車票含稅總額」（例：實際車資 650）。",
                        "● 系統會自動反算為「原幣未稅 619 ＋ 原幣稅額 31 ＝ 原幣含稅 650」，請核對與紙本票根相符。",
                        "● 畫面數字 650／單號皆僅供範例，申請時請務必依個人實際高鐵票面金額登打。",
                    ],
                },
                "caption": "T02 應稅內含 5%：報銷金額 Key 含稅總額，系統自動拆算未稅與稅額並與高鐵票核對",
            },
        ],
        "narration": (
            "接下來補充一般出差搭高鐵與停車費的實務填法，提醒大家，高鐵與停車費都不算在私車里程費裡面。"
            "先看高鐵 A01，第一點記得先把右上角的憑證日期改成高鐵票實際日期；"
            "第二點是會計特別提醒，高鐵票的號碼格式跟一般發票不同，沒有前面兩碼英文字軌，"
            "在發票號碼欄請直接輸入高鐵車票上的 13 碼數字票號。"
            "第三點看金額與稅別，高鐵通常選 T02 應稅內含百分之五，這時報銷金額要直接輸入含稅總額，"
            "就像畫面範例 Key 入 650 元，系統會自動算成未稅 619 加稅額 31 等於含稅 650，"
            "請核對最下方三個金額欄位跟實際車票完全一致。"
        ),
        "subtitle": "A01 高鐵實務：改憑證日期 → 發票號碼填車票 13 碼數字 → T02 內含 5% 直接 Key 含稅總額",
        "key_points": ["憑證日期必改實際日期", "高鐵發票欄填 13 碼票號", "T02 內含 5% Key 含稅總額"],
    },
    {
        "id": "shot06",
        "index": 6,
        "title": "A06 停車費與「未稅／含稅金額 Key 法」總整理",
        "chapter": "十一之二、停車費（A06）與會計稅別金額對照",
        "engine": "ui",
        "figures": ["fig11_a06_parking.png"],
        "beats": [
            {
                "figure": "fig11_a06_parking.png",
                "zoom": 1.01,
                "boxes": [
                    {
                        "box": (0.505, 0.002, 0.995, 0.056),
                        "label": "1. 憑證日期：務必改為停車發票開立日期",
                        "color": "cyan",
                        "label_pos": "left",
                    },
                    {
                        "box": (0.010, 0.365, 0.995, 0.460),
                        "label": "2. 依實體發票填入賣方統編（8 碼）與完整發票號碼（2 英文＋8 數字）",
                        "color": "gold",
                        "label_pos": "bottom",
                    },
                ],
                "info_card": {
                    "title": "【停車費 A06 實務提醒｜不可併入 A05 私車里程費】",
                    "border": "gold",
                    "lines": [
                        "● 停車費須獨立選用類別 A06，右上角「憑證日期」請改成發票實際日期。",
                        "● 賣方統編與發票號碼請依手中發票／收據實際登打（圖中 95389059、TJ30825219 僅為範例）。",
                    ],
                },
                "caption": "停車費 A06：憑證日期改為實際日期，並依實體發票填入賣方統編與發票號碼（勿抄範例）",
            },
            {
                "figure": "fig11_a06_parking.png",
                "zoom": 1.01,
                "boxes": [
                    {
                        "box": (0.010, 0.056, 0.992, 0.250),
                        "label": "3. 選 T01（應稅外加 5%）→ 報銷金額請 Key「未稅金額」",
                        "color": "gold",
                        "label_pos": "bottom",
                    },
                    {
                        "box": (0.010, 0.560, 0.995, 0.662),
                        "label": "4. 確認原幣未稅 152 ＋ 原幣稅額 8 ＝ 原幣含稅 160 與發票總計相符",
                        "color": "cyan",
                        "label_pos": "top",
                    },
                ],
                "info_card": {
                    "title": "【會計關鍵規則｜報銷金額要 Key 未稅還是含稅？】",
                    "border": "gold",
                    "lines": [
                        "● T01（應稅外加 5%）：報銷金額 Key「未稅金額」，系統外加 5%（例：Key 152 → 稅 8 → 含稅 160）。",
                        "● T02（應稅內含 5%）：報銷金額 Key「含稅總額」，系統內扣 5%（例：Key 650 → 未稅 619 ＋ 稅 31）。",
                        "● T05／T04（免稅／無進項稅額）：稅額為 0，直接 Key 實付金額；送簽前務必核對「含稅合計＝發票實付」。",
                    ],
                },
                "caption": "發票金額總原則：T01 應稅外加 Key 未稅、T02 應稅內含 Key 含稅、免稅直接 Key 實額",
            },
        ],
        "narration": (
            "接著看停車費 A06，一樣先把右上角憑證日期改成停車發票實際日期，"
            "中間依照實際發票填入賣方統編八碼與英文開頭十碼發票號碼。"
            "這裡幫大家整理會計最常提醒的金額 Key 法："
            "如果選 T01 應稅外加百分之五，像這張發票實付 160 元，報銷金額欄就要 Key 未稅金額 152 元，系統會外加 8 元稅額，變成含稅 160；"
            "相反地，如果選 T02 應稅內含百分之五，報銷金額就要直接 Key 含稅總額；"
            "至於 T05 或 T04 免稅則直接填實付金額。不管哪一種，都一定要核對下方『原幣未稅加稅額等於原幣含稅』跟手中紙本發票完全一樣！"
        ),
        "subtitle": "必記對照：T01 應稅外加 5% Key 未稅金額｜T02 應稅內含 5% Key 含稅總額｜免稅 Key 實額",
        "key_points": ["T01 外加 5% Key 未稅金額", "T02 內含 5% Key 含稅總額", "核對未稅＋稅額＝含稅"],
    },
    {
        "id": "shot07",
        "index": 7,
        "title": "多筆明細總檢核、附件上傳與送簽",
        "chapter": "八～十、完成明細、送出前檢核與常見問題",
        "engine": "ui",
        "figures": ["fig09_multi_list.jpg"],
        "beats": [
            {
                "figure": "fig09_multi_list.jpg",
                "zoom": 1.03,
                "boxes": [
                    {
                        "box": (0.03, 0.34, 0.98, 0.62),
                        "label": "檢查清單：確認每筆憑證日期、類別、未稅／含稅與明細合計皆與總金額一致",
                        "color": "gold",
                        "label_pos": "top",
                    },
                ],
                "caption": "上傳本人出差登記、實際去回程截圖、eTag 明細與發票佐證並確認皆可開啟",
            },
            {
                "figure": "fig09_multi_list.jpg",
                "zoom": 1.02,
                "boxes": [
                    {
                        "box": (0.03, 0.34, 0.98, 0.62),
                        "label": "送出前最後確認：先按「儲存」無檢核錯誤 → 再按「送出」取 BPM 單號",
                        "color": "green",
                        "label_pos": "top",
                    },
                ],
                "checklist": [
                    "[OK] 出差登記單號、日期、地點與出差原因為本人實際行程（非範例）",
                    "[OK] 每筆明細之「憑證日期」皆已改為實際發生或發票開立日期",
                    "[OK] A05／A07／A01(13碼票號)／A06 分列，且未稅＋稅額＝含稅完全相符",
                    "[OK] 去回程截圖與佐證附件皆已上傳且可開啟，明細合計＝表頭總金額",
                    "[OK] 已先儲存確認無必填錯誤，並送出簽核取得 BPM 單號",
                ],
                "caption": "若找不到出差單或附件太大，先確認核准狀態或將截圖轉為 PDF/JPG 縮圖",
            },
        ],
        "narration": (
            "全部依照實際發生費用登打完之後，我們檢查一下底下的明細表，"
            "確認每一筆的憑證日期、費用類別、未稅與含稅金額都跟手中憑證一致，"
            "明細加起來跟表頭總金額一模一樣，也要把出差單、路線截圖跟相關明細全部上傳並確認檔案打得開。"
            "最後先按『儲存』，沒跳紅字錯誤再按『送出』，並把 BPM 單號記下來。"
        ),
        "subtitle": "確認每筆憑證日期、未稅／含稅金額與合計無誤 → 附件上傳驗證 → 先儲存再送簽",
        "key_points": ["檢查每筆憑證日期", "核對未稅＋稅額＝含稅", "先儲存再送簽"],
    },
    {
        "id": "shot08",
        "index": 8,
        "title": "紙本正本繳交：申請人 → 人事核對 → 會計審核",
        "chapter": "十二、正本繳交與後續審核流程（實務交件流程）",
        "engine": "ui",
        "kind": "handover_flow",
        "figures": [],
        "narration": (
            "線上送出還不算完全結束喔！請把申請單印出來，連同實際發生的發票、高鐵票或停車收據正本、"
            "路線截圖跟費用計算依據整理好，先交給人事單位核對；"
            "等人事確認正本金額與日期跟系統登打完全一致之後，就會幫你轉交給會計做最後審核與撥款囉！"
        ),
        "subtitle": "交件鐵律：申請人備妥實際憑證正本 → 交由人事核對無誤 → 人事轉交會計最後審核",
        "key_points": ["檢附實際發票／高鐵／收據正本", "先交人事核對系統與正本一致", "人事無誤再轉會計"],
    },
]


# ---------------------------------------------------------------------------
# 4. 語音合成：優先 edge-tts，網路受阻時自動切換 Windows SAPI5 離線語音
# ---------------------------------------------------------------------------

VOICE_PROFILES = {
    "hsiaochen": "zh-TW-HsiaoChenNeural",
    "yunjhe": "zh-TW-YunJheNeural",
    "hsiaoyu": "zh-TW-HsiaoYuNeural",
}
DUET_YUNJHE_SHOTS = {"shot01", "shot04", "shot05", "shot08"}

_EDGE_CA_LOADED = False


def _load_windows_ca_for_edge_tts():
    global _EDGE_CA_LOADED
    if _EDGE_CA_LOADED:
        return
    _EDGE_CA_LOADED = True
    try:
        import edge_tts.communicate as comm
        if hasattr(ssl, "enum_certificates"):
            pem_chunks = []
            for store in ("ROOT", "CA"):
                for cert, enc, _trust in ssl.enum_certificates(store):
                    if enc == "x509_asn":
                        pem_chunks.append(ssl.DER_cert_to_PEM_cert(cert))
            if pem_chunks:
                comm._SSL_CTX.load_verify_locations(cadata="\n".join(pem_chunks))
        if hasattr(ssl, "VERIFY_X509_STRICT"):
            comm._SSL_CTX.verify_flags &= ~ssl.VERIFY_X509_STRICT
    except Exception:
        pass


def resolve_edge_voice(shot_id: str, voice_profile: str) -> str:
    if voice_profile == "duet":
        return "zh-TW-YunJheNeural" if shot_id in DUET_YUNJHE_SHOTS else "zh-TW-HsiaoChenNeural"
    return VOICE_PROFILES.get(voice_profile, "zh-TW-HsiaoChenNeural")


async def _edge_tts_save(text: str, out_mp3: Path, edge_voice: str, rate: str = "+20%"):
    import edge_tts
    _load_windows_ca_for_edge_tts()
    communicate = edge_tts.Communicate(text, voice=edge_voice, rate=rate)
    await communicate.save(str(out_mp3))


def _sapi5_fallback_save(text: str, out_mp3: Path, ffmpeg_exe: str):
    tmp_wav = out_mp3.with_suffix(".wav")
    escaped = text.replace("'", "''")
    ps_script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$v = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like 'zh*' } | Select-Object -First 1; "
        "if ($v) { $s.SelectVoice($v.VoiceInfo.Name) }; "
        "$s.Rate = 1; "
        f"$s.SetOutputToWaveFile('{tmp_wav}'); "
        f"$s.Speak('{escaped}'); "
        "$s.Dispose();"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=True)
    subprocess.run(
        [ffmpeg_exe, "-y", "-i", str(tmp_wav), "-ar", "44100", "-ac", "2", "-b:a", "192k", str(out_mp3)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    tmp_wav.unlink(missing_ok=True)


def synthesize_all_audio(
    ffmpeg_exe: str,
    rebuild_audio: bool = False,
    voice_profile: str = "hsiaochen",
    rate: str = "+20%",
    audio_dir: Optional[Path] = None,
) -> Dict[str, float]:
    target_audio_dir = audio_dir or AUDIO_DIR
    target_audio_dir.mkdir(parents=True, exist_ok=True)
    durations: Dict[str, float] = {}
    for shot in SHOTS:
        sid = shot["id"]
        mp3_path = target_audio_dir / f"{sid}.mp3"
        if not rebuild_audio and mp3_path.exists() and mp3_path.stat().st_size > 1000:
            mode = "快取沿用"
        else:
            edge_voice = resolve_edge_voice(sid, voice_profile)
            try:
                asyncio.run(_edge_tts_save(shot["narration"], mp3_path, edge_voice, rate=rate))
                mode = f"edge-tts:{edge_voice} ({rate})"
            except Exception as exc:
                print(f"[提示] {sid} edge-tts 失敗 ({exc})，改用本機 Windows 離線語音...")
                _sapi5_fallback_save(shot["narration"], mp3_path, ffmpeg_exe)
                mode = "SAPI5"
        dur = get_media_duration(ffmpeg_exe, mp3_path)
        durations[sid] = round(dur + 0.5, 2)
        print(f"      - {sid}.mp3 ({mode}): {dur:.2f}s -> 影片配長 {durations[sid]:.2f}s")
    print(f"[3/5] 8 段台灣中文旁白配音準備完成！({rate})")
    return durations


# ---------------------------------------------------------------------------
# 5. 1080p 畫面繪製與 FFmpeg 串流合成
# ---------------------------------------------------------------------------

def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    lines: List[str] = []
    cur = ""
    for ch in text:
        test = cur + ch
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def draw_chrome_bars(
    canvas: Image.Image,
    shot: dict,
    progress: float,
    caption_text: str,
    total_shots: int = 8,
):
    """繪製頂部步驟導覽列與底部大字幕欄（RGBA 半透明疊層）。"""
    overlay = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # Top Header Bar (y: 0..88)
    d.rectangle([0, 0, VIDEO_W, 88], fill=(10, 16, 30, 232))
    d.line([(0, 88), (VIDEO_W, 88)], fill=(56, 189, 248, 120), width=2)

    if shot["engine"] == "flow":
        badge_col = (16, 185, 129, 255)
        badge_txt = "FLOW 情境"
    elif shot.get("kind"):
        badge_col = (16, 185, 129, 255)
        badge_txt = "實務流程"
    else:
        badge_col = (250, 204, 21, 255)
        badge_txt = "UI 實操導覽"
    d.rounded_rectangle([32, 18, 206, 70], radius=12, fill=badge_col)
    d.text((50, 29), badge_txt, fill=(10, 16, 30, 255), font=get_font(24, bold=True))

    title_str = shot["title"]
    d.text((228, 16), title_str, fill=(248, 250, 252, 255), font=get_font(30, bold=True))
    d.text((228, 54), shot["chapter"], fill=(148, 163, 184, 255), font=get_font(20))

    # Clean official top-right system badge (no draft shot count)
    sys_tag = "鼎新 BPM 費用報銷教學"
    tfont = get_font(21, bold=True)
    tw = d.textlength(sys_tag, font=tfont)
    d.rounded_rectangle([VIDEO_W - int(tw) - 64, 22, VIDEO_W - 32, 66], radius=10, fill=(30, 41, 59, 220), outline=(56, 189, 248, 120), width=1)
    d.text((VIDEO_W - int(tw) - 48, 31), sys_tag, fill=(186, 230, 253, 230), font=tfont)

    # Bottom Subtitle Bar (y: 952..1080)
    d.rectangle([0, 950, VIDEO_W, VIDEO_H], fill=(10, 16, 30, 236))
    d.line([(0, 950), (VIDEO_W, 950)], fill=(56, 189, 248, 90), width=2)

    sub_font = get_font(26, bold=True)
    lines = wrap_text(d, caption_text, sub_font, VIDEO_W - 140)
    sy = 964 if len(lines) > 1 else 982
    for ln in lines[:2]:
        tw = d.textlength(ln, font=sub_font)
        d.text(((VIDEO_W - tw) / 2, sy), ln, fill=(248, 250, 252, 255), font=sub_font)
        sy += 36

    # Bottom timeline progress line
    d.rectangle([0, VIDEO_H - 7, int(VIDEO_W * max(0.0, min(1.0, progress))), VIDEO_H], fill=(56, 189, 248, 255))

    canvas.paste(overlay, (0, 0), overlay)


BOX_PALETTE = {
    "gold": ((250, 204, 21), (254, 240, 138)),
    "cyan": ((56, 189, 248), (186, 230, 253)),
    "green": ((16, 185, 129), (167, 243, 208)),
}


def _draw_spotlight_box(
    od: ImageDraw.ImageDraw,
    rx1: int,
    ry1: int,
    rx2: int,
    ry2: int,
    label: str,
    color_key: str,
    label_pos: str,
    pulse: float,
    vx: int,
    vy: int,
    vw: int,
    vh: int,
):
    main_rgb, text_rgb = BOX_PALETTE.get(color_key, BOX_PALETTE["gold"])
    ring_alpha = int(205 + 50 * pulse)

    # Outer dark contrast halo so yellow/cyan pops even on white forms or red BPM headers
    od.rounded_rectangle([rx1 - 5, ry1 - 5, rx2 + 5, ry2 + 5], radius=14, outline=(10, 16, 30, 235), width=11)
    od.rounded_rectangle([rx1, ry1, rx2, ry2], radius=10, outline=(*main_rgb, ring_alpha), width=5)

    # Corner L-brackets for extra spotlight precision
    blen = max(14, min(28, (rx2 - rx1) // 6, (ry2 - ry1) // 3))
    for cx, cy, dx, dy in [(rx1, ry1, 1, 1), (rx2, ry1, -1, 1), (rx1, ry2, 1, -1), (rx2, ry2, -1, -1)]:
        od.line([(cx, cy), (cx + dx * blen, cy)], fill=(255, 255, 255, 245), width=4)
        od.line([(cx, cy), (cx, cy + dy * blen)], fill=(255, 255, 255, 245), width=4)

    # High-contrast label pill (deep navy bg + bright accent border)
    lfont = get_font(23, bold=True)
    lw = int(od.textlength(label, font=lfont)) + 34
    lh = 44

    if label_pos == "left":
        lx = max(vx + 10, rx1 - lw - 14)
        ly = max(vy + 8, min(vy + vh - lh - 8, (ry1 + ry2 - lh) // 2))
    elif label_pos == "bottom":
        lx = max(vx + 10, min(vx + vw - lw - 10, rx1))
        ly = min(vy + vh - lh - 8, ry2 + 10)
    else:  # "top"
        lx = max(vx + 10, min(vx + vw - lw - 10, rx1))
        ly = ry1 - lh - 10 if ry1 - lh - 10 >= vy + 8 else min(vy + vh - lh - 8, ry2 + 10)

    od.rounded_rectangle(
        [lx, ly, lx + lw, ly + lh],
        radius=10,
        fill=(11, 17, 32, 246),
        outline=(*main_rgb, 255),
        width=3,
    )
    od.text((lx + 17, ly + 8), label, fill=(*text_rgb, 255), font=lfont)


def draw_practical_card_frame(
    shot: dict,
    t_norm: float,
    img_cache: Dict[str, Image.Image],
    total_shots: int = 8,
) -> Image.Image:
    """繪製純實務重點看板幀（鏡次 01 行前佐證三寶 / 鏡次 08 正本交件 3 步驟，無 3D 動畫）。"""
    canvas = Image.new("RGB", (VIDEO_W, VIDEO_H), (13, 20, 36))
    ov = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    if shot.get("kind") == "prep_three":
        # Left card: Approved Trip Form Checklist
        d.rounded_rectangle([48, 122, 608, 912], radius=20, fill=(15, 23, 42, 245), outline=(56, 189, 248, 235), width=4)
        d.rounded_rectangle([76, 148, 580, 212], radius=12, fill=(14, 116, 144, 245))
        d.text((104, 162), "1. 本人已核准之出差登記單", fill=(255, 255, 255, 255), font=get_font(28, bold=True))
        bullets = [
            "● 確認本人當次出差單已經核准",
            "● 核對出差起訖日期與報銷一致",
            "● 核對出差地點與申請事由正確",
            "● 不確定單號時於 BPM 查詢帶入",
        ]
        by = 252
        for idx, line in enumerate(bullets):
            alpha = 255 if t_norm >= idx * 0.1 else 135
            d.rounded_rectangle([78, by, 578, by + 110], radius=12, fill=(30, 41, 59, 240), outline=(56, 189, 248, 140), width=2)
            d.text((100, by + 36), line, fill=(241, 245, 249, alpha), font=get_font(24, bold=True))
            by += 138

        # Middle card: Real Go/Back Route Screenshots
        d.rounded_rectangle([634, 122, 1252, 912], radius=20, fill=(15, 23, 42, 245), outline=(250, 204, 21, 235), width=4)
        d.rounded_rectangle([662, 148, 1224, 212], radius=12, fill=(202, 138, 4, 245))
        d.text((688, 162), "2. Google 地圖去／回程實際截圖", fill=(255, 255, 255, 255), font=get_font(28, bold=True))
        d.text((666, 228), "依個人實際跑幾公里計算（圖為範例截圖）", fill=(254, 240, 138, 255), font=get_font(22, bold=True))

        # Right card: Real ETag Record Screenshot with Official Seal
        d.rounded_rectangle([1278, 122, 1872, 912], radius=20, fill=(15, 23, 42, 245), outline=(16, 185, 129, 235), width=4)
        d.rounded_rectangle([1306, 148, 1844, 212], radius=12, fill=(5, 150, 105, 245))
        d.text((1332, 162), "3. 遠通 eTag 官方紀錄（含專用章）", fill=(255, 255, 255, 255), font=get_font(27, bold=True))
        d.text((1310, 228), "須具備遠通專用章（不可僅用線上未出帳截圖）", fill=(167, 243, 208, 255), font=get_font(21, bold=True))

        canvas.paste(ov, (0, 0), ov)

        for fname in ["fig07_route_go.jpg", "fig08_route_back.jpg", "fig06_etag_record.jpg"]:
            if fname not in img_cache:
                img_cache[fname] = Image.open(FIG_DIR / fname).convert("RGB")
        go_im = img_cache["fig07_route_go.jpg"].resize((272, 540), Image.Resampling.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))
        bk_im = img_cache["fig08_route_back.jpg"].resize((272, 540), Image.Resampling.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))
        etag_im = img_cache["fig06_etag_record.jpg"].resize((536, 405), Image.Resampling.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))
        canvas.paste(go_im, (662, 275))
        canvas.paste(bk_im, (952, 275))
        canvas.paste(etag_im, (1306, 275))

        ov2 = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
        d2 = ImageDraw.Draw(ov2)
        d2.rounded_rectangle([662, 830, 934, 886], radius=10, fill=(30, 41, 59, 245), outline=(250, 204, 21, 220), width=2)
        d2.text((712, 843), "去程路線（實距）", fill=(254, 240, 138, 255), font=get_font(22, bold=True))
        d2.rounded_rectangle([952, 830, 1224, 886], radius=10, fill=(30, 41, 59, 245), outline=(250, 204, 21, 220), width=2)
        d2.text((1002, 843), "回程路線（實距）", fill=(254, 240, 138, 255), font=get_font(22, bold=True))
        d2.rounded_rectangle([1306, 705, 1842, 886], radius=12, fill=(30, 41, 59, 245), outline=(16, 185, 129, 220), width=2)
        d2.text((1334, 730), "● 下載含「電子憑證專用章」之官方紀錄 PDF", fill=(241, 245, 249, 255), font=get_font(23, bold=True))
        d2.text((1334, 780), "● 依單據上實際已扣款金額申請（畫面 18 元）", fill=(241, 245, 249, 255), font=get_font(23, bold=True))
        d2.text((1334, 830), "● 嚴禁併入 A05 私車里程費，須獨立新增 A07", fill=(110, 231, 183, 255), font=get_font(23, bold=True))
        canvas.paste(ov2, (0, 0), ov2)
    else:
        # Handover flow 3-step accounting board (Shot 08)
        d.text((64, 122), "BPM 線上送簽完成後，仍須辦理「實體正本交件」流程：", fill=(254, 240, 138, 255), font=get_font(32, bold=True))
        cols = [
            (
                64,
                (56, 189, 248),
                "步驟 1｜申請人備妥正本",
                [
                    "● 確認 BPM 已送出並留存單號",
                    "● 列印或整理一般費用報銷申請單",
                    "● 備齊發票／高鐵票／停車收據正本",
                    "● 附上路線截圖、ETag 與計算依據",
                ],
                "注意：不可只傳線上截圖或影本",
            ),
            (
                674,
                (16, 185, 129),
                "步驟 2｜先交人事單位核對",
                [
                    "● 依人事指定方式與期限交付正本",
                    "● 人事核對申請人與出差日期相符",
                    "● 核對費用類別、發票號碼與金額",
                    "● 若發現缺件或金額不符將退回補件",
                ],
                "通過判斷：人事核對無誤才可轉交",
            ),
            (
                1284,
                (250, 204, 21),
                "步驟 3｜轉交會計最後審核",
                [
                    "● 人事核對無誤後轉送會計單位",
                    "● 會計依稅務及付款規範進行複核",
                    "● 確認未稅＋稅額＝含稅與憑證一致",
                    "● 審核通過後正式完成核銷與撥款",
                ],
                "完成狀態：案件進入會計審核入帳",
            ),
        ]
        for idx, (cx, col, title, items, foot) in enumerate(cols):
            active = t_norm >= idx * 0.25
            border_a = 255 if active else 140
            d.rounded_rectangle([cx, 188, cx + 572, 888], radius=22, fill=(15, 23, 42, 245), outline=(*col, border_a), width=4)
            d.rounded_rectangle([cx + 24, 214, cx + 548, 286], radius=14, fill=(*col, 245))
            d.text((cx + 48, 232), title, fill=(10, 16, 30, 255), font=get_font(29, bold=True))
            iy = 318
            for item in items:
                d.rounded_rectangle([cx + 26, iy, cx + 546, iy + 96], radius=12, fill=(30, 41, 59, 240))
                d.text((cx + 46, iy + 32), item, fill=(241, 245, 249, 255), font=get_font(23, bold=True))
                iy += 116
            d.rounded_rectangle([cx + 26, 796, cx + 546, 862], radius=12, fill=(2, 6, 23, 245), outline=(*col, 190), width=2)
            d.text((cx + 46, 814), foot, fill=(*col, 255), font=get_font(22, bold=True))
            if idx < 2:
                ax = cx + 580
                d.polygon([(ax, 510), (ax + 24, 538), (ax, 566)], fill=(250, 204, 21, 255))
        canvas.paste(ov, (0, 0), ov)

    draw_chrome_bars(canvas, shot, t_norm, shot["subtitle"], total_shots=total_shots)
    return canvas


def draw_ui_beat_frame(
    shot: dict,
    beat: dict,
    beat_t: float,
    overall_progress: float,
    img_cache: Dict[str, Image.Image],
    total_shots: int = 8,
) -> Image.Image:
    """繪製單一 UI 導覽幀：聚光燈壓暗遮罩 + 高對比亮黃/青雙框 + 憑證日期與會計實務提醒卡。"""
    canvas = Image.new("RGB", (VIDEO_W, VIDEO_H), (13, 20, 36))
    fig_name = beat["figure"]
    if fig_name not in img_cache:
        img_cache[fig_name] = Image.open(FIG_DIR / fig_name).convert("RGB")
    src = img_cache[fig_name]
    sw, sh = src.size

    # Viewport area between header (y=96) and subtitle (y=942) -> 1856 x 836
    vx, vy, vw, vh = 32, 96, 1856, 836
    base_scale = min(vw / sw, vh / sh)

    boxes = beat.get("boxes") or [
        {"box": beat["box"], "label": beat["label"], "color": "gold", "label_pos": "top"}
    ]

    ease = 1 - pow(1 - min(1.0, beat_t * 1.4), 3)
    target_zoom = beat.get("zoom", 1.02)
    cur_zoom = 1.0 + (target_zoom - 1.0) * ease

    bx1, by1, bx2, by2 = boxes[0]["box"]
    focus_cx = ((bx1 + bx2) * 0.5) * sw
    focus_cy = ((by1 + by2) * 0.5) * sh

    cx = sw * 0.5 + (focus_cx - sw * 0.5) * ease * 0.85
    cy = sh * 0.5 + (focus_cy - sh * 0.5) * ease * 0.85

    disp_w = int(sw * base_scale * cur_zoom)
    disp_h = int(sh * base_scale * cur_zoom)
    resized = src.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
    if cur_zoom > 1.0 or base_scale > 1.0:
        resized = resized.filter(ImageFilter.UnsharpMask(radius=1.2, percent=125, threshold=2))

    img_x_in_disp = (cx / sw) * disp_w
    img_y_in_disp = (cy / sh) * disp_h
    paste_x = int(vx + vw * 0.5 - img_x_in_disp)
    paste_y = int(vy + vh * 0.5 - img_y_in_disp)

    if disp_w > vw:
        paste_x = min(vx, max(vx + vw - disp_w, paste_x))
    else:
        paste_x = int(vx + (vw - disp_w) * 0.5)
    if disp_h > vh:
        paste_y = min(vy, max(vy + vh - disp_h, paste_y))
    else:
        paste_y = int(vy + (vh - disp_h) * 0.5)

    vp_layer = Image.new("RGB", (vw, vh), (15, 23, 42))
    vp_layer.paste(resized, (paste_x - vx, paste_y - vy))
    canvas.paste(vp_layer, (vx, vy))

    # Build spotlight dim mask across viewport and punch clear bright holes at target boxes
    dim_mask = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    dm = ImageDraw.Draw(dim_mask)
    dm.rectangle([vx, vy, vx + vw, vy + vh], fill=(4, 8, 18, 118))

    mapped_boxes = []
    for item in boxes:
        ibx1, iby1, ibx2, iby2 = item["box"]
        rx1 = max(vx + 6, int(paste_x + ibx1 * disp_w))
        ry1 = max(vy + 6, int(paste_y + iby1 * disp_h))
        rx2 = min(vx + vw - 6, int(paste_x + ibx2 * disp_w))
        ry2 = min(vy + vh - 6, int(paste_y + iby2 * disp_h))
        dm.rounded_rectangle([rx1, ry1, rx2, ry2], radius=10, fill=(0, 0, 0, 0))
        mapped_boxes.append((rx1, ry1, rx2, ry2, item))

    canvas.paste(dim_mask, (0, 0), dim_mask)

    overlay = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    pulse = 0.5 + 0.5 * math.sin(beat_t * math.pi * 4.0)

    for rx1, ry1, rx2, ry2, item in mapped_boxes:
        _draw_spotlight_box(
            od,
            rx1,
            ry1,
            rx2,
            ry2,
            item["label"],
            item.get("color", "gold"),
            item.get("label_pos", "top"),
            pulse,
            vx,
            vy,
            vw,
            vh,
        )

    # Optional Accounting Practice Info Card placed cleanly in lower open area
    if "info_card" in beat:
        card = beat["info_card"]
        border_rgb, title_rgb = BOX_PALETTE.get(card.get("border", "gold"), BOX_PALETTE["gold"])
        cw = 1780
        lines = card["lines"]
        ch = 68 + len(lines) * 44 + 18
        cx0 = (VIDEO_W - cw) // 2
        cy0 = vy + vh - ch - 12
        od.rounded_rectangle(
            [cx0, cy0, cx0 + cw, cy0 + ch],
            radius=16,
            fill=(11, 17, 32, 245),
            outline=(*border_rgb, 255),
            width=4,
        )
        od.text((cx0 + 28, cy0 + 18), card["title"], fill=(*title_rgb, 255), font=get_font(27, bold=True))
        ly = cy0 + 64
        for ln in lines:
            od.text((cx0 + 32, ly), ln, fill=(248, 250, 252, 255), font=get_font(23, bold=True))
            ly += 44

    # Optional final checklist card overlay (Shot 07 Beat 2)
    if "checklist" in beat:
        cw, ch = 1280, 470
        cx0, cy0 = (VIDEO_W - cw) // 2, 230
        od.rectangle([vx, vy, vx + vw, vy + vh], fill=(7, 11, 20, 185))
        od.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + ch], radius=24, fill=(15, 23, 42, 248), outline=(16, 185, 129, 255), width=4)
        od.text((cx0 + 48, cy0 + 34), "【送出簽核前 5 大必查檢核表】", fill=(110, 231, 183, 255), font=get_font(34, bold=True))
        iy = cy0 + 105
        for idx, item in enumerate(beat["checklist"]):
            revealed = beat_t >= idx * 0.12
            text_alpha = 255 if revealed else 115
            border_col = (16, 185, 129, 220) if revealed else (71, 85, 105, 180)
            od.rounded_rectangle([cx0 + 44, iy, cx0 + cw - 44, iy + 58], radius=12, fill=(30, 41, 59, 242), outline=border_col, width=2)
            od.text((cx0 + 68, iy + 13), item, fill=(248, 250, 252, text_alpha), font=get_font(25, bold=True))
            iy += 68

    canvas.paste(overlay, (0, 0), overlay)
    draw_chrome_bars(canvas, shot, overall_progress, beat.get("caption") or shot["subtitle"], total_shots=total_shots)
    return canvas


def draw_flow_fallback_frame(
    shot: dict,
    t_norm: float,
    flow_pair: Tuple[Path, Path],
    img_cache: Dict[str, Image.Image],
    total_shots: int = 8,
) -> Image.Image:
    """當使用者尚未放入 Google Flow 算出的 MP4 時，以首尾幀＋SOP佐證圖合成高質感動態轉場幀。"""
    p_first, p_last = flow_pair
    for key, path in [(f"{shot['id']}_f", p_first), (f"{shot['id']}_l", p_last)]:
        if key not in img_cache:
            img_cache[key] = Image.open(path).convert("RGB").resize((1856, 836), Image.Resampling.BILINEAR)

    im_f = img_cache[f"{shot['id']}_f"]
    im_l = img_cache[f"{shot['id']}_l"]

    # Smooth cross-dissolve between first & last scene frames
    blend_alpha = max(0.0, min(1.0, (t_norm - 0.18) / 0.64))
    scene = Image.blend(im_f, im_l, blend_alpha)

    # Subtle Ken Burns zoom (1.0 -> 1.07)
    zoom = 1.0 + 0.07 * t_norm
    zw, zh = int(1856 * zoom), int(836 * zoom)
    z_scene = scene.resize((zw, zh), Image.Resampling.BILINEAR)
    crop_x = (zw - 1856) // 2
    crop_y = (zh - 836) // 2
    vp = z_scene.crop((crop_x, crop_y, crop_x + 1856, crop_y + 836))

    canvas = Image.new("RGB", (VIDEO_W, VIDEO_H), (13, 20, 36))
    canvas.paste(vp, (32, 96))

    # For Shot 01, overlay the real Go/Back Google Maps screenshots cleanly on the right
    if shot["id"] == "shot01":
        for fname in ["fig07_route_go.jpg", "fig08_route_back.jpg"]:
            if fname not in img_cache:
                img_cache[fname] = Image.open(FIG_DIR / fname).convert("RGB")
        ov = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.rounded_rectangle([1220, 120, 1860, 740], radius=20, fill=(10, 16, 30, 224), outline=(56, 189, 248, 220), width=3)
        od.text((1245, 138), "範例路線截圖（依個人實際里程計算）", fill=(125, 211, 252, 255), font=get_font(23, bold=True))
        go_im = img_cache["fig07_route_go.jpg"].resize((285, 420), Image.Resampling.BILINEAR)
        bk_im = img_cache["fig08_route_back.jpg"].resize((285, 420), Image.Resampling.BILINEAR)
        canvas.paste(ov, (0, 0), ov)
        canvas.paste(go_im, (1245, 195))
        canvas.paste(bk_im, (1550, 195))
        ov2 = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
        od2 = ImageDraw.Draw(ov2)
        od2.rounded_rectangle([1245, 635, 1530, 705], radius=12, fill=(16, 185, 129, 235))
        od2.text((1280, 654), "去程實際里程", fill=(10, 16, 30, 255), font=get_font(24, bold=True))
        od2.rounded_rectangle([1550, 635, 1835, 705], radius=12, fill=(245, 158, 11, 235))
        od2.text((1585, 654), "回程實際里程", fill=(10, 16, 30, 255), font=get_font(24, bold=True))
        canvas.paste(ov2, (0, 0), ov2)

    # Badge reminding user this slot supports Google Flow MP4 drop-in
    badge_ov = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge_ov)
    bd.rounded_rectangle([54, 116, 560, 164], radius=10, fill=(15, 23, 42, 215), outline=(16, 185, 129, 220), width=2)
    bd.text((74, 126), "[FLOW] Google Flow 情境分鏡預覽（支援替換 AI 實片）", fill=(110, 231, 183, 255), font=get_font(19, bold=True))
    canvas.paste(badge_ov, (0, 0), badge_ov)

    draw_chrome_bars(canvas, shot, t_norm, shot["subtitle"], total_shots=total_shots)
    return canvas


def render_flow_clip_with_real_mp4(
    ffmpeg_exe: str,
    shot: dict,
    flow_mp4: Path,
    audio_path: Path,
    out_mp4: Path,
    duration: float,
    total_shots: int = 8,
):
    """若使用者已將 Google Flow 產生的 MP4 放入 flow_clips/，將其與頂部導覽/底部字幕疊層及旁白合成 1080p。"""
    overlay = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    draw_chrome_bars(overlay, shot, 1.0, shot["subtitle"], total_shots=total_shots)
    hud_png = out_mp4.with_suffix(".hud.png")
    overlay.save(hud_png)

    cmd = [
        ffmpeg_exe,
        "-y",
        "-stream_loop",
        "-1",
        "-i",
        str(flow_mp4),
        "-i",
        str(hud_png),
        "-i",
        str(audio_path),
        "-filter_complex",
        f"[0:v]scale=1856:836:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:96:color=#0d1424,fps={FPS}[bg];"
        "[bg][1:v]overlay=0:0[v]",
        "-map",
        "[v]",
        "-map",
        "2:a",
        "-af",
        "apad",
        "-t",
        f"{duration:.2f}",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-b:a",
        "192k",
        str(out_mp4),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    hud_png.unlink(missing_ok=True)


def render_pipe_clip(
    ffmpeg_exe: str,
    shot: dict,
    duration: float,
    audio_path: Path,
    out_mp4: Path,
    flow_pair: Optional[Tuple[Path, Path]],
    total_shots: int = 8,
):
    total_frames = max(24, int(round(duration * FPS)))
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{VIDEO_W}x{VIDEO_H}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-i",
        str(audio_path),
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "17",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-b:a",
        "192k",
        "-af",
        "apad",
        "-t",
        f"{duration:.2f}",
        str(out_mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    img_cache: Dict[str, Image.Image] = {}
    try:
        for fidx in range(total_frames):
            t_norm = fidx / max(1, total_frames - 1)
            if shot.get("kind"):
                frame_img = draw_practical_card_frame(shot, t_norm, img_cache, total_shots=total_shots)
            elif shot["engine"] == "ui":
                beats = shot["beats"]
                seg = min(len(beats) - 1, int(t_norm * len(beats)))
                seg_start = seg / len(beats)
                seg_len = 1.0 / len(beats)
                beat_t = max(0.0, min(1.0, (t_norm - seg_start) / seg_len))
                frame_img = draw_ui_beat_frame(shot, beats[seg], beat_t, t_norm, img_cache, total_shots=total_shots)
            else:
                assert flow_pair is not None
                frame_img = draw_flow_fallback_frame(shot, t_norm, flow_pair, img_cache, total_shots=total_shots)
            assert proc.stdin is not None
            try:
                proc.stdin.write(frame_img.tobytes())
            except (BrokenPipeError, OSError):
                break
    finally:
        if proc.stdin:
            try:
                proc.stdin.close()
            except OSError:
                pass
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg 渲染失敗 ({shot['id']}), exit={ret}")


def render_all_clips_and_concat(
    ffmpeg_exe: str,
    durations: Dict[str, float],
    flow_paths: Dict[str, Tuple[Path, Path]],
    only_shots: Optional[set] = None,
    voice_profile: str = "hsiaochen",
    audio_dir: Optional[Path] = None,
    clips_dir: Optional[Path] = None,
    final_video_path: Optional[Path] = None,
    manifest_path: Optional[Path] = None,
    title_suffix: str = "",
):
    target_audio_dir = audio_dir or AUDIO_DIR
    target_clips_dir = clips_dir or CLIPS_DIR
    target_final_path = final_video_path or FINAL_VIDEO_PATH
    target_manifest_path = manifest_path or MANIFEST_PATH

    target_clips_dir.mkdir(parents=True, exist_ok=True)
    FLOW_CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    concat_entries = []
    manifest_shots = []
    elapsed = 0.0

    print(f"[4/5] 正在處理 8 段 1920x1080 (24fps) 高清分鏡影片 ({target_clips_dir.name})...")
    for shot in SHOTS:
        sid = shot["id"]
        dur = durations[sid]
        audio_path = target_audio_dir / f"{sid}.mp3"
        out_mp4 = target_clips_dir / f"{sid}.mp4"
        real_flow_mp4 = FLOW_CLIPS_DIR / f"{sid}_flow.mp4"

        used_real_flow = shot["engine"] == "flow" and real_flow_mp4.exists()
        need_render = (
            only_shots is None
            or sid in only_shots
            or not out_mp4.exists()
            or out_mp4.stat().st_size < 50_000
        )
        if need_render:
            if used_real_flow:
                render_flow_clip_with_real_mp4(ffmpeg_exe, shot, real_flow_mp4, audio_path, out_mp4, dur)
            else:
                pair = flow_paths.get(shot.get("flow_theme", ""))
                render_pipe_clip(ffmpeg_exe, shot, dur, audio_path, out_mp4, pair)

        actual_dur = get_media_duration(ffmpeg_exe, out_mp4)
        status_note = " [沿用]" if not need_render else ""
        flow_note = " [已嵌入 Google Flow 實片]" if used_real_flow else ""
        print(f"      ✓ {out_mp4.name} ({actual_dur:.2f}s){flow_note}{status_note}")
        concat_entries.append(f"file '{out_mp4.as_posix()}'")

        first_rel = f"./bpm_sop/flow_frames/{shot['flow_theme']}_first.png" if shot.get("flow_theme") else ""
        last_rel = f"./bpm_sop/flow_frames/{shot['flow_theme']}_last.png" if shot.get("flow_theme") else ""
        manifest_shots.append(
            {
                "id": sid,
                "index": shot["index"],
                "title": shot["title"],
                "chapter": shot["chapter"],
                "engine": shot["engine"],
                "flow_theme": shot.get("flow_theme", ""),
                "flow_prompt": shot.get("flow_prompt", ""),
                "first_frame": first_rel,
                "last_frame": last_rel,
                "used_real_flow_mp4": used_real_flow,
                "expected_flow_drop_path": f"bpm_sop/flow_clips/{sid}_flow.mp4",
                "figures": [
                    {
                        "file": f"./bpm_sop/figures/{fn}",
                        "caption": FIGURE_CAPTIONS.get(fn, fn),
                    }
                    for fn in shot.get("figures", [])
                ],
                "narration": shot["narration"],
                "subtitle": shot["subtitle"],
                "key_points": shot["key_points"],
                "clip_url": f"./bpm_sop/{target_clips_dir.name}/{sid}.mp4",
                "audio_url": f"./bpm_sop/{target_audio_dir.name}/{sid}.mp3",
                "start_sec": round(elapsed, 2),
                "duration_sec": round(actual_dur, 2),
            }
        )
        elapsed += actual_dur

    concat_list = target_clips_dir / "concat_list.txt"
    concat_list.write_text("\n".join(concat_entries), encoding="utf-8")

    subprocess.run(
        [
            ffmpeg_exe,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(target_final_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    full_title = f"BPM 一般費用報銷單（出差與私車公用）實務教學總片{title_suffix}"
    manifest = {
        "title": full_title,
        "source_docx": str(SOP_DOCX),
        "final_video_url": f"./bpm_sop/{target_final_path.name}",
        "total_duration_sec": round(elapsed, 2),
        "flow_cost_credits": 90,
        "voice_profile": voice_profile,
        "shots": manifest_shots,
    }
    target_manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[5/5] 總片合成完成！({elapsed:.2f}s) -> {target_final_path}")


def main():
    parser = argparse.ArgumentParser(description="BPM 一般費用報銷單雙軌分鏡影片建置器")
    parser.add_argument("--only-flow", action="store_true", help="僅重新渲染 Flow 情境分鏡與缺漏片段並重新合成總片")
    parser.add_argument("--only", nargs="+", help="指定只重算特定鏡次 (例如 shot07 shot08)")
    parser.add_argument("--rebuild-audio", action="store_true", help="強制重新合成所有語音 MP3")
    parser.add_argument(
        "--voice",
        choices=["hsiaochen", "yunjhe", "hsiaoyu", "duet"],
        default="hsiaochen",
        help="台灣語音音色 (hsiaochen 曉臻 / yunjhe 雲哲 / hsiaoyu 曉雨 / duet 雙人搭檔)",
    )
    parser.add_argument(
        "--speed",
        choices=["1.2", "1.0", "both", "normal"],
        default="both",
        help="輸出版本語速：1.2 (1.2x快)、1.0/normal (正常語速)、both (雙版本皆輸出)",
    )
    args = parser.parse_args()

    if args.only:
        only_shots = set(args.only)
    elif args.only_flow and not args.rebuild_audio:
        only_shots = {s["id"] for s in SHOTS if s["engine"] == "flow"}
    else:
        only_shots = None

    ffmpeg_exe = find_ffmpeg()
    print(f"使用 FFmpeg: {ffmpeg_exe}")
    extract_figures_from_docx()
    flow_paths = generate_flow_keyframes()

    speeds_to_build = []
    if args.speed in ("1.2", "both"):
        speeds_to_build.append("1.2")
    if args.speed in ("1.0", "normal", "both"):
        speeds_to_build.append("1.0")

    for sp in speeds_to_build:
        if sp == "1.2":
            rate_val = "+20%"
            a_dir = OUT_ROOT / "audio"
            c_dir = OUT_ROOT / "clips"
            v_path = OUT_ROOT / "BPM_一般費用報銷單_私車公用教學總片_1.2x.mp4"
            m_path = OUT_ROOT / "storyboard_manifest.json"
            suffix = "（1.2x 語速版）"
        else:
            rate_val = "+0%"
            a_dir = OUT_ROOT / "audio_normal"
            c_dir = OUT_ROOT / "clips_normal"
            v_path = OUT_ROOT / "BPM_一般費用報銷單_私車公用教學總片_正常語速.mp4"
            m_path = OUT_ROOT / "storyboard_manifest_normal.json"
            suffix = "（正常語速版）"

        print(f"\n==========================================")
        print(f"開始建置版本：{sp}x 語速 ({rate_val})")
        print(f"==========================================")
        durations = synthesize_all_audio(
            ffmpeg_exe,
            rebuild_audio=args.rebuild_audio,
            voice_profile=args.voice,
            rate=rate_val,
            audio_dir=a_dir,
        )
        render_all_clips_and_concat(
            ffmpeg_exe,
            durations,
            flow_paths,
            only_shots=only_shots,
            voice_profile=args.voice,
            audio_dir=a_dir,
            clips_dir=c_dir,
            final_video_path=v_path,
            manifest_path=m_path,
            title_suffix=suffix,
        )
        # 同步複製到根目錄供方便點選
        try:
            shutil.copy2(v_path, Path(r"C:\GOOGLE ANGET") / v_path.name)
            if sp == "1.2":
                shutil.copy2(v_path, OUT_ROOT / "BPM_一般費用報銷單_私車公用教學總片.mp4")
                shutil.copy2(v_path, Path(r"C:\GOOGLE ANGET") / "BPM_一般費用報銷單_私車公用教學總片.mp4")
            print(f"[複製完成] -> C:\\GOOGLE ANGET\\{v_path.name}")
        except Exception as e:
            print(f"[警告] 複製到根目錄失敗: {e}")


if __name__ == "__main__":
    main()
