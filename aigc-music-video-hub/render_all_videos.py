import os
import re
import subprocess
import sys
from pathlib import Path

# Configure sys.stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

workspace_dir = Path(r"c:\GOOGLE ANGET\aigc-music-video-hub")
output_root = workspace_dir / "創作庫"

template_shanyi = workspace_dir / "勝一化學_純淨之光_MV.mp4"
template_changbin = workspace_dir / "《彰濱的科技之翼》—電音版.mp4"

def get_audio_duration(audio_path):
    cmd = ["ffmpeg", "-i", str(audio_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3))
        return hours * 3600 + minutes * 60 + seconds
    return None

def apply_template(template_path, audio_path, output_path, duration):
    # Mux template video loop with the audio track
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(template_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
    ]
    if duration:
        cmd.extend(["-t", f"{duration:.3f}"])
    else:
        cmd.append("-shortest")
    cmd.append(str(output_path))
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [X] FFmpeg 合成失敗: {e.stderr}")
        return False

def main():
    print("==================================================")
    print("🎬 開始偵測並生成缺少的 AI 音樂影片 (MV)...")
    print("==================================================")
    
    if not template_shanyi.exists() and not template_changbin.exists():
        print("❌ 錯誤: 找不到任何母片影片！")
        return
        
    folders = sorted([d for d in os.listdir(output_root) if (output_root / d).is_dir()])
    
    rendered_count = 0
    skipped_count = 0
    
    for folder in folders:
        song_dir = output_root / folder
        
        # Find MP3 inside this folder
        mp3s = [f for f in os.listdir(song_dir) if f.endswith(".mp3")]
        if not mp3s:
            continue
            
        mp3_file = mp3s[0]
        mp3_path = song_dir / mp3_file
        
        # Check if MV already exists
        output_mv_path = song_dir / f"{folder}_MV.mp4"
        
        if output_mv_path.exists():
            skipped_count += 1
            continue
            
        # Determine the template
        # If it's a Hongsheng, Changbin, scan, or SOP song, use the electro template
        folder_lower = folder.lower()
        if any(kw in folder_lower for kw in ["彰濱", "鴻勝", "虹昇", "智慧流動", "網格交響", "流動軌跡", "流向", "去化", "格外"]):
            template_path = template_changbin
            template_name = "彰濱版電音母片"
        else:
            template_path = template_shanyi
            template_name = "勝一版純淨母片"
            
        if not template_path.exists():
            print(f"  [!] 無法處理 {folder}：找不到對應的 {template_name} ({template_path.name})")
            continue
            
        duration = get_audio_duration(mp3_path)
        print(f"➔ 發現缺少影片: 【{folder}】")
        print(f"  音軌長度: {duration:.2f} 秒 | 套用模版: {template_name}")
        
        if apply_template(template_path, mp3_path, output_mv_path, duration):
            print(f"  [✓] 成功生成: {output_mv_path.name}")
            rendered_count += 1
        else:
            print(f"  [X] 生成失敗: {folder}")
            
    print("--------------------------------------------------")
    print(f"🎉 影片生成任務完成！")
    print(f"  - 新增渲染 MV 影片: {rendered_count} 個")
    print(f"  - 已存在跳過: {skipped_count} 個")
    print("==================================================")

if __name__ == "__main__":
    main()
