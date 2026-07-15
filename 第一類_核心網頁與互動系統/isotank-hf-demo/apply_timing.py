"""
apply_timing.py — 更新 index.html 時間，串接音軌，mux 最終影片
執行: python apply_timing.py
"""
import subprocess, json, math, shutil, re
from pathlib import Path

# ══ 設定 ══════════════════════════════════════════════════
NARR  = Path(r"C:\GOOGLE ANGET\isotank-training\assets\narration")
HF    = Path(r"C:\GOOGLE ANGET\isotank-hf-demo")
AUDIO = HF / "assets" / "audio"
AUDIO.mkdir(parents=True, exist_ok=True)
BUFFER = 1.0
N = 12

# ══ Step 1: 取得時長 ══════════════════════════════════════
def get_dur(path):
    r = subprocess.run(
        ["ffprobe","-v","quiet","-print_format","json","-show_format",str(path)],
        capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])

print("=== 讀取 MP3 時長 ===")
durs = []
for i in range(1, N+1):
    d = get_dur(NARR / f"page-{i:02d}.mp3")
    pd = math.ceil(d + BUFFER)
    durs.append(pd)
    print(f"  p{i:02d}: {d:.2f}s -> {pd}s")

starts = [sum(durs[:i]) for i in range(N)]
total  = sum(durs)
print(f"  Total: {total}s ({total/60:.1f} min)\n")

# ══ Step 2: 更新 index.html ══════════════════════════════
print("=== 更新 index.html ===")
html = (HF / "index.html").read_text(encoding="utf-8")

# 更新 root duration
html = html.replace('data-duration="120"', f'data-duration="{total}"')

# 更新每頁 clip 的 data-start / data-duration
for i in range(N):
    pid = i + 1
    old = f'id="p{pid}" class="slide clip" data-start="{i*10}" data-duration="10"'
    new = f'id="p{pid}" class="slide clip" data-start="{starts[i]}" data-duration="{durs[i]}"'
    if old in html:
        html = html.replace(old, new)
        print(f"  p{pid}: start={starts[i]} dur={durs[i]}")
    else:
        print(f"  WARNING p{pid}: pattern not found, try fallback")
        # 備用: 只匹配 data-start 和 data-duration
        html = re.sub(
            rf'(id="p{pid}" class="slide clip" data-start=")[^"]*(" data-duration=")[^"]*(")',
            f'id="p{pid}" class="slide clip" data-start="{starts[i]}" data-duration="{durs[i]}"',
            html
        )

# 更新 GSAP timeline: O(n) -> 實際 start 秒數
for i in range(1, N+1):
    html = html.replace(f', O({i})+', f', {starts[i-1]}+')

# 更新 O() helper function 本身 (如果還在的話移除)
# html = re.sub(r'const O = [^\n]+\n', '', html)  # 不需要了但保留也無妨

# 更新進度條動畫時長 (#p{n}p 的 duration 改為 durs[n-1]-0.5)
for i in range(1, N+1):
    pct = round(i * 100 / N, 2)
    # 找到對應的 .to('#p{i}p', {width:'...%', duration:..., ease:'none'}, ...)
    html = re.sub(
        rf"(\.to\s*\('#p{i}p',\s*{{width:')[^']*(',\s*duration:)[^,]*(,\s*ease:'none'}},\s*){starts[i-1]}",
        lambda m, ni=i: f"{m.group(1)}{round(ni*100/N,2)}%{m.group(2)}{durs[ni-1]-0.5}{m.group(3)}{starts[ni-1]}",
        html
    )

(HF / "index.html").write_text(html, encoding="utf-8")
print("  index.html 更新完成\n")

# ══ Step 3: 複製音檔 ════════════════════════════════════
print("=== 複製音檔 ===")
for i in range(1, N+1):
    shutil.copy2(NARR / f"page-{i:02d}.mp3", AUDIO / f"page-{i:02d}.mp3")
print("  done\n")

# ══ Step 4: 串接音軌（各頁 adelay 到正確時間點）═════════
print("=== 串接音軌 ===")
combined = HF / "combined_audio.mp3"
input_args = []
filter_parts = []

for i in range(N):
    mp3 = AUDIO / f"page-{i+1:02d}.mp3"
    input_args += ["-i", str(mp3)]
    delay_ms = starts[i] * 1000
    filter_parts.append(f"[{i}]adelay={delay_ms}|{delay_ms}[a{i}]")

filter_complex = ";".join(filter_parts) + ";"
filter_complex += "".join(f"[a{i}]" for i in range(N))
filter_complex += f"amix=inputs={N}:duration=longest[out]"

cmd = (["ffmpeg", "-y"] + input_args +
       ["-filter_complex", filter_complex,
        "-map", "[out]", "-ar", "44100", "-ac", "2", str(combined)])
print("  ffmpeg amix...")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("  STDERR:", r.stderr[-500:])
    raise RuntimeError("ffmpeg amix failed")
print(f"  combined_audio.mp3 ({combined.stat().st_size//1024} KB)\n")

# ══ Step 5: HyperFrames render ══════════════════════════
print("=== HyperFrames render ===")
no_audio = HF / "isotank-noaudio.mp4"
subprocess.run(
    ["npx", "hyperframes", "render", "-o", str(no_audio)],
    cwd=str(HF), check=True
)
print(f"  rendered: {no_audio}\n")

# ══ Step 6: Mux 音軌 ════════════════════════════════════
print("=== Mux 音軌 ===")
final = HF / "isotank-final.mp4"
r = subprocess.run([
    "ffmpeg", "-y",
    "-i", str(no_audio),
    "-i", str(combined),
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest", str(final)
], capture_output=True, text=True)
if r.returncode != 0:
    print("STDERR:", r.stderr[-500:])
    raise RuntimeError("ffmpeg mux failed")

print(f"\n✅ 完成！")
print(f"   {final}")
print(f"   {final.stat().st_size//1024//1024} MB · {total}s")
