# 同時生成「有旁白+背景音樂」與「無旁白僅有背景音樂」兩種版本的影片
import os, glob, subprocess

dir_path = os.path.dirname(__file__)
renders_dir = os.path.join(dir_path, "renders")

webm_files = glob.glob(os.path.join(renders_dir, "*.webm"))
if not webm_files:
    print("❌ 找不到錄製好的 WebM 影片檔！")
    exit(1)

webm_file = max(webm_files, key=os.path.getmtime)
master_audio = os.path.join(renders_dir, "master_audio.mp3")
bgm_audio = os.path.join(dir_path, "assets", "audio", "bgm.mp3")

output_a = os.path.join(renders_dir, "國小畢旅二天一夜回憶錄_有旁白與背景音樂.mp4")
output_b = os.path.join(renders_dir, "國小畢旅二天一夜回憶錄_僅背景音樂版.mp4")

print(f"WebM 影片源：{webm_file}")
print(f"MP3 旁白源：{master_audio}")
print(f"MP3 鋼琴背景音樂源：{bgm_audio}")

# ==================== 1. 合成版本 A（有旁白與背景音樂） ====================
print("\n[1/2] 正在合成：有旁白與背景音樂版...")
# 使用 filter_complex 將旁白 (加強至 1.2倍) 與背景音樂 (壓低至 0.22倍) 完美混音
cmd_a = [
    "ffmpeg", "-y",
    "-i", webm_file,
    "-i", master_audio,
    "-i", bgm_audio,
    "-filter_complex", "[1:a]volume=1.2[a1];[2:a]volume=0.22[a2];[a1][a2]amix=inputs=2:duration=first[a]",
    "-map", "0:v:0",
    "-map", "[a]",
    "-c:v", "libx264",
    "-crf", "20",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    output_a
]
subprocess.run(cmd_a, check=True)
print(f"✓ 版本 A 合成完成：{output_a}")

# ==================== 2. 合成版本 B（僅背景音樂版） ====================
print("\n[2/2] 正在合成：僅背景音樂版...")
# 直接將影片 WebM 與背景音樂 bgm.mp3 (音量 0.75倍) 進行 mux 合成
cmd_b = [
    "ffmpeg", "-y",
    "-i", webm_file,
    "-i", bgm_audio,
    "-filter_complex", "[1:a]volume=0.75[a1]",
    "-map", "0:v:0",
    "-map", "[a1]",
    "-c:v", "libx264",
    "-crf", "20",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    output_b
]
subprocess.run(cmd_b, check=True)
print(f"✓ 版本 B 合成完成：{output_b}")

print("\n✅ 兩種版本的影片全部順利合成完畢！")
