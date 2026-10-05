from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / ".video_demo" / "frames"
OUT = ROOT / "操作影片_多情境"
SLIDES = OUT / "slides"
OUT.mkdir(parents=True, exist_ok=True)
SLIDES.mkdir(parents=True, exist_ok=True)

W, H = 1280, 720
FONT_PATH = r"C:\Windows\Fonts\msjh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msjhbd.ttc"


def font(size: int, bold: bool = False):
    p = FONT_BOLD if bold and Path(FONT_BOLD).exists() else FONT_PATH
    return ImageFont.truetype(p, size)


def text(draw, xy, value, size=20, fill="#0f172a", bold=False):
    draw.text(xy, value, font=font(size, bold), fill=fill)


def pill(draw, xy, label, bg, fg):
    x, y = xy
    f = font(15, True)
    box = draw.textbbox((0, 0), label, font=f)
    width = box[2] - box[0] + 28
    draw.rounded_rectangle((x, y, x + width, y + 32), 16, fill=bg)
    draw.text((x + 14, y + 5), label, font=f, fill=fg)


def get_source(filename: str) -> Image.Image:
    path = SOURCE / filename
    if not path.exists():
        raise FileNotFoundError(path)
    return Image.open(path).convert("RGB")


def make_updated_schedule_frame(filename: str) -> Image.Image:
    im = get_source(filename)
    d = ImageDraw.Draw(im)
    # Mirror the additional T100 filters visible on the currently deployed page
    # (today, yesterday, pending, resample, and all) while keeping the old
    # local PWA screenshot as a privacy-safe synthetic-data background.
    d.rectangle((180, 153, 762, 189), fill="#f0fdf4")
    labels = ["今日排程", "昨天排程", "待送樣放櫃", "取樣重送", "顯示全部"]
    widths = [96, 96, 112, 96, 96]
    x, y = 187, 155
    for i, (label, width) in enumerate(zip(labels, widths)):
        fill = "#16a34a" if i == 0 else "#ffffff"
        outline = "#16a34a" if i == 0 else "#86c79b"
        fg = "#ffffff" if i == 0 else "#166534"
        d.rounded_rectangle((x, y, x + width, y + 29), 7, fill=fill, outline=outline, width=1)
        f = font(10, True)
        bbox = d.textbbox((0, 0), label, font=f)
        tx = x + (width - (bbox[2] - bbox[0])) // 2
        d.text((tx, y + 8), label, font=f, fill=fg)
        x += width + 5
    return im


def make_overdue() -> Image.Image:
    im = get_source("06-pending-visible.png")
    d = ImageDraw.Draw(im)
    # Demonstration data: show one pending item beyond the two-hour SLA.
    d.rounded_rectangle((226, 109, 422, 196), 12, fill="#fff")
    d.rounded_rectangle((226, 109, 232, 196), 8, fill="#ef4444")
    text(d, (246, 119), "1", 34, "#ef4444", True)
    text(d, (247, 159), "已逾期 (>2小時)", 13, "#64748b")
    d.rectangle((455, 445, 590, 496), fill="#fff")
    text(d, (458, 448), "送樣 09/25 13:59", 13, "#64748b")
    d.rounded_rectangle((456, 466, 587, 491), 6, fill="#fee2e2")
    text(d, (463, 469), "⚠ 等候 3.3 小時", 12, "#b91c1c", True)
    return im


def make_failed_row() -> Image.Image:
    im = get_source("08-completed-visible.png")
    d = ImageDraw.Draw(im)
    # Replace only the sample's synthetic result cells in the screenshot.
    d.rounded_rectangle((497, 562, 538, 585), 5, fill="#fee2e2")
    text(d, (502, 564), "FAIL", 13, "#b91c1c", True)
    d.rectangle((659, 556, 865, 610), fill="#fff")
    text(d, (669, 568), "判定備註：檢測值超出規格", 12, "#b91c1c")
    return im


def make_resample_board() -> Image.Image:
    im = get_source("06-pending-visible.png")
    d = ImageDraw.Draw(im)
    # Clearly mark the synthetic second-round sample for training.
    d.rounded_rectangle((92, 429, 151, 451), 5, fill="#ffedd5")
    text(d, (99, 431), "第 2 次", 11, "#c2410c", True)
    d.rounded_rectangle((266, 425, 345, 449), 5, fill="#ffedd5")
    text(d, (273, 427), "取樣重送", 11, "#c2410c", True)
    return im


def make_judge_modal() -> Image.Image:
    im = make_failed_row().convert("RGBA")
    shade = Image.new("RGBA", im.size, (15, 23, 42, 150))
    im = Image.alpha_composite(im, shade)
    d = ImageDraw.Draw(im)
    card = (180, 105, 692, 526)
    d.rounded_rectangle(card, 18, fill="#fff", outline="#e2e8f0", width=2)
    text(d, (208, 127), "不合格退回／建立重送", 23, "#111827", True)
    text(d, (208, 170), "系統將保留本次判定，並新增下一輪待檢驗紀錄。", 13, "#64748b")
    text(d, (208, 221), "退回原因 / 不合格說明", 15, "#334155", True)
    d.rounded_rectangle((208, 248, 663, 317), 7, fill="#f8fafc", outline="#cbd5e1")
    text(d, (223, 264), "水分檢測值超出內控規格，請重新取樣。", 15, "#334155")
    text(d, (208, 344), "品管授權 PIN", 15, "#334155", True)
    d.rounded_rectangle((208, 372, 663, 421), 7, fill="#fff", outline="#cbd5e1")
    text(d, (382, 380), "••••", 23, "#334155", True)
    d.rounded_rectangle((208, 451, 510, 495), 8, fill="#f97316")
    text(d, (239, 461), "確認退回並建立重送記錄", 14, "#fff", True)
    return im.convert("RGB")


def make_alert_card() -> Image.Image:
    im = make_overdue().convert("RGBA")
    shade = Image.new("RGBA", im.size, (15, 23, 42, 115))
    im = Image.alpha_composite(im, shade)
    d = ImageDraw.Draw(im)
    card = (210, 138, 663, 493)
    d.rounded_rectangle(card, 16, fill="#fff", outline="#fecaca", width=3)
    d.rounded_rectangle((210, 138, 663, 197), 16, fill="#b91c1c")
    d.rectangle((210, 179, 663, 197), fill="#b91c1c")
    text(d, (239, 154), "QC 檢驗逾時提醒", 22, "#fff", True)
    text(d, (240, 224), "送樣單位　資材課（示範）", 16, "#334155")
    text(d, (240, 262), "品名　　　DEMO-IPA", 16, "#334155")
    text(d, (240, 300), "槽號 / 車牌 TK-DEMO-01 / DEMO-TRUCK-01", 14, "#334155")
    text(d, (240, 338), "等待時間　3.3 小時（超過 2 小時）", 15, "#b91c1c", True)
    d.rounded_rectangle((239, 394, 632, 456), 8, fill="#fef2f2")
    text(d, (256, 406), "通知目標：品管主管 + 送樣單位頻道", 14, "#7f1d1d", True)
    text(d, (256, 430), "影片展示通知卡片示意；未送出 Teams 訊息。", 11, "#7f1d1d")
    return im.convert("RGB")


MOCKS = {
    "overdue.png": make_overdue,
    "failed-row.png": make_failed_row,
    "resample-board.png": make_resample_board,
    "judge-resample-modal.png": make_judge_modal,
    "overdue-alert-card.png": make_alert_card,
}


def panel_slide(outpath: Path, shot: Image.Image | None, chapter: str, heading: str,
                steps: list[str], active: int, note: str, intro: bool = False):
    im = Image.new("RGB", (W, H), "#0b1220")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((24, 22, 1256, 698), 22, fill="#f8fafc")
    d.rounded_rectangle((24, 22, 1256, 84), 20, fill="#0f172a")
    d.rectangle((24, 62, 1256, 84), fill="#0f172a")
    text(d, (49, 36), "QC 進出貨樣品登錄", 23, "#f8fafc", True)
    text(d, (333, 41), "多情境操作教學", 16, "#cbd5e1")
    pill(d, (1028, 36), "本機示範｜合成資料", "#164e63", "#cffafe")

    # Screen capture area
    d.rounded_rectangle((42, 102, 883, 655), 15, fill="#fff", outline="#cbd5e1", width=2)
    if shot is not None:
        maxw, maxh = 815, 529
        scale = min(maxw / shot.width, maxh / shot.height)
        sw, sh = round(shot.width * scale), round(shot.height * scale)
        view = shot.resize((sw, sh), Image.Resampling.LANCZOS)
        x, y = 462 - sw // 2, 378 - sh // 2
        im.paste(view, (x, y))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((x - 2, y - 2, x + sw + 1, y + sh + 1), 7, outline="#dbeafe", width=2)
    else:
        text(d, (98, 237), "鴻勝化學 QC 檢驗即時看板系統", 31, "#0f172a", True)
        text(d, (98, 295), "多情境操作影片", 27, "#2563eb", True)
        d.rounded_rectangle((98, 365, 796, 492), 16, fill="#eff6ff")
        text(d, (130, 390), "排程匯入　→　樣品送驗　→　QC 判定", 22, "#1e3a8a", True)
        text(d, (130, 439), "含合格放行、不合格重送、逾時追蹤等情境", 16, "#334155")
        text(d, (99, 535), "畫面與欄位以 2026/09/30 本機 PWA 示範版為基礎", 14, "#64748b")

    # Instruction panel
    d.rounded_rectangle((900, 102, 1238, 655), 15, fill="#fff", outline="#cbd5e1", width=2)
    pill(d, (920, 123), chapter, "#dbeafe", "#1d4ed8")
    heading_size = 22
    while heading_size > 15 and d.textbbox((0, 0), heading, font=font(heading_size, True))[2] > 298:
        heading_size -= 1
    text(d, (920, 171), heading, heading_size, "#0f172a", True)
    d.line((920, 214, 1217, 214), fill="#e2e8f0", width=2)
    y = 232
    for i, line in enumerate(steps):
        bg = "#eff6ff" if i == active else "#f8fafc"
        fg = "#1d4ed8" if i == active else "#475569"
        d.rounded_rectangle((918, y, 1218, y + 66), 10, fill=bg)
        d.ellipse((930, y + 16, 962, y + 48), fill="#2563eb" if i == active else "#cbd5e1")
        b = d.textbbox((0, 0), str(i + 1), font=font(15, True))
        d.text((946 - (b[2] - b[0]) / 2, y + 21), str(i + 1), font=font(15, True), fill="#fff")
        step_font = font(13, i == active)
        words, line_part = [], ""
        for char in line:
            candidate = line_part + char
            if line_part and d.textbbox((0, 0), candidate, font=step_font)[2] > 222:
                words.append(line_part)
                line_part = char
            else:
                line_part = candidate
        if line_part:
            words.append(line_part)
        for li, part in enumerate(words[:2]):
            text(d, (973, y + (15 if len(words) > 1 else 23) + li * 19), part, 13, fg, i == active)
        y += 74
    d.rounded_rectangle((918, 548, 1218, 631), 10, fill="#f1f5f9")
    text(d, (933, 557), "本段重點", 13, "#475569", True)
    for j, ln in enumerate(note.split("\n")):
        text(d, (933, 579 + j * 21), ln, 12, "#334155")
    text(d, (50, 668), "示範畫面及資料均為合成內容；雲端 API 已隔離，影片不會操作正式紀錄。", 12, "#64748b")
    im.save(outpath, optimize=True)


def ffmpeg_video(name: str, frames: list[Path], seconds: float = 4.4) -> Path:
    output = OUT / name
    args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    for frame in frames:
        args += ["-loop", "1", "-t", str(seconds), "-i", str(frame)]
    filters = []
    n = len(frames)
    for i in range(n):
        filters.append(f"[{i}:v]scale={W}:{H},fps=30,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[v{i}]")
    last = "v0"
    overlap = 0.30
    for i in range(1, n):
        nxt = "out" if i == n - 1 else f"x{i}"
        offset = seconds * i - overlap * i
        filters.append(f"[{last}][v{i}]xfade=transition=fade:duration={overlap}:offset={offset:.2f}[{nxt}]")
        last = nxt
    args += ["-filter_complex", ";".join(filters), "-map", f"[{last}]", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-movflags", "+faststart", str(output)]
    subprocess.run(args, check=True)
    return output


def main():
    for name, factory in MOCKS.items():
        factory().save(SLIDES / name, optimize=True)

    scenarios = [
        ("01_排程匯入與送樣.mp4", "01｜排程與送樣", "匯入排程 → 自動帶入 → 提交送樣",
         [
             ("01-initial.png", ["開啟 QC 看板並選擇日期", "使用今日／昨日快速篩選", "可看待送樣、取樣重送或全部"], 0, "新版排程列提供五種快速篩選\n目前畫面及資料皆為合成示範"),
             ("02-schedule-imported.png", ["按「匯入最新 T100 排程 Excel」", "確認排程已載入", "使用快速篩選找到車次"], 0, "Excel 僅使用影片合成檔\n匯入不會同步至正式雲端"),
             ("03-schedule-selected.png", ["選擇一筆待送樣車次", "核對品名、槽號、車牌", "確認動向與等級"], 1, "選取車次會帶入排程欄位\n提交前仍要檢查資料"),
             ("04-sample-form-ready.png", ["確認自動帶入的欄位", "選送樣單位與人員", "檢查必填欄位"], 1, "單號、品名、槽號及車牌\n請依現場資訊核對"),
             ("05-sample-pending.png", ["點「確認提交送樣」", "確認表單清空／成功提示", "看板出現待驗樣品"], 2, "送樣後建立待驗紀錄\n系統依單位分流通知"),
             ("06-pending-visible.png", ["在待檢驗看板確認新紀錄", "可列印送樣標籤", "後續由 QC 人員判定"], 2, "本段示範 sample：DEMO-IPA\n車次與人名皆為合成內容"),
         ]),
        ("02_QC合格判定與通知.mp4", "02｜合格判定", "品管授權 → PASS → 通知預覽",
         [
             ("06-pending-visible.png", ["找到待檢驗樣品", "按該筆「判定」", "核對樣品與送樣單位"], 0, "判定前先核對單號、品名\n及槽號／車牌"),
             ("07-judge-preview.png", ["選 PASS（合格放行）", "填檢驗備註", "輸入品管授權並確認"], 1, "Teams 卡片為本機預覽畫面\n影片不會實際推播"),
             ("08-completed-visible.png", ["確認資料移至已檢驗完成", "核對 PASS 與判定備註", "查詢歷史紀錄追蹤"], 2, "正式環境通知目標依系統設定\n示範時已停用外部發送"),
         ]),
        ("03_QC不合格退回與重送.mp4", "03｜不合格與重送", "FAIL 判定 → 退回 → 建立下一輪",
         [
             ("06-pending-visible.png", ["在待驗清單開啟判定", "選 FAIL（不合格）", "填寫檢驗異常說明"], 1, "示範原因：水分檢測值\n超出內控規格"),
             ("failed-row.png", ["確認 FAIL 與判定備註", "按「退回重新送樣」", "填退回原因並輸入品管 PIN"], 1, "FAIL 後可從完成列啟動\n「退回重新送樣」"),
             ("judge-resample-modal.png", ["確認退回原因正確", "送出「建立重送記錄」", "系統產生下一輪待驗記錄"], 1, "依目前程式流程：原紀錄標記退回\n並建立新一輪 pending 記錄"),
             ("resample-board.png", ["查看新一輪待檢樣品", "確認輪次與送樣資訊", "新樣品完成後再次判定"], 2, "重送記錄沿用原樣品關聯\n送樣歷程可查各輪結果"),
         ]),
        ("04_逾時預警與處理.mp4", "04｜逾時預警", "超過 2 小時 → 看板提醒 → 優先處理",
         [
             ("06-pending-visible.png", ["查看待驗件數與等候時間", "持續追蹤未判定樣品", "逾時門檻為 2 小時"], 0, "畫面展示看板的待驗／逾期計數\n時間為示範情境"),
             ("overdue.png", ["逾期樣品以紅色提醒", "核對樣品與送樣單位", "安排優先檢驗"], 1, "等待超過 2 小時會標示逾期\n前端看板可視覺辨識"),
             ("overdue-alert-card.png", ["系統定時巡檢逾時樣品", "Teams 告警定位相關單位", "完成檢驗後更新判定"], 1, "專案文件描述：每 10 分鐘巡檢\n此卡片是示意，未實際傳送"),
         ]),
    ]

    videos = []
    all_frames = []
    for si, (filename, chapter, title, entries) in enumerate(scenarios, start=1):
        paths = []
        intro = SLIDES / f"clip{si:02d}-intro.png"
        panel_slide(intro, None, chapter, title,
                    ["本機示範｜合成資料", "依序展示實際作業節點", "以目前 PWA 版流程編排"], 0,
                    "雲端連線及 Teams 實際發送\n已隔離；僅示範操作概念")
        paths.append(intro)
        all_frames.append(intro)
        for ei, (src, steps, active, note) in enumerate(entries, start=1):
            if src in MOCKS:
                shot = Image.open(SLIDES / src).convert("RGB")
            elif si == 1 and src.startswith(("01-", "02-", "03-", "04-", "05-")):
                shot = make_updated_schedule_frame(src)
            else:
                shot = get_source(src)
            slide = SLIDES / f"clip{si:02d}-step{ei:02d}.png"
            panel_slide(slide, shot, chapter, title, steps, active, note)
            paths.append(slide)
            all_frames.append(slide)
        video = ffmpeg_video(filename, paths, 4.3)
        videos.append(video)
        print(f"created {video} ({video.stat().st_size:,} bytes)")

    # Join chapter videos without re-encoding; all clips use identical H.264 settings.
    list_path = OUT / "chapters.txt"
    list_path.write_text("\n".join(f"file '{p.name}'" for p in videos) + "\n", encoding="utf-8")
    combined = OUT / "QC_多情境操作影片_合輯.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path), "-c", "copy", "-movflags", "+faststart", str(combined)], check=True)
    list_path.unlink(missing_ok=True)
    print(f"created {combined} ({combined.stat().st_size:,} bytes)")

    readme = """# QC 多情境操作影片\n\n影片依本機 PWA 專案畫面與目前部署頁（2026/10/03 可見之排程快速篩選）編排，示範資料皆為合成資料。正式版可能因系統更新、權限與設定而略有差異。影片沒有連線正式雲端 API，也沒有實際送出 Teams 訊息。\n\n## 影片\n\n- `QC_多情境操作影片_合輯.mp4`：四種情境合輯\n- `01_排程匯入與送樣.mp4`：匯入 T100 Excel、日期快速篩選、選擇車次、自動帶入、提交送樣\n- `02_QC合格判定與通知.mp4`：PASS 判定、授權與通知卡片預覽\n- `03_QC不合格退回與重送.mp4`：FAIL 判定、退回原因及下一輪送樣紀錄\n- `04_逾時預警與處理.mp4`：超過 2 小時提醒與告警處理\n\n影片右側列有每一步操作提示；畫面下方標示示範資料與隔離狀態。`slides/` 內為影片用逐格圖片；可用於後續調整。\n"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
