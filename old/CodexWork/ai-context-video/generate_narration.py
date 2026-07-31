from __future__ import annotations

import math
import os
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RENDERS = ROOT / "renders"
NARRATION = ROOT / "assets" / "narration"
RENDERS.mkdir(parents=True, exist_ok=True)
NARRATION.mkdir(parents=True, exist_ok=True)

SCRIPT = [
    "你有沒有遇過，AI 回答得很完整，卻完全不是你要的？",
    "因為一句話本身，通常不夠。像幫我整理一下，到底是整理成表格、摘要，還是簡報？",
    "上下文就像 AI 的視野。你給它越多相關背景，它越能判斷任務、限制、風格和標準。",
    "如果你只說寫一段介紹，AI 只能猜：給誰看？多長？正式還是活潑？要不要放例子？",
    "壞提示是幫我寫文案。好提示會說：產品是什麼、對象是誰、要放在哪裡、希望對方做什麼。",
    "比較好的比喻是：AI 像剛加入團隊的新同事。它能力很強，但不知道你的專案背景。",
    "給 AI 上下文，可以用四件事檢查：目標、背景、限制、輸出格式。",
    "如果你有喜歡的格式，直接貼一個範例。AI 會從範例裡學到語氣、結構和細節密度。",
    "所以上下文不是把答案先寫好，而是把地圖交給 AI，讓它少猜一點。",
    "下一次問 AI 前，先補一句：我要做什麼、給誰看、限制是什麼、希望長什麼樣。",
]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def generate_tts() -> list[Path]:
    outputs: list[Path] = []
    for idx, text in enumerate(SCRIPT, start=1):
        out = NARRATION / f"line-{idx:02d}.mp3"
        outputs.append(out)
        if out.exists():
            continue
        run([
            sys.executable,
            "-m",
            "edge_tts",
            "--voice",
            "zh-TW-HsiaoChenNeural",
            "--rate",
            "-2%",
            "--text",
            text,
            "--write-media",
            str(out),
        ])
    return outputs


def make_silence(path: Path, seconds: float = 0.35) -> None:
    sample_rate = 44100
    frames = int(sample_rate * seconds)
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * frames)


def concat_audio(parts: list[Path]) -> Path:
    temp = Path(os.environ.get("TEMP", str(RENDERS))) / "cvs-ai-context"
    temp.mkdir(parents=True, exist_ok=True)
    silence_wav = temp / "silence.wav"
    silence_mp3 = temp / "silence.mp3"
    make_silence(silence_wav)
    run(["ffmpeg", "-y", "-i", str(silence_wav), str(silence_mp3)])

    expanded: list[Path] = []
    for part in parts:
        expanded.append(part)
        expanded.append(silence_mp3)

    list_file = temp / "concat.txt"
    list_file.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in expanded),
        encoding="utf-8",
    )
    narration = RENDERS / "narration.mp3"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(narration)])
    return narration


def make_bgm(duration: int = 125) -> Path:
    bgm = RENDERS / "bgm.mp3"
    # Synthetic ambient bed: licensed as self-generated.
    expr = (
        "0.18*sin(2*PI*110*t)+"
        "0.12*sin(2*PI*164.81*t)+"
        "0.08*sin(2*PI*220*t)+"
        "0.04*sin(2*PI*(55+8*sin(2*PI*0.03*t))*t)"
    )
    run([
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"aevalsrc='{expr}':s=44100:d={duration}",
        "-af",
        f"afade=t=in:st=0:d=2,afade=t=out:st={duration-3}:d=3,volume=0.12",
        str(bgm),
    ])
    return bgm


def mix(narration: Path, bgm: Path) -> Path:
    master = RENDERS / "master_audio.mp3"
    run([
        "ffmpeg",
        "-y",
        "-i",
        str(narration),
        "-i",
        str(bgm),
        "-filter_complex",
        "[0:a]volume=1.0[a0];[1:a]volume=0.22[a1];[a0][a1]amix=inputs=2:duration=longest:dropout_transition=0",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "192k",
        str(master),
    ])
    return master


def main() -> None:
    parts = generate_tts()
    narration = concat_audio(parts)
    bgm = make_bgm()
    master = mix(narration, bgm)
    print(f"master audio: {master}")


if __name__ == "__main__":
    main()
