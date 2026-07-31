from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RENDERS = ROOT / "renders"
RENDERS.mkdir(exist_ok=True)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    out = RENDERS / "bgm.wav"
    duration = 75
    # Warm synthetic school-trip theme. Self-generated, no external music.
    expr = (
        "0.18*sin(2*PI*261.63*t)*lt(mod(t,1.0),0.08)+"
        "0.14*sin(2*PI*329.63*t)*lt(mod(t+0.25,1.0),0.08)+"
        "0.12*sin(2*PI*392.00*t)*lt(mod(t+0.50,1.0),0.08)+"
        "0.10*sin(2*PI*523.25*t)*lt(mod(t+0.75,1.0),0.06)+"
        "0.06*sin(2*PI*130.81*t)+"
        "0.04*sin(2*PI*196.00*t)"
    )
    run([
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"aevalsrc='{expr}':s=44100:d={duration}",
        "-af",
        f"afade=t=in:st=0:d=1.5,afade=t=out:st={duration-3}:d=3,volume=0.45",
        str(out),
    ])
    print(out)


if __name__ == "__main__":
    main()
