"""
BPM 一般費用報銷單（私車公用）方案 C：全 Google Flow 6 鏡 3D 概念宣導動畫版建置器
===================================================================================
- 獨立輸出至 bpm_sop_plan_c/，不覆蓋方案 A (bpm_sop/)
- 自動複用方案 A 已生成的 3 支 Google Flow 實片 (c01 / c04 / c06)
- 自動生成新 3 鏡 (c02 / c03 / c05) 的 1280x720 首尾幀並存入 flow_frames/ 與 new_flow_frames/
- 使用 edge-tts 台灣真人女聲 (zh-TW-HsiaoChenNeural) 合成 6 段自然台灣口語旁白與 1080p 總片
"""

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent
_CINEMA_SCRIPTS = BASE_DIR.parent / ".agents" / "skills" / "sop-cinema-video" / "scripts"
if str(_CINEMA_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_CINEMA_SCRIPTS))

from cinema_post_engine import (
    concat_with_xfade,
    export_voice_jobs_json,
    mix_bgm_with_ducking,
    render_cinema_flow_clip,
    render_cover_clip,
    render_ending_clip,
    synthesize_gemini_tts,
)

from build_bpm_sop_video import (
    FLOW_H,
    FLOW_W,
    _edge_tts_save,
    _sapi5_fallback_save,
    draw_vertical_gradient,
    find_ffmpeg,
    get_font,
    get_media_duration,
    render_flow_clip_with_real_mp4,
    render_pipe_clip,
    resolve_edge_voice,
)

PLAN_A_ROOT = BASE_DIR / "bpm_sop"
OUT_ROOT = BASE_DIR / "bpm_sop_plan_c"
FLOW_FRAMES_DIR = OUT_ROOT / "flow_frames"
NEW_FLOW_FRAMES_DIR = OUT_ROOT / "new_flow_frames"
FLOW_CLIPS_DIR = OUT_ROOT / "flow_clips"
AUDIO_DIR = OUT_ROOT / "audio"
CLIPS_DIR = OUT_ROOT / "clips"
MANIFEST_PATH = OUT_ROOT / "storyboard_manifest_plan_c.json"
FINAL_VIDEO_PATH = OUT_ROOT / "BPM_一般費用報銷單_方案C_全Flow概念動畫總片.mp4"


SHOTS_C: List[dict] = [
    {
        "id": "c01",
        "index": 1,
        "title": "行前準備：核准出差單、實際里程截圖與 ETag 明細",
        "chapter": "概念鏡 01｜出差出發前先備齊三樣佐證",
        "engine": "flow",
        "flow_theme": "bpm_shot01",
        "reuse_from_plan_a": "shot01_flow.mp4",
        "flow_prompt": (
            "Clean modern corporate 3D animation, smooth camera tracking a silver sedan driving along a sunny "
            "Taiwan highway passing underneath a glowing blue eTag electronic toll gantry, transitioning smoothly "
            "to arriving cleanly at a modern steel material factory gate with a digital route map display, "
            "bright daylight, crisp professional explainer video style, 4k."
        ),
        "narration": (
            "歡迎收看 BPM 私車公用報銷快速導覽！開車出差報帳前，先備好三樣資料："
            "第一是本人核准的出差登記單，第二是用 Google 地圖截下當次實際去回程路線圖，"
            "看實際跑了多少公里就依實際里程計算，第三則是遠通 eTag 實際扣款明細。"
        ),
        "subtitle": "出差三寶：本人核准出差單 ＋ 個人實際去／回程路線截圖 ＋ ETag 實際扣款明細",
        "key_points": ["複用已生成 Flow 實片", "依個人實際里程計算", "備妥三樣佐證"],
    },
    {
        "id": "c02",
        "index": 2,
        "title": "進入 EPM 一般費用報銷單並選取本人出差單號",
        "chapter": "概念鏡 02｜開啟表單並帶入當次實際出差單",
        "engine": "flow",
        "flow_theme": "bpm_c02",
        "flow_prompt": (
            "Clean modern corporate 3D explainer animation, smooth zoom toward a glowing glass desktop monitor "
            "displaying a sleek blue BPM expense portal icon, then smoothly opening floating translucent trip selector "
            "cards where an animated cursor highlights and selects the employee's matching business trip record, "
            "crisp clean corporate tech aesthetic, soft studio lighting, 4k."
        ),
        "narration": (
            "接著進到鼎新 BPM，點開 EPM 裡面的『一般費用報銷單』，確認表頭的公司別、部門跟日期。"
            "然後到費用明細點選『出差登記單號』旁邊的查詢鈕，從清單裡選出你這趟實際出差的單號，"
            "讓系統自動帶入日期、地點跟出差事由，千萬別選錯張喔！"
        ),
        "subtitle": "進入 EPM 一般費用報銷單 → 點選查詢鈕，選取你這趟實際出差的單號",
        "key_points": ["EPM 一般費用報銷單", "選取本人當次出差單號", "核對日期與地點"],
    },
    {
        "id": "c03",
        "index": 3,
        "title": "雙軌分流鐵律：私車里程 A05 與 ETag 通行費 A07 分開列",
        "chapter": "概念鏡 03｜私車公用 (A05) 與 ETag (A07) 絕不合併",
        "engine": "flow",
        "flow_theme": "bpm_c03",
        "flow_prompt": (
            "Clean modern corporate 3D infographic animation, starting with a glowing mileage odometer and sedan icon "
            "flowing into a blue left track labeled A05, while a glowing highway eTag wave splits smoothly into a "
            "separate green right track labeled A07, emphasizing two distinct parallel glass cards floating cleanly "
            "side by side in a dark slate studio, crisp 4k."
        ),
        "narration": (
            "填費用明細時，最重要的原則就是『分開列示』！"
            "私車公用里程費選 A05，依你自己實際跑的公里數與公司核定單價計算登打，並備註實際車牌號碼；"
            "而高速公路的 eTag 通行費一定要另外新增一筆 A07，照遠通實際扣款金額填報，絕不能跟里程費混在一起。"
        ),
        "subtitle": "雙軌分流：A05 私車里程費（依實際公里與車號）vs A07 eTag（依實扣金額獨立列示）",
        "key_points": ["A05 私車公用依實際里程", "A07 eTag 依實扣獨立列", "說明務必填車號"],
    },
    {
        "id": "c04",
        "index": 4,
        "title": "非私車公用情境：高鐵 (A01) 與停車費 (A06)",
        "chapter": "概念鏡 04｜搭高鐵與停車費依實際票據獨立申報",
        "engine": "flow",
        "flow_theme": "bpm_shot05",
        "reuse_from_plan_a": "shot05_flow.mp4",
        "flow_prompt": (
            "Clean modern corporate 3D animation transition, starting at a bright high-speed rail station platform "
            "as a sleek streamlined bullet train arrives, smoothly gliding to a modern parking garage exit kiosk "
            "with a rising green barrier gate and glowing receipt card, bright professional explainer style, 4k."
        ),
        "narration": (
            "如果你這趟出差改搭高鐵，或是有產生額外的停車費，記得要選 A01 高鐵或 A06 停車費。"
            "而且畫面上的數字都只是範例，報銷時請一律依照手中車票、電子發票或停車收據上的實際金額與發票號碼來登打喔！"
        ),
        "subtitle": "一般交通費：高鐵選 A01、停車費選 A06，皆依實際票據金額與發票號碼登打",
        "key_points": ["複用已生成 Flow 實片", "A01 高鐵 / A06 停車費", "依實際票據勿照抄範例"],
    },
    {
        "id": "c05",
        "index": 5,
        "title": "總額對齊、附件上傳與「先儲存再送出」",
        "chapter": "概念鏡 05｜確認明細合計一致、附件可開、完成送簽",
        "engine": "flow",
        "flow_theme": "bpm_c05",
        "flow_prompt": (
            "Clean modern corporate 3D motion graphics animation, starting with floating invoice and map screenshot "
            "documents flying neatly into a glowing digital upload folder beside a balanced scale icon, smoothly "
            "transforming into three illuminated emerald milestone pills lighting up in sequence: Save, Submit, "
            "and Approved Ticket Badge, crisp dark tech studio, 4k."
        ),
        "narration": (
            "全部實際費用都新增完畢後，請先檢查所有明細加總是否等於表頭報銷總金額，"
            "再把出差單、路線截圖、eTag 與發票附件全部上傳，確認點得開。"
            "送簽前先按一次『儲存』確認沒有紅字提醒，再正式按下『送出』並留存 BPM 單號！"
        ),
        "subtitle": "明細合計＝表頭總額 → 上傳並檢查所有附件 → 先按儲存無誤再送出簽核",
        "key_points": ["合計＝表頭總額", "附件須可開啟", "先儲存再送出取單號"],
    },
    {
        "id": "c06",
        "index": 6,
        "title": "紙本正本繳交：申請人 → 人事核對 → 會計審核",
        "chapter": "概念鏡 06｜實體正本交件流程與最後審核",
        "engine": "flow",
        "flow_theme": "bpm_shot08",
        "reuse_from_plan_a": "shot08_flow.mp4",
        "flow_prompt": (
            "Clean modern corporate office animation, starting with an employee neatly organizing printed BPM expense "
            "forms and paper receipts on a desk, smoothly transitioning to a three-step glass workflow visualization "
            "showing Applicant handing originals to HR for verification stamp, then forwarding to Accounting for final "
            "approval, warm bright office lighting, crisp 4k."
        ),
        "narration": (
            "最後提醒，線上送簽完成不代表結束喔！請把申請單印出來，連同實際發生的發票、"
            "收據正本、路線截圖與計算資料一起交給人事單位核對；"
            "等人事確認正本與線上內容無誤後，才會正式轉交給會計審核與撥款。"
        ),
        "subtitle": "交件鐵律：申請人備妥實際憑證正本 → 交由人事核對無誤 → 人事轉交會計最後審核",
        "key_points": ["複用已生成 Flow 實片", "正本先交人事核對", "無誤再轉會計審核"],
    },
]


def sync_reused_assets_from_plan_a() -> Dict[str, Tuple[Path, Path]]:
    """從方案 A 複用已生成的 3 支 Flow 實片與對應首尾幀圖檔。"""
    FLOW_FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    NEW_FLOW_FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    FLOW_CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    pairs: Dict[str, Tuple[Path, Path]] = {}
    reuse_frames = [
        ("bpm_shot01", "bpm_c01"),
        ("bpm_shot05", "bpm_c04"),
        ("bpm_shot08", "bpm_c06"),
    ]
    for src_prefix, dst_prefix in reuse_frames:
        for suffix in ("first.png", "last.png"):
            src = PLAN_A_ROOT / "flow_frames" / f"{src_prefix}_{suffix}"
            dst = FLOW_FRAMES_DIR / f"{dst_prefix}_{suffix}"
            if src.exists():
                shutil.copy2(src, dst)
        pairs[src_prefix] = (
            FLOW_FRAMES_DIR / f"{dst_prefix}_first.png",
            FLOW_FRAMES_DIR / f"{dst_prefix}_last.png",
        )

    for shot in SHOTS_C:
        src_name = shot.get("reuse_from_plan_a")
        if src_name:
            src_mp4 = PLAN_A_ROOT / "flow_clips" / src_name
            dst_mp4 = FLOW_CLIPS_DIR / f"{shot['id']}_flow.mp4"
            if src_mp4.exists() and not dst_mp4.exists():
                shutil.copy2(src_mp4, dst_mp4)
                print(f"[複用] 已連結既有 Flow 實片：{src_name} -> {dst_mp4.name}")
    return pairs


def generate_new_plan_c_keyframes(pairs: Dict[str, Tuple[Path, Path]]) -> Dict[str, Tuple[Path, Path]]:
    """生成方案 C 新增 3 鏡 (C02 / C03 / C05) 之 1280x720 首尾幀圖檔。"""

    # 若已有高階 3D 擬真圖檔，優先保留
    p2_f = FLOW_FRAMES_DIR / "bpm_c02_first.png"
    p2_l = FLOW_FRAMES_DIR / "bpm_c02_last.png"
    p3_f = FLOW_FRAMES_DIR / "bpm_c03_first.png"
    p3_l = FLOW_FRAMES_DIR / "bpm_c03_last.png"
    p5_f = FLOW_FRAMES_DIR / "bpm_c05_first.png"
    p5_l = FLOW_FRAMES_DIR / "bpm_c05_last.png"

    if p2_f.exists() and p2_l.exists() and p3_f.exists() and p3_l.exists() and p5_f.exists() and p5_l.exists():
        pairs["bpm_c02"] = (p2_f, p2_l)
        pairs["bpm_c03"] = (p3_f, p3_l)
        pairs["bpm_c05"] = (p5_f, p5_l)
        print(f"[2/5] 方案 C 偵測到現有高階 3D 擬真首尾幀，保留使用: {FLOW_FRAMES_DIR}")
        return pairs

    def save_both(name: str, img: Image.Image) -> Path:
        p_all = FLOW_FRAMES_DIR / name
        p_new = NEW_FLOW_FRAMES_DIR / name
        img.save(p_all)
        img.save(p_new)
        return p_all

    # --- C02 First: BPM Portal -> EPM ---
    c2_f = Image.new("RGB", (FLOW_W, FLOW_H))
    draw_vertical_gradient(c2_f, (10, 22, 48), (24, 58, 108))
    d = ImageDraw.Draw(c2_f)
    d.rounded_rectangle([180, 95, 1100, 585], radius=24, fill=(15, 23, 42), outline=(56, 189, 248), width=5)
    d.rectangle([180, 95, 1100, 165], fill=(30, 58, 138))
    d.text((230, 112), "鼎新 BPM System｜EPM 表單入口", fill=(248, 250, 252), font=get_font(30, bold=True))
    d.rounded_rectangle([240, 215, 480, 520], radius=16, fill=(30, 41, 59), outline=(100, 116, 139), width=3)
    d.rounded_rectangle([265, 315, 455, 385], radius=10, fill=(14, 165, 233))
    d.text((322, 332), "EPM", fill=(255, 255, 255), font=get_font(34, bold=True))
    d.rounded_rectangle([540, 215, 1040, 520], radius=18, fill=(248, 250, 252), outline=(56, 189, 248), width=4)
    d.ellipse([720, 255, 860, 395], fill=(6, 182, 212))
    d.text((755, 305), "BPM", fill=(255, 255, 255), font=get_font(32, bold=True))
    d.text((645, 425), "一般費用報銷單", fill=(15, 23, 42), font=get_font(38, bold=True))
    p2_f = save_both("bpm_c02_first.png", c2_f)

    # --- C02 Last: Selecting Own Trip Record ---
    c2_l = Image.new("RGB", (FLOW_W, FLOW_H))
    draw_vertical_gradient(c2_l, (10, 22, 48), (15, 45, 82))
    d = ImageDraw.Draw(c2_l)
    d.rounded_rectangle([140, 100, 1140, 620], radius=24, fill=(15, 23, 42), outline=(16, 185, 129), width=4)
    d.rounded_rectangle([140, 100, 1140, 175], radius=18, fill=(14, 116, 144))
    d.text((200, 118), "出差登記單號選取器（選取你當次出差單）", fill=(255, 255, 255), font=get_font(32, bold=True))
    rows = [
        (215, True, "本人當次出差單｜依實際出差日期與地點帶入"),
        (345, False, "歷史出差紀錄 A｜核對姓名與行程勿選錯"),
        (475, False, "歷史出差紀錄 B｜核對出差事由與起訖時間"),
    ]
    for ry, active, txt in rows:
        bg = (16, 185, 129) if active else (30, 41, 59)
        fg = (10, 16, 30) if active else (203, 213, 225)
        border = (110, 231, 183) if active else (71, 85, 105)
        d.rounded_rectangle([200, ry, 1080, ry + 95], radius=14, fill=bg, outline=border, width=3)
        d.text((240, ry + 30), txt, fill=fg, font=get_font(28, bold=active))
    p2_l = save_both("bpm_c02_last.png", c2_l)
    pairs["bpm_c02"] = (p2_f, p2_l)

    # --- C03 First: Unified Flow Input (Car + Highway eTag) ---
    c3_f = Image.new("RGB", (FLOW_W, FLOW_H))
    draw_vertical_gradient(c3_f, (12, 20, 38), (28, 46, 78))
    d = ImageDraw.Draw(c3_f)
    d.rounded_rectangle([240, 115, 1040, 250], radius=22, fill=(30, 41, 59), outline=(56, 189, 248), width=4)
    d.text((335, 158), "私車公用出差費用明細分流", fill=(248, 250, 252), font=get_font(42, bold=True))
    # Split arrows
    d.line([(640, 250), (350, 380)], fill=(56, 189, 248), width=8)
    d.line([(640, 250), (930, 380)], fill=(16, 185, 129), width=8)
    d.rounded_rectangle([120, 380, 580, 610], radius=22, fill=(15, 23, 42), outline=(56, 189, 248), width=5)
    d.text((225, 425), "A05 私車公用", fill=(125, 211, 252), font=get_font(36, bold=True))
    d.text((190, 505), "個人實際行駛里程", fill=(241, 245, 249), font=get_font(28))
    d.rounded_rectangle([700, 380, 1160, 610], radius=22, fill=(15, 23, 42), outline=(16, 185, 129), width=5)
    d.text((810, 425), "A07 eTag", fill=(110, 231, 183), font=get_font(36, bold=True))
    d.text((775, 505), "實際扣款通行明細", fill=(241, 245, 249), font=get_font(28))
    p3_f = save_both("bpm_c03_first.png", c3_f)

    # --- C03 Last: Two Separate Cards Side by Side ---
    c3_l = Image.new("RGB", (FLOW_W, FLOW_H))
    draw_vertical_gradient(c3_l, (10, 18, 34), (20, 36, 62))
    d = ImageDraw.Draw(c3_l)
    d.rounded_rectangle([80, 130, 595, 590], radius=26, fill=(15, 23, 42), outline=(56, 189, 248), width=5)
    d.rounded_rectangle([115, 165, 560, 245], radius=14, fill=(14, 165, 233))
    d.text((195, 184), "A05 私車里程費", fill=(255, 255, 255), font=get_font(34, bold=True))
    d.text((135, 300), "• 依實際公里計算金額", fill=(241, 245, 249), font=get_font(28))
    d.text((135, 370), "• 說明欄註明車牌號碼", fill=(241, 245, 249), font=get_font(28))
    d.text((135, 440), "• 稅別依公司規定選取", fill=(241, 245, 249), font=get_font(28))

    d.rounded_rectangle([685, 130, 1200, 590], radius=26, fill=(15, 23, 42), outline=(16, 185, 129), width=5)
    d.rounded_rectangle([720, 165, 1165, 245], radius=14, fill=(16, 185, 129))
    d.text((805, 184), "A07 通行費 eTag", fill=(10, 16, 30), font=get_font(34, bold=True))
    d.text((740, 300), "• 必須與 A05 分開列", fill=(241, 245, 249), font=get_font(28))
    d.text((740, 370), "• 依遠通實扣金額填寫", fill=(241, 245, 249), font=get_font(28))
    d.text((740, 440), "• 嚴禁併入里程費申請", fill=(241, 245, 249), font=get_font(28))
    p3_l = save_both("bpm_c03_last.png", c3_l)
    pairs["bpm_c03"] = (p3_f, p3_l)

    # --- C05 First: Balance Totals & Attachment Folder ---
    c5_f = Image.new("RGB", (FLOW_W, FLOW_H))
    draw_vertical_gradient(c5_f, (12, 22, 42), (30, 48, 82))
    d = ImageDraw.Draw(c5_f)
    d.rounded_rectangle([120, 140, 620, 560], radius=24, fill=(15, 23, 42), outline=(56, 189, 248), width=4)
    d.text((185, 185), "明細合計 ＝ 表頭總額", fill=(125, 211, 252), font=get_font(34, bold=True))
    for idx, label in enumerate(["A05 私車實際里程", "A07 ETag 實際扣款", "A01/A06 票據實付"]):
        yy = 275 + idx * 80
        d.rounded_rectangle([165, yy, 575, yy + 56], radius=10, fill=(30, 41, 59))
        d.text((195, yy + 12), label, fill=(241, 245, 249), font=get_font(26))

    d.rounded_rectangle([680, 140, 1160, 560], radius=24, fill=(15, 23, 42), outline=(245, 158, 11), width=4)
    d.text((775, 185), "上傳完整佐證", fill=(252, 211, 77), font=get_font(34, bold=True))
    for idx, label in enumerate(["出差登記資料", "去／回程路線截圖", "ETag 與發票檔案"]):
        yy = 275 + idx * 80
        d.rounded_rectangle([725, yy, 1115, yy + 56], radius=10, fill=(30, 41, 59))
        d.text((760, yy + 12), label, fill=(241, 245, 249), font=get_font(26))
    p5_f = save_both("bpm_c05_first.png", c5_f)

    # --- C05 Last: Save -> Submit -> BPM Ticket ---
    c5_l = Image.new("RGB", (FLOW_W, FLOW_H))
    draw_vertical_gradient(c5_l, (10, 20, 38), (22, 46, 76))
    d = ImageDraw.Draw(c5_l)
    steps = [
        (110, (56, 189, 248), "1. 先按儲存", "確認無錯誤訊息"),
        (475, (16, 185, 129), "2. 正式送出", "發起簽核流程"),
        (840, (245, 158, 11), "3. 取得單號", "待辦區確認產生"),
    ]
    for idx, (sx, col, stitle, sdesc) in enumerate(steps):
        d.rounded_rectangle([sx, 205, sx + 325, 495], radius=24, fill=(15, 23, 42), outline=col, width=5)
        d.rounded_rectangle([sx + 28, 240, sx + 297, 320], radius=14, fill=col)
        d.text((sx + 68, 258), stitle, fill=(10, 16, 30), font=get_font(34, bold=True))
        d.text((sx + 56, 380), sdesc, fill=(248, 250, 252), font=get_font(28, bold=True))
        if idx < 2:
            ax = sx + 335
            d.polygon([(ax, 335), (ax + 18, 350), (ax, 365)], fill=(248, 250, 252))
    p5_l = save_both("bpm_c05_last.png", c5_l)
    pairs["bpm_c05"] = (p5_f, p5_l)

    print(f"[2/5] 已生成方案 C 新增 3 鏡首尾幀至 {FLOW_FRAMES_DIR} 與 {NEW_FLOW_FRAMES_DIR}")
    return pairs


def synthesize_plan_c_audio(
    ffmpeg_exe: str, rebuild_audio: bool, voice_profile: str, tts_engine: str = "edge"
) -> Dict[str, float]:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    durations: Dict[str, float] = {}
    for shot in SHOTS_C:
        sid = shot["id"]
        mp3_path = AUDIO_DIR / f"{sid}.mp3"
        if not rebuild_audio and mp3_path.exists() and mp3_path.stat().st_size > 1000:
            mode = "快取沿用"
        elif tts_engine == "gemini":
            used_model = synthesize_gemini_tts(shot["narration"], mp3_path, ffmpeg_exe)
            mode = f"gemini-tts:{used_model}"
        else:
            edge_voice = resolve_edge_voice(sid, voice_profile)
            try:
                asyncio.run(_edge_tts_save(shot["narration"], mp3_path, edge_voice))
                mode = f"edge-tts:{edge_voice}"
            except Exception as exc:
                print(f"[提示] {sid} edge-tts 失敗 ({exc})，改用本機 Windows 離線語音...")
                _sapi5_fallback_save(shot["narration"], mp3_path, ffmpeg_exe)
                mode = "SAPI5"
        dur = get_media_duration(ffmpeg_exe, mp3_path)
        durations[sid] = round(dur + 0.5, 2)
        print(f"      - {sid}.mp3 ({mode}): {dur:.2f}s -> 影片配長 {durations[sid]:.2f}s")
    print(f"[3/5] 方案 C 6 段台灣中文旁白配音完成！(engine={tts_engine})")
    return durations


def render_plan_c_all_and_concat(
    ffmpeg_exe: str,
    durations: Dict[str, float],
    flow_pairs: Dict[str, Tuple[Path, Path]],
    voice_profile: str,
    legacy_hud: bool = False,
    bgm_path: Optional[Path] = None,
):
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    concat_entries = []
    manifest_shots = []
    cinema_clips: List[Path] = []
    elapsed = 0.0
    total_shots = len(SHOTS_C)

    if not legacy_hud:
        cover_mp4 = CLIPS_DIR / "00_cover.mp4"
        render_cover_clip(
            ffmpeg_exe,
            cover_mp4,
            title="BPM 一般費用報銷單｜微電影概念篇",
            subtitle="私車公用出差報帳 6 步驟快速導覽",
            cover_img=FLOW_FRAMES_DIR / "cover.png",
            duration=3.0,
        )
        cinema_clips.append(cover_mp4)

    print(f"[4/5] 正在處理方案 C {total_shots} 段 1920x1080 (24fps) 概念動畫...")
    for shot in SHOTS_C:
        sid = shot["id"]
        dur = durations[sid]
        audio_path = AUDIO_DIR / f"{sid}.mp3"
        out_mp4 = CLIPS_DIR / f"{sid}.mp4"
        real_flow_mp4 = FLOW_CLIPS_DIR / f"{sid}_flow.mp4"

        used_real_flow = real_flow_mp4.exists()
        if used_real_flow:
            if legacy_hud:
                render_flow_clip_with_real_mp4(
                    ffmpeg_exe, shot, real_flow_mp4, audio_path, out_mp4, dur, total_shots=total_shots
                )
            else:
                render_cinema_flow_clip(
                    ffmpeg_exe,
                    real_flow_mp4,
                    audio_path,
                    out_mp4,
                    dur,
                    subtitle=shot["subtitle"],
                    chapter_badge=shot["chapter"],
                )
        else:
            pair = flow_pairs[shot["flow_theme"]]
            render_pipe_clip(ffmpeg_exe, shot, dur, audio_path, out_mp4, pair, total_shots=total_shots)

        actual_dur = get_media_duration(ffmpeg_exe, out_mp4)
        mode_tag = " [電影滿版 Flow 實片]" if (used_real_flow and not legacy_hud) else (" [已嵌入 Google Flow 實片]" if used_real_flow else " [首尾幀動態預覽]")
        print(f"      ✓ {out_mp4.name} ({actual_dur:.2f}s){mode_tag}")
        concat_entries.append(f"file '{out_mp4.as_posix()}'")
        cinema_clips.append(out_mp4)

        pair_f, pair_l = flow_pairs[shot["flow_theme"]]
        manifest_shots.append(
            {
                "id": sid,
                "index": shot["index"],
                "title": shot["title"],
                "chapter": shot["chapter"],
                "engine": "flow",
                "flow_theme": shot["flow_theme"],
                "flow_prompt": shot["flow_prompt"],
                "first_frame": f"./bpm_sop_plan_c/flow_frames/{pair_f.name}",
                "last_frame": f"./bpm_sop_plan_c/flow_frames/{pair_l.name}",
                "used_real_flow_mp4": used_real_flow,
                "expected_flow_drop_path": f"bpm_sop_plan_c/flow_clips/{sid}_flow.mp4",
                "figures": [],
                "narration": shot["narration"],
                "subtitle": shot["subtitle"],
                "key_points": shot["key_points"],
                "clip_url": f"./bpm_sop_plan_c/clips/{sid}.mp4",
                "audio_url": f"./bpm_sop_plan_c/audio/{sid}.mp3",
                "start_sec": round(elapsed, 2),
                "duration_sec": round(actual_dur, 2),
            }
        )
        elapsed += actual_dur

    concat_list = CLIPS_DIR / "concat_list.txt"
    concat_list.write_text("\n".join(concat_entries), encoding="utf-8")

    if legacy_hud:
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
                str(FINAL_VIDEO_PATH),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    else:
        ending_mp4 = CLIPS_DIR / "99_ending.mp4"
        render_ending_clip(
            ffmpeg_exe,
            ending_mp4,
            title="謝謝收看",
            subtitle="申請人備齊正本 → 人事核對 → 會計審核入帳",
            end_img=FLOW_FRAMES_DIR / "ending.png",
            duration=3.0,
        )
        cinema_clips.append(ending_mp4)
        resolved_bgm = bgm_path if (bgm_path and bgm_path.exists()) else (OUT_ROOT / "bgm.mp3")
        if resolved_bgm.exists():
            pre_bgm = CLIPS_DIR / "pre_bgm_xfade.mp4"
            concat_with_xfade(ffmpeg_exe, cinema_clips, pre_bgm, fade_sec=0.4)
            mix_bgm_with_ducking(ffmpeg_exe, pre_bgm, resolved_bgm, FINAL_VIDEO_PATH)
        else:
            concat_with_xfade(ffmpeg_exe, cinema_clips, FINAL_VIDEO_PATH, fade_sec=0.4)
        elapsed = get_media_duration(ffmpeg_exe, FINAL_VIDEO_PATH)

    real_count = sum(1 for s in manifest_shots if s["used_real_flow_mp4"])
    manifest = {
        "title": "BPM 一般費用報銷單（方案 C：全 Google Flow 6 鏡概念動畫版）",
        "source_docx": str(BASE_DIR.parent / "BPM一般費用報銷單_私車公用操作流程.docx"),
        "final_video_url": "./bpm_sop_plan_c/BPM_一般費用報銷單_方案C_全Flow概念動畫總片.mp4",
        "total_duration_sec": round(elapsed, 2),
        "flow_cost_credits": 180,
        "real_flow_count": real_count,
        "voice_profile": voice_profile,
        "shots": manifest_shots,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[5/5] 方案 C 總片合成完成！({elapsed:.2f}s, 已嵌入 {real_count}/6 支 Flow 實片) -> {FINAL_VIDEO_PATH}")


def main():
    parser = argparse.ArgumentParser(description="BPM 一般費用報銷單 方案 C (全 Flow 6 鏡概念動畫版)")
    parser.add_argument("--rebuild-audio", action="store_true", help="強制重新合成所有語音 MP3")
    parser.add_argument(
        "--voice",
        choices=["hsiaochen", "yunjhe", "hsiaoyu", "duet"],
        default="hsiaochen",
        help="台灣語音音色",
    )
    parser.add_argument("--export-voice-jobs", action="store_true", help="匯出 bpm_plan_c_voice_jobs.json 供 Colab T4 配音")
    parser.add_argument("--legacy-hud", action="store_true", help="沿用舊版上下簡報邊框與硬切合成")
    parser.add_argument("--bgm", default="", help="無人聲背景音樂 BGM 檔案路徑")
    parser.add_argument("--tts", choices=["edge", "gemini"], default="edge", help="語音合成引擎")
    args = parser.parse_args()

    if args.export_voice_jobs:
        jobs_out = OUT_ROOT / "bpm_plan_c_voice_jobs.json"
        export_voice_jobs_json(SHOTS_C, jobs_out, project_name="BPM_方案C_全Flow概念版")
        print(f"[匯出完成] Colab T4 配音工作單已輸出：{jobs_out}")
        if not args.rebuild_audio and not args.bgm:
            return

    ffmpeg_exe = find_ffmpeg()
    print(f"使用 FFmpeg: {ffmpeg_exe}")
    pairs = sync_reused_assets_from_plan_a()
    pairs = generate_new_plan_c_keyframes(pairs)
    durations = synthesize_plan_c_audio(
        ffmpeg_exe, rebuild_audio=args.rebuild_audio, voice_profile=args.voice, tts_engine=args.tts
    )
    bgm_arg = Path(args.bgm) if args.bgm else None
    render_plan_c_all_and_concat(
        ffmpeg_exe,
        durations,
        pairs,
        voice_profile=args.voice,
        legacy_hud=args.legacy_hud,
        bgm_path=bgm_arg,
    )


if __name__ == "__main__":
    main()
