"""
《Peace and Love》電影級 1080p MV 自動組裝器
=============================================
功能：
1. 讀取 peace_love_mv/storyboard.json 與原曲 peace_love_mv/audio/peace_and_love.mp3 (203.16s)
2. 智慧雙軌選源：
   - 若 flow_clips/sXX_flow.mp4 存在 (>50KB) → 自動採用 Google Flow 真實 AI 影片，精準對齊該鏡秒數並升頻 1080p
   - 若尚未下載 Flow 影片 → 自動以 keyframes/sXX.png 搭配流暢 1080p 電影運鏡 (Ken Burns) 補位，隨時可預覽完整 3:23 MV
3. 自動產生電影質感 .ass 同步歌詞字幕（含淡入淡出）並壓印
4. 輸出完整 1920x1080 24fps H.264 + AAC 256k MV 成品與中英文分鏡總表
"""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

MV_DIR = Path(__file__).resolve().parent
STORYBOARD_PATH = MV_DIR / "storyboard.json"
CLIPS_DIR = MV_DIR / "clips"
ASS_PATH = MV_DIR / "peace_and_love.ass"
SCRIPT_MD_PATH = MV_DIR / "Peace_and_Love_MV分鏡與Flow提示詞總表.md"
OUT_VIDEO = MV_DIR / "Peace_and_Love_MV_1080p.mp4"

W, H, FPS = 1920, 1080, 24


def find_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        winget_dir = Path(local_app) / "Microsoft" / "WinGet" / "Packages"
        if winget_dir.exists():
            for p in winget_dir.rglob("ffmpeg.exe"):
                return str(p)
    raise FileNotFoundError("找不到 ffmpeg，請先安裝 FFmpeg。")


def find_ffprobe(ffmpeg_exe: str) -> str:
    cand = Path(ffmpeg_exe).with_name("ffprobe.exe")
    if cand.exists():
        return str(cand)
    found = shutil.which("ffprobe")
    if found:
        return found
    raise FileNotFoundError("找不到 ffprobe。")


def get_duration(ffprobe_exe: str, media_path: Path) -> float:
    out = subprocess.check_output(
        [
            ffprobe_exe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(media_path),
        ],
        text=True,
    ).strip()
    return float(out)


def fmt_ass_time(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def generate_ass_subtitles(data: dict, ass_path: Path):
    header = """[Script Info]
Title: Peace and Love MV
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: LyricMain,Microsoft JhengHei,52,&H00FFFFFF,&H0000D7FF,&H00141414,&H80000000,1,0,0,0,100,100,3,0,1,2.5,2.0,2,80,80,68,1
Style: LyricSub,Microsoft JhengHei,34,&H00D8ECFF,&H00FFFFFF,&H00141414,&H80000000,0,0,0,0,100,100,2,0,1,2.0,1.5,2,80,80,26,1
Style: TitleCard,Microsoft JhengHei,76,&H00FFFFFF,&H0000D7FF,&H001A1A1A,&H64000000,1,0,0,0,100,100,8,0,1,3.0,3.0,5,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    # 開場片名淡入
    lines.append(
        "Dialogue: 1,0:00:01.00,0:00:05.20,TitleCard,,0,0,0,,{\\fad(800,800)}Peace and Love\n"
    )

    for sc in data["scenes"]:
        for lyr in sc.get("lyrics", []):
            t0 = fmt_ass_time(lyr["t0"])
            t1 = fmt_ass_time(lyr["t1"])
            zh = lyr.get("zh", "").strip()
            en = lyr.get("en", "").strip()
            if zh:
                lines.append(
                    f"Dialogue: 0,{t0},{t1},LyricMain,,0,0,0,,{{\\fad(220,220)}}{zh}\n"
                )
            if en:
                lines.append(
                    f"Dialogue: 0,{t0},{t1},LyricSub,,0,0,0,,{{\\fad(220,220)}}{en}\n"
                )

    ass_path.write_text("".join(lines), encoding="utf-8-sig")


def generate_storyboard_md(data: dict, md_path: Path):
    rows = [
        "# 🎬 《Peace and Love》電影級寫實 MV 分鏡與 Google Flow 提示詞總表\n",
        f"- **音檔長度**：`{data['duration_sec']:.2f} 秒`（3 分 23 秒）\n",
        f"- **整體風格**：{data['style']}\n",
        f"- **女角一致錨點**：{data['characters']['female']['anchor_en']}\n",
        f"- **男角一致錨點**：{data['characters']['male']['anchor_en']}\n\n",
        "| 鏡號 | 段落 | 時間軸 | 秒數 | 登場角色 | 景別運鏡 | 來源狀態 | 中文畫面說明 | Google Flow 英文 Prompt |\n",
        "|---|---|---|---|---|---|---|---|---|\n",
    ]
    for sc in data["scenes"]:
        dur = sc["end"] - sc["start"]
        chars = "、".join(sc["chars"]) if sc["chars"] else "空鏡/意象"
        flow_mp4 = MV_DIR / sc["flow_clip"]
        status = "✅ Flow真片" if (flow_mp4.exists() and flow_mp4.stat().st_size > 50_000) else "🖼️ 首幀運鏡"
        t_range = f"{sc['start']:.1f}s - {sc['end']:.1f}s"
        rows.append(
            f"| `{sc['id']}` | {sc['section']} | `{t_range}` | {dur:.1f}s | {chars} | {sc['shot_type']} | {status} | {sc['prompt_zh']} | `{sc['flow_prompt_en']}` |\n"
        )
    md_path.write_text("".join(rows), encoding="utf-8")


def render_flow_clip(ffmpeg_exe: str, ffprobe_exe: str, src_mp4: Path, out_mp4: Path, target_dur: float):
    src_dur = max(0.5, get_duration(ffprobe_exe, src_mp4))
    # 溫和變速對齊 target_dur（容許 0.65x ~ 1.45x，避免過快或卡頓）
    pts_factor = target_dur / src_dur
    pts_factor = max(0.68, min(1.55, pts_factor))
    vf = (
        f"setpts={pts_factor:.5f}*PTS,"
        f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={W}:{H},fps={FPS},"
        f"unsharp=5:5:0.5:3:3:0.0,format=yuv420p"
    )
    cmd = [
        ffmpeg_exe, "-y", "-i", str(src_mp4),
        "-an", "-vf", vf, "-t", f"{target_dur:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", str(out_mp4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def render_keyframe_clip(ffmpeg_exe: str, img_path: Path, out_mp4: Path, target_dur: float, motion: str):
    frames = max(24, int(round(target_dur * FPS)))
    # 先放大至 2400px 避免 zoompan 抖動，再流暢運鏡回 1920x1080
    if motion == "dolly_out":
        z_expr = f"1.14-0.14*(on/{frames})"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif motion == "pan_right":
        z_expr = "1.12"
        x_expr = f"(iw-iw/zoom)*(on/{frames})"
        y_expr = "ih/2-(ih/zoom/2)"
    elif motion == "pan_left":
        z_expr = "1.12"
        x_expr = f"(iw-iw/zoom)*(1-on/{frames})"
        y_expr = "ih/2-(ih/zoom/2)"
    elif motion == "zoom_focus":
        z_expr = f"1.0+0.16*(on/{frames})"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih*0.46-(ih/zoom/2)"
    else:  # dolly_in
        z_expr = f"1.0+0.12*(on/{frames})"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"

    vf = (
        f"scale=2560:1440:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop=2560:1440,"
        f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d={frames}:s={W}x{H}:fps={FPS},"
        f"format=yuv420p"
    )
    cmd = [
        ffmpeg_exe, "-y", "-loop", "1", "-i", str(img_path),
        "-t", f"{target_dur:.3f}", "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", str(out_mp4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def main():
    parser = argparse.ArgumentParser(description="組裝《Peace and Love》1080p MV")
    parser.add_argument("--no-subtitles", action="store_true", help="不壓印歌詞字幕")
    parser.add_argument("--rebuild-clips", action="store_true", help="強制重算所有單鏡 clips")
    args = parser.parse_args()

    ffmpeg_exe = find_ffmpeg()
    ffprobe_exe = find_ffprobe(ffmpeg_exe)
    data = json.loads(STORYBOARD_PATH.read_text(encoding="utf-8"))
    audio_path = MV_DIR / data["audio_file"]
    if not audio_path.exists():
        raise FileNotFoundError(f"找不到音檔：{audio_path}")

    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    generate_ass_subtitles(data, ASS_PATH)
    generate_storyboard_md(data, SCRIPT_MD_PATH)

    clip_paths: list[Path] = []
    flow_count = 0
    kf_count = 0

    for sc in data["scenes"]:
        sid = sc["id"]
        target_dur = sc["end"] - sc["start"]
        flow_mp4 = MV_DIR / sc["flow_clip"]
        kf_png = MV_DIR / sc["keyframe"]
        out_clip = CLIPS_DIR / f"{sid}_norm.mp4"
        tag_file = CLIPS_DIR / f"{sid}.source"

        use_flow = flow_mp4.exists() and flow_mp4.stat().st_size > 50_000
        expected_tag = f"flow:{flow_mp4.stat().st_mtime_ns}" if use_flow else f"kf:{kf_png.stat().st_mtime_ns if kf_png.exists() else 0}"

        need_render = args.rebuild_clips or (not out_clip.exists()) or (not tag_file.exists()) or (tag_file.read_text().strip() != expected_tag)

        if use_flow:
            flow_count += 1
            if need_render:
                print(f"🎬 [{sid}] 處理 Google Flow 真片 ({target_dur:.2f}s)...")
                render_flow_clip(ffmpeg_exe, ffprobe_exe, flow_mp4, out_clip, target_dur)
                tag_file.write_text(expected_tag)
            else:
                print(f"⚡ [{sid}] 沿用快取 Flow 分鏡 ({target_dur:.2f}s)")
        else:
            if not kf_png.exists():
                raise FileNotFoundError(f"[{sid}] 既無 Flow 影片也無首幀圖：{kf_png}")
            kf_count += 1
            if need_render:
                print(f"🖼️ [{sid}] 渲染首幀電影運鏡 ({sc['motion']}, {target_dur:.2f}s)...")
                render_keyframe_clip(ffmpeg_exe, kf_png, out_clip, target_dur, sc["motion"])
                tag_file.write_text(expected_tag)
            else:
                print(f"⚡ [{sid}] 沿用快取首幀運鏡 ({target_dur:.2f}s)")

        clip_paths.append(out_clip)

    # 寫入 concat 清單
    concat_txt = CLIPS_DIR / "concat_list.txt"
    concat_txt.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in clip_paths) + "\n",
        encoding="utf-8",
    )

    total_dur = data["duration_sec"]
    fade_out_start = max(0.0, total_dur - 2.8)

    vf_parts = [f"fade=t=in:st=0:d=1.2", f"fade=t=out:st={fade_out_start:.2f}:d=2.8"]
    if not args.no_subtitles:
        # FFmpeg ass filter 需要將 Windows 路徑反斜線與冒號跳脫
        ass_escaped = ASS_PATH.resolve().as_posix().replace(":", "\\:")
        vf_parts.append(f"ass='{ass_escaped}'")

    vf_final = ",".join(vf_parts)

    print(f"\n🎞️ 正在合成最終 1080p MV（Flow真片 {flow_count} 鏡 + 首幀運鏡 {kf_count} 鏡）...")
    cmd_final = [
        ffmpeg_exe, "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", str(audio_path),
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", vf_final,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-shortest",
        str(OUT_VIDEO),
    ]
    subprocess.run(cmd_final, check=True)
    print(f"\n✅ 完成！MV 已輸出：{OUT_VIDEO} ({OUT_VIDEO.stat().st_size / (1024*1024):.1f} MB)")
    print(f"📋 分鏡總表：{SCRIPT_MD_PATH}")


if __name__ == "__main__":
    main()
