import os
import re
import shutil
import sys
import subprocess

# Configure sys.stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Root paths
workspace_dir = r"c:\GOOGLE ANGET\ai anget"
images_source_dir = os.path.join(workspace_dir, "圖片")
output_root = os.path.join(workspace_dir, "創作庫")

# Verify source images exist
images_list = [f"{i:02d}" for i in range(1, 18)] # 01 to 17
all_images = [f for f in os.listdir(images_source_dir) if f.endswith(".png")]

def get_audio_duration(audio_path):
    cmd = ["ffmpeg", "-i", audio_path]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3))
        return hours * 3600 + minutes * 60 + seconds
    return None

def compile_mv(audio_path, images_paths, output_video_path, duration_per_image):
    # Create temp concat file
    inputs_txt_path = os.path.join(workspace_dir, "temp_slideshow.txt")
    with open(inputs_txt_path, "w", encoding="utf-8") as out:
        for img_path in images_paths:
            escaped_path = img_path.replace("'", "'\\''").replace("\\", "/")
            out.write(f"file '{escaped_path}'\n")
            out.write(f"duration {duration_per_image}\n")
        # Write last image twice as required by ffmpeg concat demuxer
        escaped_last_path = images_paths[-1].replace("'", "'\\''").replace("\\", "/")
        out.write(f"file '{escaped_last_path}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", inputs_txt_path, "-i", audio_path,
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", output_video_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        success = True
    except subprocess.CalledProcessError as e:
        print(f"  [X] ffmpeg 失敗: {e.stderr}")
        success = False
    finally:
        if os.path.exists(inputs_txt_path):
            os.remove(inputs_txt_path)
    return success

def main():
    if not os.path.exists(images_source_dir):
        print(f"錯誤: 找不到圖片來源資料夾: {images_source_dir}")
        return

    # Find all source images and sort them numerically
    src_images = []
    for img in sorted(os.listdir(images_source_dir)):
        if img.endswith(".png"):
            src_images.append(os.path.join(images_source_dir, img))

    if not src_images:
        print("錯誤: 圖片資料夾內無 PNG 檔案！")
        return
        
    print(f"已載入 {len(src_images)} 張故事板圖片。")

    # Find all MP3 files
    mp3_files = [f for f in os.listdir(workspace_dir) if f.endswith(".mp3") and f != "勝一化學_Suno音樂合輯.mp3"]
    print(f"偵測到 {len(mp3_files)} 首歌曲。準備進行分類與影片渲染...\n")

    for mp3 in mp3_files:
        song_name = os.path.splitext(mp3)[0]
        song_dir = os.path.join(output_root, song_name)
        song_images_dir = os.path.join(song_dir, "圖片")

        print(f"➔ 正在處理歌曲: 【{song_name}】")
        
        # 1. Create directories
        os.makedirs(song_images_dir, exist_ok=True)
        
        # 2. Copy MP3
        src_mp3_path = os.path.join(workspace_dir, mp3)
        dest_mp3_path = os.path.join(song_dir, mp3)
        shutil.copy2(src_mp3_path, dest_mp3_path)
        print(f"  [✓] 已複製音訊檔")

        # 3. Copy Images
        copied_images = []
        for img_path in src_images:
            basename = os.path.basename(img_path)
            dest_img_path = os.path.join(song_images_dir, basename)
            shutil.copy2(img_path, dest_img_path)
            copied_images.append(dest_img_path)
        print(f"  [✓] 已複製 {len(copied_images)} 張故事板圖片")

        # 4. Detect Duration & Compile Video
        duration = get_audio_duration(dest_mp3_path)
        if duration:
            duration_per_image = duration / len(copied_images)
            output_video_path = os.path.join(song_dir, f"{song_name}_MV.mp4")
            print(f"  [*] 偵測長度: {duration:.2f} 秒，每張圖播放時長: {duration_per_image:.2f} 秒。渲染影片中...")
            
            if compile_mv(dest_mp3_path, copied_images, output_video_path, duration_per_image):
                print(f"  [✓] MV 影片生成成功！儲存於: {os.path.basename(output_video_path)}")
            else:
                print(f"  [X] MV 影片生成失敗！")
        else:
            print(f"  [X] 無法偵測音訊長度，跳過影片生成。")
        print("-" * 50)

    print("\n🎉 所有歌曲資料夾分類與 MV 生成完成！")

if __name__ == "__main__":
    main()
