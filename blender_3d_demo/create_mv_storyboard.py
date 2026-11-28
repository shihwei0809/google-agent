"""
MV 歌詞自動切拍 & storyboard.json 產生器
=========================================
從音檔 (.mp3/.wav) 與歌詞檔 (.lrc 或純文字 .txt) 自動切分鏡頭時間軸，
產出與 mv_flow_runner.py / mv_builder.py 100% 相容的 <project>/storyboard.json 與資料夾骨架。

用法：
  python create_mv_storyboard.py --project my_new_mv --audio song.mp3 --lyrics lyrics.lrc --title "夜空星光" --actors f35,m35
  python create_mv_storyboard.py --project my_new_mv --audio song.mp3 --lyrics lyrics.txt --shot-sec 6.5 --white-model-shots s01,s09
"""

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ACTOR_LIB_PATH = BASE_DIR / "actor_library" / "actors.json"

LRC_LINE_RE = re.compile(r"^((?:\[\d{1,2}:\d{2}(?:[.:]\d{1,3})?\])+)\s*(.*)$")
LRC_TAG_RE = re.compile(r"\[(\d{1,2}):(\d{2})(?:[.:](\d{1,3}))?\]")

MOTION_CYCLE = ["dolly_in", "pan_right", "dolly_out", "pan_left", "zoom_focus"]


def find_ffprobe() -> str:
    found = shutil.which("ffprobe")
    if found:
        return found
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        winget_dir = Path(local_app) / "Microsoft" / "WinGet" / "Packages"
        if winget_dir.exists():
            for p in winget_dir.rglob("ffprobe.exe"):
                return str(p)
    raise FileNotFoundError("找不到 ffprobe，請先安裝 FFmpeg 或透過 --duration 手動指定秒數。")


def probe_audio_duration(audio_path: Path) -> float:
    ffprobe = find_ffprobe()
    out = subprocess.check_output(
        [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        text=True,
    ).strip()
    return round(float(out), 2)


def parse_lrc_or_txt(lyrics_path: Path, total_duration: float) -> list[dict]:
    """回傳 [{t0, t1, zh, en}] 列表。支援 .lrc 時間標籤與純文字 .txt 均分。"""
    raw_lines = [ln.strip() for ln in lyrics_path.read_text(encoding="utf-8-sig").splitlines() if ln.strip()]
    lrc_entries: list[tuple[float, str]] = []

    for ln in raw_lines:
        m = LRC_LINE_RE.match(ln)
        if m:
            tags_str, text = m.group(1), m.group(2).strip()
            if not text:
                continue
            for mm, ss, frac in LRC_TAG_RE.findall(tags_str):
                sec = int(mm) * 60 + int(ss) + (float(f"0.{frac}") if frac else 0.0)
                lrc_entries.append((sec, text))

    if lrc_entries:
        lrc_entries.sort(key=lambda x: x[0])
        out = []
        for idx, (t0, text) in enumerate(lrc_entries):
            t1 = lrc_entries[idx + 1][0] if idx + 1 < len(lrc_entries) else total_duration
            t1 = max(t0 + 1.2, min(total_duration, t1))
            out.append({"t0": round(t0, 2), "t1": round(t1, 2), "zh": text, "en": ""})
        return out

    # 純文字 .txt 模式：扣除前後留白平均分配
    text_lines = [ln for ln in raw_lines if not (ln.startswith("[") and ln.endswith("]"))]
    if not text_lines:
        return []
    lead_in = min(4.0, total_duration * 0.05)
    lead_out = min(4.0, total_duration * 0.05)
    usable = max(10.0, total_duration - lead_in - lead_out)
    step = usable / len(text_lines)
    return [
        {
            "t0": round(lead_in + i * step, 2),
            "t1": round(lead_in + (i + 1) * step, 2),
            "zh": text,
            "en": "",
        }
        for i, text in enumerate(text_lines)
    ]


def group_lyrics_into_scenes(
    lyrics: list[dict],
    total_duration: float,
    target_shot_sec: float,
    actor_keys: list[str],
    style: str,
    white_model_shots: set[str],
) -> list[dict]:
    """依 target_shot_sec 自動將歌詞合併分鏡，確保頭尾無縫覆蓋 0.0 -> total_duration。"""
    if not lyrics:
        # 無歌詞時純依節拍等分
        count = max(1, round(total_duration / target_shot_sec))
        step = total_duration / count
        buckets = [
            (round(i * step, 2), round((i + 1) * step if i + 1 < count else total_duration, 2), [])
            for i in range(count)
        ]
    else:
        buckets: list[tuple[float, float, list[dict]]] = []
        cur_start = 0.0
        cur_items: list[dict] = []

        for item in lyrics:
            cur_items.append(item)
            span = item["t1"] - cur_start
            if span >= target_shot_sec:
                buckets.append((round(cur_start, 2), round(item["t1"], 2), cur_items))
                cur_start = item["t1"]
                cur_items = []

        if cur_items:
            if buckets and (total_duration - cur_start) < 3.5:
                prev_s, _, prev_items = buckets[-1]
                buckets[-1] = (prev_s, round(total_duration, 2), prev_items + cur_items)
            else:
                buckets.append((round(cur_start, 2), round(total_duration, 2), cur_items))
        elif buckets:
            prev_s, _, prev_items = buckets[-1]
            buckets[-1] = (prev_s, round(total_duration, 2), prev_items)

    scenes = []
    for idx, (start, end, items) in enumerate(buckets, start=1):
        sid = f"s{idx:02d}"
        lyric_preview = " / ".join(x["zh"] for x in items) if items else f"純音樂過場 {idx}"
        motion = "fpv_white_model" if sid in white_model_shots else MOTION_CYCLE[(idx - 1) % len(MOTION_CYCLE)]
        shot_type = "Blender白模大運鏡" if sid in white_model_shots else "電影感中景"
        chars = [] if sid in white_model_shots else actor_keys[:2]

        prompt_zh = f"[{shot_type}] {lyric_preview}"
        white_hint = (
            "Follow the exact 3D white-model camera perspective and spatial depth from the attached first/last frame reference, "
            if sid in white_model_shots
            else ""
        )
        keyframe_prompt_en = (
            f"{style}. {white_hint}Cinematic music video frame inspired by: {lyric_preview}. "
            "Photorealistic 4K, dramatic lighting, no text."
        )
        flow_prompt_en = (
            f"{style}. {white_hint}Smooth {motion.replace('_', ' ')} camera movement, "
            f"emotional storytelling matching: {lyric_preview}. Photorealistic 4K, no text."
        )

        scenes.append(
            {
                "id": sid,
                "section": f"Scene {idx:02d}",
                "start": start,
                "end": end,
                "chars": chars,
                "shot_type": shot_type,
                "motion": motion,
                "keyframe": f"keyframes/{sid}.jpg",
                "flow_clip": f"flow_clips/{sid}_flow.mp4",
                "lyrics": items,
                "prompt_zh": prompt_zh,
                "keyframe_prompt_en": keyframe_prompt_en,
                "flow_prompt_en": flow_prompt_en,
            }
        )
    return scenes


def load_selected_actors(actor_ids: list[str]) -> dict:
    if not ACTOR_LIB_PATH.exists():
        return {}
    raw = json.loads(ACTOR_LIB_PATH.read_text(encoding="utf-8"))
    by_id = {a["id"]: a for a in raw.get("actors", [])}
    out = {}
    for aid in actor_ids:
        if aid in by_id:
            a = by_id[aid]
            out[aid] = {
                "actor_id": aid,
                "name": a.get("name_zh", aid),
                "anchor_en": a.get("anchor_en", ""),
            }
    return out


def main():
    parser = argparse.ArgumentParser(description="MV 歌詞自動切拍 storyboard.json 產生器")
    parser.add_argument("--project", required=True, help="新 MV 專案資料夾名稱（位於 blender_3d_demo/<project>）")
    parser.add_argument("--audio", required=True, help="音檔路徑 (.mp3/.wav)")
    parser.add_argument("--lyrics", required=True, help="歌詞路徑 (.lrc 或純文字 .txt)")
    parser.add_argument("--title", default="", help="MV 片名（預設同專案名稱）")
    parser.add_argument("--actors", default="", help="固定演員 ID，逗號分隔，例如 f35,m35")
    parser.add_argument(
        "--style",
        default="35mm cinematic film look, warm anamorphic bokeh, atmospheric lighting",
        help="全片英文視覺風格描述",
    )
    parser.add_argument("--shot-sec", type=float, default=6.5, help="每鏡目標秒數（預設 6.5 秒）")
    parser.add_argument("--duration", type=float, default=0.0, help="手動指定音檔總秒數（略過 ffprobe）")
    parser.add_argument(
        "--white-model-shots",
        default="",
        help="預留給 Blender 白模運鏡的鏡號，逗號分隔，例如 s01,s09",
    )
    args = parser.parse_args()

    proj_dir = BASE_DIR / args.project
    for sub in ("audio", "keyframes", "flow_clips", "clips"):
        (proj_dir / sub).mkdir(parents=True, exist_ok=True)

    src_audio = Path(args.audio).resolve()
    dst_audio = proj_dir / "audio" / src_audio.name
    if src_audio.exists() and src_audio != dst_audio:
        shutil.copy2(src_audio, dst_audio)

    total_duration = args.duration if args.duration > 0 else probe_audio_duration(dst_audio if dst_audio.exists() else src_audio)
    lyrics = parse_lrc_or_txt(Path(args.lyrics).resolve(), total_duration)

    actor_ids = [x.strip() for x in args.actors.split(",") if x.strip()]
    white_shots = {x.strip() for x in args.white_model_shots.split(",") if x.strip()}
    scenes = group_lyrics_into_scenes(
        lyrics=lyrics,
        total_duration=total_duration,
        target_shot_sec=args.shot_sec,
        actor_keys=actor_ids,
        style=args.style,
        white_model_shots=white_shots,
    )

    storyboard = {
        "title": args.title or args.project,
        "audio_file": f"audio/{src_audio.name}",
        "duration_sec": total_duration,
        "style": args.style,
        "actors": actor_ids,
        "characters": load_selected_actors(actor_ids),
        "scenes": scenes,
    }

    out_json = proj_dir / "storyboard.json"
    out_json.write_text(json.dumps(storyboard, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] 已建立 {out_json}（總長 {total_duration}s，共 {len(scenes)} 鏡）")


if __name__ == "__main__":
    main()
