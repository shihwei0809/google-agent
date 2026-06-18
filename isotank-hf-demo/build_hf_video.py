"""
build_hf_video.py
1. 讀取 12 個 MP3 的實際時長
2. 更新 isotank-hf-demo/index.html 的 data-duration 與 GSAP 時間偏移
3. 把 MP3 複製到 isotank-hf-demo/assets/audio/
4. 用 ffmpeg 串接成一段合併音軌 combined.mp3
5. render HyperFrames → isotank-full.mp4
6. 用 ffmpeg 把音軌 mux 進影片 → isotank-final.mp4
"""
import subprocess, shutil, json, re, math
from pathlib import Path

# ── 路徑 ──────────────────────────────────────────────────
NARR   = Path(r"C:\GOOGLE ANGET\isotank-training\assets\narration")
HF     = Path(r"C:\GOOGLE ANGET\isotank-hf-demo")
AUDIO  = HF / "assets" / "audio"
AUDIO.mkdir(parents=True, exist_ok=True)

BUFFER = 1.0   # 每頁旁白結束後多留 1 秒
N_PAGES = 12

# ── Step 1: 取得各頁時長 ──────────────────────────────────
def get_dur(path):
    r = subprocess.run(
        ["ffprobe","-v","quiet","-print_format","json","-show_format", str(path)],
        capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])

print("=== Step 1: 讀取 MP3 時長 ===")
durs = []
for i in range(1, N_PAGES+1):
    mp3 = NARR / f"page-{i:02d}.mp3"
    if not mp3.exists():
        raise FileNotFoundError(f"Missing: {mp3}")
    d = get_dur(mp3)
    page_dur = math.ceil(d + BUFFER)   # 無條件進位到整秒
    durs.append(page_dur)
    print(f"  page-{i:02d}.mp3  {d:.2f}s  → slide {page_dur}s")

total = sum(durs)
print(f"  Total: {total}s ({total/60:.1f} min)\n")

# ── Step 2: 複製 MP3 到 HF assets ────────────────────────
print("=== Step 2: 複製音檔 ===")
for i in range(1, N_PAGES+1):
    src = NARR / f"page-{i:02d}.mp3"
    dst = AUDIO / f"page-{i:02d}.mp3"
    shutil.copy2(src, dst)
    print(f"  copied page-{i:02d}.mp3")

# ── Step 3: 更新 index.html 時間 ─────────────────────────
print("\n=== Step 3: 更新 index.html ===")
html_path = HF / "index.html"
html = html_path.read_text(encoding="utf-8")

# 更新 root data-duration
html = re.sub(
    r'(data-composition-id="main"[^>]*data-duration=")[^"]+(")',
    lambda m: m.group(0).replace(
        m.group(0),
        m.group(0)[:m.group(0).index('data-duration="')+15] + str(total) + '"' + m.group(0)[m.group(0).index('data-duration="')+15:].split('"')[1:][-0] + '"'
    ),
    html
)
# 簡單直接替換
html = re.sub(r'data-duration="120"', f'data-duration="{total}"', html)

# 更新每頁 data-start 和 data-duration
starts = [0]
for d in durs[:-1]:
    starts.append(starts[-1] + d)

for i in range(N_PAGES):
    pid = i + 1
    old_start = i * 10
    old_dur = 10
    new_start = starts[i]
    new_dur = durs[i]
    # 替換每個 clip 的 data-start 和 data-duration
    html = html.replace(
        f'id="p{pid}" class="slide clip" data-start="{old_start}" data-duration="{old_dur}"',
        f'id="p{pid}" class="slide clip" data-start="{new_start}" data-duration="{new_dur}"'
    )
    print(f"  p{pid}: start={new_start}s dur={new_dur}s")

# 更新 GSAP O() 函數和進度條寬度
# O(n) = starts[n-1]，直接在 JS 裡改成硬編碼
def O(n): return starts[n-1]

# 替換 GSAP 時間偏移 O(1)~O(12) → 實際數值
for i in range(1, N_PAGES+1):
    html = html.replace(f', O({i})+', f', {O(i)}+')

# 替換進度條寬度
pct_map = {
    1: 100/N_PAGES, 2: 200/N_PAGES, 3: 300/N_PAGES, 4: 400/N_PAGES,
    5: 500/N_PAGES, 6: 600/N_PAGES, 7: 700/N_PAGES, 8: 800/N_PAGES,
    9: 900/N_PAGES, 10: 1000/N_PAGES, 11: 1100/N_PAGES, 12: 100.0
}
for i, pct in pct_map.items():
    old = f"width:'{pct_map[i]:.2f}%'"
    # 進度條動畫時長也要更新
    html = re.sub(
        rf"(#p{i}p.*?width:')[\d.]+(%'.*?duration:)[\d.]+",
        lambda m, ni=i: m.group(0)[:m.group(0).index("width:'")+7] +
                        f"{pct:.2f}" + m.group(0)[m.group(0).index("%'"):m.group(0).index("duration:")+9] +
                        str(durs[ni-1]-0.5),
        html
    )

html_path.write_text(html, encoding="utf-8")
print("  index.html 更新完成\n")

# ── Step 4: 串接音軌 ─────────────────────────────────────
print("=== Step 4: 串接音軌 ===")
combined = HF / "combined_audio.mp3"
filter_parts = []
input_args = []

for i in range(1, N_PAGES+1):
    mp3 = AUDIO / f"page-{i:02d}.mp3"
    input_args += ["-i", str(mp3)]

# 建立 silence + audio concat
# 使用 adelay 讓每段音頻在正確時間點播放
delays_ms = [int(s * 1000) for s in starts]

filter_complex = ""
for i in range(N_PAGES):
    filter_complex += f"[{i}]adelay={delays_ms[i]}|{delays_ms[i]}[a{i}];"
filter_complex += "".join(f"[a{i}]" for i in range(N_PAGES))
filter_complex += f"amix=inputs={N_PAGES}:duration=longest[out]"

cmd = ["ffmpeg", "-y"] + input_args + [
    "-filter_complex", filter_complex,
    "-map", "[out]",
    "-ar", "44100", "-ac", "2",
    str(combined)
]
print("  running ffmpeg amix...")
subprocess.run(cmd, check=True, capture_output=True)
print(f"  combined_audio.mp3 → {combined.stat().st_size//1024} KB\n")

# ── Step 5: Render HyperFrames ───────────────────────────
print("=== Step 5: HyperFrames render ===")
video_no_audio = HF / "isotank-full-noaudio.mp4"
subprocess.run(
    ["npx", "hyperframes", "render", "-o", str(video_no_audio)],
    cwd=str(HF), check=True
)
print(f"  rendered: {video_no_audio}\n")

# ── Step 6: Mux 音軌 ─────────────────────────────────────
print("=== Step 6: Mux 音軌進影片 ===")
final = HF / "isotank-final.mp4"
subprocess.run([
    "ffmpeg", "-y",
    "-i", str(video_no_audio),
    "-i", str(combined),
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest", str(final)
], check=True)
print(f"\n✅ 完成！最終影片：{final}")
print(f"   大小：{final.stat().st_size//1024//1024} MB")
