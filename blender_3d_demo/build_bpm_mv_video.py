"""
BPM 一般費用報銷單（私車公用）AI MV 級 34 鏡微鏡頭流水線建置器
===============================================================
借鏡《已讀不懂》AI MV 製作流水線：
1. 精準卡點音訊：34 段獨立台灣口語旁白 + 去頭尾靜音 (zero dead air) + 微音效 (whoosh/click/stamp/chime)
2. 34 鏡微鏡頭分鏡：每鏡 2.5~5 秒，遠景/中景/特寫/POV/UI聚焦快速交替，徹底告別 30 秒靜態簡報感
3. Banana 3D 高擬真首幀 + 實務截圖局部推近 (Lanczos + UnsharpMask) 雙軌混剪
4. 支援單鏡替換真 AI 影片：將 Google Flow / MiniMax H3 產出之 MP4 放入 bpm_sop_mv/flow_clips/mXX_flow.mp4 即可自動無縫嵌合
5. 自動輸出中英文對照分鏡表 (BPM_MV_34鏡中英文分鏡腳本.md) 與 mv_manifest.json
"""

import argparse
import asyncio
import json
import math
import shutil
import struct
import subprocess
import wave
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter

from build_bpm_sop_video import (
    FIG_DIR,
    _edge_tts_save,
    _sapi5_fallback_save,
    find_ffmpeg,
    get_font,
    get_media_duration,
)

BASE_DIR = Path(__file__).resolve().parent
PLAN_A_FLOW_DIR = BASE_DIR / "bpm_sop" / "flow_frames"
PLAN_C_FLOW_DIR = BASE_DIR / "bpm_sop_plan_c" / "flow_frames"

OUT_ROOT = BASE_DIR / "bpm_sop_mv"
KEYFRAMES_DIR = OUT_ROOT / "keyframes"
FLOW_CLIPS_DIR = OUT_ROOT / "flow_clips"
AUDIO_DIR = OUT_ROOT / "audio"
SFX_DIR = OUT_ROOT / "sfx"
CLIPS_DIR = OUT_ROOT / "clips"
MANIFEST_PATH = OUT_ROOT / "mv_manifest.json"
SCRIPT_MD_PATH = OUT_ROOT / "BPM_MV_34鏡中英文分鏡腳本.md"
FINAL_VIDEO_PATH = OUT_ROOT / "BPM_一般費用報銷單_MV節奏34鏡版.mp4"
ROOT_COPY_PATH = BASE_DIR.parent / "BPM_一般費用報銷單_MV節奏34鏡版.mp4"

VIDEO_W, VIDEO_H = 1920, 1080
FPS = 24


# ==============================================================================
# 34 微鏡頭腳本定義 (每鏡 2.5 ~ 5 秒，高節奏景別交替)
# ==============================================================================
SHOTS_MV: List[dict] = [
    # --- 第一篇：行前準備與佐證三寶 (m01 - m06) ---
    {
        "id": "m01", "act": "第一篇｜行前佐證三寶", "shot_type": "遠景・跟拍",
        "source_type": "ai_scene", "keyframe": "m01_highway.png", "motion": "dolly_in", "sfx": "whoosh",
        "narration": "私車公用報銷，出差前先備齊三樣佐證。",
        "subtitle": "私車公用報銷｜出發前先備齊 3 樣關鍵佐證",
        "badge": "PART 1｜行前佐證",
        "flow_prompt_en": "Photorealistic commercial film, smooth low-angle tracking shot following a sleek metallic silver sedan cruising along a sunlit Taiwan multi-lane highway, green mountains in background, natural daylight, 35mm cinema lens, 4K, 3 seconds, steady fluid motion, no text.",
    },
    {
        "id": "m02", "act": "第一篇｜行前佐證三寶", "shot_type": "特寫・門架",
        "source_type": "ai_scene", "keyframe": "m01_highway.png", "motion": "pan_right", "sfx": "chime",
        "crop_focus": [0.15, 0.05, 0.85, 0.72],
        "narration": "高速公路通行紀錄，決定你的過路費憑證。",
        "subtitle": "高速公路 eTag 通行紀錄＝過路費報銷依據",
        "badge": "eTag 門架感應",
        "flow_prompt_en": "Dynamic low-angle upward tracking shot as a silver sedan passes underneath a modern steel overhead ETC electronic toll gantry on a sunny highway, subtle blue sensor glow, crisp asphalt motion blur, 35mm cinema lens, 4K, 3 seconds.",
    },
    {
        "id": "m03", "act": "第一篇｜行前佐證三寶", "shot_type": "中景・抵達",
        "source_type": "ai_scene", "keyframe": "m03_plant_gate.png", "motion": "dolly_in", "sfx": "whoosh",
        "narration": "第一，確認本人出差登記單已經核准。",
        "subtitle": "佐證 1｜本人已核准之「出差登記單」",
        "badge": "1/3 出差登記單",
        "flow_prompt_en": "Photorealistic corporate film, smooth dolly-in as a silver executive sedan arrives at a modern chemical manufacturing plant entrance gate, glass guardhouse, red-and-white boom barrier arm rising smoothly in bright daylight, 4K, 3 seconds.",
    },
    {
        "id": "m04", "act": "第一篇｜行前佐證三寶", "shot_type": "UI聚焦・去回程",
        "source_type": "ui_dual", "figs": ["fig07_route_go.jpg", "fig08_route_back.jpg"],
        "labels": ["去程路線（住址已打碼）", "回程路線（住址已打碼）"],
        "motion": "dolly_in", "sfx": "click",
        "narration": "第二，用 Google 地圖截下當次實際去回程路線。",
        "subtitle": "佐證 2｜Google 地圖去／回程實際路線截圖（個資可遮蔽）",
        "badge": "2/3 實際里程截圖",
        "flow_prompt_en": "POV close-up inside a modern car interior, a hand holding a smartphone displaying a clean GPS navigation route map from start to destination, finger tapping to capture screenshot, warm natural window light, 4K, 3 seconds.",
    },
    {
        "id": "m05", "act": "第一篇｜行前佐證三寶", "shot_type": "UI特寫・里程",
        "source_type": "ui_macro", "fig": "fig07_route_go.jpg",
        "focus_box": [0.02, 0.62, 0.98, 0.96], "callout": "依個人實際行駛公里數計算",
        "motion": "zoom_focus", "sfx": "chime",
        "narration": "跑幾公里就按個人實際里程與公司單價計算。",
        "subtitle": "里程原則｜依個人實際公里數 × 公司核定單價計算",
        "badge": "實距計算",
        "flow_prompt_en": "Macro close-up pushing smoothly toward a glowing smartphone map screen highlighting total driving distance kilometers on a route summary bar, crisp shallow depth of field, corporate explainer style, 4K, 3 seconds.",
    },
    {
        "id": "m06", "act": "第一篇｜行前佐證三寶", "shot_type": "UI特寫・專用章",
        "source_type": "ui_macro", "fig": "fig06_etag_official_pdf.png",
        "focus_box": [0.02, 0.02, 0.98, 0.98], "callout": "須下載官方 PDF（含遠通電收專用章）",
        "motion": "zoom_focus", "sfx": "stamp",
        "narration": "第三，下載含遠通專用章的 eTag 官方扣款明細，不能只截線上畫面。",
        "subtitle": "佐證 3｜遠通官方 PDF 明細（須含「遠通電收電子憑證專用章」）",
        "badge": "3/3 官方 eTag 專用章",
        "flow_prompt_en": "Macro top-down camera push-in on an official printed highway electronic toll statement paper resting on a desk, focusing sharply on a crisp official circular stamp at the bottom corner, warm office daylight, 4K, 3 seconds.",
    },

    # --- 第二篇：登入系統與選取本人出差單 (m07 - m12) ---
    {
        "id": "m07", "act": "第二篇｜進入系統選單號", "shot_type": "中景・工作站",
        "source_type": "ai_scene", "keyframe": "m07_office_laptop.png", "motion": "dolly_in", "sfx": "whoosh",
        "narration": "回到座位，打開電腦進入鼎新 BPM 系統。",
        "subtitle": "PART 2｜回到座位開啟鼎新 BPM 系統",
        "badge": "PART 2｜進入 BPM",
        "flow_prompt_en": "Medium cinematic shot in a sunlit modern Taiwan corporate office, a young office worker in smart casual attire sits smoothly at a walnut desk and opens a sleek silver laptop, natural window light, 35mm lens, 4K, 3 seconds.",
    },
    {
        "id": "m08", "act": "第二篇｜進入系統選單號", "shot_type": "特寫・系統入口",
        "source_type": "ai_scene", "keyframe": "m08_bpm_portal.png", "motion": "dolly_in", "sfx": "click",
        "narration": "點擊左側選單的 EPM，開啟一般費用報銷單。",
        "subtitle": "路徑｜鼎新 BPM ➔ EPM ➔ 一般費用報銷單",
        "badge": "EPM 表單入口",
        "flow_prompt_en": "Smooth slow dolly-in toward an ultrawide curved monitor on an executive desk, soft ambient blue office lighting, clean enterprise portal UI glowing softly as a cursor glides to click a blue menu card, 4K, 3 seconds.",
    },
    {
        "id": "m09", "act": "第二篇｜進入系統選單號", "shot_type": "UI特寫・EPM",
        "source_type": "ui_macro", "fig": "fig01_entry_epm.png",
        "focus_box": [0.05, 0.05, 0.95, 0.92], "callout": "點選「一般費用報銷單」開啟新單",
        "motion": "zoom_focus", "sfx": "click",
        "narration": "進表單後先核對表頭的公司別、部門跟申請日期。",
        "subtitle": "步驟 1｜確認表頭公司別、申請部門與日期無誤",
        "badge": "表頭核對",
        "flow_prompt_en": "Over-the-shoulder close-up of a crisp office monitor displaying a modern enterprise expense portal as a mouse cursor clicks the General Expense Claim button, soft depth of field, 4K, 3 seconds.",
    },
    {
        "id": "m10", "act": "第二篇｜進入系統選單號", "shot_type": "UI特寫・查詢鈕",
        "source_type": "ui_macro", "fig": "fig02_trip_selector.jpg",
        "focus_box": [0.02, 0.02, 0.98, 0.45], "callout": "點選「出差登記單號」放大鏡查詢",
        "motion": "zoom_focus", "sfx": "click",
        "narration": "接著在費用明細點選「出差登記單號」旁的查詢鈕。",
        "subtitle": "步驟 2｜點擊「出差登記單號」旁放大鏡查詢鈕",
        "badge": "查詢出差單",
        "flow_prompt_en": "Macro close-up of a hand moving an ergonomic mouse and clicking cleanly, monitor glow reflecting softly on the walnut desk surface, crisp 35mm commercial film, 4K, 3 seconds.",
    },
    {
        "id": "m11", "act": "第二篇｜進入系統選單號", "shot_type": "UI特寫・清單勾選",
        "source_type": "ui_macro", "fig": "fig02_trip_selector.jpg",
        "focus_box": [0.08, 0.25, 0.92, 0.88], "callout": "務必選取「本人當次」實際出差單號",
        "motion": "zoom_focus", "sfx": "chime",
        "narration": "從清單選出你這趟實際出差的單號，千萬別選錯張。",
        "subtitle": "步驟 3｜精準勾選「本人當次」出差單號（勿誤選他筆）",
        "badge": "勾選當次單號",
        "flow_prompt_en": "Close-up cinematic screen view as a clean translucent modal list appears and highlights a verified business trip row with a soft emerald checkmark glow, steady push-in, 4K, 3 seconds.",
    },
    {
        "id": "m12", "act": "第二篇｜進入系統選單號", "shot_type": "UI特寫・憑證日期",
        "source_type": "ui_macro", "fig": "fig03_a05_mileage.jpg",
        "focus_box": [0.35, 0.02, 0.96, 0.30], "callout": "⚠️ 憑證日期務必改為「實際出差日期」",
        "motion": "zoom_focus", "sfx": "stamp",
        "narration": "特別注意右上角的憑證日期，一定要改成實際出差日。",
        "subtitle": "會計重點｜右上角「憑證日期」務必修改為實際出差日！",
        "badge": "⚠️ 必改憑證日期",
        "flow_prompt_en": "Sharp macro focus rack on a sleek computer monitor corner showing a date picker field updating smoothly with a warm golden highlight ring, clean corporate aesthetic, 4K, 3 seconds.",
    },

    # --- 第三篇：雙軌分流核心登打 (m13 - m19) ---
    {
        "id": "m13", "act": "第三篇｜雙軌分流登打", "shot_type": "3D全息・分流",
        "source_type": "ai_scene", "keyframe": "m13_dual_track.png", "motion": "dolly_in", "sfx": "whoosh",
        "narration": "登打明細的核心鐵律，就是私車里程跟過路費「分開列示」。",
        "subtitle": "PART 3 核心鐵律｜A05 私車里程 與 A07 eTag 絕不合併！",
        "badge": "PART 3｜雙軌分流",
        "flow_prompt_en": "High-end 3D corporate motion graphics in a sleek dark boardroom, slow smooth orbital camera around a holographic glass visualization splitting into a glowing cyan left track and an emerald green right track, Apple keynote style, 4K, 3 seconds.",
    },
    {
        "id": "m14", "act": "第三篇｜雙軌分流登打", "shot_type": "UI特寫・選A05",
        "source_type": "ui_macro", "fig": "fig03_a05_mileage.jpg",
        "focus_box": [0.02, 0.14, 0.96, 0.44], "callout": "第一筆選 A05 國內出差-交通-私車公用",
        "motion": "zoom_focus", "sfx": "click",
        "narration": "第一筆費用類別選 A05 私車公用，稅別碼為免稅。",
        "subtitle": "第一筆明細｜選取「A05 私車公用」（稅別碼：T05 免稅）",
        "badge": "A05 私車公用",
        "flow_prompt_en": "Clean close-up on a dark-framed desktop monitor as a sleek dropdown menu opens and selects a blue highlighted category option smoothly, modern office lighting, 4K, 3 seconds.",
    },
    {
        "id": "m15", "act": "第三篇｜雙軌分流登打", "shot_type": "特寫・敲鍵盤",
        "source_type": "ai_scene", "keyframe": "m15_keyboard_typing.png", "motion": "pan_right", "sfx": "click",
        "narration": "輸入你依實際公里數算出的報銷金額。",
        "subtitle": "金額登打｜輸入依個人實際里程算出的報銷金額",
        "badge": "輸入實際金額",
        "flow_prompt_en": "Dramatic macro close-up of fingers typing briskly on the numeric keypad of a sleek modern office keyboard, warm desk lamp glow, blurred monitor light in background, shallow depth of field, 35mm lens, 4K, 3 seconds.",
    },
    {
        "id": "m16", "act": "第三篇｜雙軌分流登打", "shot_type": "UI特寫・車號備註",
        "source_type": "ui_macro", "fig": "fig03_a05_mileage.jpg",
        "focus_box": [0.42, 0.65, 0.96, 0.96], "callout": "費用說明務必填寫「實際車牌號碼」",
        "motion": "zoom_focus", "sfx": "chime",
        "narration": "右下角費用說明，務必填上你實際駕駛的車牌號碼。",
        "subtitle": "必填欄位｜費用說明欄務必備註「實際車牌號碼」",
        "badge": "備註車牌號碼",
        "flow_prompt_en": "Close-up tracking pan across a clean digital form notes field as crisp characters appear swiftly, soft amber highlight glow along the border, 4K, 3 seconds.",
    },
    {
        "id": "m17", "act": "第三篇｜雙軌分流登打", "shot_type": "UI特寫・新增列",
        "source_type": "ui_macro", "fig": "fig04_a05_list_check.jpg",
        "focus_box": [0.02, 0.45, 0.98, 0.96], "callout": "A05 完成後，點擊新增第二筆明細",
        "motion": "zoom_focus", "sfx": "click",
        "narration": "A05 存好後，另外新增第二筆明細報過路費。",
        "subtitle": "新增第二筆｜A05 確認入列後，再新增獨立一筆過路費",
        "badge": "＋新增明細列",
        "flow_prompt_en": "Clean macro UI shot of a bright blue plus button being clicked on a crisp enterprise web table, triggering a smooth new row expansion animation, 4K, 3 seconds.",
    },
    {
        "id": "m18", "act": "第三篇｜雙軌分流登打", "shot_type": "UI特寫・選A07",
        "source_type": "ui_macro", "fig": "fig05_a07_etag.jpg",
        "focus_box": [0.02, 0.14, 0.96, 0.44], "callout": "第二筆選 A07 高速公路通行費 (eTag)",
        "motion": "zoom_focus", "sfx": "click",
        "narration": "第二筆類別選 A07 高速公路通行費。",
        "subtitle": "第二筆明細｜選取「A07 高速公路通行費 (eTag)」",
        "badge": "A07 eTag 通行費",
        "flow_prompt_en": "Smooth macro zoom onto a sleek emerald green tag badge pulsing gently on a clean corporate dashboard screen, crisp 4K lighting, 3 seconds.",
    },
    {
        "id": "m19", "act": "第三篇｜雙軌分流登打", "shot_type": "UI特寫・實扣金額",
        "source_type": "ui_macro", "fig": "fig05_a07_etag.jpg",
        "focus_box": [0.02, 0.35, 0.96, 0.72], "callout": "依遠通 PDF 實際扣款登打（絕不與 A05 合併）",
        "motion": "zoom_focus", "sfx": "stamp",
        "narration": "照遠通官方明細的實際扣款金額填報，絕不跟里程混算。",
        "subtitle": "分列鐵律｜依遠通官方 PDF 實扣金額獨立填報",
        "badge": "絕不合併里程",
        "flow_prompt_en": "Close-up of two neatly separated glowing glass cards floating side by side in a dark studio, cyan on left and emerald on right, gently pulsing to emphasize separation, 4K, 3 seconds.",
    },

    # --- 第四篇：高鐵 A01 與停車費 A06 提醒 (m20 - m24) ---
    {
        "id": "m20", "act": "第四篇｜高鐵與停車費", "shot_type": "中景・高鐵進站",
        "source_type": "ai_scene", "keyframe": "m20_hsr_train.png", "motion": "pan_left", "sfx": "whoosh",
        "narration": "如果出差改搭高鐵，費用類別請選 A01。",
        "subtitle": "PART 4 其他交通｜搭高鐵選「A01 高鐵車資」",
        "badge": "A01 高鐵車資",
        "flow_prompt_en": "Photorealistic commercial shot, warm morning sunlight streaming through a modern glass-canopy high-speed rail platform as a sleek white-and-orange bullet train glides smoothly into the station, horizontal tracking pan, 35mm lens, 4K, 3 seconds.",
    },
    {
        "id": "m21", "act": "第四篇｜高鐵與停車費", "shot_type": "UI特寫・13碼票號",
        "source_type": "ui_macro", "fig": "fig10_a01_hsr.png",
        "focus_box": [0.02, 0.04, 0.98, 0.96], "callout": "高鐵填「13 碼票號」＋ T02 內含 5% 含稅總額",
        "motion": "zoom_focus", "sfx": "chime",
        "narration": "高鐵發票號碼填票面 13 碼票號，稅別 T02 登打含稅總額。",
        "subtitle": "高鐵重點｜發票號碼填「13 碼票號」｜T02 填含稅總金額",
        "badge": "13 碼票號 / T02",
        "flow_prompt_en": "Macro close-up of a crisp high-speed rail ticket held in hand under bright daylight, shallow depth of field focusing sharply on the printed ticket number strip, 4K, 3 seconds.",
    },
    {
        "id": "m22", "act": "第四篇｜高鐵與停車費", "shot_type": "中景・停車場",
        "source_type": "ai_scene", "keyframe": "m22_parking.png", "motion": "dolly_in", "sfx": "whoosh",
        "narration": "若有產生額外停車費，則選 A06 停車費。",
        "subtitle": "停車費用｜類別選「A06 停車費」",
        "badge": "A06 停車費",
        "flow_prompt_en": "Photorealistic commercial shot of a modern underground smart parking exit lane with linear LED ceiling lights, a sleek automated payment kiosk glowing green as a receipt slides out and the LED barrier arm rises smoothly, 4K, 3 seconds.",
    },
    {
        "id": "m23", "act": "第四篇｜高鐵與停車費", "shot_type": "UI特寫・未稅含稅",
        "source_type": "ui_macro", "fig": "fig11_a06_parking.png",
        "focus_box": [0.02, 0.04, 0.98, 0.96], "callout": "T01 外加 5% 填「未稅額」｜T02 內含 5% 填「含稅額」",
        "motion": "zoom_focus", "sfx": "stamp",
        "narration": "有發票時看清稅別：T01 填未稅金額，T02 填含稅總額。",
        "subtitle": "稅別鐵律｜T01（外加5%）填未稅額 ｜ T02（內含5%）填含稅總額",
        "badge": "T01 未稅 / T02 含稅",
        "flow_prompt_en": "Macro shot of a printed official receipt paper on an executive desk, a metallic pen pointing gently at the subtotal and tax lines, crisp warm lighting, 4K, 3 seconds.",
    },
    {
        "id": "m24", "act": "第四篇｜高鐵與停車費", "shot_type": "UI特寫・實報實銷",
        "source_type": "ui_macro", "fig": "fig09_multi_list.jpg",
        "focus_box": [0.02, 0.05, 0.98, 0.95], "callout": "畫面數字皆為範例，一律依手中實際憑證登打！",
        "motion": "dolly_out", "sfx": "chime",
        "narration": "畫面數字只是範例，一律依手中實際票據金額登打。",
        "subtitle": "實報實銷｜畫面皆為範例，請依手中實際發票與里程登打",
        "badge": "勿照抄範例",
        "flow_prompt_en": "Slow smooth pull-back over a neat corporate desk showing multiple neatly aligned travel receipts and a tablet calculator displaying verified totals, clean office daylight, 4K, 3 seconds.",
    },

    # --- 第五篇：防呆檢查、附件上傳與送出 (m25 - m30) ---
    {
        "id": "m25", "act": "第五篇｜防呆檢查送簽", "shot_type": "3D特寫・保險庫",
        "source_type": "ai_scene", "keyframe": "m25_vault_dashboard.png", "motion": "pan_left", "sfx": "whoosh",
        "crop_focus": [0.0, 0.05, 0.58, 0.95],
        "narration": "所有明細加總，務必等於表頭報銷總金額。",
        "subtitle": "PART 5 防呆 1｜確認「明細合計 ＝ 表頭總金額」完全一致",
        "badge": "合計＝表頭總額",
        "flow_prompt_en": "High-end 3D corporate CGI close-up of glowing document cards gliding smoothly into a brushed-steel digital vault with a soft blue confirmation light pulse, dark glass boardroom table, 4K, 3 seconds.",
    },
    {
        "id": "m26", "act": "第五篇｜防呆檢查送簽", "shot_type": "UI特寫・總額檢核",
        "source_type": "ui_macro", "fig": "fig09_multi_list.jpg",
        "focus_box": [0.02, 0.40, 0.98, 0.98], "callout": "逐筆核對金額、憑證日期與發票號碼",
        "motion": "zoom_focus", "sfx": "click",
        "narration": "接著把出差單、路線截圖、eTag 與發票全部上傳附件。",
        "subtitle": "防呆 2｜完整上傳出差單、去回程路線圖、eTag PDF 與發票",
        "badge": "上傳完整佐證",
        "flow_prompt_en": "Close-up of a computer screen as three clean PDF and image icons drag and drop smoothly into a glowing digital upload dropzone, progress bars hitting 100 percent green, 4K, 3 seconds.",
    },
    {
        "id": "m27", "act": "第五篇｜防呆檢查送簽", "shot_type": "UI特寫・開檔檢查",
        "source_type": "ui_macro", "fig": "fig06_etag_official_pdf.png",
        "focus_box": [0.08, 0.12, 0.92, 0.88], "callout": "上傳後務必「親自點開」確認檔案清晰可讀",
        "motion": "dolly_out", "sfx": "click",
        "narration": "上傳後記得親自點開檢查，確認每份附件都清晰可讀。",
        "subtitle": "防呆 3｜上傳後務必「點開預覽」確認無破圖、印章清晰",
        "badge": "點開確認無誤",
        "flow_prompt_en": "Over-the-shoulder close-up of an office worker reviewing a crisp PDF document preview on a bright monitor, nodding subtly in confirmation, soft natural daylight, 4K, 3 seconds.",
    },
    {
        "id": "m28", "act": "第五篇｜防呆檢查送簽", "shot_type": "3D特寫・先儲存",
        "source_type": "ai_scene", "keyframe": "m25_vault_dashboard.png", "motion": "zoom_focus", "sfx": "click",
        "crop_focus": [0.42, 0.10, 0.98, 0.90],
        "narration": "送簽前，先按一次「儲存」，確認沒有紅字提醒。",
        "subtitle": "防呆 4｜送出前「先按儲存」，確認無任何紅字欄位漏填",
        "badge": "1. 先按儲存",
        "flow_prompt_en": "Macro 3D CGI shot of a sleek metallic blue Save Draft pill badge illuminating brightly with a gentle specular light sweep over a glass table, shallow depth of field, 4K, 3 seconds.",
    },
    {
        "id": "m29", "act": "第五篇｜防呆檢查送簽", "shot_type": "3D特寫・按送出",
        "source_type": "ai_scene", "keyframe": "m25_vault_dashboard.png", "motion": "pan_right", "sfx": "chime",
        "crop_focus": [0.45, 0.12, 1.0, 0.88],
        "narration": "確認無誤後，再正式按下「送出」發起簽核。",
        "subtitle": "步驟 5｜無錯誤提示後，正式按下「送出」發起線上簽核",
        "badge": "2. 正式送出",
        "flow_prompt_en": "Macro 3D CGI shot of an emerald green Submit pill badge lighting up sequentially next to a blue Save badge, emitting a crisp clean light ripple, 4K, 3 seconds.",
    },
    {
        "id": "m30", "act": "第五篇｜防呆檢查送簽", "shot_type": "特寫・取得單號",
        "source_type": "ai_scene", "keyframe": "m30_desk_approved.png", "motion": "dolly_in", "sfx": "chime",
        "crop_focus": [0.50, 0.12, 0.98, 0.88],
        "narration": "並到待辦區確認已成功產生正式 BPM 單號。",
        "subtitle": "步驟 6｜至待辦區確認已產生正式 BPM 單號才算送出成功",
        "badge": "3. 確認單號",
        "flow_prompt_en": "Close-up of a sleek modern smartphone resting on a sunlit walnut office desk, screen illuminating with a crisp green checkmark Approved notification glow, warm morning light, 4K, 3 seconds.",
    },

    # --- 第六篇：實體紙本整理與三階段交件 (m31 - m34) ---
    {
        "id": "m31", "act": "第六篇｜實體正本交件", "shot_type": "中景・列印正本",
        "source_type": "ai_scene", "keyframe": "m31_laser_printer.png", "motion": "dolly_in", "sfx": "whoosh",
        "narration": "線上送完還沒結束！請把報銷申請單列印出來。",
        "subtitle": "PART 6 實體交件｜線上送出後，請列印 BPM 報銷申請單正本",
        "badge": "列印申請單",
        "flow_prompt_en": "Medium close-up of a sleek modern corporate multifunction laser printer smoothly printing and sliding a crisp white expense report sheet into the output tray, bright clean office lighting, 35mm lens, 4K, 3 seconds.",
    },
    {
        "id": "m32", "act": "第六篇｜實體正本交件", "shot_type": "特寫・裝訂發票",
        "source_type": "ai_scene", "keyframe": "m32_stapler_receipts.png", "motion": "dolly_in", "sfx": "stamp",
        "narration": "連同實體發票、收據正本、路線圖與 eTag 明細整齊裝訂。",
        "subtitle": "裝訂正本｜報銷單 ＋ 發票／收據正本 ＋ 路線截圖 ＋ eTag 蓋章明細",
        "badge": "正本整齊裝訂",
        "flow_prompt_en": "Macro top-angle close-up on a warm walnut desk, hands pressing a sleek metallic stapler neatly onto a white corporate expense form aligned with official paper receipts bearing red circular stamps, crisp daylight, 4K, 3 seconds.",
    },
    {
        "id": "m33", "act": "第六篇｜實體正本交件", "shot_type": "中景・人事核對",
        "source_type": "ai_scene", "keyframe": "m33_hr_handover.png", "motion": "pan_right", "sfx": "stamp",
        "narration": "先親手交給人事單位核對正本與線上內容完全無誤。",
        "subtitle": "交件順序 1｜申請人先交由「人事單位」核對正本無誤",
        "badge": "人事核對蓋章",
        "flow_prompt_en": "Medium cinematic shot in a bright glass-walled corporate office, a Taiwanese employee politely hands a neat stack of stapled expense papers across a desk to a smiling HR specialist who raises a red verification stamp, natural sunlight, 4K, 3 seconds.",
    },
    {
        "id": "m34", "act": "第六篇｜實體正本交件", "shot_type": "全景・會計入帳",
        "source_type": "ai_scene", "keyframe": "m34_three_stage.png", "motion": "dolly_out", "sfx": "chime",
        "narration": "最後由人事轉交會計審核入帳，零退件順利完成報銷！",
        "subtitle": "交件順序 2｜人事轉交「會計審核入帳」➔ 零退件順利完成！",
        "badge": "申請人 ➔ 人事 ➔ 會計",
        "flow_prompt_en": "Wide cinematic pull-back inside a sunlit modern glass corporate office showcasing three luminous frosted-glass workflow pillars lighting up in sequence connected by a flowing golden-blue light beam, warm professional film look, 4K, 4 seconds.",
    },
]


# ==============================================================================
# 1. 音效合成器 (純 Python 產生細緻微音效，免外部檔案)
# ==============================================================================
def ensure_sfx_assets() -> Dict[str, Path]:
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    sr = 44100

    def write_wav(path: Path, samples: List[float]):
        with wave.open(str(path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            raw = bytearray()
            for s in samples:
                v = max(-1.0, min(1.0, s))
                raw.extend(struct.pack("<h", int(v * 32767)))
            wf.writeframes(bytes(raw))

    # 1. Subtle UI Click (45ms crisp high-tech pop)
    p_click = SFX_DIR / "click.wav"
    if not p_click.exists():
        n = int(sr * 0.05)
        samples = []
        for i in range(n):
            t = i / sr
            env = math.exp(-t * 95.0)
            s = (math.sin(2 * math.pi * 1450 * t) * 0.6 + math.sin(2 * math.pi * 2900 * t) * 0.3) * env * 0.35
            samples.append(s)
        write_wav(p_click, samples)

    # 2. Gentle Chime (180ms warm corporate ding)
    p_chime = SFX_DIR / "chime.wav"
    if not p_chime.exists():
        n = int(sr * 0.22)
        samples = []
        for i in range(n):
            t = i / sr
            env = math.exp(-t * 16.0) * min(1.0, t / 0.008)
            s = (math.sin(2 * math.pi * 880 * t) * 0.55 + math.sin(2 * math.pi * 1318.5 * t) * 0.35) * env * 0.28
            samples.append(s)
        write_wav(p_chime, samples)

    # 3. Crisp Stamp Thump (110ms low-mid tactile stamp)
    p_stamp = SFX_DIR / "stamp.wav"
    if not p_stamp.exists():
        n = int(sr * 0.12)
        samples = []
        for i in range(n):
            t = i / sr
            freq = 180.0 * math.exp(-t * 18.0) + 55.0
            env = math.exp(-t * 32.0)
            s = math.sin(2 * math.pi * freq * t) * env * 0.42
            samples.append(s)
        write_wav(p_stamp, samples)

    # 4. Soft Cinema Whoosh (220ms airy sweep)
    p_whoosh = SFX_DIR / "whoosh.wav"
    if not p_whoosh.exists():
        n = int(sr * 0.24)
        samples = []
        seed = 1234567
        prev = 0.0
        for i in range(n):
            t = i / sr
            # simple deterministic white noise + low-pass sweep
            seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
            noise = (seed / 0x7FFFFFFF) * 2.0 - 1.0
            env = math.sin(math.pi * (i / n)) ** 1.5
            alpha = 0.06 + 0.14 * env
            prev = prev + alpha * (noise - prev)
            samples.append(prev * env * 0.32)
        write_wav(p_whoosh, samples)

    return {"click": p_click, "chime": p_chime, "stamp": p_stamp, "whoosh": p_whoosh}


# ==============================================================================
# 2. 同步既有 Banana 3D 首幀至 bpm_sop_mv/keyframes/
# ==============================================================================
def sync_existing_keyframes():
    KEYFRAMES_DIR.mkdir(parents=True, exist_ok=True)
    FLOW_CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    reuse_map = {
        "m01_highway.png": PLAN_A_FLOW_DIR / "bpm_shot01_first.png",
        "m03_plant_gate.png": PLAN_A_FLOW_DIR / "bpm_shot01_last.png",
        "m08_bpm_portal.png": PLAN_C_FLOW_DIR / "bpm_c02_first.png",
        "m13_dual_track.png": PLAN_C_FLOW_DIR / "bpm_c03_first.png",
        "m20_hsr_train.png": PLAN_A_FLOW_DIR / "bpm_shot05_first.png",
        "m22_parking.png": PLAN_A_FLOW_DIR / "bpm_shot05_last.png",
        "m25_vault_dashboard.png": PLAN_C_FLOW_DIR / "bpm_c05_first.png",
        "m30_desk_approved.png": PLAN_A_FLOW_DIR / "bpm_shot08_first.png",
        "m34_three_stage.png": PLAN_A_FLOW_DIR / "bpm_shot08_last.png",
    }
    for dst_name, src_path in reuse_map.items():
        dst = KEYFRAMES_DIR / dst_name
        if src_path.exists() and not dst.exists():
            shutil.copy2(src_path, dst)


# ==============================================================================
# 3. 合成 34 段緊湊卡點台灣旁白 (去靜音 + 微音效混音)
# ==============================================================================
def synthesize_mv_audio(ffmpeg_exe: str, sfx_map: Dict[str, Path], rebuild_audio: bool, rate: str) -> Dict[str, float]:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    durations: Dict[str, float] = {}
    voice = "zh-TW-HsiaoChenNeural"

    print(f"[1/4] 正在合成 34 段 MV 卡點旁白 ({voice}, rate={rate})...")
    for shot in SHOTS_MV:
        sid = shot["id"]
        raw_mp3 = AUDIO_DIR / f"{sid}_raw.mp3"
        final_mp3 = AUDIO_DIR / f"{sid}.mp3"

        if rebuild_audio or not final_mp3.exists() or final_mp3.stat().st_size < 1000:
            try:
                asyncio.run(_edge_tts_save(shot["narration"], raw_mp3, voice, rate=rate))
            except Exception as exc:
                print(f"  [fallback] {sid} edge-tts failed ({exc}), using SAPI5")
                _sapi5_fallback_save(shot["narration"], raw_mp3, ffmpeg_exe)

            # Trim leading/trailing silence for tight MV pacing + mix subtle SFX at t=0
            sfx_key = shot.get("sfx")
            sfx_path = sfx_map.get(sfx_key) if sfx_key else None
            if sfx_path and sfx_path.exists():
                cmd = [
                    ffmpeg_exe, "-y",
                    "-i", str(raw_mp3),
                    "-i", str(sfx_path),
                    "-filter_complex",
                    "[0:a]silenceremove=start_periods=1:start_silence=0.04:start_threshold=-42dB,"
                    "areverse,silenceremove=start_periods=1:start_silence=0.05:start_threshold=-42dB,areverse,"
                    "apad=pad_dur=0.14[v0];"
                    "[1:a]volume=0.45[s1];"
                    "[v0][s1]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[out]",
                    "-map", "[out]",
                    "-c:a", "libmp3lame", "-b:a", "192k",
                    str(final_mp3),
                ]
            else:
                cmd = [
                    ffmpeg_exe, "-y",
                    "-i", str(raw_mp3),
                    "-af",
                    "silenceremove=start_periods=1:start_silence=0.04:start_threshold=-42dB,"
                    "areverse,silenceremove=start_periods=1:start_silence=0.05:start_threshold=-42dB,areverse,"
                    "apad=pad_dur=0.14",
                    "-c:a", "libmp3lame", "-b:a", "192k",
                    str(final_mp3),
                ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        dur = get_media_duration(ffmpeg_exe, final_mp3)
        durations[sid] = round(max(2.1, dur + 0.08), 2)
    total_s = sum(durations.values())
    print(f"      ✓ 34 段緊湊旁白就緒！預估總長 {total_s:.1f}s (平均每鏡 {total_s/len(SHOTS_MV):.2f}s)")
    return durations


# ==============================================================================
# 4. 電影級 MV 畫面渲染引擎 (極簡電影字幕 + 動態景別運鏡)
# ==============================================================================
def ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - max(0.0, min(1.0, t))) ** 3


def draw_mv_hud(canvas: Image.Image, shot: dict, t_norm: float, shot_idx: int, total_shots: int):
    ov = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # Top-left clean minimal pill badge (Act + Highlight)
    badge_text = shot.get("badge", shot["act"])
    b_font = get_font(22, bold=True)
    bbox = d.textbbox((0, 0), badge_text, font=b_font)
    bw = (bbox[2] - bbox[0]) + 40
    d.rounded_rectangle([38, 28, 38 + bw, 74], radius=22, fill=(10, 18, 34, 210), outline=(56, 189, 248, 220), width=2)
    d.text((58, 37), badge_text, fill=(224, 242, 254, 255), font=b_font)

    # Top-right subtle brand tag
    brand_text = "鼎新 BPM 費用報銷"
    br_font = get_font(20, bold=True)
    br_box = d.textbbox((0, 0), brand_text, font=br_font)
    br_w = (br_box[2] - br_box[0]) + 32
    d.rounded_rectangle([VIDEO_W - 38 - br_w, 28, VIDEO_W - 38, 68], radius=18, fill=(10, 18, 34, 175), outline=(148, 163, 184, 140), width=1)
    d.text((VIDEO_W - 38 - br_w + 16, 36), brand_text, fill=(203, 213, 225, 235), font=br_font)

    # Bottom cinematic gradient bar + crisp centered subtitle
    for y in range(VIDEO_H - 160, VIDEO_H):
        alpha = int(215 * ((y - (VIDEO_H - 160)) / 160.0) ** 1.2)
        d.line([(0, y), (VIDEO_W, y)], fill=(8, 13, 24, alpha))

    sub_text = shot["subtitle"]
    s_font = get_font(34, bold=True)
    sb = d.textbbox((0, 0), sub_text, font=s_font)
    sw = sb[2] - sb[0]
    sx = (VIDEO_W - sw) // 2
    sy = VIDEO_H - 96
    # subtle shadow
    d.text((sx + 2, sy + 2), sub_text, fill=(0, 0, 0, 220), font=s_font)
    d.text((sx, sy), sub_text, fill=(255, 255, 255, 255), font=s_font)

    # Sleek thin bottom progress bar across whole MV
    prog = (shot_idx + t_norm) / max(1, total_shots)
    d.rectangle([0, VIDEO_H - 6, VIDEO_W, VIDEO_H], fill=(30, 41, 59, 200))
    d.rectangle([0, VIDEO_H - 6, int(VIDEO_W * prog), VIDEO_H], fill=(56, 189, 248, 255))

    canvas.paste(ov, (0, 0), ov)


def render_ai_scene_frame(shot: dict, t_norm: float, cache: Dict[str, Image.Image]) -> Image.Image:
    kf_name = shot["keyframe"]
    kf_path = KEYFRAMES_DIR / kf_name
    if kf_name not in cache:
        im = Image.open(kf_path).convert("RGB")
        # Optional pre-crop for close-up cut from a wider Banana keyframe
        if "crop_focus" in shot:
            cx1, cy1, cx2, cy2 = shot["crop_focus"]
            w, h = im.size
            im = im.crop((int(w * cx1), int(h * cy1), int(w * cx2), int(h * cy2)))
        # Scale up cleanly to overscan 2160x1215 for butter-smooth kinetic pan/zoom
        cache[kf_name] = im.resize((2160, 1215), Image.Resampling.LANCZOS)

    base = cache[kf_name]
    bw, bh = base.size
    e = ease_out_cubic(t_norm)
    motion = shot.get("motion", "dolly_in")

    if motion == "dolly_in":
        scale = 1.0 + 0.11 * e
        vw, vh = int(bw / scale), int(bh / scale)
        x0, y0 = (bw - vw) // 2, (bh - vh) // 2
    elif motion == "dolly_out":
        scale = 1.11 - 0.11 * e
        vw, vh = int(bw / scale), int(bh / scale)
        x0, y0 = (bw - vw) // 2, (bh - vh) // 2
    elif motion == "pan_right":
        vw, vh = int(bw / 1.10), int(bh / 1.10)
        x0 = int((bw - vw) * (0.1 + 0.8 * e))
        y0 = (bh - vh) // 2
    elif motion == "pan_left":
        vw, vh = int(bw / 1.10), int(bh / 1.10)
        x0 = int((bw - vw) * (0.9 - 0.8 * e))
        y0 = (bh - vh) // 2
    else:  # zoom_focus
        scale = 1.0 + 0.14 * e
        vw, vh = int(bw / scale), int(bh / scale)
        x0, y0 = (bw - vw) // 2, (bh - vh) // 2

    cropped = base.crop((x0, y0, x0 + vw, y0 + vh))
    frame = cropped.resize((VIDEO_W, VIDEO_H), Image.Resampling.LANCZOS)
    return frame


def render_ui_macro_frame(shot: dict, t_norm: float, cache: Dict[str, Image.Image]) -> Image.Image:
    fig_name = shot["fig"]
    if fig_name not in cache:
        im = Image.open(FIG_DIR / fig_name).convert("RGB")
        cache[fig_name] = im.filter(ImageFilter.UnsharpMask(radius=1.1, percent=120, threshold=2))

    src = cache[fig_name]
    sw, sh = src.size
    fx1, fy1, fx2, fy2 = shot["focus_box"]
    e = ease_out_cubic(t_norm)

    # Interpolate viewport from slightly wider view into tight focus box
    pad = 0.08 * (1.0 - e)
    x1 = max(0.0, fx1 - pad)
    y1 = max(0.0, fy1 - pad)
    x2 = min(1.0, fx2 + pad)
    y2 = min(1.0, fy2 + pad)

    crop = src.crop((int(sw * x1), int(sh * y1), int(sw * x2), int(sh * y2)))
    # Fit inside 1780x840 stage with crisp Lanczos
    cw, ch = crop.size
    ratio = min(1780 / max(1, cw), 820 / max(1, ch))
    nw, nh = max(1, int(cw * ratio)), max(1, int(ch * ratio))
    resized = crop.resize((nw, nh), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (VIDEO_W, VIDEO_H), (13, 20, 36))
    px = (VIDEO_W - nw) // 2
    py = 96 + (820 - nh) // 2

    # Glowing card border behind UI macro
    ov = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle([px - 10, py - 10, px + nw + 10, py + nh + 10], radius=16, fill=(15, 23, 42, 245), outline=(56, 189, 248, 230), width=4)
    canvas.paste(ov, (0, 0), ov)
    canvas.paste(resized, (px, py))

    # Crisp kinetic callout tag floating at top-center
    callout = shot.get("callout")
    if callout:
        ov2 = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
        d2 = ImageDraw.Draw(ov2)
        c_font = get_font(28, bold=True)
        cb = d2.textbbox((0, 0), callout, font=c_font)
        cw_t = (cb[2] - cb[0]) + 48
        cx = (VIDEO_W - cw_t) // 2
        cy = int(28 + 8 * (1.0 - e))
        d2.rounded_rectangle([cx, cy, cx + cw_t, cy + 54], radius=26, fill=(234, 88, 12, 238), outline=(254, 240, 138, 255), width=3)
        d2.text((cx + 24, cy + 10), callout, fill=(255, 255, 255, 255), font=c_font)
        canvas.paste(ov2, (0, 0), ov2)

    return canvas


def render_ui_dual_frame(shot: dict, t_norm: float, cache: Dict[str, Image.Image]) -> Image.Image:
    canvas = Image.new("RGB", (VIDEO_W, VIDEO_H), (13, 20, 36))
    e = ease_out_cubic(t_norm)
    scale = 1.0 + 0.04 * e
    slot_w, slot_h = int(680 * scale), int(760 * scale)

    for idx, fname in enumerate(shot["figs"]):
        if fname not in cache:
            cache[fname] = Image.open(FIG_DIR / fname).convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.1, percent=120, threshold=2))
        im = cache[fname]
        ratio = min(slot_w / im.width, slot_h / im.height)
        nw, nh = int(im.width * ratio), int(im.height * ratio)
        rim = im.resize((nw, nh), Image.Resampling.LANCZOS)
        cx = 520 if idx == 0 else 1400
        px = cx - nw // 2
        py = 105 + (760 - nh) // 2

        ov = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        col = (56, 189, 248, 230) if idx == 0 else (250, 204, 21, 230)
        d.rounded_rectangle([px - 8, py - 8, px + nw + 8, py + nh + 8], radius=14, fill=(15, 23, 42, 240), outline=col, width=4)
        canvas.paste(ov, (0, 0), ov)
        canvas.paste(rim, (px, py))

        lbl = shot["labels"][idx]
        ov2 = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
        d2 = ImageDraw.Draw(ov2)
        lf = get_font(24, bold=True)
        lb = d2.textbbox((0, 0), lbl, font=lf)
        lw = (lb[2] - lb[0]) + 36
        d2.rounded_rectangle([cx - lw // 2, py + nh + 16, cx + lw // 2, py + nh + 62], radius=14, fill=(30, 41, 59, 240), outline=col, width=2)
        d2.text((cx - lw // 2 + 18, py + nh + 25), lbl, fill=(248, 250, 252, 255), font=lf)
        canvas.paste(ov2, (0, 0), ov2)

    return canvas


def render_single_mv_clip(
    ffmpeg_exe: str,
    shot: dict,
    shot_idx: int,
    total_shots: int,
    duration: float,
    audio_path: Path,
    out_mp4: Path,
) -> bool:
    sid = shot["id"]
    real_flow_mp4 = FLOW_CLIPS_DIR / f"{sid}_flow.mp4"
    if real_flow_mp4.exists():
        # Overlay minimal MV HUD on user's real Flow / MiniMax H3 video clip
        hud = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
        draw_mv_hud(hud, shot, 1.0, shot_idx, total_shots)
        hud_png = out_mp4.with_suffix(".hud.png")
        hud.save(hud_png)
        cmd = [
            ffmpeg_exe, "-y",
            "-stream_loop", "-1", "-i", str(real_flow_mp4),
            "-i", str(hud_png),
            "-i", str(audio_path),
            "-filter_complex",
            f"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps={FPS}[bg];"
            "[bg][1:v]overlay=0:0[v]",
            "-map", "[v]", "-map", "2:a:0",
            "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
            "-t", f"{duration:.2f}",
            str(out_mp4),
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        hud_png.unlink(missing_ok=True)
        return True

    total_frames = max(24, int(round(duration * FPS)))
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{VIDEO_W}x{VIDEO_H}", "-r", str(FPS), "-i", "-",
        "-i", str(audio_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
        "-af", "apad", "-t", f"{duration:.2f}",
        str(out_mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cache: Dict[str, Image.Image] = {}
    try:
        for fidx in range(total_frames):
            t_norm = fidx / max(1, total_frames - 1)
            st = shot["source_type"]
            if st == "ai_scene":
                frame = render_ai_scene_frame(shot, t_norm, cache)
            elif st == "ui_macro":
                frame = render_ui_macro_frame(shot, t_norm, cache)
            else:
                frame = render_ui_dual_frame(shot, t_norm, cache)
            draw_mv_hud(frame, shot, t_norm, shot_idx, total_shots)
            assert proc.stdin is not None
            try:
                proc.stdin.write(frame.tobytes())
            except (BrokenPipeError, OSError):
                break
    finally:
        if proc.stdin:
            try:
                proc.stdin.close()
            except OSError:
                pass
        proc.wait()
    return False


# ==============================================================================
# 5. 匯出 34 鏡中英文對照分鏡表 (可直接貼入 Google Flow / MiniMax H3)
# ==============================================================================
def export_bilingual_storyboard_md(durations: Dict[str, float]):
    lines = [
        "# BPM 一般費用報銷單（私車公用）AI MV 級 34 鏡中英文分鏡腳本",
        "",
        "> 借鏡 AI MV《已讀不懂》流水線：全片拆為 **34 個 2.5~5 秒微鏡頭**，景別快速交替（遠景/中景/特寫/POV/UI推近）。",
        "> **單鏡替換成真 AI 影片方式**：用下方任一鏡的英文 Prompt 在 Google Flow / MiniMax H3 生成 3~5 秒影片後，存成 `mXX_flow.mp4` 放入 `bpm_sop_mv/flow_clips/`，再重跑 `python build_bpm_mv_video.py --only mXX` 即可秒換！",
        "",
    ]
    t_acc = 0.0
    cur_act = ""
    for shot in SHOTS_MV:
        sid = shot["id"]
        dur = durations[sid]
        t_start = t_acc
        t_end = t_acc + dur
        t_acc = t_end

        if shot["act"] != cur_act:
            cur_act = shot["act"]
            lines.append(f"## {cur_act}")
            lines.append("")

        kf = f"`bpm_sop_mv/keyframes/{shot['keyframe']}`" if shot.get("keyframe") else f"實務 UI 截圖 (`{shot.get('fig', shot.get('figs'))}`)"
        lines.extend([
            f"### {sid.upper()}｜`{t_start:05.1f}s - {t_end:05.1f}s` ({dur:.1f}s)｜{shot['shot_type']}",
            f"- **中文旁白**：{shot['narration']}",
            f"- **畫面字幕**：{shot['subtitle']}",
            f"- **首幀素材**：{kf}",
            f"- **Google Flow / MiniMax 英文 Prompt**：",
            "```text",
            shot["flow_prompt_en"],
            "```",
            "",
        ])

    SCRIPT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[4/4] 已匯出 34 鏡中英文腳本 -> {SCRIPT_MD_PATH}")


def main():
    parser = argparse.ArgumentParser(description="BPM AI MV 級 34 鏡微鏡頭總片建置器")
    parser.add_argument("--only", nargs="+", help="僅重算指定鏡次 (例如 m01 m07)")
    parser.add_argument("--rebuild-audio", action="store_true", help="強制重新合成旁白音訊")
    parser.add_argument("--rate", default="+12%", help="旁白語速 (預設 +12%% 緊湊 MV 節奏)")
    args = parser.parse_args()

    only_set = set(args.only) if args.only else None
    ffmpeg_exe = find_ffmpeg()
    print(f"使用 FFmpeg: {ffmpeg_exe}")

    sync_existing_keyframes()
    sfx_map = ensure_sfx_assets()
    durations = synthesize_mv_audio(ffmpeg_exe, sfx_map, args.rebuild_audio, args.rate)

    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    concat_entries = []
    manifest_shots = []
    elapsed = 0.0
    total_shots = len(SHOTS_MV)

    print(f"[2/4] 正在渲染 {total_shots} 段 1080p 微鏡頭 (每鏡 2.5~5s)...")
    for idx, shot in enumerate(SHOTS_MV):
        sid = shot["id"]
        dur = durations[sid]
        audio_path = AUDIO_DIR / f"{sid}.mp3"
        out_mp4 = CLIPS_DIR / f"{sid}.mp4"
        need_render = only_set is None or sid in only_set or not out_mp4.exists() or out_mp4.stat().st_size < 30_000

        used_flow = False
        if need_render:
            used_flow = render_single_mv_clip(ffmpeg_exe, shot, idx, total_shots, dur, audio_path, out_mp4)

        actual_dur = get_media_duration(ffmpeg_exe, out_mp4)
        tag = " [真Flow實片]" if used_flow else (" [沿用]" if not need_render else "")
        print(f"      ✓ {sid}.mp4 ({actual_dur:.2f}s) | {shot['shot_type']}{tag}")
        concat_entries.append(f"file '{out_mp4.as_posix()}'")

        manifest_shots.append({
            "id": sid,
            "index": idx + 1,
            "act": shot["act"],
            "shot_type": shot["shot_type"],
            "start_sec": round(elapsed, 2),
            "end_sec": round(elapsed + actual_dur, 2),
            "duration": round(actual_dur, 2),
            "narration": shot["narration"],
            "subtitle": shot["subtitle"],
            "flow_prompt_en": shot["flow_prompt_en"],
            "used_real_flow": used_flow,
        })
        elapsed += actual_dur

    concat_txt = CLIPS_DIR / "concat_list.txt"
    concat_txt.write_text("\n".join(concat_entries) + "\n", encoding="utf-8")

    print("[3/4] 正在無縫串接 34 鏡 MV 總片...")
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c", "copy", "-movflags", "+faststart",
        str(FINAL_VIDEO_PATH),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    shutil.copy2(FINAL_VIDEO_PATH, ROOT_COPY_PATH)

    MANIFEST_PATH.write_text(
        json.dumps({"total_duration": round(elapsed, 2), "shot_count": total_shots, "shots": manifest_shots}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    export_bilingual_storyboard_md(durations)
    print(f"\n🎉 MV 級 34 鏡總片完成！({elapsed:.2f}s) -> {FINAL_VIDEO_PATH}")
    print(f"   已同步至根目錄 -> {ROOT_COPY_PATH}")


if __name__ == "__main__":
    main()
