"""
第 2 部《儲槽出貨與灌裝篇》混合雙軌 SOP 電影教學影片管線
===========================================================================
對應文件：C50110-INV-02-01（版別 3.1）《儲槽進出貨作業方法》
涵蓋範圍：5.3 出貨作業（一般槽車 + ISO TANK）/ 5.4 其他注意事項（放櫃管制、GAA 保溫、四大風險）/ 附件 6.2 / 6.3 / 6.5

核心特色：
1. 自動從原始 PDF 以 260 DPI 擷取 2 張出貨流程圖（P.16、P.19）+ 3 張完整檢點表單（6.2、6.3、6.5）並精準裁切銳化
2. 沿用第 1 部獨家「表單檢點聚光燈引擎」：暗影壓暗遮罩 + 琥珀金 / 晴空青 / 翡翠綠 / 科技橘雙層亮框 + 局部原圖放大鏡 + 白話檢點步驟卡
3. 語音停頓中點吸附（silencedetect），確保每句唸完才切換畫面
4. 支援 Google Flow Agent 真人過場與 PiP、--export-voice-jobs 匯出 Colab T4 台灣配音工作單、--cinema 封面/封底 + xfade + BGM 閃避
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

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
    render_cover_clip,
    render_ending_clip,
    synthesize_gemini_tts,
)

# 路徑設定
PDF_CANDIDATES = [
    Path(r"C:\Users\C606\Desktop\C50110-INV-02-01 儲槽進出貨作業方法(3.1版).pdf"),
    BASE_DIR / "tank_outbound_sop" / "C50110-INV-02-01 儲槽進出貨作業方法(3.1版).pdf",
    BASE_DIR / "tank_inbound_sop" / "C50110-INV-02-01 儲槽進出貨作業方法(3.1版).pdf",
]
OUT_ROOT = BASE_DIR / "tank_outbound_sop"
FIG_DIR = OUT_ROOT / "figures"
FLOW_FRAMES_DIR = OUT_ROOT / "flow_frames"
FLOW_CLIPS_DIR = OUT_ROOT / "flow_clips"
AUDIO_DIR = OUT_ROOT / "audio"
CLIPS_DIR = OUT_ROOT / "clips"
WORK_DIR = OUT_ROOT / "_work"
VOICE_JOBS_PATH = OUT_ROOT / "outbound_voice_jobs.json"
FINAL_VIDEO_PATH = OUT_ROOT / "第2部_儲槽出貨與灌裝篇_表單檢點教學總片.mp4"

VIDEO_W, VIDEO_H = 1920, 1080
FPS = 24

COLOR_BG_DARK = (11, 18, 32)
COLOR_CARD_BG = (20, 30, 48)
COLOR_BORDER_SUB = (46, 64, 92)
COLOR_TEXT_MAIN = (244, 247, 252)
COLOR_TEXT_MUTED = (168, 184, 208)

PALETTE = {
    "amber": (245, 158, 11),
    "cyan": (14, 165, 233),
    "emerald": (16, 185, 129),
    "orange": (249, 115, 22),
}

# PDF 頁面與自動裁切座標 (left, top, right, bottom)
PDF_EXTRACTS = {
    "fig01_tanker_outbound_flow.png": (16, (0.16, 0.21, 0.85, 0.90)),
    "fig02_isotank_outbound_flow.png": (19, (0.16, 0.21, 0.85, 0.90)),
    "fig03_form_6_2.png": (24, (0.18, 0.24, 0.86, 0.92)),
    "fig04_form_6_3.png": (25, (0.18, 0.24, 0.86, 0.92)),
    "fig05_form_6_5.png": (27, (0.17, 0.27, 0.87, 0.84)),
}


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


def extract_pdf_figures() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = next((p for p in PDF_CANDIDATES if p.exists()), None)
    if not pdf_path:
        missing = [k for k in PDF_EXTRACTS if not (FIG_DIR / k).exists()]
        if missing:
            raise FileNotFoundError(f"找不到原始 PDF，且缺少圖檔：{missing}")
        print("[Figures] 使用既有 figures/ 圖檔。")
        return

    import fitz

    doc = fitz.open(pdf_path)
    for fname, (pno, crop_rel) in PDF_EXTRACTS.items():
        page = doc[pno - 1]
        pix = page.get_pixmap(dpi=260)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        w, h = img.size
        l, t, r, b = crop_rel
        cropped = img.crop((int(w * l), int(h * t), int(w * r), int(h * b)))
        cropped = cropped.filter(ImageFilter.UnsharpMask(radius=1.0, percent=120, threshold=3))
        cropped.save(FIG_DIR / fname, quality=95)
        print(f"[Figures] 擷取 P.{pno:02d} -> {fname} ({cropped.size[0]}x{cropped.size[1]})")


def get_shots() -> List[dict]:
    return [
        {
            "id": "shot01",
            "type": "flow",
            "flow_clips": ["b01_outbound_intro.mp4", "s01_b.mp4"],
            "theme": "cyan",
            "chapter": "01｜出貨開工核對、PPE 與 EBR 攪拌",
            "form_badge": "WI 5.3.1 槽車入廠 / 5.3.2(8) EBR",
            "figure": "fig01_tanker_outbound_flow.png",
            "narration": (
                "歡迎來到儲槽進出貨作業教學第二部：出貨與灌裝篇。"
                "執行任何灌裝出貨前，所有現場人員都必須先穿戴完整個人防護裝備。"
                "槽車入廠後，先依出貨通知單核對品名、槽別、數量與車號，再引導司機駛入灌裝位置。"
                "停妥後務必接妥靜電接地線、放妥兩組車輪檔固定車頭與槽車輪胎、"
                "擺設滅火器、三角錐與盛漏盤、將車鑰匙交到鑰匙箱鎖管，並檢查槽車各項凡爾是否正確。"
                "特別提醒：如果是 E B R 系列產品出貨前，必須先在儲槽槽邊或馬達排氣口接妥氮氣管，"
                "開啟氮氣主閥進行攪拌十到三十分鐘，等槽車定位完成後再關閉氮氣攪拌！"
            ),
            "card_title": "出貨開工前 5 大確認（5.3.1）",
            "card_points": [
                "穿妥完整 PPE：安全帽、安全鞋、護目鏡、防毒面具、防護手套",
                "核對『出貨通知單』：品名 / 儲槽別 / 預定出貨量 / 車號",
                "定位固定：2 組輪檔、滅火器、三角錐、盛漏盤、接地線、鑰匙入箱",
                "逐一檢查槽車各項凡爾開關位置正確",
                "★ EBR 系列專屬：出貨前氮氣攪拌 10–30 分鐘，槽車定位後關閉",
            ],
        },
        {
            "id": "shot02",
            "type": "form_spotlight",
            "theme": "cyan",
            "chapter": "02｜表單檢點特寫：附件 6.2（裝貨前安檢＋清潔度）",
            "form_badge": "表單 C50110-INV-02-01(03)",
            "figure": "fig03_form_6_2.png",
            "narration": (
                "一般槽車灌裝前，請拿出第一張出貨核心表單：附件六之二，運輸油槽車安檢清潔度檢核表。"
                "這張表單採「運輸公司檢點」與「現場人員確認」雙欄交叉核對。"
                "先看上半部裝貨前十一項安檢：車輛鑰匙掛指定位置、接地線實測十歐姆以下並抄寫數值、"
                "輪檔定位、運輸物質標示牌與 S D S 備妥、安全閥與液位閥正常，"
                "以及最關鍵的第十一項：再次確認出貨灌裝軟管的儲槽編號與出貨通知單完全相符，徹底防混料！"
                "接著看中段清潔度檢核五項：確認出口凡爾數量、單槽或雙槽設計，"
                "以及油槽車內部、出口凡爾皆清潔無殘液、車體外部無油漬，確認合格才能接管灌裝。"
            ),
            "focus_steps": [
                {
                    "weight": 0.56,
                    "box": (0.04, 0.135, 0.96, 0.455),
                    "color": "cyan",
                    "badge_tag": "雙欄核對｜10Ω 實填＋防混料",
                    "zoom_title": "附件 6.2：裝貨前安檢項目（1–11 項）",
                    "check_points": [
                        "運輸公司與現場人員【雙欄核對】；鑰匙掛指定位置、輪檔定位",
                        "第 2 項接地線必實測【10 歐姆以下】並填入實測歐姆值",
                        "確認 SDS 標示牌、VOC 回收管固定、第 11 項出貨管件與儲槽相符",
                    ],
                },
                {
                    "weight": 0.44,
                    "box": (0.04, 0.45, 0.96, 0.595),
                    "color": "amber",
                    "badge_tag": "清潔度紅線｜無殘液無油漬",
                    "zoom_title": "附件 6.2：清潔度檢核項目（1–5 項）",
                    "check_points": [
                        "紀錄槽車出口 Valve 數量，勾選單槽或雙槽設計",
                        "檢查油槽車內部與出口 Valve 是否【清潔無殘液】",
                        "確認槽車外部清潔無油漬，雙欄簽認後才可接管",
                    ],
                },
            ],
        },
        {
            "id": "shot03",
            "type": "form_spotlight",
            "theme": "cyan",
            "chapter": "03｜表單檢點特寫：附件 6.2（裝貨中監控＋完成簽核）",
            "form_badge": "表單 C50110-INV-02-01(03) & WI 5.3.2",
            "figure": "fig03_form_6_2.png",
            "narration": (
                "軟管接妥槽車底部出口後，操作員要先依預定出貨量，算出儲槽預計下降的液位點，"
                "再啟動泵浦灌裝——請牢記安全鐵律：灌裝期間現場操作員絕對不可以離開現場！"
                "同時填寫六之二表單的裝貨中兩項：確認槽車無洩漏，並實抄泵浦作業壓力。"
                "灌裝達預定出貨量時進行取樣檢驗：第一、二輪由每年經品管認證的現場操作員取樣，"
                "第三輪起強制由品管人員親自取樣，確認合格後才完成出貨。"
                "灌裝結束後，先用氮氣將管線壓空並確實洩壓，再拆除管線、蓋妥塞頭扣緊掛耳、"
                "拔離 V O C 管線與接地線、移除輪檔歸位，最後勾完裝貨完成五項並由駕駛員、現場人員、品管與組課長完成簽核。"
            ),
            "focus_steps": [
                {
                    "weight": 0.48,
                    "box": (0.04, 0.59, 0.96, 0.665),
                    "color": "amber",
                    "badge_tag": "裝貨中｜嚴禁離場＋取樣輪次",
                    "zoom_title": "裝貨中檢查（2 項）＋ 5.3.2 監控規範",
                    "check_points": [
                        "先算儲槽預計下降液位點；灌裝期間操作員【嚴禁離開現場】",
                        "確認無洩漏並實填 PUMP 作業壓力 (Kg/cm²)",
                        "取樣規則：第 1–2 輪認證操作員取樣，第 3 輪起品管人員取樣",
                    ],
                },
                {
                    "weight": 0.52,
                    "box": (0.04, 0.66, 0.96, 0.95),
                    "color": "emerald",
                    "badge_tag": "壓空洩壓拆管＋完整簽核",
                    "zoom_title": "裝貨完成檢查（5 項）＋多方簽核欄",
                    "check_points": [
                        "氮氣壓空管線並【洩壓】才拆管；軟管塞頭蓋妥、掛耳扣緊",
                        "VOC 管線拔離並關妥閥件，接地線與輪檔移除歸位",
                        "填寫出貨通知單號，完成駕駛員／現場／品管／組長／課(副)長簽核",
                    ],
                },
            ],
        },
        {
            "id": "shot04",
            "type": "flow",
            "flow_clips": ["b02_outbound_isotank.mp4"],
            "theme": "orange",
            "chapter": "04｜Part B ISO TANK 灌裝流程與 Flush 鐵律",
            "form_badge": "WI 5.3.3 ISO TANK 灌裝流程",
            "figure": "fig02_isotank_outbound_flow.png",
            "narration": (
                "接下來進入第二種車型：ISO TANK 貨櫃化學槽出貨灌裝。"
                "定位固定並填完檢點表後，將砲管接妥底部進料閥，頂部入口接上氮氣管補壓並對外排吹三到五次，確認槽內無殘液才銜接灌裝管線。"
                "正式灌裝前一定要先做管線 Flush：把灌裝管線內料品沖洗至一噸桶約一百公升，取樣送品管檢驗合格才開始灌裝。"
                "特別注意殘料情境：如果 ISO TANK 內部還有殘存料品，必須先用氮氣加壓取樣分析；"
                "一旦判定內部受污染，就必須把殘料徹底排空、以氮氣排吹三到五分鐘，再充填兩百公升入槽重新取樣，"
                "直到品管判定合格，才可以設定預計出貨量開始灌裝！"
            ),
            "card_title": "ISO TANK 灌裝 4 大關鍵數值（5.3.3）",
            "card_points": [
                "頂部接氮氣管補壓 → 對外排吹【3–5 次】確認無殘液",
                "灌裝管線 Flush 至 1T 桶約【100L】→ 1–2 輪操作員 / 第 3 輪品管取樣",
                "槽內若有殘料 → 氮氣加壓取樣；若受污染 → 排空＋氮氣排吹【3–5 分鐘】",
                "受污染槽體再充填【200L】取樣合格 → 設定預計出貨量開始灌裝",
            ],
        },
        {
            "id": "shot05",
            "type": "form_spotlight",
            "theme": "orange",
            "chapter": "05｜表單檢點特寫：附件 6.3（接合前 17 項＋品管卡控）",
            "form_badge": "表單 C50110-INV-02-01(04)",
            "figure": "fig04_form_6_3.png",
            "narration": (
                "ISO TANK 出貨必檢這張表單：附件六之三，ISO TANK 作業檢點表。"
                "表頭填好槽別、品名與 ISO TANK 號碼，先逐項勾填「接合前」十七項檢查："
                "輪檔、接地線實測十歐姆以下、三角錐與手提滅火器、氮氣與化學品閥關閉、N S B 管帽與軟管無洩漏折損、"
                "槽頂箱無化學品、安全閥與本體外觀完好；"
                "作業中更要實抄槽體壓力零點五到一公斤、泵浦壓力、袋式過濾器壓力（超過兩公斤立即更換濾袋），"
                "以及第十六、十七項：殘液紀錄量、客戶需求充填量、設定流量與完成充填量。"
                "請看中段粗框處：依附註二規定，ISO TANK 內部檢查須入料五百公升後壓出取樣，"
                "一定要由品管人員簽章判定合格，才可以開始正式充填！"
            ),
            "focus_steps": [
                {
                    "weight": 0.58,
                    "box": (0.06, 0.08, 0.97, 0.62),
                    "color": "orange",
                    "badge_tag": "接合前 17 項｜壓力＋充填量必抄",
                    "zoom_title": "附件 6.3：接合前檢點欄位（1–17 項）",
                    "check_points": [
                        "第 2 項接地線實測【10Ω 以下】；確認閥件關閉、NSB 管帽與軟管無折損",
                        "實填槽體壓力 (0.5–1 kg/cm²)、PUMP 壓力、袋濾器 (> 2 kg/cm² 換袋)",
                        "第 16–17 項必抄：殘液量 / 客戶需求充填量 (KG) / 設定流量 (L) / 完成量",
                    ],
                },
                {
                    "weight": 0.42,
                    "box": (0.06, 0.61, 0.97, 0.72),
                    "color": "emerald",
                    "badge_tag": "強制停等｜500L 取樣品管簽章",
                    "zoom_title": "中段粗框：ISO TANK 內部判定合格簽章",
                    "check_points": [
                        "依附註 2：ISO TANK 內部檢查須入料【500L】後壓出取樣",
                        "由品管人員判定合格並【簽章核可】後，始可正式充填",
                        "實施者須於接合前簽名確認，嚴禁跳過品管放行關卡",
                    ],
                },
            ],
        },
        {
            "id": "shot06",
            "type": "form_spotlight",
            "theme": "orange",
            "chapter": "06｜表單檢點特寫：附件 6.3（保壓收管＋拆卸後簽核）",
            "form_badge": "表單 6.3 拆卸後 & WI 5.3.3(7–10)",
            "figure": "fig04_form_6_3.png",
            "narration": (
                "ISO TANK 灌裝期間操作員同樣不可離開現場，而且要隨時盯緊槽內壓力是否正常排壓，"
                "如果壓力異常升高，立刻檢查排氣閥是否確實開啟。"
                "灌裝達預定出貨量後，依序關閉馬達、將管線排空並拆管，把 ISO TANK 槽體保壓至零點五到一公斤每平方公分。"
                "接著通知品管人員取樣；取樣完成後，把砲管剩餘料品排至一噸桶回收，"
                "確認氮氣管內部壓力完全釋放後再拆除氮氣管、轉接頭與接地線——"
                "請記得：一定要確認品質檢驗合格後才能拆除砲管！"
                "最後把附件六之三「拆卸後」直欄勾填完畢，正常打勾、異常打叉並把改善處置寫進備註，送交組長與課長簽核。"
            ),
            "focus_steps": [
                {
                    "weight": 0.55,
                    "box": (0.64, 0.08, 0.97, 0.77),
                    "color": "cyan",
                    "badge_tag": "保壓 0.5–1.0｜合格才拆砲管",
                    "zoom_title": "拆卸後直欄＋實施者 / 組長 / 課長簽核",
                    "check_points": [
                        "灌裝中緊盯排壓（異常查排氣閥）；灌畢關馬達排空並【保壓 0.5–1.0 kg/cm²】",
                        "品管取樣後殘料排回 1T 桶、釋放氮氣管壓再拆管；【檢驗合格後才拆砲管】",
                        "勾填【拆卸後】直欄，實施者簽名並送組長確認、課(副)長簽核",
                    ],
                },
                {
                    "weight": 0.45,
                    "box": (0.06, 0.77, 0.97, 0.93),
                    "color": "amber",
                    "badge_tag": "附註 4 條鐵律必讀",
                    "zoom_title": "附件 6.3 備註與附註填表規範",
                    "check_points": [
                        "符號規範：V 代表正常、X 代表異常（異常狀況必須於備註欄說明）",
                        "若有異常須立即改善維修，並將異常處理經過完整敘述於表內",
                        "接地完成必檢測接地電阻【10Ω 以下】，確認設備歸位再通知開往地磅",
                    ],
                },
            ],
        },
        {
            "id": "shot07",
            "type": "form_spotlight",
            "theme": "amber",
            "chapter": "07｜油罐車放櫃例外管制：附件 6.5 檢點表",
            "form_badge": "表單 C50110-INV-02-01(01) & WI 5.4.6–7",
            "figure": "fig05_form_6_5.png",
            "narration": (
                "再來介紹一個極容易被忽略的工安紅線：油罐車放櫃管制。"
                "依規定，廠內油罐車原則上絕對不可以放櫃，裝卸作業時司機必須全程在場；"
                "只有台積電回收油罐車或特殊製程需求才可例外，若司機臨時需離場也必須經單位主管同意。"
                "凡是執行放櫃作業前，必須先填妥這張附件六之五：油罐車放櫃作業前檢點表。"
                "先勾選充填或卸料作業，由運輸公司與現場人員雙欄確認安檢八項：接地線十歐姆以下、輪檔、三角錐滅火器、"
                "第四項槽車排氣閥與呼吸閥開啟、標示牌、封蓋、安全閥與液位閥，"
                "接著核對清潔度五項，最關鍵的是下方簽核欄：必須在作業前先經單位主管簽核批准，才可以開始作業！"
            ),
            "focus_steps": [
                {
                    "weight": 0.52,
                    "box": (0.03, 0.08, 0.98, 0.43),
                    "color": "amber",
                    "badge_tag": "原則禁放櫃｜安檢 8 項雙欄確認",
                    "zoom_title": "附件 6.5：充填／卸料前安檢（1–8 項）",
                    "check_points": [
                        "原則【禁止放櫃】且司機須全程在場（僅台積回收車及製程需求例外）",
                        "勾選充填或卸料作業，雙欄核對第 1 項接地線【10Ω 以下】與輪檔定位",
                        "確認第 4 項槽車排氣閥／呼吸閥已開啟、標示牌與安全閥完好",
                    ],
                },
                {
                    "weight": 0.48,
                    "box": (0.03, 0.42, 0.98, 0.78),
                    "color": "emerald",
                    "badge_tag": "強制卡控｜作業前主管先簽核",
                    "zoom_title": "清潔度 5 項＋作業前單位主管簽核",
                    "check_points": [
                        "核對出口 Valve 數量、單/雙槽設計、槽內外清潔無殘液與油漬",
                        "★ 紅線：放櫃前須完成駕駛員、現場人員與【單位主管簽核】始可作業",
                        "若司機不配合繳交鑰匙或有任何異常，立即回報主管協助處理",
                    ],
                },
            ],
        },
        {
            "id": "shot08",
            "type": "flow",
            "flow_clips": ["b03_outbound_outro.mp4"],
            "theme": "emerald",
            "chapter": "08｜出貨安全總結、醋酸低溫保溫與地磅放行",
            "form_badge": "WI 5.4 安全紅線 / GAA 保溫 / 四大風險",
            "figure": "fig01_tanker_outbound_flow.png",
            "narration": (
                "最後總複習四項出貨安全與設備紅線："
                "第一，灌裝量必須落在出貨通知單容許誤差內，超過的數量應泵回原儲槽，實際出貨量一律以地磅磅單為準。"
                "第二，氮氣軟管在灌裝前中後若發現異音、變形或龜裂，立刻暫停更換。"
                "第三，冬季特別注意醋酸儲槽保溫：只要中央氣象署預報彰化縣當日溫度低於或等於攝氏十六度，"
                "必須啟動熱水馬達泵浦保溫、記錄蒸氣壓力於儲槽作業日報表，並確認槽溫回升超過十六度。"
                "第四，防範誤接管線、馬達空轉、氮氣過壓與擅離現場四大風險，堅持雙人作業與拆管前洩壓。"
                "確認槽車無洩漏、表單簽核無誤，即可安全指揮槽車開往地磅。第二部出貨與灌裝篇到此圓滿完成！"
            ),
            "card_title": "出貨安全總檢核 4 大紅線（5.4）",
            "card_points": [
                "數量誤差控管：超量泵回原儲槽，實際出貨量以【地磅出貨磅單】為準",
                "軟管防爆檢視：氮氣軟管出現異音 / 變形 / 龜裂，立即暫停更換",
                "★ 醋酸 (GAA) 保溫：彰化預報 16°C 以下啟熱水泵保溫，抄蒸氣壓並確認 > 16°C",
                "杜絕 4 大風險（誤接 / 空轉 / 過壓 / 離場）→ 確認無洩漏再開往地磅",
            ],
        },
    ]


def normalize_industrial_tts(text: str) -> str:
    replacements = {
        "ISO TANK": "I S O Tank",
        "PPE": "P P E",
        "PDA": "P D A",
        "NSB": "N S B",
        "SDS": "S D S",
        "VOC": "V O C",
        "EBR": "E B R",
        "GAA": "G A A",
        "PUMP": "泵浦",
        "Flush": "沖洗",
        "kg/cm²": "公斤每平方公分",
        "Kg/cm²": "公斤每平方公分",
        "10Ω": "十歐姆",
        "1T桶": "一噸桶",
        "100L": "一百公升",
        "200L": "兩百公升",
        "500L": "五百公升",
        "16°C": "攝氏十六度",
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


def draw_rounded_rect(draw: ImageDraw.ImageDraw, xy, radius: int, fill=None, outline=None, width: int = 1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def render_top_bar(canvas: Image.Image, chapter: str, form_badge: str, accent_rgb: Tuple[int, int, int]) -> None:
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(0, 0), (VIDEO_W, 76)], fill=(14, 22, 38))
    draw.rectangle([(0, 74), (VIDEO_W, 78)], fill=accent_rgb)

    draw_rounded_rect(draw, (32, 16, 260, 60), radius=10, fill=accent_rgb)
    draw.text((146, 38), "第2部｜儲槽出貨篇", font=get_font(22, bold=True), fill=(10, 15, 25), anchor="mm")
    draw.text((284, 38), chapter, font=get_font(28, bold=True), fill=COLOR_TEXT_MAIN, anchor="lm")

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

    dimmed = ImageEnhance.Brightness(resized).enhance(0.48)
    bx1_rel, by1_rel, bx2_rel, by2_rel = step["box"]
    rx1, ry1 = max(0, int(dw * bx1_rel)), max(0, int(dh * by1_rel))
    rx2, ry2 = min(dw, int(dw * bx2_rel)), min(dh, int(dh * by2_rel))

    bright_patch = resized.crop((rx1, ry1, rx2, ry2))
    dimmed.paste(bright_patch, (rx1, ry1))
    canvas.paste(dimmed, (ox, oy))

    draw = ImageDraw.Draw(canvas)
    fx1, fy1, fx2, fy2 = ox + rx1, oy + ry1, ox + rx2, oy + ry2
    draw.rectangle((fx1 - 4, fy1 - 4, fx2 + 4, fy2 + 4), outline=(255, 255, 255), width=2)
    draw.rectangle((fx1, fy1, fx2, fy2), outline=hl_color, width=5)

    tag = step.get("badge_tag", "檢點重點")
    f_tag = get_font(20, bold=True)
    tw = int(draw.textlength(tag, font=f_tag)) + 26
    ty = fy1 - 34 if fy1 - 34 > panel_t + 6 else fy1 + 6
    draw_rounded_rect(draw, (fx1, ty, fx1 + tw, ty + 30), radius=6, fill=hl_color)
    draw.text((fx1 + tw // 2, ty + 15), tag, font=f_tag, fill=(12, 18, 28), anchor="mm")

    zm_l, zm_t, zm_r, zm_b = 1088, 96, 1884, 515
    draw_rounded_rect(draw, (zm_l, zm_t, zm_r, zm_b), radius=16, fill=COLOR_CARD_BG, outline=hl_color, width=3)
    draw.rectangle((zm_l + 3, zm_t + 3, zm_r - 3, zm_t + 48), fill=(26, 38, 60))
    draw.text((zm_l + 20, zm_t + 26), f"【放大檢視】{step.get('zoom_title', '')}", font=get_font(22, bold=True), fill=hl_color, anchor="lm")

    sx1, sy1 = max(0, int(sw * bx1_rel)), max(0, int(sh * by1_rel))
    sx2, sy2 = min(sw, int(sw * bx2_rel)), min(sh, int(sh * by2_rel))
    crop_hi = src.crop((sx1, sy1, sx2, sy2))
    cw, ch = crop_hi.size
    box_w, box_h = (zm_r - zm_l - 28), (zm_b - zm_t - 66)
    zscale = min(box_w / max(1, cw), box_h / max(1, ch))
    zw, zh = max(1, int(cw * zscale)), max(1, int(ch * zscale))
    crop_resized = crop_hi.resize((zw, zh), Image.Resampling.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.0, percent=125, threshold=2))
    canvas.paste(crop_resized, (zm_l + 14 + (box_w - zw) // 2, zm_t + 56 + (box_h - zh) // 2))

    ck_l, ck_t, ck_r, ck_b = 1088, 536, 1884, 944
    draw = ImageDraw.Draw(canvas)
    draw_rounded_rect(draw, (ck_l, ck_t, ck_r, ck_b), radius=16, fill=COLOR_CARD_BG, outline=COLOR_BORDER_SUB, width=2)
    header_txt = "● 現場實作 × 檢點重點" if has_pip else "● 現場檢點怎麼做？"
    draw.text((ck_l + 24, ck_t + 30), header_txt, font=get_font(25, bold=True), fill=PALETTE["emerald"], anchor="lm")
    draw.line((ck_l + 20, ck_t + 54, ck_r - 20, ck_t + 54), fill=COLOR_BORDER_SUB, width=2)

    if has_pip:
        px1, py1, px2, py2 = 1108, 608, 1468, 810
        draw.rectangle((px1 - 3, py1 - 3, px2 + 3, py2 + 3), outline=hl_color, width=3)
        draw_rounded_rect(draw, (px1, py2 + 10, px2, py2 + 44), radius=8, fill=(24, 38, 60), outline=hl_color, width=1)
        draw.text(((px1 + px2) // 2, py2 + 27), "LIVE 現場滿配 PPE 實演", font=get_font(18, bold=True), fill=hl_color, anchor="mm")
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
    accent = PALETTE.get(theme_name, PALETTE["cyan"])
    canvas = Image.new("RGB", (VIDEO_W, VIDEO_H), COLOR_BG_DARK)
    render_top_bar(canvas, chapter, form_badge, accent)

    draw = ImageDraw.Draw(canvas)
    pl, pt, pr, pb = 36, 96, 940, 944
    draw_rounded_rect(draw, (pl, pt, pr, pb), radius=16, fill=(248, 250, 252), outline=accent, width=3)
    src = Image.open(fig_path).convert("RGB")
    scale = min((pr - pl - 28) / src.width, (pb - pt - 28) / src.height)
    dw, dh = int(src.width * scale), int(src.height * scale)
    canvas.paste(src.resize((dw, dh), Image.Resampling.LANCZOS), (pl + (pr - pl - dw) // 2, pt + (pb - pt - dh) // 2))

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
    sentences = [s.strip() for s in re.split(r"(?<=[。！？；])", text) if s.strip()]
    if not sentences:
        return [text] * n_chunks
    if len(sentences) <= n_chunks:
        res = sentences[:]
        while len(res) < n_chunks:
            res.append(res[-1])
        return res
    chunks: List[str] = []
    per = len(sentences) / n_chunks
    for i in range(n_chunks):
        s_idx = int(round(i * per))
        e_idx = int(round((i + 1) * per))
        chunks.append("".join(sentences[s_idx:max(s_idx + 1, e_idx)]))
    return chunks


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


def render_mixed_segments_clip(ffmpeg_exe: str, segments: List[dict], audio_path: Path, out_mp4: Path) -> Path:
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
        "-map", "[vout]", "-map", "[aout]",
        "-t", f"{total_dur:.4f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_mp4


def detect_speech_pauses(ffmpeg_exe: str, audio_path: Path, noise_db: str = "-30dB", min_dur: float = 0.22) -> List[float]:
    cmd = [ffmpeg_exe, "-i", str(audio_path), "-af", f"silencedetect=noise={noise_db}:d={min_dur}", "-f", "null", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    starts: List[float] = []
    mids: List[float] = []
    for line in proc.stderr.splitlines():
        m1 = re.search(r"silence_start:\s*([0-9.]+)", line)
        if m1:
            starts.append(float(m1.group(1)))
        m2 = re.search(r"silence_end:\s*([0-9.]+)", line)
        if m2 and starts:
            mids.append((starts.pop(0) + float(m2.group(1))) / 2.0)
    return mids


def compute_speech_aligned_durations(ffmpeg_exe: str, audio_path: Path, total_dur: float, subtitles: List[str]) -> List[float]:
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
        lo = max(cuts[-1] + 2.0, target - 4.5)
        hi = min(total_dur - 2.0 * (n - 1 - i), target + 4.5)
        cands = [p for p in pauses if lo <= p <= hi]
        cuts.append(min(cands, key=lambda p: abs(p - target)) if cands else max(cuts[-1] + 2.0, min(hi, target)))
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

        avail_flows = [FLOW_CLIPS_DIR / fn for fn in s.get("flow_clips", []) if (FLOW_CLIPS_DIR / fn).exists() and (FLOW_CLIPS_DIR / fn).stat().st_size > 50_000]
        post_count = len(s["focus_steps"]) if s["type"] == "form_spotlight" else 2
        total_segs = len(avail_flows) + post_count
        all_subs = split_subtitles(s["narration"], total_segs)
        seg_durs = compute_speech_aligned_durations(ffmpeg_exe, audio_p, dur, all_subs)

        segments: List[dict] = []
        for idx, fp in enumerate(avail_flows):
            hud_p = _make_flow_hud_png(WORK_DIR / f"{sid}_hud{idx+1}.png", s["chapter"], all_subs[idx], accent)
            segments.append({"kind": "flow_full", "mp4": fp, "hud": hud_p, "dur": seg_durs[idx]})

        rem_subs = all_subs[len(avail_flows):]
        rem_durs = seg_durs[len(avail_flows):]

        if s["type"] == "form_spotlight":
            for idx, (st, sub_txt, seg_dur) in enumerate(zip(s["focus_steps"], rem_subs, rem_durs)):
                pip_name = st.get("pip_clip")
                pip_p = (FLOW_CLIPS_DIR / pip_name) if pip_name else None
                has_pip = bool(pip_p and pip_p.exists() and pip_p.stat().st_size > 50_000)
                img = build_spotlight_frame(fig_p, s["chapter"], s["form_badge"], s["theme"], st, sub_txt, has_pip=has_pip)
                img_out = WORK_DIR / f"{sid}_step{idx+1}.png"
                img.save(img_out)
                segments.append({"kind": "still_pip", "img": img_out, "pip": pip_p, "dur": seg_dur} if has_pip else {"kind": "still", "img": img_out, "dur": seg_dur})
        else:
            for idx, (sub_txt, seg_dur) in enumerate(zip(rem_subs, rem_durs)):
                img = build_flow_fallback_frame(fig_p, s["chapter"], s["form_badge"], s["theme"], s["card_title"], s["card_points"], sub_txt)
                img_out = WORK_DIR / f"{sid}_post{idx+1}.png"
                img.save(img_out)
                segments.append({"kind": "still", "img": img_out, "dur": seg_dur})

        dur_str = " / ".join(f"{d:.1f}s" for d in seg_durs)
        print(f"[Render] {sid} ({dur:.1f}s｜段長=[{dur_str}])")
        render_mixed_segments_clip(ffmpeg_exe, segments, audio_p, out_mp4)
        clip_paths.append(out_mp4)

    return clip_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="第 2 部《儲槽出貨與灌裝篇》SOP 電影教學影片生成器")
    parser.add_argument("--export-voice-jobs", action="store_true", help="僅匯出 Colab T4 配音工作單 (JSON)")
    parser.add_argument("--cinema", action="store_true", help="啟用完整電影後製（封面/封底 + xfade + BGM 閃避）")
    parser.add_argument("--speed", type=float, default=1.12, help="edge-tts 旁白倍速（預設 1.12）")
    parser.add_argument("--gemini-tts", action="store_true", help="改用 Gemini TTS 合成旁白")
    parser.add_argument("--audio-dir", type=str, default="", help="指定外部音檔目錄（如 audio_myvoice）")
    parser.add_argument("--out-video", type=str, default="", help="指定輸出影片路徑")
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
            project_name="儲槽進出貨SOP_第2部_出貨與灌裝篇",
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
            title="儲槽進出貨作業方法｜第 2 部：出貨與灌裝篇",
            subtitle="C50110-INV-02-01 (v3.1)｜附件 6.2 / 6.3 / 6.5 表單檢點實戰教學",
            cover_img=cover_img if cover_img.exists() else None,
            duration=3.0,
            fps=FPS,
        )
        render_ending_clip(
            ffmpeg_exe=ffmpeg_exe,
            out_mp4=ending_mp4,
            title="精準灌裝・零混料・安全放行",
            subtitle="請確認附件 6.2 / 6.3 / 6.5 簽核完整，並依地磅磅單出貨",
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
    if not bgm_path.exists():
        alt_bgm = BASE_DIR / "tank_inbound_sop" / "bgm.mp3"
        if alt_bgm.exists():
            bgm_path = alt_bgm
    if args.cinema and bgm_path.exists():
        print(f"[BGM] 偵測到 {bgm_path.name}，套用語音閃避混音...")
        mix_bgm_with_ducking(ffmpeg_exe, merged_no_bgm, bgm_path, FINAL_VIDEO_PATH, bgm_vol=0.16)
    else:
        shutil.copy2(merged_no_bgm, FINAL_VIDEO_PATH)

    total_dur = probe_duration(ffmpeg_exe, FINAL_VIDEO_PATH)
    size_mb = FINAL_VIDEO_PATH.stat().st_size / (1024 * 1024)
    print(f"\n✅ 第 2 部成片完成：{FINAL_VIDEO_PATH}")
    print(f"   片長：{total_dur:.1f} 秒（{total_dur/60:.1f} 分鐘）｜大小：{size_mb:.1f} MB")


if __name__ == "__main__":
    main()
