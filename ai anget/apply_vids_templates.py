import os
import re
import sys
import subprocess

# Configure sys.stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

workspace_dir = r"c:\GOOGLE ANGET\ai anget"
output_root = os.path.join(workspace_dir, "創作庫")

# Template video names expected at the root
template_shanyi = os.path.join(workspace_dir, "勝一化學_純淨之光_MV.mp4")
template_changbin = os.path.join(workspace_dir, "《彰濱的科技之翼》—電音版.mp4")

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

def apply_template(template_path, audio_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", template_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [X] FFmpeg 套用失敗: {e.stderr}")
        return False

def main():
    print("🎬 開始執行 Google Vids 母片影片音軌批次套用程序...")
    
    shanyi_exists = os.path.exists(template_shanyi)
    changbin_exists = os.path.exists(template_changbin)
    
    if not shanyi_exists and not changbin_exists:
        print("\n❌ 錯誤: 在根目錄下找不到任何母片影片！")
        print(f"請確保您已將 Vids 生成的影片下載並命名為以下檔案放在根目錄中:")
        print(f"  1. [勝一版] -> {os.path.basename(template_shanyi)}")
        print(f"  2. [彰濱版] -> {os.path.basename(template_changbin)}")
        return
        
    if shanyi_exists:
        print(f"  [✓] 偵測到勝一母片: {os.path.basename(template_shanyi)}")
    else:
        print(f"  [!] 未偵測到勝一母片，將跳過勝一版套用。")
        
    if changbin_exists:
        print(f"  [✓] 偵測到彰濱母片: {os.path.basename(template_changbin)}")
    else:
        print(f"  [!] 未偵測到彰濱母片，將跳過彰濱版套用。")

    mp3_files = [f for f in os.listdir(workspace_dir) if f.endswith(".mp3") and f != "勝一化學_Suno音樂合輯.mp3"]
    print(f"\n🎵 找到 {len(mp3_files)} 首 MP3 歌曲。開始處理...")
    
    for mp3 in mp3_files:
        song_name = os.path.splitext(mp3)[0]
        song_dir = os.path.join(output_root, song_name)
        dest_mp3_path = os.path.join(song_dir, mp3)
        
        os.makedirs(song_dir, exist_ok=True)
        
        print(f"\n➔ 正在處理歌曲: 【{song_name}】")
        
        src_mp3 = dest_mp3_path if os.path.exists(dest_mp3_path) else os.path.join(workspace_dir, mp3)
        
        if shanyi_exists:
            output_shanyi = os.path.join(song_dir, f"{song_name}_純淨之光_Vids版.mp4")
            print(f"  [*] 套用 [勝一版] 模版...")
            if apply_template(template_shanyi, src_mp3, output_shanyi):
                print(f"  [✓] 成功生成: {os.path.basename(output_shanyi)}")
            else:
                print(f"  [X] 生成 [勝一版] 失敗")
                
        if changbin_exists:
            output_changbin = os.path.join(song_dir, f"{song_name}_彰濱之翼_Vids版.mp4")
            print(f"  [*] 套用 [彰濱版] 模版...")
            if apply_template(template_changbin, src_mp3, output_changbin):
                print(f"  [✓] 成功生成: {os.path.basename(output_changbin)}")
            else:
                print(f"  [X] 生成 [彰濱版] 失敗")
                
    print("\n🎉 所有 MP3 歌曲的 Vids 母片音軌套用完成！已分發至各自資料夾！")

if __name__ == "__main__":
    main()
