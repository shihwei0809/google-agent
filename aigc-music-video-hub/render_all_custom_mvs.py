import os
import re
import subprocess
import sys
from pathlib import Path

# Configure sys.stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

workspace_dir = Path(os.path.dirname(os.path.abspath(__file__)))
output_root = workspace_dir / "創作庫"
images_dir = workspace_dir / "圖片"

def get_audio_duration(audio_path):
    cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)]
    result = subprocess.run(cmd, capture_output=True)
    duration_str = result.stdout.decode('utf-8', errors='ignore').strip()
    if duration_str:
        try:
            return float(duration_str)
        except ValueError:
            pass
    return 0

def render_slideshow(song_dir, folder_name):
    md_path = song_dir / "vids_storyboard_prompts.md"
    if not md_path.exists():
        print(f"    [!] 找不到故事板 MD 檔案: {md_path.name}")
        return False
        
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Read duration
    duration_match = re.search(r"歌曲總長度.*?`(.*?) 秒`", content)
    if duration_match:
        duration = float(duration_match.group(1))
    else:
        print("    [!] 無法從故事板中解析長度")
        return False

    # Find MP3 file in the directory
    mp3_files = [f for f in os.listdir(song_dir) if f.endswith(".mp3")]
    if not mp3_files:
        print("    [!] 找不到 MP3 檔案")
        return False
    mp3_name = mp3_files[0]
    mp3_path = song_dir / mp3_name
    
    # Recalculate duration from MP3 to be precise
    audio_duration = get_audio_duration(mp3_path)
    if audio_duration > 0:
        duration = audio_duration

    # Find all image filenames
    image_filenames = re.findall(r"圖片檔名.*?`(.*?)`", content)
    if not image_filenames:
        # Retry with Chinese character pattern if any
        image_filenames = re.findall(r"圖片狀態.*?你可以直接在資料夾內的.*?圖片.*?目錄找到此檔上傳.*?檔案名稱為.*?`(.*?)`", content)
        if not image_filenames:
            print("    [!] 無法從故事板解析圖片檔名列表")
            return False
        
    num_images = len(image_filenames)
    duration_per_image = duration / num_images

    # Generate slideshow_inputs.txt
    inputs_txt_path = song_dir / "slideshow_inputs.txt"
    with open(inputs_txt_path, "w", encoding="utf-8") as out:
        for img in image_filenames:
            # First try local song folder images dir, then fallback to root images dir
            img_path = song_dir / "圖片" / img
            if not img_path.exists():
                img_path = images_dir / img
            
            # If still not exist, warn
            if not img_path.exists():
                print(f"    [!] 找不到圖片: {img}")
                
            escaped_path = str(img_path).replace("'", "'\\''").replace("\\", "/")
            out.write(f"file '{escaped_path}'\n")
            out.write(f"duration {duration_per_image:.4f}\n")
            
        # Repeat the last file once at the end without duration (ffmpeg concat demuxer requirement)
        last_img = image_filenames[-1]
        last_img_path = song_dir / "圖片" / last_img
        if not last_img_path.exists():
            last_img_path = images_dir / last_img
        escaped_last_path = str(last_img_path).replace("'", "'\\''").replace("\\", "/")
        out.write(f"file '{escaped_last_path}'\n")

    output_mv_path = song_dir / f"{folder_name}_MV.mp4"
    
    # Render with FFmpeg
    # -shortest: stops writing when the audio stream ends
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(inputs_txt_path),
        "-i", str(mp3_path),
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        str(output_mv_path)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        # Clean up temp concat file
        if inputs_txt_path.exists():
            os.remove(inputs_txt_path)
        return True
    except subprocess.CalledProcessError as e:
        print(f"    [X] FFmpeg 渲染失敗: {e.stderr.decode('utf-8', errors='ignore')[-500:]}")
        if inputs_txt_path.exists():
            os.remove(inputs_txt_path)
        return False

def main():
    print("==================================================")
    print("🎬 開始在 [ai anget] 專案渲染所有客製化投影片 MV...")
    print("==================================================")
    
    folders = sorted([d for d in os.listdir(output_root) if (output_root / d).is_dir()])
    
    success_count = 0
    fail_count = 0
    
    for idx, folder in enumerate(folders, 1):
        song_dir = output_root / folder
        print(f"[{idx}/{len(folders)}] 正在處理: 【{folder}】")
        
        # Render custom slideshow (always overwrite)
        if render_slideshow(song_dir, folder):
            print(f"  [✓] 成功生成投影片 MV")
            success_count += 1
        else:
            print(f"  [X] 無法生成投影片 MV")
            fail_count += 1
            
    print("--------------------------------------------------")
    print(f"🎉 任務完成！")
    print(f"  - 成功生成: {success_count} 個")
    print(f"  - 跳過或失敗: {fail_count} 個")
    print("==================================================")

if __name__ == "__main__":
    main()
