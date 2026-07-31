from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RENDERS = ROOT / "renders"
RENDERS.mkdir(exist_ok=True)


def run(cmd: list[str]) -> None:
    print(" ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    os.environ["PYTHONUTF8"] = "1"
    python = shutil.which("python") or shutil.which("py")
    node = shutil.which("node")
    if not python:
        raise SystemExit("找不到 Python。請先安裝 Python，或改用完整 python.exe 路徑執行。")
    if not node:
        raise SystemExit("找不到 Node.js。請先安裝 Node.js 18+。")

    node_path = os.environ.get("NODE_PATH")
    if not node_path:
        temp_node_modules = Path(os.environ.get("TEMP", "")) / "cvs-render" / "node_modules"
        if temp_node_modules.exists():
            os.environ["NODE_PATH"] = str(temp_node_modules)

    run([python, "generate_narration.py"])
    run([node, "record.cjs"])
    run([
        "ffmpeg",
        "-y",
        "-i",
        str(RENDERS / "video.webm"),
        "-i",
        str(RENDERS / "master_audio.mp3"),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "libx264",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        str(ROOT / "final.mp4"),
    ])


if __name__ == "__main__":
    main()
