"""
100% 全自動「本人原聲 (VoxCPM2 48kHz ZeroGPU)」克隆與電影混剪管線
===========================================================================
1. 清除舊暫存，使用經過真人試聽驗證之 `Kansasfan/voxcpm2-7`（附多節點 ZeroGPU 自動切換備援）
2. 內建台灣化工廠口語同音糾音表（如「儲槽 -> 除槽」防破音，字幕仍保持正體「儲槽」）
3. 每鏡切分為 2 段自然語句（共 16 次呼叫），強制驗證輸出 WAV > 150KB 杜絕空音檔
4. 自動去頭尾多餘靜音 + 句間 0.22s 自然停頓 + -16 LUFS 響度標準化 -> audio_myvoice/shot01..08.mp3
5. 自動呼叫 build_tank_inbound_video.py 輸出獨立成片：
   tank_inbound_sop/第1部_儲槽進貨與卸料篇_本人原聲克隆終極版.mp4（保留原女聲版不覆蓋）
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
SOP_DIR = BASE_DIR / "tank_inbound_sop"
REF_WAV = SOP_DIR / "ref.wav"
JOBS_JSON = SOP_DIR / "inbound_voice_jobs.json"
OUT_AUDIO_DIR = SOP_DIR / "audio_myvoice"
WORK_SUB = SOP_DIR / "_work" / "voxcpm2_chunks"
OUT_VIDEO = SOP_DIR / "第1部_儲槽進貨與卸料篇_本人原聲克隆終極版.mp4"

ZEROGPU_SPACES = [
    "Kansasfan/voxcpm2-7",
    "yunaisbusy/voxcpm2-7",
]


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def fix_tw_factory_pronunciation(text: str) -> str:
    """針對試聽實測修正台灣化工廠現場口語讀音（僅影響 TTS 輸入，不改畫面字幕）。"""
    rules = {
        "儲槽": "除槽",
        "入槽": "入曹",
        "滿槽": "滿曹",
        "換槽": "換曹",
        "槽別": "曹別",
        "槽車": "曹車",
        "油罐槽車": "油罐曹車",
        "化學槽": "化學曹",
        "槽頂": "曹頂",
        "槽體": "曹體",
        "槽內": "曹內",
        "泵浦": "幫浦",
        "泵料": "幫料",
        "泵空": "幫空",
        "停泵": "停幫",
        "I S O Tank": "I S O Tank",
        "P D A": "P D A",
        " 沖洗 ": "沖洗",
        " 沖洗": "沖洗",
    }
    out = text
    for k, v in rules.items():
        out = out.replace(k, v)
    return out


def split_two_halves(text: str) -> list[str]:
    """將每鏡約 200 字旁白依句號平均切為 2 段（每段約 90-120 字），兼顧連貫語氣與防超時。"""
    sents = [s.strip() for s in re.split(r"(?<=[。！？；])", text) if s.strip()]
    if len(sents) <= 2:
        return ["".join(sents)]
    mid = len(text) // 2
    cur = ""
    first_part = ""
    idx_split = 1
    for i, s in enumerate(sents):
        if len(cur) + len(s) <= mid or i == 0:
            cur += s
            idx_split = i + 1
        else:
            break
    first_part = cur
    second_part = "".join(sents[idx_split:])
    return [p for p in (first_part, second_part) if p]


def merge_chunks_to_mp3(ffmpeg_exe: str, wav_paths: list[Path], out_mp3: Path) -> None:
    inputs: list[str] = []
    fc_parts: list[str] = []
    tags: list[str] = []
    for idx, wp in enumerate(wav_paths):
        inputs += ["-i", str(wp)]
        fc_parts.append(
            f"[{idx}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=mono,"
            f"silenceremove=start_periods=1:start_threshold=-45dB:detection=peak,"
            f"areverse,silenceremove=start_periods=1:start_threshold=-45dB:detection=peak,areverse,"
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
    data = json.loads(JOBS_JSON.read_text(encoding="utf-8"))
    ref_text = data.get("ref_text") or "大家好，我是這個頻道的作者，今天我要跟大家分享一個實用的AI工具。"
    jobs = data["jobs"]

    # 清理前次無效的小音檔 (<150KB)
    OUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    for old_f in OUT_AUDIO_DIR.glob("*.mp3"):
        if old_f.stat().st_size < 150_000:
            old_f.unlink()

    WORK_SUB.mkdir(parents=True, exist_ok=True)

    clients: dict[str, Client] = {}

    def get_client(space_id: str) -> Client:
        if space_id not in clients:
            clients[space_id] = Client(space_id, httpx_kwargs={"timeout": 150.0})
        return clients[space_id]

    space_cursor = 0

    for job in jobs:
        sid = job["name"]
        out_mp3 = OUT_AUDIO_DIR / f"{sid}.mp3"
        if out_mp3.exists() and out_mp3.stat().st_size >= 250_000:
            print(f"[Skip] 已有高品質本人克隆音檔：{out_mp3.name} ({out_mp3.stat().st_size // 1024} KB)")
            continue

        spoken_text = fix_tw_factory_pronunciation(job["text"])
        parts = split_two_halves(spoken_text)
        part_wavs: list[Path] = []
        print(f"\n[{sid}] 切分為 {len(parts)} 段進行 VoxCPM2 48kHz 本人原聲克隆...")

        for p_idx, p_txt in enumerate(parts, 1):
            pw_out = WORK_SUB / f"{sid}_half{p_idx}.wav"
            if pw_out.exists() and pw_out.stat().st_size > 200_000:
                print(f"  [Cache] 沿用已生成片段：{pw_out.name} ({pw_out.stat().st_size // 1024} KB)")
                part_wavs.append(pw_out)
                continue

            success = False
            for attempt in range(1, 7):
                sp = ZEROGPU_SPACES[space_cursor % len(ZEROGPU_SPACES)]
                try:
                    t0 = time.time()
                    cl = get_client(sp)
                    res_wav = cl.predict(
                        text_input=p_txt,
                        control_instruction="",
                        reference_wav_path_input=handle_file(str(REF_WAV)),
                        use_prompt_text=True,
                        prompt_text_input=ref_text,
                        cfg_value_input=2.0,
                        do_normalize=True,
                        denoise=False,
                        api_name="/generate",
                    )
                    sz = Path(res_wav).stat().st_size
                    if sz < 150_000:
                        raise RuntimeError(f"回傳音檔過小 ({sz} bytes)，判定無效重試")
                    shutil.copy2(res_wav, pw_out)
                    print(f"  ✔ {sid} 第 {p_idx}/{len(parts)} 段完成 ({time.time()-t0:.1f}s | {sz//1024} KB | {sp})")
                    part_wavs.append(pw_out)
                    success = True
                    time.sleep(1.5)
                    break
                except Exception as exc:
                    print(f"  [Retry {attempt}/6 on {sp}] {exc}")
                    clients.pop(sp, None)
                    space_cursor += 1
                    time.sleep(6 * attempt)

            if not success:
                raise RuntimeError(f"{sid} 第 {p_idx} 段多次重試失敗")

        merge_chunks_to_mp3(ffmpeg_exe, part_wavs, out_mp3)
        print(f"✅ [{sid}] 合併標準化完成 -> {out_mp3.name} ({out_mp3.stat().st_size // 1024} KB)")

    print(f"\n🎬 8 段本人 48kHz 原聲全部克隆完成！開始壓製專屬成片：{OUT_VIDEO.name} ...")
    subprocess.run(
        [
            sys.executable,
            str(BASE_DIR / "build_tank_inbound_video.py"),
            "--cinema",
            "--audio-dir", str(OUT_AUDIO_DIR),
            "--out-video", str(OUT_VIDEO),
        ],
        check=True,
    )
    print(f"\n🎉 大功告成！本人原聲克隆終極版已輸出：{OUT_VIDEO}")


if __name__ == "__main__":
    main()
