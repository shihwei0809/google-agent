"""
直連聯發科原作者公開雲端 ZeroGPU (`Splend1dchan/BreezyVoice-Playground`)
全自動完成第 2 部《儲槽出貨與灌裝篇》台灣國語男聲克隆 + 自動壓製專屬 1080p 成片！
"""

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from gradio_client import Client, handle_file

BASE_DIR = Path(__file__).resolve().parent.parent
SOP_DIR = BASE_DIR / "tank_outbound_sop"
REF_WAV = SOP_DIR / "ref.wav"
JOBS_JSON = SOP_DIR / "outbound_voice_jobs.json"
OUT_AUDIO_DIR = SOP_DIR / "audio_breezy"
WORK_SUB = SOP_DIR / "_work" / "breezy_chunks"
OUT_VIDEO = SOP_DIR / "第2部_儲槽出貨與灌裝篇_聯發科BreezyVoice台灣男聲終極版.mp4"


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def split_into_safe_chunks(text: str, max_chars: int = 82) -> list[str]:
    clean = (
        text.replace("I S O Tank", "ISO Tank")
        .replace("P D A", "PDA")
        .replace("P P E", "PPE")
        .replace("S D S", "SDS")
        .replace("V O C", "VOC")
        .replace("N S B", "NSB")
        .replace("E B R", "EBR")
        .replace("G A A", "GAA")
        .replace(" 沖洗 ", "沖洗")
        .replace(" 沖洗", "沖洗")
    )
    sents = [s.strip() for s in re.split(r"(?<=[。！？；])", clean) if s.strip()]
    chunks: list[str] = []
    cur = ""
    for s in sents:
        if len(cur) + len(s) <= max_chars:
            cur += s
        else:
            if cur:
                chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)
    return chunks


def merge_chunks_to_mp3(ffmpeg_exe: str, wav_paths: list[Path], out_mp3: Path) -> None:
    inputs: list[str] = []
    fc_parts: list[str] = []
    tags: list[str] = []
    for idx, wp in enumerate(wav_paths):
        inputs += ["-i", str(wp)]
        fc_parts.append(
            f"[{idx}:a]aresample=24000,aformat=sample_fmts=fltp:channel_layouts=mono,"
            f"silenceremove=start_periods=1:start_threshold=-42dB:detection=peak,"
            f"areverse,silenceremove=start_periods=1:start_threshold=-42dB:detection=peak,areverse,"
            f"apad=pad_dur=0.22[a{idx}]"
        )
        tags.append(f"[a{idx}]")

    fc_parts.append(
        f"{''.join(tags)}concat=n={len(tags)}:v=0:a=1,"
        f"loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100[aout]"
    )
    cmd = [
        ffmpeg_exe, "-y",
        *inputs,
        "-filter_complex", ";".join(fc_parts),
        "-map", "[aout]",
        "-c:a", "libmp3lame", "-b:a", "192k", "-ac", "2",
        str(out_mp3),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
    ffmpeg_exe = find_ffmpeg()
    if not REF_WAV.exists():
        shutil.copy2(BASE_DIR / "tank_inbound_sop" / "ref.wav", REF_WAV)

    data = json.loads(JOBS_JSON.read_text(encoding="utf-8"))
    ref_text = data.get("ref_text") or "大家好，我是這個頻道的作者，今天我要跟大家分享一個實用的AI工具。"
    jobs = data["jobs"]

    OUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    WORK_SUB.mkdir(parents=True, exist_ok=True)

    print("[Init] 連線至聯發科 MediaTek BreezyVoice 雲端引擎 (Splend1dchan/BreezyVoice-Playground)...")
    client = Client("Splend1dchan/BreezyVoice-Playground")

    for job in jobs:
        sid = job["name"]
        out_mp3 = OUT_AUDIO_DIR / f"{sid}.mp3"
        if out_mp3.exists() and out_mp3.stat().st_size > 15_000:
            print(f"[Skip] 已存在音檔：{out_mp3.name}")
            continue

        chunks = split_into_safe_chunks(job["text"], max_chars=82)
        chunk_wavs: list[Path] = []
        print(f"\n[{sid}] 共切分為 {len(chunks)} 句短句進行聯發科 BreezyVoice 台灣國語合成...")

        for c_idx, c_txt in enumerate(chunks, 1):
            cw_out = WORK_SUB / f"{sid}_part{c_idx}.wav"
            if cw_out.exists() and cw_out.stat().st_size > 8_000:
                chunk_wavs.append(cw_out)
                continue

            for attempt in range(1, 5):
                try:
                    t0 = time.time()
                    res_wav = client.predict(
                        tts_text=c_txt,
                        prompt_text=ref_text,
                        prompt_wav_upload=handle_file(str(REF_WAV)),
                        prompt_wav_record=None,
                        seed=42,
                        select_which="上傳檔案",
                        api_name="/generate_audio",
                    )
                    shutil.copy2(res_wav, cw_out)
                    print(f"  ✔ {sid} 第 {c_idx}/{len(chunks)} 句完成 ({time.time()-t0:.1f}s)：{c_txt[:26]}...")
                    chunk_wavs.append(cw_out)
                    time.sleep(0.8)
                    break
                except Exception as exc:
                    wait_s = 8 * attempt
                    print(f"  [Retry {attempt}/4] ZeroGPU 短暫忙碌 ({exc})，等待 {wait_s}s 後重試...")
                    time.sleep(wait_s)
                    client = Client("Splend1dchan/BreezyVoice-Playground")
            else:
                raise RuntimeError(f"{sid} 第 {c_idx} 句重試 4 次仍失敗。")

        merge_chunks_to_mp3(ffmpeg_exe, chunk_wavs, out_mp3)
        print(f"✅ [{sid}] 合併與響度標準化完成 -> {out_mp3.name}")

    print(f"\n🎬 8 段聯發科 BreezyVoice 台灣國語男聲全部完成！開始合成專屬成片：{OUT_VIDEO.name} ...")
    subprocess.run(
        [
            sys.executable,
            str(BASE_DIR / "build_tank_outbound_video.py"),
            "--cinema",
            "--audio-dir", str(OUT_AUDIO_DIR),
            "--out-video", str(OUT_VIDEO),
        ],
        check=True,
    )
    print(f"\n🎉 大功告成！聯發科 BreezyVoice 台灣男聲終極版已輸出：{OUT_VIDEO}")


if __name__ == "__main__":
    main()
