from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "操作影片_輸出"
FRAMES = OUT / "frames"
AUDIO = OUT / "voice"
WIDTH, HEIGHT = 1280, 720
FONT_REGULAR = r"C:\Windows\Fonts\msjh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msjhbd.ttc"
PWSH = r"C:\Users\C606\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe"
NAVY = "#173554"
BLUE = "#087cf0"
GREEN = "#29984b"
AMBER = "#e6a400"
GRAY = "#66768a"

scenes = [
    ("01｜回收液入料記錄 App", "這支影片介紹回收液入料記錄 App 的基本操作。每筆作業分成入料前與入料完成兩個階段，分別留下液位與車輛照片，方便後續查詢與追蹤。影片中的車號與日期為示範資料。", "intro", "before"),
    ("02｜填寫入料前資料", "在入料前頁面，先確認日期，再輸入車牌號碼或儲槽號。接著拍攝入料前的儲槽液位照片，以及能辨識車輛的照片。車號和兩張照片都是必填，資料齊全後再按儲存。", "before", "before"),
    ("03｜儲存與雲端同步", "按下儲存後，系統會先在裝置上保存紀錄並處理照片，再自動嘗試同步到雲端。同步完成時，頁面會顯示全部已同步雲端。請留意畫面上的同步狀態，確認資料已送出。", "saved", "before"),
    ("04｜查看待入料車輛", "切換到入料完成頁，系統會列出等待入料的車輛。找到正確車號後，按選擇完成入料，確認畫面顯示的車號與作業對象一致，再進入下一步。", "pending", "after"),
    ("05｜完成入料記錄", "入料完成後，拍攝入料後的儲槽液位照片，再按完成入料記錄。這張照片為必填。系統會記下完成時間，並把紀錄狀態更新為已完成；若前後時間可計算，也會保存作業歷時。", "after", "after"),
    ("06｜查詢歷史紀錄", "需要追查時，開啟查詢歷史。查詢頁需先通過授權，再輸入車號或日期搜尋。結果可查看待入料或已完成狀態、前後時間、作業歷時，以及已保存的液位和車輛照片。請只使用授權帳號查閱。", "history", "query"),
    ("07｜離線時先完成現場記錄", "若現場網路中斷，頁面會顯示離線提示。仍可先在裝置完成入料前或入料後記錄，資料會暫存在本機；網路恢復或重新開啟 App 時，系統會自動重試同步。", "offline", "before"),
    ("08｜檢查同步狀態", "若同步按鈕顯示仍有未同步資料，點開可檢視待同步項目，並選擇立即手動重試。請先確認網路，再確認狀態回到全部已同步雲端。清除本機暫存會移除尚未送出的資料，操作前務必確認。", "sync", "before"),
    ("09｜拍照與資料核對", "拍照時，請讓液位刻度清楚入鏡，車輛照片也要能辨認作業車輛。儲存前再次核對日期、車號或儲槽號；完成後確認入料前、入料後照片都連到正確紀錄。", "quality", "after"),
    ("10｜操作流程總結", "操作順序是：填寫入料前資料並拍攝兩張照片、儲存並確認同步、選擇待入料車輛、拍攝入料後液位照片並完成記錄，最後依授權需要查詢歷史。謝謝觀看。", "summary", "before"),
]


def ft(size: int, bold: bool = False):
    path = FONT_BOLD if bold and Path(FONT_BOLD).exists() else FONT_REGULAR
    return ImageFont.truetype(path, size)


def rounded(draw, box, radius=10, fill="white", outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap(draw, text, f, max_width):
    lines, line = [], ""
    for ch in text:
        if line and draw.textbbox((0, 0), line + ch, font=f)[2] > max_width:
            lines.append(line)
            line = ch
        else:
            line += ch
    if line:
        lines.append(line)
    return lines


def button(draw, x, y, w, text, color=GREEN, h=42):
    rounded(draw, (x, y, x + w, y + h), 7, color)
    draw.text((x + 14, y + 9), text, font=ft(17, True), fill="white")


def field(draw, x, y, w, label, value, hint=None):
    rounded(draw, (x, y, x + w, y + 68), 9, "white", "#d6dee8")
    draw.text((x + 18, y + 11), label, font=ft(17, True), fill="#313d4c")
    rounded(draw, (x + 16, y + 36, x + w - 16, y + 61), 5, "#fbfcfe", "#cbd3dd")
    draw.text((x + 26, y + 38), value, font=ft(15), fill="#344457" if value else "#96a1ad")


def photo_field(draw, x, y, w, title, filename=None):
    rounded(draw, (x, y, x + w, y + 68), 9, "white", "#d6dee8")
    draw.text((x + 18, y + 8), title, font=ft(16, True), fill="#313d4c")
    rounded(draw, (x + 16, y + 34, x + w - 16, y + 60), 5, "#f8fafc", "#b9cbe0")
    if filename:
        draw.text((x + 28, y + 38), f"已選取：{filename}", font=ft(14), fill=GREEN)
    else:
        draw.text((x + 28, y + 38), "選擇檔案／拍攝照片", font=ft(14), fill=BLUE)


def app_shell(draw, active="before", status="✅ 全部已同步雲端", offline=False):
    # Browser-like window and app chrome, based on the real web app layout.
    rounded(draw, (46, 92, 1234, 548), 12, "white", "#d5dde7", 2)
    draw.rectangle((48, 94, 1232, 151), fill=BLUE)
    draw.text((78, 107), "入料記錄 App", font=ft(25, True), fill="white")
    status_color = AMBER if offline or "未同步" in status else GREEN
    pill_w = 214 if len(status) < 12 else 260
    rounded(draw, (1200 - pill_w, 105, 1205, 139), 7, status_color)
    draw.text((1212 - pill_w, 111), status, font=ft(14, True), fill="#17212f" if status_color == AMBER else "white")
    if offline:
        draw.rectangle((48, 151, 1232, 181), fill="#c93636")
        draw.text((80, 157), "目前離線模式，操作將暫存於手機中", font=ft(14, True), fill="white")
        nav_y = 181
    else:
        nav_y = 151
    navs = [("before", "入料前"), ("after", "入料完成！"), ("query", "查詢歷史")]
    for i, (key, label) in enumerate(navs):
        x = 48 + i * 394
        draw.rectangle((x, nav_y, x + 394, nav_y + 48), fill="white")
        draw.text((x + 154, nav_y + 13), label, font=ft(16, key == active), fill=BLUE if key == active else "#596575")
        if key == active:
            draw.rectangle((x, nav_y + 45, x + 394, nav_y + 48), fill=BLUE)
    return nav_y + 56


def draw_scene(scene, number):
    title, narration, kind, active = scene
    im = Image.new("RGB", (WIDTH, HEIGHT), "#eef2f7")
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, WIDTH, 72), fill=NAVY)
    d.text((46, 18), "回收液入料記錄 App｜操作教學", font=ft(26, True), fill="white")
    d.text((1040, 26), f"{number:02d} / 10", font=ft(16), fill="#d8e6f3")
    current_status = "離線暫存中" if kind == "offline" else ("仍有 1 筆未同步" if kind == "sync" else "全部已同步雲端")
    y = app_shell(d, active=active, status=current_status, offline=kind == "offline")

    if kind in ("intro", "before", "saved", "offline", "sync"):
        step = 68 if kind == "offline" else 74
        field(d, 72, y + 0, 1136, "日期", "2026/10/13")
        field(d, 72, y + step, 1136, "車號\儲槽號", "TEST-001 / T-01")
        photo_field(d, 72, y + step * 2, 1136, "入料前 - 儲槽液位照片", "液位照_示範.jpg" if kind == "saved" else None)
        photo_field(d, 72, y + step * 3, 1136, "入料前 - 車輛照片", "車輛照_示範.jpg" if kind == "saved" else None)
        button(d, 72, y + step * 4, 1136, "儲存", GREEN, 36)
    elif kind == "pending":
        rounded(d, (72, y + 7, 1208, y + 89), 9, "white", "#d6dee8")
        d.text((94, y + 18), "車號：TEST-001 / T-01", font=ft(19, True), fill="#28384a")
        d.text((94, y + 49), "入料前時間：2026/10/13 09:20", font=ft(15), fill=GRAY)
        button(d, 890, y + 32, 280, "選擇完成入料", BLUE, 42)
        d.text((79, y + 112), "先核對車號，再選取正確紀錄。", font=ft(17), fill=GRAY)
    elif kind == "after":
        rounded(d, (72, y + 3, 1208, y + 61), 9, "#f1f3f5", "#d6dee8")
        d.text((94, y + 17), "返回列表", font=ft(15, True), fill=GRAY)
        d.text((96, y + 73), "處理中：TEST-001 / T-01", font=ft(20, True), fill="#28384a")
        photo_field(d, 72, y + 113, 1136, "入料後 - 儲槽液位照片", "液位照_完成示範.jpg")
        button(d, 72, y + 221, 1136, "完成入料記錄", GREEN, 46)
        rounded(d, (72, y + 285, 1208, y + 337), 8, "#e8f5eb", "#a1d1ad")
        d.text((92, y + 299), "完成後記下時間、更新狀態，並觸發同步。", font=ft(16), fill=GREEN)
    elif kind == "history":
        rounded(d, (275, y + 24, 1005, y + 300), 12, "white", "#d6dee8", 2)
        d.text((354, y + 53), "查詢功能已鎖定", font=ft(25, True), fill="#26364a")
        d.text((354, y + 102), "請輸入授權密碼方可查閱歷史紀錄", font=ft(16), fill=GRAY)
        rounded(d, (354, y + 148, 926, y + 198), 8, "#fbfcfe", "#cbd3dd")
        d.text((377, y + 160), "••••••••", font=ft(18), fill="#8390a0")
        button(d, 354, y + 218, 572, "解鎖進入", BLUE, 45)
        d.text((316, y + 331), "授權後可依車號或日期搜尋，並查看狀態與照片。", font=ft(17), fill=GRAY)
    elif kind == "quality":
        cards = [("入料前", "儲槽液位照片", "確認液位刻度清晰"), ("入料前", "車輛照片", "確認車輛可辨識"), ("入料後", "儲槽液位照片", "確認與車號紀錄相符")]
        for i, (stage, name, tip) in enumerate(cards):
            x = 72 + i * 380
            rounded(d, (x, y + 15, x + 350, y + 270), 12, "white", "#d6dee8", 2)
            rounded(d, (x + 20, y + 36, x + 330, y + 166), 8, "#edf3f8", "#cdd8e4")
            d.text((x + 102, y + 84), "照片示意", font=ft(20, True), fill="#8091a5")
            d.text((x + 20, y + 183), stage + "｜" + name, font=ft(16, True), fill="#29384b")
            d.text((x + 20, y + 218), tip, font=ft(15), fill=GRAY)
    elif kind == "summary":
        steps = [("1", "入料前", "日期、車號、兩張照片"), ("2", "同步", "確認雲端同步狀態"), ("3", "入料後", "選車、拍照、完成記錄"), ("4", "查詢", "授權後搜尋歷史")]
        for i, (n, label, body) in enumerate(steps):
            x = 76 + i * 290
            rounded(d, (x, y + 50, x + 260, y + 196), 12, "white", "#d6dee8", 2)
            d.ellipse((x + 18, y + 66, x + 58, y + 106), fill=BLUE)
            d.text((x + 32, y + 73), n, font=ft(17, True), fill="white")
            d.text((x + 72, y + 69), label, font=ft(19, True), fill="#25364a")
            d.text((x + 18, y + 128), body, font=ft(15), fill=GRAY)

    # Clear disclaimer: scenes are recreated, and the example record is fictitious.
    d.text((WIDTH - 366, 565), "介面示意｜車號為虛構範例", font=ft(13), fill="#7c8898")
    d.text((48, 582), title, font=ft(24, True), fill=NAVY)
    d.text((49, 615), f"第 {number:02d} 段 / 10 段", font=ft(14), fill=GRAY)
    for i, line in enumerate(wrap(d, narration, ft(18), 1170)[:3]):
        d.text((48, 641 + i * 24), line, font=ft(17), fill="#26364a")
    return im


async def make_audio(path: Path, text: str):
    # Use the installed zh-TW female Windows voice locally; no text is sent to an online TTS service.
    text_path = path.with_suffix(".txt")
    if path.exists() and text_path.exists() and text_path.read_text(encoding="utf-8") == text:
        return
    text_path.write_text(text, encoding="utf-8")
    ps_path = AUDIO / "synthesize_voice.ps1"
    if not ps_path.exists():
        ps_path.write_text(
            "param([string]$TextPath, [string]$WavePath)\n"
            "Add-Type -AssemblyName System.Speech\n"
            "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
            "$synth.SelectVoice('Microsoft Hanhan')\n"
            "$synth.Rate = 0\n"
            "$synth.Volume = 100\n"
            "$synth.SetOutputToWaveFile($WavePath)\n"
            "$text = [System.IO.File]::ReadAllText($TextPath, [System.Text.Encoding]::UTF8)\n"
            "$synth.Speak($text)\n"
            "$synth.Dispose()\n",
            encoding="utf-8",
        )
    subprocess.run([PWSH, "-NoProfile", "-File", str(ps_path), str(text_path), str(path)], check=True)


def run(command):
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    AUDIO.mkdir(parents=True, exist_ok=True)
    clips = []
    for idx, scene in enumerate(scenes, 1):
        frame = FRAMES / f"scene_{idx:02d}.png"
        voice = AUDIO / f"scene_{idx:02d}.wav"
        clip = OUT / f"clip_{idx:02d}.mp4"
        draw_scene(scene, idx).save(frame)
        await make_audio(voice, scene[1])
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(voice)], capture_output=True, text=True, check=True)
        duration = float(probe.stdout.strip()) + 0.7
        run(["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(frame), "-i", str(voice), "-t", f"{duration:.3f}",
             "-vf", "format=yuv420p", "-af", "atempo=1.25", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", str(clip)])
        clips.append(clip)
    concat = OUT / "concat.txt"
    concat.write_text("\n".join(f"file '{p.as_posix()}'" for p in clips), encoding="utf-8")
    video = OUT / "回收液入料記錄App_操作教學.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(video)])
    (OUT / "旁白稿.txt").write_text("\n\n".join(f"{s[0]}\n{s[1]}" for s in scenes), encoding="utf-8")
    print(video)
    print("10 scenes | Microsoft Hanhan | zh-TW female | 1.25x")


if __name__ == "__main__":
    asyncio.run(main())
