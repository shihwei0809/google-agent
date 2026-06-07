# 動態尋找 WebM 並與 MP3 進行高音質 Mux 合成
import os, glob, subprocess

dir_path = os.path.dirname(__file__)
renders_dir = os.path.join(dir_path, "renders")

# 尋找 renders/ 目錄下的所有 .webm 檔案
webm_files = glob.glob(os.path.join(renders_dir, "*.webm"))
if not webm_files:
    print("❌ 找不到錄製好的 WebM 影片檔！")
    exit(1)

# 取得最新的一份 WebM 檔案
webm_file = max(webm_files, key=os.path.getmtime)
master_audio = os.path.join(renders_dir, "master_audio.mp3")
final_output = os.path.join(renders_dir, "ISOTANK_卸料安全訓練影片.mp4")

print(f"WebM 影片源：{webm_file}")
print(f"MP3 旁白源：{master_audio}")
print("正在合併音視頻...")

# ffmpeg Mux 指令 — 依規範加 -map 以防 webm 空音軌覆蓋旁白，並轉成 H.264 MP4 格式
cmd = [
    "ffmpeg", "-y",
    "-i", webm_file,
    "-i", master_audio,
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-c:v", "libx264",
    "-crf", "20",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    final_output
]

subprocess.run(cmd, check=True)
print(f"[OK] 合成完成！最終影片路徑：{final_output}")
