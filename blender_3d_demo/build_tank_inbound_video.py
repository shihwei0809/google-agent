"""
第 1 部《儲槽進貨與卸料篇》混合雙軌 SOP 電影教學影片管線
===========================================================================
對應文件：C50110-INV-02-01（版別 3.1）《儲槽進出貨作業方法》
涵蓋範圍：5.1 一般檢查 / 5.2 進貨作業（一般槽車 + ISO TANK）/ 附件 6.1 / 附件 6.4

核心特色：
1. 自動從原始 PDF 以 250 DPI 擷取 3 張流程圖 + 2 張完整檢點表單（6.1、6.4）並精準裁切留白
2. 獨家「表單檢點聚光燈引擎」：
   - 暗影壓暗遮罩 + 琥珀金 / 晴空青 / 翡翠綠雙層亮框（嚴格禁用純紅框）
   - 右側同步顯示 2.2x 局部原圖放大鏡特寫 + 白話檢點步驟卡
   - 單一鏡頭內依旁白進度自動切換多個焦點區塊，逐欄教會新人怎麼檢點與填寫
3. 雙軌電影化後製（無縫整合 cinema_post_engine）：
   - 支援 Google Flow Agent 3 段真人過場（b01 / b02 / b03），未放入前自動以高質感流程卡片補位
   - 支援 --export-voice-jobs 匯出 Colab T4 (BreezyVoice / VoxCPM2) 台灣讀音正規化配音工作單
   - 預設採用 edge-tts 台灣女聲（zh-TW-HsiaoChenNeural），可透過 --speed 調整倍速
   - 輸出 1920x1080 24fps 柔順 xfade 轉場 + 3 秒電影封面/封底 + BGM 語音閃避成片
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

BASE_DIR = Path(__file__).resolve().parent
_CINEMA_SCRIPTS = BASE_DIR.parent / ".agents" / "skills" / "sop-cinema-video" / "scripts"
if str(_CINEMA_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_CINEMA_SCRIPTS))

from cinema_post_engine import (
    concat_with_xfade,
    export_voice_jobs_json,
    mix_bgm_with_ducking,
    probe_duration,
    render_cinema_flow_clip,
    render_cover_clip,
    render_ending_clip,
    synthesize_gemini_tts,
)

# 路徑設定
PDF_CANDIDATES = [
    Path(r"C:\Users\C606\Desktop\C50110-INV-02-01 儲槽進出貨作業方法(3.1版).pdf"),
    BASE_DIR / "tank_inbound_sop" / "C50110-INV-02-01 儲槽進出貨作業方法(3.1版).pdf",
]
OUT_ROOT = BASE_DIR / "tank_inbound_sop"
FIG_DIR = OUT_ROOT / "figures"
FLOW_FRAMES_DIR = OUT_ROOT / "flow_frames"
FLOW_CLIPS_DIR = OUT_ROOT / "flow_clips"
AUDIO_DIR = OUT_ROOT / "audio"
CLIPS_DIR = OUT_ROOT / "clips"
WORK_DIR = OUT_ROOT / "_work"
VOICE_JOBS_PATH = OUT_ROOT / "inbound_voice_jobs.json"
FINAL_VIDEO_PATH = OUT_ROOT / "第1部_儲槽進貨與卸料篇_表單檢點教學總片.mp4"

VIDEO_W, VIDEO_H = 1920, 1080
FPS = 24

# 色彩系統（遵循 sop_hybrid_rules：禁用純紅框，改用琥珀金 / 晴空青 / 翡翠綠）
COLOR_BG_DARK = (11, 18, 32)       # 深海藍底
COLOR_CARD_BG = (20, 30, 48)       # 卡片深藍
COLOR_BORDER_SUB = (46, 64, 92)    # 細邊框
COLOR_TEXT_MAIN = (244, 247, 252)
COLOR_TEXT_MUTED = (168, 184, 208)

PALETTE = {
    "amber": (245, 158, 11),       # 琥珀金（核心紅線 / 必填數值）
    "cyan": (14, 165, 233),        # 晴空青（一般槽車 / 流程步驟）
    "emerald": (16, 185, 129),     # 翡翠綠（品管簽章 / 安全歸位）
    "orange": (249, 115, 22),      # 科技橘（ISO TANK 專屬識別色）
}

# PDF 頁面與自動裁切座標 (left, top, right, bottom) 相對比例
PDF_EXTRACTS = {
    "fig01_general_flow.png": (6, (0.18, 0.21, 0.82, 0.88)),
    "fig02_tanker_flow.png": (9, (0.18, 0.21, 0.84, 0.90)),
    "fig03_isotank_flow.png": (13, (0.18, 0.21, 0.84, 0.89)),
    "fig04_form_6_1.png": (23, (0.20, 0.245, 0.84, 0.915)),
    "fig05_form_6_4.png": (26, (0.20, 0.245, 0.86, 0.89)),
}


# ---------------------------------------------------------------------------
# 字型與 FFmpeg 工具
# ---------------------------------------------------------------------------

def find_font_path(bold: bool = False) -> str:
    candidates = (
        [r"C:\Windows\Fonts\msjhbd.ttc", r"C:\Windows\Fonts\NotoSansTC-VF.ttf", r"C:\Windows\Fonts\msjh.ttc"]
        if bold
        else [r"C:\Windows\Fonts\msjh.ttc", r"C:\Windows\Fonts\NotoSansTC-VF.ttf", r"C:\Windows\Fonts\mingliu.ttc"]
    )
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("找不到繁體中文字型 (msjh.ttc)")


_FONT_CACHE: Dict[Tuple[bool, int], ImageFont.FreeTypeFont] = {}


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (bold, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(find_font_path(bold=bold), size)
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
    raise FileNotFoundError("找不到 ffmpeg")


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    lines: List[str] = []
    cur = ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
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


# ---------------------------------------------------------------------------
# Step 1：從 PDF 擷取並精準裁切高清表單與流程圖
# ---------------------------------------------------------------------------

def extract_pdf_figures() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = next((p for p in PDF_CANDIDATES if p.exists()), None)
    if not pdf_path:
        missing = [k for k in PDF_EXTRACTS if not (FIG_DIR / k).exists()]
        if missing:
            raise FileNotFoundError(f"找不到原始 PDF，且缺少圖檔：{missing}")
        print("[Figures] 使用既有 figures/ 圖檔。")
        return

    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    for fname, (pno, crop_rel) in PDF_EXTRACTS.items():
        page = doc[pno - 1]
        pix = page.get_pixmap(dpi=260)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        w, h = img.size
        l, t, r, b = crop_rel
        cropped = img.crop((int(w * l), int(h * t), int(w * r), int(h * b)))
        # 輕微銳化讓表單文字在 1080p 下極致清晰
        cropped = cropped.filter(ImageFilter.UnsharpMask(radius=1.0, percent=120, threshold=3))
        cropped.save(FIG_DIR / fname, quality=95)
        print(f"[Figures] 擷取 P.{pno:02d} -> {fname} ({cropped.size[0]}x{cropped.size[1]})")


# ---------------------------------------------------------------------------
# Step 2：第 1 部 8 大分鏡定義（含表單聚光燈分段座標）
# ---------------------------------------------------------------------------

def get_shots() -> List[dict]:
    """
    每個 shot 支援：
    - type: 'flow' (支援 Flow 實片自動取代，未放實片時以流程圖+卡片呈現) 或 'form_spotlight' (表單聚光燈教學)
    - focus_steps: 表單聚光燈分段列表，每段包含：
        - weight: 時間權重
        - box: (x1, y1, x2, y2) 在裁切後表單圖上的相對比例 (0.0~1.0)
        - color: 'amber' | 'cyan' | 'emerald' | 'orange'
        - zoom_title: 右上角放大鏡標題
        - check_points: 右下角檢點步驟清單 (2~4 條)
        - badge_tag: 焦點標籤（如「必算容積」「≤ 10Ω 必抄」「品管強制卡控」）
    """
    return [
        {
            "id": "shot01",
            "type": "flow",
            "flow_clips": ["b01_intro_flow.mp4", "s01_b.mp4"],
            "theme": "cyan",
            "chapter": "01｜進貨前一般檢查 & PPE",
            "form_badge": "WI 5.1 一般檢查 / 5.4.1 PPE",
            "figure": "fig01_general_flow.png",
            "narration": (
                "歡迎來到儲槽進出貨作業教學第一部：進貨與卸料篇。"
                "每天開始進貨作業前，第一關絕對是個人防護裝備與一般檢查。"
                "所有現場人員都必須確實穿戴安全帽、安全鞋、護目鏡、防毒面具與防護手套。"
                "接著依當日進貨或調撥通知，核對產品名稱與儲槽別，確認管線凡爾、泵浦運轉正常、"
                "油水分離凡爾全關，並檢視滅火設備是否合乎要求。"
                "特別提醒：如果要用到管線接合室，必須先開立管線接合室異動單，"
                "並請轄區組長陪同、用 P D A 掃描確認後，才能開始進貨。"
            ),
            "tts_override": (
                "歡迎來到儲槽進出貨作業教學第一部：進貨與卸料篇。"
                "每天開始進貨作業前，第一關絕對是個人防護裝備與一般檢查。"
                "所有現場人員都必須確實穿戴安全帽、安全鞋、護目鏡、防毒面具與防護手套。"
                "接著依當日進貨或調撥通知，核對產品名稱與儲槽別，確認管線凡爾、泵浦運轉正常、"
                "油水分離凡爾全關，並檢視滅火設備是否合乎要求。"
                "特別提醒：如果要用到管線接合室，必須先開立管線接合室異動單，"
                "並請轄區組長陪同、用 P D A 掃描確認後，才能開始進貨。"
            ),
            "card_title": "進貨開工前 5 大確認（5.1）",
            "card_points": [
                "穿妥完整 PPE：安全帽、安全鞋、護目鏡、防毒面具、手套",
                "核對本日進貨/調撥通知之【產品名稱】與【儲槽別】",
                "確認儲槽管線、凡爾開關、泵浦正常，油水分離閥【全關】",
                "檢視現場滅火設備合乎要求",
                "若需使用管線接合室 → 填異動單 + 組長陪同 + PDA 確認",
            ],
        },
        {
            "id": "shot02",
            "type": "form_spotlight",
            "flow_clips": ["s02_a.mp4", "s02_b.mp4"],
            "theme": "cyan",
            "chapter": "02｜Part A 一般槽車入廠與取樣規則",
            "form_badge": "WI 5.2.1 槽車入廠流程",
            "figure": "fig02_tanker_flow.png",
            "narration": (
                "先來看一般油罐槽車進貨。槽車入廠後，先依進貨通知單核對品名、槽別、數量與車號。"
                "引導司機停妥卸貨位置後，務必熄火、拉手煞車、關閉收音機，"
                "放好兩組輪檔固定輪胎、擺設滅火器、三角錐與盛漏盤、接妥靜電接地線，"
                "並且把車鑰匙統一收到鑰匙箱鎖管。"
                "卸貨前必須先取樣檢驗：第一、二輪由每年經品管認證的現場操作員取樣；"
                "如果連兩次不合格，第三輪起就必須改由品管人員親自取樣。"
                "檢驗不合格絕對不可擅自卸貨，必須立刻回報主管判定特採或退貨。"
            ),
            "focus_steps": [
                {
                    "weight": 0.55,
                    "box": (0.20, 0.04, 0.72, 0.36),
                    "color": "cyan",
                    "badge_tag": "進廠定位與防呆鎖管",
                    "zoom_title": "5.2.1 槽車進廠定位動作",
                    "check_points": [
                        "核對進貨通知單：品名 / 槽別 / 數量 / 車號",
                        "熄火、拉手煞車、關收音機，車鑰匙交至鑰匙箱",
                        "放妥 2 組輪檔、滅火器、三角錐、盛漏盤與接地線",
                    ],
                },
                {
                    "weight": 0.45,
                    "box": (0.04, 0.34, 0.78, 0.48),
                    "color": "amber",
                    "badge_tag": "取樣輪次紅線",
                    "zoom_title": "第 1–2 輪操作員｜第 3 輪品管",
                    "check_points": [
                        "第 1、2 輪：每年經品管認證之現場操作員取樣",
                        "第 3 輪起：強制通知品管人員親自取樣（噸桶/桶裝品直接品管取樣）",
                        "檢驗不合格【嚴禁擅卸】，回報主管判定特採或退貨",
                    ],
                },
            ],
        },
        {
            "id": "shot03",
            "type": "form_spotlight",
            "theme": "cyan",
            "chapter": "03｜表單檢點特寫：附件 6.1（表頭＋入料前）",
            "form_badge": "表單 C50110-INV-02-01(05)",
            "figure": "fig04_form_6_1.png",
            "narration": (
                "取樣合格準備泵料前，請拿出第一張核心表單：附件六之一，槽車泵料入儲槽檢查表，當日作業前必檢一次。"
                "第一步先看表頭容積試算：把儲槽最大容積減去目前容積，算出目前可存容積再乘上比重，"
                "對照本日預定入槽量，確認絕對不會滿槽溢料。"
                "接著看入料前十二項檢點，有三個最容易出事的紅線："
                "第一，接地線電阻必須在十歐姆以下，而且一定要把歐姆計實測數值抄進表格；"
                "第二，卸貨區兩公尺內淨空、鑰匙掛指定位置、消防系統待命；"
                "第三，部分儲槽務必使用掃描設備對刷，確認入料軟管與儲槽編號完全相符才能銜接，徹底杜絕混料！"
            ),
            "focus_steps": [
                {
                    "weight": 0.34,
                    "box": (0.02, 0.055, 0.98, 0.205),
                    "color": "amber",
                    "badge_tag": "表頭必算｜防爆槽溢料",
                    "zoom_title": "表頭：(A)最大 - (B)目前 = (C)可存容積",
                    "check_points": [
                        "勾選彰濱 1 廠(線西) 或 2 廠(崙尾) 並填日期與儲槽/泵浦編號",
                        "試算：(C)可存容積 × 比重 = 目前可存數量 (M/T)",
                        "比對「本日預定入槽量」，空間不足嚴禁入料",
                    ],
                },
                {
                    "weight": 0.33,
                    "box": (0.02, 0.24, 0.98, 0.415),
                    "color": "cyan",
                    "badge_tag": "紅線 1｜10Ω 以下必抄數值",
                    "zoom_title": "入料前檢查（第 1–6 項）",
                    "pip_clip": "s03_a.mp4",
                    "check_points": [
                        "車輛鑰匙掛至指定位置、輪檔定位、三角錐與滅火器備妥",
                        "接地線接妥且電阻【10 歐姆以下】→ 必須實填歐姆值",
                        "卸貨區 2 公尺內不可有影響安全之事物、消防待命",
                    ],
                },
                {
                    "weight": 0.33,
                    "box": (0.02, 0.415, 0.98, 0.56),
                    "color": "emerald",
                    "badge_tag": "紅線 2｜掃描對刷防混料",
                    "zoom_title": "入料前檢查（第 7–12 項）",
                    "pip_clip": "s03_b.mp4",
                    "check_points": [
                        "核對品名與進貨通知單相符、入料泵浦清潔、管線無破損",
                        "★ 必做：使用掃描設備【對刷確認】入料軟管與儲槽相符",
                        "確認該儲槽相關阻閥與管線全數在正確開關位置",
                    ],
                },
            ],
        },
        {
            "id": "shot04",
            "type": "form_spotlight",
            "theme": "cyan",
            "chapter": "04｜表單檢點特寫：附件 6.1（入料中/後＋泵浦操作）",
            "form_badge": "表單 C50110-INV-02-01(05) & WI 5.2.3",
            "figure": "fig04_form_6_1.png",
            "narration": (
                "啟動泵浦時記得標準口訣：先開卸貨泵浦洩壓閥三分之一排空軟管氣體，關閉洩壓閥再啟動電源；"
                "接著開出口閥三分之一觀察壓力表正常才全開，同時開啟槽車排氣閥避免負壓損壞槽車，並沿管線巡查至儲槽。"
                "這時請填寫六之一表單的入料中四項：確認液位計作動、洩壓開啟、實抄泵浦作業壓力，"
                "以及最關鍵的袋式過濾器壓力——只要超過兩公斤每平方公分，或使用滿十二個月、累計超過一萬兩千噸，就必須更換過濾袋！"
                "泵空後先關出口閥、確認壓力歸零再關電源，拆管前必用氮氣排空並洩壓，確保化學品不落地。"
                "最後勾完入料後五項，記住填表規定：正常打是、異常打否、不適用用斜線劃掉，再送交組長與課長簽核。"
            ),
            "focus_steps": [
                {
                    "weight": 0.52,
                    "box": (0.02, 0.555, 0.98, 0.695),
                    "color": "amber",
                    "badge_tag": "入料中｜> 2 kg/cm² 換濾袋",
                    "zoom_title": "入料中檢查（4 項＋5.2.3 泵浦口訣）",
                    "pip_clip": "s04_a.mp4",
                    "check_points": [
                        "泵浦口訣：開 1/3 洩壓排氣 → 關洩壓啟電 → 開 1/3 出口閥確認壓力 → 全開",
                        "同步開槽車排氣閥防負壓，入料後沿管線巡查至儲槽、緊盯液位",
                        "實填 PUMP 壓力與袋式過濾器壓力（> 2 kg/cm² / 12月 / 12,000噸換袋）",
                    ],
                },
                {
                    "weight": 0.48,
                    "box": (0.02, 0.695, 0.98, 0.97),
                    "color": "emerald",
                    "badge_tag": "入料後｜排空洩壓＋填表規範",
                    "zoom_title": "入料後檢查（5 項）＋備註與三級簽核",
                    "pip_clip": "s04_b.mp4",
                    "check_points": [
                        "停泵後先氮氣排空＋洩壓才拆管（化學品不落地），塞頭蓋妥扣緊掛耳",
                        "閥件關妥、接地線收納、輪檔歸位、氮氣源頭關閉拔除",
                        "填表規則：正常打「是」、異常打「否」、不適用「\\」劃掉 → 三級簽核",
                    ],
                },
            ],
        },
        {
            "id": "shot05",
            "type": "flow",
            "flow_clips": ["s05_b.mp4", "b02_bridge_flow.mp4"],
            "theme": "orange",
            "chapter": "05｜Part B ISO TANK 進場與高處防墜",
            "form_badge": "WI 5.2.5 ISO TANK 卸貨安全紅線",
            "figure": "fig03_isotank_flow.png",
            "narration": (
                "接下來切換到第二種車型：ISO TANK 貨櫃化學槽進貨。"
                "跟一般油罐車最大的不同有兩點：第一，引導駛入定位後，必須拔除車頭、"
                "放妥輪檔、滅火器、三角錐並接妥接地線，確認全部完成後，車頭才可以駛離現場。"
                "第二，ISO TANK 頂部作業高度超過兩公尺，所有人員銜接頂部氮氣管或進行取樣時，"
                "都必須依規定穿戴背負式安全帶，並將安全掛勾確實勾掛在防墜桿或車體上，嚴防墜落意外。"
            ),
            "card_title": "ISO TANK 專屬 2 大工安鐵律",
            "card_points": [
                "定位拔車頭前：先放輪檔 + 滅火器 + 三角錐 + 接妥接地線，車頭才可駛離",
                "2 公尺以上高處作業：必穿【背負式安全帶】並勾掛於防墜桿或車體",
                "頂部出料取樣前：必先填寫【附件 6.4 ISO TANK 取樣作業檢點表】",
                "接妥頂部氮氣軟管前：先用轉接頭對外排吹 3–5 次，確保管線潔淨",
            ],
        },
        {
            "id": "shot06",
            "type": "form_spotlight",
            "theme": "orange",
            "chapter": "06｜表單檢點特寫：附件 6.4（接合前＋品管卡控）",
            "form_badge": "表單 C50110-INV-02-01(02)",
            "figure": "fig05_form_6_4.png",
            "narration": (
                "進行 ISO TANK 頂部出料取樣前，請拿出第二張核心表單：附件六之四，ISO TANK 取樣作業檢點表。"
                "這張表單採「接合前」與「拆卸後」雙欄對照設計，填寫符號要注意：正常打勾，異常打叉並寫明備註。"
                "接合前先逐項檢查第一到第十五項：輪檔、接地線實測十歐姆以下、三角錐與滅火器、"
                "氮氣與化學品閥關閉、軟管管帽與接頭無異常折損、槽頂箱無殘液、安全閥與外觀完好，並簽上實施者姓名。"
                "接著將化學品軟管接妥取樣箱，氮氣管接上槽頂前先對外排吹三到五次，再對槽內料品進行 Flush。"
                "請看表單中段粗框處：依附註二規定，壓出四十公升後請品管人員取樣判定，"
                "一定要等到品管人員簽章確認合格，才可以進入下一步收管與卸貨！"
            ),
            "focus_steps": [
                {
                    "weight": 0.55,
                    "box": (0.02, 0.08, 0.98, 0.63),
                    "color": "orange",
                    "badge_tag": "接合前 15 項｜V 正常 / X 異常",
                    "zoom_title": "附件 6.4：接合前檢點欄位（1–15 項）",
                    "check_points": [
                        "寫明品名與 ISO TANK 號碼，先填【接合前】直欄（V 正常 / X 異常寫備註）",
                        "第 2 項接地線必實測 ≤ 10Ω 並紀錄；確認閥關閉、NSB 管帽/接頭/軟管無折損",
                        "確認槽頂箱無化學品、安全閥無破裂、槽體壓力 0.5–1 kg/cm² 紀錄",
                    ],
                },
                {
                    "weight": 0.45,
                    "box": (0.02, 0.605, 0.98, 0.725),
                    "color": "emerald",
                    "badge_tag": "強制停等｜品管簽章才放行",
                    "zoom_title": "中段粗框：ISO TANK 內部判定合格簽章",
                    "pip_clip": "s06_a.mp4",
                    "check_points": [
                        "氮氣管接妥前先對外排吹 3–5 次，Flush 壓出 40L 後請品管取樣",
                        "若檢驗不合格，必須重複 Flush 取樣步驟直到合格",
                        "★ 必有【品管人員簽章】判定合格，始可收管與卸料",
                    ],
                },
            ],
        },
        {
            "id": "shot07",
            "type": "form_spotlight",
            "theme": "orange",
            "chapter": "07｜表單檢點特寫：附件 6.4（拆卸後）& 5.2.5 Flush 基準",
            "form_badge": "表單 6.4 拆卸後 / WI 5.2.5 卸貨",
            "figure": "fig05_form_6_4.png",
            "narration": (
                "取樣合格後，把剩餘料品排至一噸桶回收，釋放氮氣與化學品管線內部壓力，再拆除管線收進頂部箱體，"
                "並立即填完附件六之四的「拆卸後」直欄，送組長與課長簽核。"
                "接下來進行正式卸料時，務必牢記不同等級的 Flush 標準量："
                "工業級 Flush 四十公升；電子級 Flush 至一噸桶兩百公升，由品管取樣檢驗；"
                "如果是超過三個月沒入廠的槽車，電子級更必須加倍 Flush 四百公升！"
                "卸料前同樣要填妥附件六之一檢查表、對刷確認軟管與儲槽相符，再開啟氮氣補壓、開啟緊急遮斷閥與卸料閥入料，"
                "過程中沿管線巡查並緊盯液位計，接近滿位適時停料換槽。"
            ),
            "focus_steps": [
                {
                    "weight": 0.48,
                    "box": (0.64, 0.08, 0.98, 0.78),
                    "color": "cyan",
                    "badge_tag": "拆卸後複檢＋三級簽核",
                    "zoom_title": "拆卸後直欄＋實施者 / 組長 / 課長簽核",
                    "check_points": [
                        "剩餘料品排至 1T 桶回收，釋放氮氣與化學品管線壓力再拆管收納",
                        "逐項勾填【拆卸後】直欄，確認閥件關閉、管帽蓋妥、槽體保壓 0.5–1 kg/cm²",
                        "實施者簽名後送組長確認與課(副)長簽核，異常處置過程須完整寫入表內",
                    ],
                },
                {
                    "weight": 0.52,
                    "box": (0.02, 0.78, 0.98, 0.97),
                    "color": "amber",
                    "badge_tag": "5.2.5 Flush 數值鐵律",
                    "zoom_title": "附註規範＋ISO TANK 卸貨 Flush 基準",
                    "pip_clip": "s06_a.mp4",
                    "check_points": [
                        "工業級 Flush 約 40L（1–2 輪認證操作員取樣，第 3 輪品管取樣）",
                        "電子級 Flush 至 1T 桶約 200L（品管取樣）；超過 3 個月未入廠須 Flush 400L",
                        "卸料前必做 6.1 檢查表 + 掃描對刷 + 氮氣補壓 + 開緊急遮斷閥與卸料閥",
                    ],
                },
            ],
        },
        {
            "id": "shot08",
            "type": "flow",
            "flow_clips": ["b03_outro_flow.mp4"],
            "theme": "emerald",
            "chapter": "08｜泵空洩壓、設備歸位與安全送行",
            "form_badge": "零洩漏・零混料・雙表單完整簽核",
            "figure": "fig03_isotank_flow.png",
            "narration": (
                "當槽車或 ISO TANK 泵空後，請依序關閉氮氣閥停止補壓，"
                "拆管前一定要再次確認管線內部已經完全洩壓，避免殘料噴濺，堅持化學品不落地原則，"
                "再拆除砲管、氮氣管、轉接頭與接地線。"
                "最後環視現場：確認氮氣源頭關閉、所有管線、轉接頭、輪檔與接地線全數放回定位，"
                "同時檢查附件六之一與六之四表單欄位與簽核無遺漏，即可安心指揮車輛開往地磅。"
                "第一部進貨與卸料篇到此結束，下一部我們將帶您演練出貨與灌裝檢點！"
            ),
            "card_title": "進貨收尾 4 步驟（安全下莊）",
            "card_points": [
                "泵空 → 關閉氮氣補壓 → 確認管線【完全洩壓】才拆管（化學品不落地）",
                "拆除砲管 / 軟管 / 氮氣管 / 轉接頭 / 接地線，塞頭蓋妥扣緊掛耳",
                "確認氮氣源頭關閉、現場與車體設備全數歸位",
                "複核附件 6.1 / 6.4 填寫與簽核完整 → 指揮開往地磅",
            ],
        },
    ]


# ---------------------------------------------------------------------------
# Step 3：台灣讀音正規化與語音合成
# ---------------------------------------------------------------------------

def normalize_industrial_tts(text: str) -> str:
    """補強化工與儲槽專有名詞讀音，避免 TTS 唸錯。"""
    replacements = {
        "ISO TANK": "I S O Tank",
        "PPE": "P P E",
        "PDA": "P D A",
        "NSB": "N S B",
        "PUMP": "泵浦",
        "Flush": "沖洗",
        "kg/cm²": "公斤每平方公分",
        "Kg/cm²": "公斤每平方公分",
        "10Ω": "十歐姆",
        "1T桶": "一噸桶",
        "40L": "四十公升",
        "200L": "兩百公升",
        "400L": "四百公升",
    }
    out = text
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


async def _edge_tts_save(text: str, out_mp3: Path, rate: str = "+12%") -> None:
    import edge_tts

    comm = edge_tts.Communicate(text=text, voice="zh-TW-HsiaoChenNeural", rate=rate)
    await comm.save(str(out_mp3))


def synthesize_audio(shots: List[dict], ffmpeg_exe: str, speed: float = 1.12, use_gemini: bool = False) -> Dict[str, Path]:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    rate_pct = int(round((speed - 1.0) * 100))
    rate_str = f"{rate_pct:+d}%"
    audio_map: Dict[str, Path] = {}

    for s in shots:
        sid = s["id"]
        out_mp3 = AUDIO_DIR / f"{sid}.mp3"
        # 若已有外部放置的高音質 Colab 克隆音檔（>10KB 且檔名存在），優先保留不覆蓋
        if out_mp3.exists() and out_mp3.stat().st_size > 10_000 and not os.environ.get("FORCE_TTS"):
            print(f"[Audio] 沿用既有音檔：{out_mp3.name} ({probe_duration(ffmpeg_exe, out_mp3):.1f}s)")
            audio_map[sid] = out_mp3
            continue

        raw_txt = s.get("tts_override") or s["narration"]
        tts_txt = normalize_industrial_tts(raw_txt)
        if use_gemini:
            try:
                synthesize_gemini_tts(tts_txt, out_mp3, ffmpeg_exe)
                print(f"[Audio] Gemini TTS 完成：{out_mp3.name}")
                audio_map[sid] = out_mp3
                continue
            except Exception as e:
                print(f"[Audio] Gemini TTS 失敗 ({e})，自動降級 edge-tts")

        asyncio.run(_edge_tts_save(tts_txt, out_mp3, rate=rate_str))
        dur = probe_duration(ffmpeg_exe, out_mp3)
        print(f"[Audio] edge-tts 完成：{out_mp3.name} ({dur:.1f}s, rate={rate_str})")
        audio_map[sid] = out_mp3
    return audio_map


# ---------------------------------------------------------------------------
# Step 4：畫面渲染器（表單聚光燈 + 局部放大鏡 + 檢點步驟卡 + 字幕條）
# ---------------------------------------------------------------------------

def draw_rounded_rect(draw: ImageDraw.ImageDraw, xy, radius: int, fill=None, outline=None, width: int = 1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def render_top_bar(canvas: Image.Image, chapter: str, form_badge: str, accent_rgb: Tuple[int, int, int]) -> None:
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(0, 0), (VIDEO_W, 76)], fill=(14, 22, 38))
    draw.rectangle([(0, 74), (VIDEO_W, 78)], fill=accent_rgb)

    # 左側系列膠囊 + 章節標題
    draw_rounded_rect(draw, (32, 16, 260, 60), radius=10, fill=accent_rgb)
    f_pill = get_font(22, bold=True)
    draw.text((146, 38), "第1部｜儲槽進貨篇", font=f_pill, fill=(10, 15, 25), anchor="mm")

    f_chap = get_font(28, bold=True)
    draw.text((284, 38), chapter, font=f_chap, fill=COLOR_TEXT_MAIN, anchor="lm")

    # 右側表單編號膠囊
    f_badge = get_font(22, bold=True)
    bw = int(draw.textlength(form_badge, font=f_badge)) + 40
    bx1 = VIDEO_W - 32 - bw
    draw_rounded_rect(draw, (bx1, 16, VIDEO_W - 32, 60), radius=10, fill=(26, 40, 64), outline=accent_rgb, width=2)
    draw.text((bx1 + bw // 2, 38), form_badge, font=f_badge, fill=accent_rgb, anchor="mm")


def render_subtitle_bar(canvas: Image.Image, subtitle: str) -> None:
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    bar_y1, bar_y2 = VIDEO_H - 118, VIDEO_H - 22
    odraw.rounded_rectangle((120, bar_y1, VIDEO_W - 120, bar_y2), radius=16, fill=(8, 14, 26, 220), outline=(72, 96, 132, 180), width=2)

    f_sub = get_font(30, bold=True)
    lines = wrap_text(odraw, subtitle, f_sub, VIDEO_W - 300)[:2]
    total_h = len(lines) * 40
    start_y = (bar_y1 + bar_y2 - total_h) // 2 + 18
    for i, line in enumerate(lines):
        odraw.text((VIDEO_W // 2, start_y + i * 40), line, font=f_sub, fill=(250, 252, 255, 255), anchor="mm")

    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB"))


def build_spotlight_frame(
    fig_path: Path,
    chapter: str,
    form_badge: str,
    theme_name: str,
    step: dict,
    subtitle: str,
    has_pip: bool = False,
) -> Image.Image:
    accent = PALETTE.get(theme_name, PALETTE["cyan"])
    hl_color = PALETTE.get(step.get("color", "amber"), PALETTE["amber"])

    canvas = Image.new("RGB", (VIDEO_W, VIDEO_H), COLOR_BG_DARK)
    render_top_bar(canvas, chapter, form_badge, accent)

    # 左側：表單原圖區域 (x: 36..1060, y: 96..944)
    panel_l, panel_t, panel_r, panel_b = 36, 96, 1060, 944
    panel_w, panel_h = panel_r - panel_l, panel_b - panel_t
    draw = ImageDraw.Draw(canvas)
    draw_rounded_rect(draw, (panel_l, panel_t, panel_r, panel_b), radius=16, fill=(18, 28, 44), outline=COLOR_BORDER_SUB, width=2)

    src = Image.open(fig_path).convert("RGB")
    sw, sh = src.size
    scale = min((panel_w - 28) / sw, (panel_h - 28) / sh)
    dw, dh = int(sw * scale), int(sh * scale)
    resized = src.resize((dw, dh), Image.Resampling.LANCZOS)
    resized = resized.filter(ImageFilter.UnsharpMask(radius=0.8, percent=110, threshold=2))

    ox = panel_l + (panel_w - dw) // 2
    oy = panel_t + (panel_h - dh) // 2

    # 暗影壓暗聚光燈遮罩（非重點區域壓暗至 48%，重點框內保持 100% 透亮）
    dimmed = ImageEnhance.Brightness(resized).enhance(0.48)
    bx1_rel, by1_rel, bx2_rel, by2_rel = step["box"]
    rx1, ry1 = int(dw * bx1_rel), int(dh * by1_rel)
    rx2, ry2 = int(dw * bx2_rel), int(dh * by2_rel)
    rx1, ry1 = max(0, rx1), max(0, ry1)
    rx2, ry2 = min(dw, rx2), min(dh, ry2)

    # 將亮區貼回 dimmed
    bright_patch = resized.crop((rx1, ry1, rx2, ry2))
    dimmed.paste(bright_patch, (rx1, ry1))
    canvas.paste(dimmed, (ox, oy))

    # 雙層聚光燈亮框（外光暈 + 內實線，禁用純紅）
    draw = ImageDraw.Draw(canvas)
    fx1, fy1, fx2, fy2 = ox + rx1, oy + ry1, ox + rx2, oy + ry2
    draw.rectangle((fx1 - 4, fy1 - 4, fx2 + 4, fy2 + 4), outline=(255, 255, 255), width=2)
    draw.rectangle((fx1, fy1, fx2, fy2), outline=hl_color, width=5)

    # 焦點標籤貼在亮框上方或內部左上角
    tag = step.get("badge_tag", "檢點重點")
    f_tag = get_font(20, bold=True)
    tw = int(draw.textlength(tag, font=f_tag)) + 26
    ty = fy1 - 34 if fy1 - 34 > panel_t + 6 else fy1 + 6
    draw_rounded_rect(draw, (fx1, ty, fx1 + tw, ty + 30), radius=6, fill=hl_color)
    draw.text((fx1 + tw // 2, ty + 15), tag, font=f_tag, fill=(12, 18, 28), anchor="mm")

    # 右側上半：高解析局部放大鏡特寫 (x: 1088..1884, y: 96..515)
    zm_l, zm_t, zm_r, zm_b = 1088, 96, 1884, 515
    draw_rounded_rect(draw, (zm_l, zm_t, zm_r, zm_b), radius=16, fill=COLOR_CARD_BG, outline=hl_color, width=3)
    draw.rectangle((zm_l + 3, zm_t + 3, zm_r - 3, zm_t + 48), fill=(26, 38, 60))
    f_zt = get_font(22, bold=True)
    draw.text((zm_l + 20, zm_t + 26), f"【放大檢視】{step.get('zoom_title', '')}", font=f_zt, fill=hl_color, anchor="lm")

    # 從原圖裁切對應區域並等比縮放塞入放大鏡區
    sx1, sy1 = max(0, int(sw * bx1_rel)), max(0, int(sh * by1_rel))
    sx2, sy2 = min(sw, int(sw * bx2_rel)), min(sh, int(sh * by2_rel))
    crop_hi = src.crop((sx1, sy1, sx2, sy2))
    cw, ch = crop_hi.size
    box_w, box_h = (zm_r - zm_l - 28), (zm_b - zm_t - 66)
    zscale = min(box_w / max(1, cw), box_h / max(1, ch))
    zw, zh = max(1, int(cw * zscale)), max(1, int(ch * zscale))
    crop_resized = crop_hi.resize((zw, zh), Image.Resampling.LANCZOS)
    crop_resized = crop_resized.filter(ImageFilter.UnsharpMask(radius=1.0, percent=125, threshold=2))
    zx = zm_l + 14 + (box_w - zw) // 2
    zy = zm_t + 56 + (box_h - zh) // 2
    canvas.paste(crop_resized, (zx, zy))

    # 右側下半：白話檢點動作卡 (x: 1088..1884, y: 536..944)
    # 若 has_pip=True，左半保留 360x202 真人實作 PiP 視窗 (1108, 608)-(1468, 810)，右半精簡條列檢點重點
    ck_l, ck_t, ck_r, ck_b = 1088, 536, 1884, 944
    draw = ImageDraw.Draw(canvas)
    draw_rounded_rect(draw, (ck_l, ck_t, ck_r, ck_b), radius=16, fill=COLOR_CARD_BG, outline=COLOR_BORDER_SUB, width=2)
    f_ck_h = get_font(25, bold=True)
    header_txt = "● 現場實作 × 檢點重點" if has_pip else "● 現場檢點怎麼做？"
    draw.text((ck_l + 24, ck_t + 30), header_txt, font=f_ck_h, fill=PALETTE["emerald"], anchor="lm")
    draw.line((ck_l + 20, ck_t + 54, ck_r - 20, ck_t + 54), fill=COLOR_BORDER_SUB, width=2)

    if has_pip:
        # 繪製 PiP 外框與底部標籤
        px1, py1, px2, py2 = 1108, 608, 1468, 810
        draw.rectangle((px1 - 3, py1 - 3, px2 + 3, py2 + 3), outline=hl_color, width=3)
        draw_rounded_rect(draw, (px1, py2 + 10, px2, py2 + 44), radius=8, fill=(24, 38, 60), outline=hl_color, width=1)
        draw.text(((px1 + px2) // 2, py2 + 27), "LIVE 現場滿配 PPE 實演", font=get_font(18, bold=True), fill=hl_color, anchor="mm")

        # 右半精簡 3 條檢點紅線
        f_pt = get_font(19, bold=False)
        tx_start = 1486
        cur_y = ck_t + 72
        for idx, pt in enumerate(step.get("check_points", []), 1):
            draw.ellipse((tx_start, cur_y + 2, tx_start + 26, cur_y + 28), fill=hl_color)
            draw.text((tx_start + 13, cur_y + 15), str(idx), font=get_font(15, bold=True), fill=(12, 18, 28), anchor="mm")
            wrapped = wrap_text(draw, pt, f_pt, ck_r - tx_start - 48)
            for j, wline in enumerate(wrapped):
                draw.text((tx_start + 34, cur_y + j * 27), wline, font=f_pt, fill=COLOR_TEXT_MAIN)
            cur_y += max(1, len(wrapped)) * 27 + 14
    else:
        f_pt = get_font(23, bold=False)
        cur_y = ck_t + 74
        for idx, pt in enumerate(step.get("check_points", []), 1):
            draw.ellipse((ck_l + 24, cur_y + 2, ck_l + 54, cur_y + 32), fill=hl_color)
            draw.text((ck_l + 39, cur_y + 17), str(idx), font=get_font(18, bold=True), fill=(12, 18, 28), anchor="mm")
            wrapped = wrap_text(draw, pt, f_pt, ck_r - ck_l - 94)
            for j, wline in enumerate(wrapped):
                draw.text((ck_l + 68, cur_y + j * 34), wline, font=f_pt, fill=COLOR_TEXT_MAIN)
            cur_y += max(1, len(wrapped)) * 34 + 18

    render_subtitle_bar(canvas, subtitle)
    return canvas


def build_flow_fallback_frame(
    fig_path: Path,
    chapter: str,
    form_badge: str,
    theme_name: str,
    card_title: str,
    card_points: List[str],
    subtitle: str,
) -> Image.Image:
    """當 Flow 實片尚未匯入時，以高質感流程圖 + 要點卡呈現，結構一致不留黑畫面。"""
    accent = PALETTE.get(theme_name, PALETTE["cyan"])
    canvas = Image.new("RGB", (VIDEO_W, VIDEO_H), COLOR_BG_DARK)
    render_top_bar(canvas, chapter, form_badge, accent)

    draw = ImageDraw.Draw(canvas)
    # 左側流程圖
    pl, pt, pr, pb = 36, 96, 940, 944
    draw_rounded_rect(draw, (pl, pt, pr, pb), radius=16, fill=(248, 250, 252), outline=accent, width=3)
    src = Image.open(fig_path).convert("RGB")
    scale = min((pr - pl - 28) / src.width, (pb - pt - 28) / src.height)
    dw, dh = int(src.width * scale), int(src.height * scale)
    resized = src.resize((dw, dh), Image.Resampling.LANCZOS)
    canvas.paste(resized, (pl + (pr - pl - dw) // 2, pt + (pb - pt - dh) // 2))

    # 右側重點摘要卡
    rl, rt, rr, rb = 972, 96, 1884, 944
    draw = ImageDraw.Draw(canvas)
    draw_rounded_rect(draw, (rl, rt, rr, rb), radius=16, fill=COLOR_CARD_BG, outline=COLOR_BORDER_SUB, width=2)
    draw.rectangle((rl + 2, rt + 2, rr - 2, rt + 74), fill=(26, 40, 66))
    draw.text((rl + 28, rt + 38), card_title, font=get_font(30, bold=True), fill=accent, anchor="lm")

    f_pt = get_font(26, bold=False)
    cur_y = rt + 104
    for idx, pt_txt in enumerate(card_points, 1):
        draw_rounded_rect(draw, (rl + 26, cur_y + 2, rl + 62, cur_y + 38), radius=8, fill=accent)
        draw.text((rl + 44, cur_y + 20), f"0{idx}", font=get_font(19, bold=True), fill=(12, 18, 28), anchor="mm")
        wrapped = wrap_text(draw, pt_txt, f_pt, rr - rl - 108)
        for j, wl in enumerate(wrapped):
            draw.text((rl + 80, cur_y + j * 38), wl, font=f_pt, fill=COLOR_TEXT_MAIN)
        cur_y += max(1, len(wrapped)) * 38 + 26

    render_subtitle_bar(canvas, subtitle)
    return canvas


def split_subtitles(text: str, n_chunks: int) -> List[str]:
    """依標點將旁白切分為對應張數的字幕。"""
    sentences = [s.strip() for s in re.split(r"(?<=[。！？；])", text) if s.strip()]
    if not sentences:
        return [text] * n_chunks
    if len(sentences) <= n_chunks:
        res = sentences[:]
        while len(res) < n_chunks:
            res.append(res[-1])
        return res
    # 平均分配句數到 n_chunks
    chunks: List[str] = []
    per = len(sentences) / n_chunks
    for i in range(n_chunks):
        s_idx = int(round(i * per))
        e_idx = int(round((i + 1) * per))
        seg = "".join(sentences[s_idx:max(s_idx + 1, e_idx)])
        chunks.append(seg)
    return chunks


# ---------------------------------------------------------------------------
# Step 5：單鏡影片編碼（FFmpeg 1080p 24fps + 音軌對齊）
# ---------------------------------------------------------------------------

def _make_flow_hud_png(out_png: Path, chapter_badge: str, subtitle: str, accent_rgb: Tuple[int, int, int]) -> Path:
    hud = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(hud)
    if chapter_badge:
        f_b = get_font(22, bold=True)
        bw = int(od.textlength(chapter_badge, font=f_b)) + 44
        bx1 = VIDEO_W - bw - 32
        od.rounded_rectangle((bx1, 24, VIDEO_W - 32, 68), radius=12, fill=(11, 18, 32, 195), outline=(*accent_rgb, 230), width=2)
        od.text((bx1 + bw // 2, 46), chapter_badge, font=f_b, fill=(248, 250, 252, 255), anchor="mm")
    if subtitle.strip():
        bar_y1, bar_y2 = VIDEO_H - 118, VIDEO_H - 22
        od.rounded_rectangle((120, bar_y1, VIDEO_W - 120, bar_y2), radius=16, fill=(8, 14, 26, 205), outline=(*accent_rgb, 170), width=2)
        f_sub = get_font(30, bold=True)
        lines = wrap_text(od, subtitle.strip(), f_sub, VIDEO_W - 300)[:2]
        total_h = len(lines) * 40
        start_y = (bar_y1 + bar_y2 - total_h) // 2 + 18
        for i, line in enumerate(lines):
            od.text((VIDEO_W // 2, start_y + i * 40), line, font=f_sub, fill=(250, 252, 255, 255), anchor="mm")
    hud.save(out_png)
    return out_png


def render_mixed_segments_clip(
    ffmpeg_exe: str,
    segments: List[dict],
    audio_path: Path,
    out_mp4: Path,
) -> Path:
    """
    通用電影混剪分段編碼器（支援 3 種分段自由串接 + apad/-t 硬鎖定 0.01s 同步）：
    - kind == 'flow_full': {'kind': 'flow_full', 'mp4': Path, 'hud': Path, 'dur': float}
    - kind == 'still_pip': {'kind': 'still_pip', 'img': Path, 'pip': Path, 'dur': float}
    - kind == 'still':     {'kind': 'still',     'img': Path, 'dur': float}
    """
    total_dur = sum(seg["dur"] for seg in segments)
    cmd: List[str] = [ffmpeg_exe, "-y"]
    fc_parts: List[str] = []
    v_tags: List[str] = []
    in_idx = 0

    for i, seg in enumerate(segments):
        d = seg["dur"]
        tag = f"[vseg{i}]"
        if seg["kind"] == "flow_full":
            cmd += ["-stream_loop", "-1", "-t", f"{d:.4f}", "-i", str(seg["mp4"])]
            i_mp4 = in_idx; in_idx += 1
            cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.4f}", "-i", str(seg["hud"])]
            i_hud = in_idx; in_idx += 1
            fc_parts.append(
                f"[{i_mp4}:v]scale={VIDEO_W}:{VIDEO_H}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={VIDEO_W}:{VIDEO_H},fps={FPS},format=rgba[fb{i}];"
                f"[fb{i}][{i_hud}:v]overlay=0:0:shortest=1,format=yuv420p{tag}"
            )
        elif seg["kind"] == "still_pip":
            cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.4f}", "-i", str(seg["img"])]
            i_img = in_idx; in_idx += 1
            cmd += ["-stream_loop", "-1", "-t", f"{d:.4f}", "-i", str(seg["pip"])]
            i_pip = in_idx; in_idx += 1
            fc_parts.append(
                f"[{i_img}:v]fps={FPS},format=rgba[bg{i}];"
                f"[{i_pip}:v]scale=360:202:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop=360:202,fps={FPS},format=rgba[pp{i}];"
                f"[bg{i}][pp{i}]overlay=1108:608:shortest=1,format=yuv420p{tag}"
            )
        else:
            cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.4f}", "-i", str(seg["img"])]
            i_img = in_idx; in_idx += 1
            fc_parts.append(f"[{i_img}:v]fps={FPS},format=yuv420p{tag}")
        v_tags.append(tag)

    audio_idx = in_idx
    cmd += ["-i", str(audio_path)]

    fc_parts.append(f"{''.join(v_tags)}concat=n={len(v_tags)}:v=1:a=0,fps={FPS},format=yuv420p[vout]")
    fc_parts.append(f"[{audio_idx}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,apad[aout]")

    cmd += [
        "-filter_complex", ";".join(fc_parts),
        "-map", "[vout]",
        "-map", "[aout]",
        "-t", f"{total_dur:.4f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_mp4


def detect_speech_pauses(ffmpeg_exe: str, audio_path: Path, noise_db: str = "-30dB", min_dur: float = 0.22) -> List[float]:
    """用 FFmpeg silencedetect 抓出真實語音的句間換氣停頓中點（秒），讓畫面永遠在講完該句才切換。"""
    cmd = [
        ffmpeg_exe, "-i", str(audio_path),
        "-af", f"silencedetect=noise={noise_db}:d={min_dur}",
        "-f", "null", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    starts: List[float] = []
    mids: List[float] = []
    for line in proc.stderr.splitlines():
        m1 = re.search(r"silence_start:\s*([0-9.]+)", line)
        if m1:
            starts.append(float(m1.group(1)))
        m2 = re.search(r"silence_end:\s*([0-9.]+)", line)
        if m2 and starts:
            s_t = starts.pop(0)
            e_t = float(m2.group(1))
            mids.append((s_t + e_t) / 2.0)
    return mids


def compute_speech_aligned_durations(
    ffmpeg_exe: str,
    audio_path: Path,
    total_dur: float,
    subtitles: List[str],
) -> List[float]:
    """
    依各字幕實際字數比例算出理論切點，再把每個切點精準吸附至最接近的真實語音停頓中點，
    確保 100% 唸完整段文字後才換畫面（絕不搶拍截斷語句）。
    """
    n = len(subtitles)
    if n <= 1:
        return [total_dur]

    pauses = detect_speech_pauses(ffmpeg_exe, audio_path)
    weights = [max(1, len(t)) for t in subtitles]
    tot_w = sum(weights)

    cuts: List[float] = [0.0]
    acc = 0
    for i in range(n - 1):
        acc += weights[i]
        target = total_dur * (acc / tot_w)
        # 在目標切點 ±4.5 秒範圍內尋找最接近的真實句間停頓（且必須大於前一個切點 + 2.0s）
        lo = max(cuts[-1] + 2.0, target - 4.5)
        hi = min(total_dur - 2.0 * (n - 1 - i), target + 4.5)
        cands = [p for p in pauses if lo <= p <= hi]
        if cands:
            best = min(cands, key=lambda p: abs(p - target))
            cuts.append(best)
        else:
            cuts.append(max(cuts[-1] + 2.0, min(hi, target)))
    cuts.append(total_dur)
    return [cuts[i + 1] - cuts[i] for i in range(n)]


def render_all_clips(shots: List[dict], audio_map: Dict[str, Path], ffmpeg_exe: str) -> List[Path]:
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    FLOW_CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    FLOW_FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    clip_paths: List[Path] = []
    for s in shots:
        sid = s["id"]
        audio_p = audio_map[sid]
        dur = probe_duration(ffmpeg_exe, audio_p) + 0.35
        out_mp4 = CLIPS_DIR / f"{sid}.mp4"
        fig_p = FIG_DIR / s["figure"]
        accent = PALETTE.get(s["theme"], PALETTE["cyan"])

        # 偵測本鏡頭可用的滿版 Flow 真人實片清單
        avail_flows: List[Path] = []
        for fn in s.get("flow_clips", []):
            p = FLOW_CLIPS_DIR / fn
            if p.exists() and p.stat().st_size > 50_000:
                avail_flows.append(p)

        # 統一先決定總段數與各段字幕，再用真實語音停頓點計算每段精準秒數（不再死鎖 10 秒導致提前換畫面！）
        post_count = len(s["focus_steps"]) if s["type"] == "form_spotlight" else 2
        total_segs = len(avail_flows) + post_count
        all_subs = split_subtitles(s["narration"], total_segs)
        seg_durs = compute_speech_aligned_durations(ffmpeg_exe, audio_p, dur, all_subs)

        segments: List[dict] = []

        # 1. 前段：滿版 Flow 真人實片（依該句實際唸完的真實停頓時間切換，絕不搶拍！）
        for idx, fp in enumerate(avail_flows):
            sd = seg_durs[idx]
            hud_p = _make_flow_hud_png(WORK_DIR / f"{sid}_hud{idx+1}.png", s["chapter"], all_subs[idx], accent)
            segments.append({"kind": "flow_full", "mp4": fp, "hud": hud_p, "dur": sd})

        # 2. 後段：表單聚光燈（支援 PiP 動態真人視窗）或 流程圖要點卡
        rem_subs = all_subs[len(avail_flows):]
        rem_durs = seg_durs[len(avail_flows):]

        if s["type"] == "form_spotlight":
            steps = s["focus_steps"]
            for idx, (st, sub_txt, seg_dur) in enumerate(zip(steps, rem_subs, rem_durs)):
                pip_name = st.get("pip_clip")
                pip_p = (FLOW_CLIPS_DIR / pip_name) if pip_name else None
                has_pip = bool(pip_p and pip_p.exists() and pip_p.stat().st_size > 50_000)
                img = build_spotlight_frame(
                    fig_path=fig_p,
                    chapter=s["chapter"],
                    form_badge=s["form_badge"],
                    theme_name=s["theme"],
                    step=st,
                    subtitle=sub_txt,
                    has_pip=has_pip,
                )
                img_out = WORK_DIR / f"{sid}_step{idx+1}.png"
                img.save(img_out)
                if has_pip:
                    segments.append({"kind": "still_pip", "img": img_out, "pip": pip_p, "dur": seg_dur})
                else:
                    segments.append({"kind": "still", "img": img_out, "dur": seg_dur})
        else:
            for idx, (sub_txt, seg_dur) in enumerate(zip(rem_subs, rem_durs)):
                img = build_flow_fallback_frame(
                    fig_path=fig_p,
                    chapter=s["chapter"],
                    form_badge=s["form_badge"],
                    theme_name=s["theme"],
                    card_title=s["card_title"],
                    card_points=s["card_points"],
                    subtitle=sub_txt,
                )
                img_out = WORK_DIR / f"{sid}_post{idx+1}.png"
                img.save(img_out)
                segments.append({"kind": "still", "img": img_out, "dur": seg_dur})

        n_flow = sum(1 for x in segments if x["kind"] == "flow_full")
        n_pip = sum(1 for x in segments if x["kind"] == "still_pip")
        dur_str = " / ".join(f"{d:.1f}s" for d in seg_durs)
        print(f"[Render] {sid} 語音停頓對齊 ({dur:.1f}s｜段長=[{dur_str}]｜滿版真人={n_flow}｜PiP={n_pip})")
        render_mixed_segments_clip(ffmpeg_exe, segments, audio_p, out_mp4)
        clip_paths.append(out_mp4)

    return clip_paths


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="第 1 部《儲槽進貨與卸料篇》SOP 電影教學影片生成器")
    parser.add_argument("--export-voice-jobs", action="store_true", help="僅匯出 Colab T4 配音工作單 (JSON)")
    parser.add_argument("--cinema", action="store_true", help="啟用完整電影後製（封面/封底 + xfade + BGM 閃避）")
    parser.add_argument("--speed", type=float, default=1.12, help="edge-tts 旁白倍速（預設 1.12）")
    parser.add_argument("--gemini-tts", action="store_true", help="改用 Gemini TTS 合成旁白")
    parser.add_argument("--audio-dir", type=str, default="", help="指定外部音檔目錄（如 audio_myvoice）")
    parser.add_argument("--out-video", type=str, default="", help="指定輸出影片路徑（避免覆蓋原版）")
    args = parser.parse_args()

    global AUDIO_DIR, FINAL_VIDEO_PATH
    if args.audio_dir:
        AUDIO_DIR = Path(args.audio_dir).resolve()
    if args.out_video:
        FINAL_VIDEO_PATH = Path(args.out_video).resolve()

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    shots = get_shots()

    if args.export_voice_jobs:
        voice_shots = [
            {
                "id": s["id"],
                "title": s["chapter"],
                "narration": normalize_industrial_tts(s.get("tts_override") or s["narration"]),
                "output_filename": f"{s['id']}.mp3",
            }
            for s in shots
        ]
        export_voice_jobs_json(
            shots=voice_shots,
            out_path=VOICE_JOBS_PATH,
            project_name="儲槽進出貨SOP_第1部_進貨與卸料篇",
            default_voice_design="一位專業沉穩、語氣親切的台灣化工廠資深工安講師，吐字清晰、節奏明快",
        )
        print(f"[VoiceJobs] 已匯出 Colab T4 配音工作單：{VOICE_JOBS_PATH}")
        return

    ffmpeg_exe = find_ffmpeg()
    print(f"[Init] FFmpeg: {ffmpeg_exe}")

    extract_pdf_figures()
    audio_map = synthesize_audio(shots, ffmpeg_exe, speed=args.speed, use_gemini=args.gemini_tts)
    clip_paths = render_all_clips(shots, audio_map, ffmpeg_exe)

    all_segments: List[Path] = []
    if args.cinema:
        cover_img = FLOW_FRAMES_DIR / "cover.png"
        end_img = FLOW_FRAMES_DIR / "ending.png"
        cover_mp4 = CLIPS_DIR / "00_cover.mp4"
        ending_mp4 = CLIPS_DIR / "99_ending.mp4"

        render_cover_clip(
            ffmpeg_exe=ffmpeg_exe,
            out_mp4=cover_mp4,
            title="儲槽進出貨作業方法｜第 1 部：進貨與卸料篇",
            subtitle="C50110-INV-02-01 (v3.1)｜附件 6.1 & 6.4 表單檢點實戰教學",
            cover_img=cover_img if cover_img.exists() else None,
            duration=3.0,
            fps=FPS,
        )
        render_ending_clip(
            ffmpeg_exe=ffmpeg_exe,
            out_mp4=ending_mp4,
            title="安全進貨・零混料・零洩漏",
            subtitle="請確認附件 6.1 / 6.4 完成三級簽核｜下一部：第 2 部 出貨與灌裝篇",
            end_img=end_img if end_img.exists() else None,
            duration=3.0,
            fps=FPS,
        )
        all_segments = [cover_mp4] + clip_paths + [ending_mp4]
    else:
        all_segments = clip_paths

    merged_no_bgm = WORK_DIR / "merged_no_bgm.mp4"
    print(f"[Concat] 正在使用 xfade 0.4s 柔順串接 {len(all_segments)} 段影片...")
    concat_with_xfade(ffmpeg_exe, all_segments, merged_no_bgm, fade_sec=0.4, fps=FPS)

    bgm_path = OUT_ROOT / "bgm.mp3"
    if args.cinema and bgm_path.exists():
        print(f"[BGM] 偵測到 {bgm_path.name}，套用語音閃避混音...")
        mix_bgm_with_ducking(ffmpeg_exe, merged_no_bgm, bgm_path, FINAL_VIDEO_PATH, bgm_vol=0.16)
    else:
        shutil.copy2(merged_no_bgm, FINAL_VIDEO_PATH)

    total_dur = probe_duration(ffmpeg_exe, FINAL_VIDEO_PATH)
    size_mb = FINAL_VIDEO_PATH.stat().st_size / (1024 * 1024)
    print(f"\n✅ 第 1 部成片完成：{FINAL_VIDEO_PATH}")
    print(f"   片長：{total_dur:.1f} 秒（{total_dur/60:.1f} 分鐘）｜大小：{size_mb:.1f} MB")


if __name__ == "__main__":
    main()
