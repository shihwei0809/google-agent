#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小妤的大阪冒險之旅 - 有聲漫畫影片自動合成腳本 (Manga E-book Video Synthesizer)
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path

# 強制將標準輸出與標準錯誤流重設為 UTF-8 避免 Windows CP950 編碼出錯
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# 角色對應中文名稱
CHARACTERS = {
    "sakura": "小妤",
    "taiga": "小融",
    "papa": "爸爸",
    "mama": "媽媽"
}

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        ms = 999
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def get_audio_duration(audio_path):
    cmd = [
        "ffprobe", "-v", "error", 
        "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        str(audio_path)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception as e:
        print(f"⚠️ 無法讀取音檔長度 {audio_path}: {e}")
        return 2.0  # 預設 2 秒

def generate_silence(duration, output_path):
    # 產生指定長度的靜音 MP3
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", 
        "-i", f"anullsrc=r=24000:cl=mono", 
        "-t", str(duration), 
        "-c:a", "libmp3lame", "-q:a", "2", 
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def main():
    base_dir = Path(__file__).parent.resolve()
    story_json_path = base_dir / "story.json"
    assets_dir = base_dir / "assets"
    audio_dir = assets_dir / "audio"
    images_dir = assets_dir / "images"
    
    if not story_json_path.exists():
        print(f"❌ 找不到 story.json：{story_json_path}")
        return 1
        
    print("📖 正在載入 story.json...")
    with open(story_json_path, "r", encoding="utf-8") as f:
        story_data = json.load(f)
        
    # 建立臨時編譯目錄
    temp_dir = base_dir / "temp_video"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 產生 0.6 秒的對話間隔靜音檔
    silence_mp3 = temp_dir / "silence.mp3"
    print("🎵 正在產生對話間隔靜音檔...")
    generate_silence(0.6, silence_mp3)
    
    # 收集各畫格影片路徑
    panel_videos = []
    
    # 建立總字幕列表
    master_srt_lines = []
    global_time_offset = 0.0
    subtitle_idx = 1
    
    print("🎬 開始處理各漫畫畫格...")
    for page in story_data["pages"]:
        page_num = page["pageNumber"]
        page_title = page["pageTitle"]
        print(f"\n📂 處理頁面 {page_num}: {page_title}")
        
        for panel in page["panels"]:
            panel_num = panel["panelNumber"]
            panel_id = f"p{page_num}_panel{panel_num}"
            print(f"  └ 畫格 {panel_num} ({panel_id})...")
            
            # 尋找圖片
            img_path = base_dir / panel["image"]
            if not img_path.exists():
                # 備用路徑
                img_path = images_dir / f"{panel_id}.png"
                if not img_path.exists():
                    print(f"    ❌ 找不到圖片檔: {panel['image']}")
                    continue
            
            # 整理對話與尋找音檔
            dialogues = panel["dialogues"]
            audio_inputs = []
            srt_entries = []
            current_panel_duration = 0.0
            
            for idx, dial in enumerate(dialogues):
                dial_id = dial["id"]
                speaker_key = dial["speaker"]
                speaker_name = CHARACTERS.get(speaker_key, speaker_key)
                text = dial["text"]
                
                # 音檔搜尋順序: ms_ > (no prefix) > el_
                audio_file = audio_dir / f"ms_{dial_id}.mp3"
                if not audio_file.exists():
                    audio_file = audio_dir / f"{dial_id}.mp3"
                if not audio_file.exists():
                    audio_file = audio_dir / f"el_{dial_id}.mp3"
                    
                if not audio_file.exists():
                    print(f"    ⚠️ 找不到音檔 {dial_id}.mp3，將產生 2 秒臨時靜音。")
                    temp_audio_file = temp_dir / f"temp_{dial_id}.mp3"
                    generate_silence(2.0, temp_audio_file)
                    audio_file = temp_audio_file
                
                duration = get_audio_duration(audio_file)
                
                # 計算對話播放區間
                start_time = current_panel_duration
                end_time = start_time + duration
                
                # 記錄單一對白字幕
                srt_entries.append({
                    "start": start_time,
                    "end": end_time,
                    "text": f"{speaker_name}: {text}"
                })
                
                # 記錄總字幕
                master_srt_lines.append(
                    f"{subtitle_idx}\n"
                    f"{format_srt_time(global_time_offset + start_time)} --> {format_srt_time(global_time_offset + end_time)}\n"
                    f"{speaker_name}: {text}\n"
                )
                subtitle_idx += 1
                
                # 收集音檔
                audio_inputs.append(audio_file)
                current_panel_duration = end_time
                
                # 插入間隔靜音 (除了最後一句)
                if idx < len(dialogues) - 1:
                    audio_inputs.append(silence_mp3)
                    current_panel_duration += 0.6
            
            # 如果整格沒有任何對話音檔，給予 3 秒預設時間
            if not audio_inputs:
                print("    ⚠️ 無對白，設定 3 秒靜音畫格。")
                temp_audio_file = temp_dir / f"temp_{panel_id}.mp3"
                generate_silence(3.0, temp_audio_file)
                audio_inputs.append(temp_audio_file)
                current_panel_duration = 3.0
                
            # 1. 合併畫格音檔
            panel_audio_path = temp_dir / f"{panel_id}_audio.mp3"
            
            # 使用 ffmpeg concat 合併
            concat_list_path = temp_dir / f"{panel_id}_audio_list.txt"
            with open(concat_list_path, "w", encoding="utf-8") as f:
                for a_in in audio_inputs:
                    # ffmpeg 讀取路徑需要將反斜線轉為正斜線
                    f.write(f"file '{str(a_in.resolve()).replace('\\', '/')}'\n")
            
            cmd_concat = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
                "-i", str(concat_list_path), 
                "-c:a", "libmp3lame", "-q:a", "2", 
                str(panel_audio_path)
            ]
            subprocess.run(cmd_concat, capture_output=True, check=True)
            
            # 2. 建立此畫格的 SRT 字幕
            panel_srt_path = temp_dir / f"{panel_id}.srt"
            with open(panel_srt_path, "w", encoding="utf-8") as f:
                for s_idx, entry in enumerate(srt_entries, 1):
                    f.write(f"{s_idx}\n")
                    f.write(f"{format_srt_time(entry['start'])} --> {format_srt_time(entry['end'])}\n")
                    f.write(f"{entry['text']}\n\n")
            
            # 3. 壓製為該畫格影片 (解析度 1024x1024，不燒錄硬字幕，保持畫面乾淨)
            panel_video_path = temp_dir / f"{panel_id}.mp4"
            
            cmd_video = [
                "ffmpeg", "-y", "-loop", "1", "-i", str(img_path.resolve()), 
                "-i", str(panel_audio_path.name),
                "-c:v", "libx264", "-t", str(current_panel_duration), 
                "-r", "25", "-pix_fmt", "yuv420p", 
                "-c:a", "aac", "-b:a", "192k", "-shortest", 
                str(panel_video_path.name)
            ]
            
            print("    🎥 正在產生畫格 MP4 (無硬字幕)...")
            subprocess.run(cmd_video, cwd=str(temp_dir), capture_output=True, check=True)
            print("    ✅ 成功合成無字幕畫格影片。")
                
            panel_videos.append(panel_video_path)
            global_time_offset += current_panel_duration
            
    if not panel_videos:
        print("❌ 沒有成功的畫格影片可以合併。")
        return 1
        
    # 4. 合併所有畫格影片
    print("\n📦 正在合併所有畫格為最終影片...")
    video_list_path = temp_dir / "video_list.txt"
    with open(video_list_path, "w", encoding="utf-8") as f:
        for pv in panel_videos:
            f.write(f"file '{pv.name}'\n")
            
    final_video_name = "osaka_adventure.mp4"
    final_video_path = assets_dir / final_video_name
    
    cmd_merge = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
        "-i", "video_list.txt", 
        "-c", "copy", 
        str(final_video_path.resolve())
    ]
    
    try:
        subprocess.run(cmd_merge, cwd=str(temp_dir), capture_output=True, check=True)
        print(f"\n🎉 影片合成成功！")
        print(f"🎬 輸出路徑：{final_video_path.resolve()}")
    except Exception as e:
        print(f"\n❌ 合併最終影片失敗: {e}")
        return 1
        
    # 5. 輸出總字幕檔
    final_srt_path = assets_dir / "osaka_adventure.srt"
    with open(final_srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(master_srt_lines))
    print(f"📝 總字幕檔輸出路徑：{final_srt_path.resolve()}")
    
    # 刪除臨時編譯目錄以節省空間
    print("🧹 正在清理臨時快取檔案...")
    try:
        shutil.rmtree(temp_dir)
        print("✅ 清理完成！")
    except Exception as e:
        print(f"⚠️ 清理臨時目錄失敗: {e}")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
