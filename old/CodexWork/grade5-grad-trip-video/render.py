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
    node_modules = Path(os.environ.get("TEMP", "")) / "cvs-render" / "node_modules"
    if node_modules.exists():
      os.environ["NODE_PATH"] = str(node_modules)

    python = shutil.which("python")
    node = shutil.which("node")
    if not python or not node:
        raise SystemExit("需要 Python 與 Node.js。")

    run([python, "generate_music.py"])
    run([node, "record.cjs"])
    run([
        "ffmpeg",
        "-y",
        "-i",
        str(RENDERS / "video.webm"),
        "-i",
        str(RENDERS / "bgm.wav"),
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
