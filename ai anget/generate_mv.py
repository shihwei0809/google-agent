import os
import re
import sys
import subprocess

# Configure sys.stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Paths
workspace_dir = r"c:\GOOGLE ANGET\ai anget"
audio_file = os.path.join(workspace_dir, "純淨之光-男女合唱.mp3")
output_video = os.path.join(workspace_dir, "勝一化學_純淨之光_MV.mp4")

# List of 17 image files in order of the storyboard
images_dir = os.path.join(workspace_dir, "圖片")
images_list = [
    "01_夜幕精餾廠區.png",
    "02_化學分子模擬.png",
    "03_全息分子模型.png",
    "04_自動化實驗室分裝.png",
    "05_專業化學_QC_檢驗.png",
    "06_精餾閥門管道.png",
    "07_無塵自動化封裝線.png",
    "08_晶圓傳送天車.png",
    "09_晶圓溶劑清洗.png",
    "10_曝光顯影製程.png",
    "11_雷射光刻奈米雕刻.png",
    "12_自動化黃光區無塵室.png",
    "13_高科技晶片核心.png",
    "14_廢溶劑綠色循環.png",
    "15_永續綠色科技廠房.png",
    "16_AI_超級電腦機房.png",
    "17_環保港口與貨輪出海.png"
]




def get_audio_duration(audio_path):
    print("正在偵測音訊檔長度...")
    cmd = ["ffmpeg", "-i", audio_path]
    # ffmpeg outputs info to stderr
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    
    # Search for Duration: HH:MM:SS.xx
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3))
        total_seconds = hours * 3600 + minutes * 60 + seconds
        print(f"偵測到音訊長度: {total_seconds} 秒 ({match.group(0).strip()})")
        return total_seconds
    else:
        print("無法從 ffmpeg 偵測到音訊長度，將使用預設 140 秒。")
        return 140.0

def main():
    if not os.path.exists(audio_file):
        print(f"錯誤: 找不到音訊檔案 {audio_file}")
        return
        
    total_duration = get_audio_duration(audio_file)
    num_images = len(images_list)
    duration_per_image = total_duration / num_images
    print(f"共計 {num_images} 張圖片，每張圖片顯示時間: {duration_per_image:.2f} 秒")
    
    # Verify all images exist
    verified_images = []
    for img in images_list:
        img_path = os.path.join(images_dir, img)
        if os.path.exists(img_path):
            verified_images.append(img_path)
        else:
            print(f"錯誤: 找不到圖片 {img_path}")
            return
            
    # Create inputs.txt for ffmpeg slideshow
    inputs_txt_path = os.path.join(workspace_dir, "slideshow_inputs.txt")
    with open(inputs_txt_path, "w", encoding="utf-8") as out:
        for img_path in verified_images:
            # Escape paths for ffmpeg concat demuxer
            escaped_path = img_path.replace("'", "'\\''").replace("\\", "/")
            out.write(f"file '{escaped_path}'\n")
            out.write(f"duration {duration_per_image}\n")
        # ffmpeg concat demuxer requires the last file to be written twice
        escaped_last_path = verified_images[-1].replace("'", "'\\''").replace("\\", "/")
        out.write(f"file '{escaped_last_path}'\n")
        
    print("\n正在使用 ffmpeg 合併圖片與音訊生成 MP4 影片 (預計需要 10-20 秒)...")
    
    # ffmpeg command to compile slideshow with audio
    # -c:v libx264: H.264 video codec
    # -tune stillimage: Optimize for still images
    # -pix_fmt yuv420p: Ensure compatibility with standard players
    # -shortest: Stop writing when the audio finishes
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", inputs_txt_path, "-i", audio_file,
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", output_video
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("\n🎉 影片合併成功！")
        print(f"🎬 輸出影片已儲存至: {output_video}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ffmpeg 影片生成失敗！")
        print(f"錯誤訊息:\n{e.stderr}")
    finally:
        # Clean up temp inputs file
        if os.path.exists(inputs_txt_path):
            os.remove(inputs_txt_path)

if __name__ == "__main__":
    main()
