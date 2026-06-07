# 自動合成與對齊旁白音軌
import os, subprocess

PAGES = [
  { "i": 1, "dur": 12.9 },
  { "i": 2, "dur": 14.3 },
  { "i": 3, "dur": 13.8 },
  { "i": 4, "dur": 15.6 },
  { "i": 5, "dur": 14.7 },
  { "i": 6, "dur": 14.0 },
  { "i": 7, "dur": 14.2 },
  { "i": 8, "dur": 12.6 },
  { "i": 9, "dur": 6.7  },
]

dir_path = os.path.dirname(__file__)
narr_dir = os.path.join(dir_path, "assets", "narration")
renders_dir = os.path.join(dir_path, "renders")
os.makedirs(renders_dir, exist_ok=True)

# 1. 將每頁音檔加上 padding 到指定的 dur 長度
padded_files = []
for p in PAGES:
    idx = p["i"]
    dur = p["dur"]
    src = os.path.join(narr_dir, f"page-{idx:02d}.mp3")
    dest = os.path.join(renders_dir, f"pad_page_{idx:02d}.mp3")
    
    print(f"Padding page-{idx:02d}.mp3 to {dur} seconds...")
    cmd = [
        "ffmpeg", "-y", "-i", src,
        "-af", f"apad=whole_dur={dur}",
        "-t", str(dur),
        dest
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    padded_files.append(dest)

# 2. 建立 concat 用的清單檔 ( ffmpeg concat list.txt )
# 為了避免中文路徑問題（GOTCHAS E-3），我們在 renders/ 目錄下使用相對路徑
list_txt_path = os.path.join(renders_dir, "list.txt")
with open(list_txt_path, "w", encoding="utf-8") as f:
    for p in PAGES:
        idx = p["i"]
        f.write(f"file 'pad_page_{idx:02d}.mp3'\n")

# 3. 合成 master_audio.mp3
master_audio = os.path.join(renders_dir, "master_audio.mp3")
print("Concatenating into master_audio.mp3...")
cmd = [
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", list_txt_path, "-c", "copy", master_audio
]
# 在 renders/ 目錄下執行以解決 ffmpeg 讀取相對路徑的問題
subprocess.run(cmd, check=True, cwd=renders_dir)

print(f"[OK] master_audio.mp3 合成完成：{master_audio}")
