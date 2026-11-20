"""
Reusable Cinema Post-Production & Voice Job Engine for `sop-cinema-video`.
Provides:
- Taiwanese Mandarin TTS text normalization (alphanumeric codes, eTag, integers, TW_BOPO)
- Voice job manifest export for Google Colab T4 (BreezyVoice / VoxCPM2)
- Full-bleed 1080p cinema Flow clip overlay (no thick presentation chrome)
- Cinema 3s push-in cover & ending clip rendering
- FFmpeg xfade + acrossfade concatenation
- FFmpeg sidechaincompress BGM auto-ducking mixer
- Gemini TTS API synthesis with Rule 10 model fallback chain
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

VIDEO_W, VIDEO_H = 1920, 1080
FPS = 24

TW_BOPO: Dict[str, str] = {
    "連假": "連假[:ㄐㄧㄚ4]",
    "放假": "放假[:ㄐㄧㄚ4]",
    "請假": "請假[:ㄐㄧㄚ4]",
    "暑假": "暑假[:ㄐㄧㄚ4]",
    "寒假": "寒假[:ㄐㄧㄚ4]",
    "假期": "假[:ㄐㄧㄚ4]期",
    "假日": "假[:ㄐㄧㄚ4]日",
}

DIGITS_ZH = "零一二三四五六七八九"

GEMINI_TTS_MODELS = [
    "gemini-3.8-flash-tts",
    "gemini-3.7-flash-tts",
    "gemini-3.6-flash-tts",
    "gemini-2.5-flash-preview-tts",
]


def _find_font_path(bold: bool = False) -> str:
    candidates = (
        [
            r"C:\Windows\Fonts\msjhbd.ttc",
            r"C:\Windows\Fonts\NotoSansTC-VF.ttf",
            r"C:\Windows\Fonts\msjh.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        ]
        if bold
        else [
            r"C:\Windows\Fonts\msjh.ttc",
            r"C:\Windows\Fonts\NotoSansTC-VF.ttf",
            r"C:\Windows\Fonts\mingliu.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
    )
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("找不到繁體中文字型 (msjh.ttc / NotoSansTC / NotoSansCJK)")


_FONT_CACHE: Dict[Tuple[bool, int], ImageFont.FreeTypeFont] = {}


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (bold, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(_find_font_path(bold=bold), size)
    return _FONT_CACHE[key]


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
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


def _find_ffprobe(ffmpeg_exe: str) -> Optional[str]:
    import shutil

    probe = shutil.which("ffprobe")
    if probe:
        return probe
    cand = Path(ffmpeg_exe).with_name("ffprobe.exe" if os.name == "nt" else "ffprobe")
    return str(cand) if cand.exists() else None


def probe_duration(ffmpeg_exe: str, media_path: Path) -> float:
    ffprobe = _find_ffprobe(ffmpeg_exe)
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
            return max(0.2, float(out))
    return 5.0


def probe_has_audio(ffmpeg_exe: str, media_path: Path) -> bool:
    ffprobe = _find_ffprobe(ffmpeg_exe)
    if not ffprobe:
        return True
    out = subprocess.check_output(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(media_path),
        ],
        text=True,
    ).strip()
    return bool(out)


def int_zh(n: int) -> str:
    """Convert non-negative integer into natural Taiwanese Mandarin reading."""
    if n < 0:
        return "負" + int_zh(-n)
    if n < 10:
        return DIGITS_ZH[n]
    if n < 100:
        t, o = divmod(n, 10)
        return ("" if t == 1 else DIGITS_ZH[t]) + "十" + (DIGITS_ZH[o] if o else "")
    if n < 1000:
        h, r = divmod(n, 100)
        if r == 0:
            return DIGITS_ZH[h] + "百"
        if r < 10:
            return DIGITS_ZH[h] + "百零" + DIGITS_ZH[r]
        if r < 20:
            return DIGITS_ZH[h] + "百一" + int_zh(r)
        return DIGITS_ZH[h] + "百" + int_zh(r)
    return "".join(DIGITS_ZH[int(c)] for c in str(n))


def normalize_tw_tts_text(text: str) -> str:
    """Normalize SOP codes, English abbreviations, digits, and TW polyphones for TTS."""
    out = text.strip()

    # 1. Replace standard alphanumeric SOP expense/tax codes first
    code_map = {
        r"\bA01\b": "A零一",
        r"\bA05\b": "A零五",
        r"\bA06\b": "A零六",
        r"\bA07\b": "A零七",
        r"\bT01\b": "T零一",
        r"\bT02\b": "T零二",
        r"\bT04\b": "T零四",
        r"\bT05\b": "T零五",
    }
    for pat, rep in code_map.items():
        out = re.sub(pat, rep, out, flags=re.IGNORECASE)

    # Generic zero-padded single letter + 2 digits like B03 -> B零三
    out = re.sub(
        r"\b([A-Za-z])0([0-9])\b",
        lambda m: f"{m.group(1).upper()}零{DIGITS_ZH[int(m.group(2))]}",
        out,
    )

    # 2. Brand / system abbreviations commonly mispronounced by Chinese TTS
    out = re.sub(r"\be[- ]?Tag\b", "一Tag", out, flags=re.IGNORECASE)
    out = re.sub(r"\bBPM\b", "B P M", out)
    out = re.sub(r"\bEPM\b", "E P M", out)
    out = re.sub(r"\bPDF\b", "P D F", out, flags=re.IGNORECASE)
    out = re.sub(r"\bKey\s*入\b", "鍵入", out, flags=re.IGNORECASE)
    out = re.sub(r"\bKey\b", "鍵入", out, flags=re.IGNORECASE)

    # 3. Convert integer literals to Chinese words while preserving [:bopomofo] tags
    out = re.sub(
        r"\[:[^\]]*\]|\d+",
        lambda m: m.group(0) if m.group(0).startswith("[") else int_zh(int(m.group(0))),
        out,
    )

    # 4. Apply Taiwan bopomofo disambiguation safely
    for word, tagged in TW_BOPO.items():
        if tagged not in out:
            out = out.replace(word, tagged)

    # 5. Clean punctuation that causes unnatural pauses in TTS
    out = out.replace("……", "，").replace("——", "，").replace("～", "！")
    return re.sub(r"\s{2,}", " ", out).strip()


def export_voice_jobs_json(
    shots: List[dict],
    out_path: Path,
    project_name: str,
    default_voice_design: str = "一位親切專業的台灣職場講師，聲音自然清亮、吐字清晰、節奏明快",
    default_engine: str = "BreezyVoice",
    seeds: int = 3,
) -> Path:
    """Export normalized voice job specification JSON for Colab T4 voice cloning."""
    jobs = []
    for shot in shots:
        raw_text = (shot.get("narration") or "").strip()
        if not raw_text:
            continue
        jobs.append(
            {
                "name": shot["id"],
                "title": shot.get("title", shot["id"]),
                "text": normalize_tw_tts_text(raw_text),
                "raw_text": raw_text,
            }
        )
    payload = {
        "project": project_name,
        "default_engine": default_engine,
        "seeds": seeds,
        "ref_audio": "ref.wav",
        "ref_text": "",
        "voice_design": default_voice_design,
        "jobs": jobs,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def _generate_cinema_poster_image(
    out_png: Path,
    title: str,
    subtitle: str = "",
    badge: str = "ENTERPRISE CINEMA SOP",
    is_ending: bool = False,
) -> Path:
    """Create a sleek 1920x1080 dark cinema title/ending card using Pillow."""
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), (9, 14, 26))
    draw = ImageDraw.Draw(img)

    # Subtle vertical slate gradient
    for y in range(VIDEO_H):
        t = y / max(1, VIDEO_H - 1)
        r = int(9 * (1 - t) + 18 * t)
        g = int(14 * (1 - t) + 30 * t)
        b = int(26 * (1 - t) + 52 * t)
        draw.line([(0, y), (VIDEO_W, y)], fill=(r, g, b))

    # Subtle cinema top/bottom hairline accents
    accent = (16, 185, 129) if is_ending else (245, 158, 11)
    draw.rectangle([160, 130, VIDEO_W - 160, 133], fill=accent)
    draw.rectangle([160, VIDEO_H - 133, VIDEO_W - 160, VIDEO_H - 130], fill=(56, 189, 248))

    # Top badge
    b_font = _get_font(24, bold=True)
    bw = int(draw.textlength(badge, font=b_font)) + 52
    bx1 = (VIDEO_W - bw) // 2
    draw.rounded_rectangle([bx1, 250, bx1 + bw, 302], radius=26, fill=(20, 32, 54), outline=accent, width=2)
    draw.text(((VIDEO_W - draw.textlength(badge, font=b_font)) / 2, 261), badge, fill=accent, font=b_font)

    # Main Title
    t_font = _get_font(76, bold=True)
    title_lines = _wrap_text(draw, title, t_font, VIDEO_W - 320)
    ty = 390 if len(title_lines) > 1 else 435
    for ln in title_lines[:3]:
        tw = draw.textlength(ln, font=t_font)
        draw.text(((VIDEO_W - tw) / 2, ty), ln, fill=(248, 250, 252), font=t_font)
        ty += 96

    # Subtitle
    if subtitle:
        s_font = _get_font(34, bold=False)
        sub_lines = _wrap_text(draw, subtitle, s_font, VIDEO_W - 380)
        sy = ty + 34
        for ln in sub_lines[:2]:
            sw = draw.textlength(ln, font=s_font)
            draw.text(((VIDEO_W - sw) / 2, sy), ln, fill=(186, 230, 253), font=s_font)
            sy += 48

    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)
    return out_png


def _render_still_push_clip(
    ffmpeg_exe: str,
    image_path: Path,
    out_mp4: Path,
    duration: float = 3.0,
    fps: int = FPS,
    fade_in: bool = True,
    fade_out: bool = False,
) -> Path:
    total_frames = max(int(round(duration * fps)), fps)
    vf_parts = [
        "scale=3840:2160:force_original_aspect_ratio=increase",
        "crop=3840:2160",
        f"zoompan=z='min(zoom+0.0007,1.05)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={VIDEO_W}x{VIDEO_H}:fps={fps}",
        "format=yuv420p",
    ]
    if fade_in:
        vf_parts.append("fade=t=in:st=0:d=0.45")
    if fade_out and duration > 0.6:
        vf_parts.append(f"fade=t=out:st={max(0.0, duration - 0.5):.2f}:d=0.5")

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        str(image_path),
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf",
        ",".join(vf_parts),
        "-map",
        "0:v",
        "-map",
        "1:a",
        "-t",
        f"{duration:.2f}",
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
        str(out_mp4),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return out_mp4


def render_cover_clip(
    ffmpeg_exe: str,
    out_mp4: Path,
    title: str,
    subtitle: str = "",
    cover_img: Optional[Path] = None,
    duration: float = 3.0,
    fps: int = FPS,
) -> Path:
    """Render 3s push-in cinema cover clip (uses cover_img if present, else generates poster)."""
    tmp_poster = None
    src_img = cover_img if (cover_img and cover_img.exists()) else None
    if src_img is None:
        tmp_poster = out_mp4.with_suffix(".cover.png")
        src_img = _generate_cinema_poster_image(
            tmp_poster,
            title=title,
            subtitle=subtitle,
            badge="SOP 微電影實務指南",
            is_ending=False,
        )
    try:
        return _render_still_push_clip(
            ffmpeg_exe,
            src_img,
            out_mp4,
            duration=duration,
            fps=fps,
            fade_in=True,
            fade_out=False,
        )
    finally:
        if tmp_poster and tmp_poster.exists():
            tmp_poster.unlink(missing_ok=True)


def render_ending_clip(
    ffmpeg_exe: str,
    out_mp4: Path,
    title: str = "謝謝收看",
    subtitle: str = "報銷零退件｜請記得將正本交由人事核對",
    end_img: Optional[Path] = None,
    duration: float = 3.0,
    fps: int = FPS,
) -> Path:
    """Render 3s push-in cinema ending clip (uses end_img if present, else generates card)."""
    tmp_poster = None
    src_img = end_img if (end_img and end_img.exists()) else None
    if src_img is None:
        tmp_poster = out_mp4.with_suffix(".ending.png")
        src_img = _generate_cinema_poster_image(
            tmp_poster,
            title=title,
            subtitle=subtitle,
            badge="THANK YOU FOR WATCHING",
            is_ending=True,
        )
    try:
        return _render_still_push_clip(
            ffmpeg_exe,
            src_img,
            out_mp4,
            duration=duration,
            fps=fps,
            fade_in=False,
            fade_out=True,
        )
    finally:
        if tmp_poster and tmp_poster.exists():
            tmp_poster.unlink(missing_ok=True)


def render_cinema_flow_clip(
    ffmpeg_exe: str,
    flow_mp4: Path,
    audio_path: Optional[Path],
    out_mp4: Path,
    duration: Optional[float],
    subtitle: str,
    chapter_badge: str = "",
    fps: int = FPS,
) -> Path:
    """Render full-bleed 1920x1080 Google Flow clip with translucent cinema subtitles (no thick chrome)."""
    if duration is None:
        if audio_path and audio_path.exists():
            duration = probe_duration(ffmpeg_exe, audio_path) + 0.45
        else:
            duration = probe_duration(ffmpeg_exe, flow_mp4)

    overlay = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    if chapter_badge:
        b_font = _get_font(22, bold=True)
        bw = int(od.textlength(chapter_badge, font=b_font)) + 44
        bx1 = VIDEO_W - bw - 36
        od.rounded_rectangle(
            [bx1, 28, VIDEO_W - 36, 74],
            radius=22,
            fill=(15, 23, 42, 165),
            outline=(245, 158, 11, 200),
            width=2,
        )
        od.text((bx1 + 22, 38), chapter_badge, fill=(248, 250, 252, 240), font=b_font)

    if subtitle.strip():
        sub_font = _get_font(34, bold=True)
        lines = _wrap_text(od, subtitle.strip(), sub_font, VIDEO_W - 280)[:2]
        card_h = 68 if len(lines) == 1 else 112
        card_y2 = VIDEO_H - 30
        card_y1 = card_y2 - card_h
        max_lw = max(od.textlength(ln, font=sub_font) for ln in lines)
        card_w = min(VIDEO_W - 120, max(720, int(max_lw) + 96))
        cx1 = (VIDEO_W - card_w) // 2
        od.rounded_rectangle(
            [cx1, card_y1, cx1 + card_w, card_y2],
            radius=18,
            fill=(10, 16, 28, 185),
            outline=(148, 163, 184, 90),
            width=1,
        )
        sy = card_y1 + (16 if len(lines) == 2 else 14)
        for ln in lines:
            lw = od.textlength(ln, font=sub_font)
            od.text(((VIDEO_W - lw) / 2, sy), ln, fill=(248, 250, 252, 255), font=sub_font)
            sy += 44

    hud_png = out_mp4.with_suffix(".cinema_hud.png")
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(hud_png)

    use_external_audio = audio_path is not None and audio_path.exists()
    if use_external_audio:
        audio_input = ["-i", str(audio_path)]
        audio_map = ["-map", "2:a", "-af", "aformat=sample_rates=44100:channel_layouts=stereo,apad"]
    elif probe_has_audio(ffmpeg_exe, flow_mp4):
        audio_input = []
        audio_map = ["-map", "0:a", "-af", "aformat=sample_rates=44100:channel_layouts=stereo,apad"]
    else:
        audio_input = ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        audio_map = ["-map", "2:a"]

    cmd = [
        ffmpeg_exe,
        "-y",
        "-stream_loop",
        "-1",
        "-i",
        str(flow_mp4),
        "-i",
        str(hud_png),
        *audio_input,
        "-filter_complex",
        f"[0:v]scale={VIDEO_W}:{VIDEO_H}:force_original_aspect_ratio=increase,crop={VIDEO_W}:{VIDEO_H},fps={fps},format=yuv420p[bg];"
        "[bg][1:v]overlay=0:0[v]",
        "-map",
        "[v]",
        *audio_map,
        "-t",
        f"{duration:.2f}",
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
        str(out_mp4),
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    finally:
        hud_png.unlink(missing_ok=True)
    return out_mp4


def concat_with_xfade(
    ffmpeg_exe: str,
    clip_paths: List[Path],
    out_mp4: Path,
    fade_sec: float = 0.4,
    fps: int = FPS,
) -> Path:
    """Concatenate clips smoothly with FFmpeg xfade + acrossfade."""
    import shutil

    valid_clips = [Path(p) for p in clip_paths if Path(p).exists()]
    if not valid_clips:
        raise ValueError("concat_with_xfade: 沒有可用的影片片段")

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    if len(valid_clips) == 1:
        shutil.copy2(valid_clips[0], out_mp4)
        return out_mp4

    durations = [probe_duration(ffmpeg_exe, p) for p in valid_clips]
    min_dur = min(durations)
    fade = max(0.1, min(fade_sec, min_dur * 0.4))

    inputs: List[str] = []
    prep_filters: List[str] = []
    for idx, clip in enumerate(valid_clips):
        inputs.extend(["-i", str(clip)])
        prep_filters.append(f"[{idx}:v]settb=AVTB,fps={fps},format=yuv420p,setsar=1[v{idx}]")
        if probe_has_audio(ffmpeg_exe, clip):
            prep_filters.append(
                f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,asetpts=PTS-STARTPTS[a{idx}]"
            )
        else:
            prep_filters.append(
                f"anullsrc=channel_layout=stereo:sample_rate=44100,atrim=0:{durations[idx]:.3f},asetpts=PTS-STARTPTS[a{idx}]"
            )

    xfade_filters: List[str] = []
    cur_v = "[v0]"
    cur_a = "[a0]"
    cumulative_dur = durations[0]

    for idx in range(1, len(valid_clips)):
        offset = max(0.05, cumulative_dur - fade)
        next_v = f"[vx{idx}]" if idx < len(valid_clips) - 1 else "[vout]"
        next_a = f"[ax{idx}]" if idx < len(valid_clips) - 1 else "[aout]"
        xfade_filters.append(
            f"{cur_v}[v{idx}]xfade=transition=fade:duration={fade:.3f}:offset={offset:.3f}{next_v}"
        )
        xfade_filters.append(
            f"{cur_a}[a{idx}]acrossfade=d={fade:.3f}:c1=tri:c2=tri{next_a}"
        )
        cur_v = next_v
        cur_a = next_a
        cumulative_dur = cumulative_dur + durations[idx] - fade

    filter_complex = ";".join(prep_filters + xfade_filters)
    cmd = [
        ffmpeg_exe,
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-map",
        "[aout]",
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
        str(out_mp4),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return out_mp4


def mix_bgm_with_ducking(
    ffmpeg_exe: str,
    video_mp4: Path,
    bgm_path: Path,
    out_mp4: Path,
    bgm_vol: float = 0.18,
) -> Path:
    """Mix instrumental BGM under video narration with sidechaincompress auto-ducking."""
    dur = probe_duration(ffmpeg_exe, video_mp4)
    fade_out_start = max(0.0, dur - 2.0)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    filter_complex = (
        f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,"
        f"atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,"
        f"afade=t=in:st=0:d=1.2,"
        f"afade=t=out:st={fade_out_start:.3f}:d=2.0,"
        f"volume={bgm_vol:.3f}[bgm_pre];"
        f"[0:a]aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[voice_out][voice_sc];"
        f"[bgm_pre][voice_sc]sidechaincompress=threshold=0.03:ratio=6:attack=80:release=450[bgm_ducked];"
        f"[voice_out][bgm_ducked]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]"
    )

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        str(video_mp4),
        "-stream_loop",
        "-1",
        "-i",
        str(bgm_path),
        "-filter_complex",
        filter_complex,
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-b:a",
        "192k",
        "-shortest",
        str(out_mp4),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return out_mp4


def synthesize_gemini_tts(
    text: str,
    out_mp3: Path,
    ffmpeg_exe: str,
    voice_name: str = "Kore",
    api_key: Optional[str] = None,
) -> str:
    """Synthesize speech via Gemini TTS API with Rule 10 Flash model fallback chain."""
    key = (api_key or os.environ.get("GEMINI_API_KEY", "")).strip()
    if not key:
        raise RuntimeError("缺少環境變數 GEMINI_API_KEY，無法呼叫 Gemini TTS（已自動保護零金鑰寫死規範）。")

    last_error = ""
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    prompt_text = f"請用自然、親切且專業的台灣國語語調朗讀以下內容：\n{text}"

    for model in GEMINI_TTS_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        body = json.dumps(
            {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {"voiceName": voice_name},
                        }
                    },
                },
            }
        ).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            inline = next((p.get("inlineData") for p in parts if p.get("inlineData")), None)
            if not inline or not inline.get("data"):
                last_error = f"{model}: 回應未包含音訊 inlineData"
                continue
            raw_bytes = base64.b64decode(inline["data"])
            mime = (inline.get("mimeType") or "").lower()
            tmp_fd, tmp_name = tempfile.mkstemp(suffix=".raw")
            os.close(tmp_fd)
            tmp_path = Path(tmp_name)
            try:
                tmp_path.write_bytes(raw_bytes)
                if "pcm" in mime or "l16" in mime:
                    rate_match = re.search(r"rate=(\d+)", mime)
                    sr = rate_match.group(1) if rate_match else "24000"
                    cmd = [
                        ffmpeg_exe,
                        "-y",
                        "-f",
                        "s16le",
                        "-ar",
                        sr,
                        "-ac",
                        "1",
                        "-i",
                        str(tmp_path),
                        "-ar",
                        "44100",
                        "-ac",
                        "2",
                        "-b:a",
                        "192k",
                        str(out_mp3),
                    ]
                else:
                    cmd = [
                        ffmpeg_exe,
                        "-y",
                        "-i",
                        str(tmp_path),
                        "-ar",
                        "44100",
                        "-ac",
                        "2",
                        "-b:a",
                        "192k",
                        str(out_mp3),
                    ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            finally:
                tmp_path.unlink(missing_ok=True)
            return model
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="ignore")[:300]
            last_error = f"{model} HTTP {exc.code}: {err_body}"
        except Exception as exc:
            last_error = f"{model}: {exc}"

    raise RuntimeError(f"Gemini TTS 全模型降級失敗，最後錯誤：{last_error}")
