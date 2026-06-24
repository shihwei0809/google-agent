import os
import re
import json
import sys
import subprocess

# Configure sys.stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

workspace_dir = os.path.dirname(os.path.abspath(__file__))
output_root = os.path.join(workspace_dir, "創作庫")
dashboard_html_path = os.path.join(workspace_dir, "音樂影片專案總覽.html")

def get_audio_duration(audio_path):
    cmd = ["ffmpeg", "-i", audio_path]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3))
        return hours * 3600 + minutes * 60 + seconds
    return 0

def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def generate_introduction(folder_name):
    cleaned = folder_name.lower()
    if "彰濱" in cleaned or "changbin" in cleaned:
        return "本曲以勝一化學彰濱二廠與綠色科技園區為主題，描繪濱海風機旋轉下的現代化精餾廠房。在純淨的溶劑與綠色永續綠能引領下，展現勝一化學深耕半導體與先進製程供應鏈的卓越實力！"
    elif "虹昇" in cleaned or "智慧流動" in cleaned or "hongsheng" in cleaned:
        return "本曲譜寫虹昇化學在工業溶劑回收、智慧化去化與綠色循環的科技藍圖。以高科技中控室與環保再生技術為核心，將廢溶劑化為純淨再生資源，譜寫循環經濟的永續交響曲！"
    elif "綠色" in cleaned or "循環" in cleaned or "脈動" in cleaned or "pulse of green" in cleaned:
        return "本曲以綠色永續發展（ESG）為主題，敘述節能減碳、廢水回收、綠色包裝與循環經濟的深遠實踐。讓綠色循環的脈動在大地上生生不息，共創對環境友好的綠色未來！"
    elif "純淨" in cleaned or "purity" in cleaned or "液態精準" in cleaned or "liquid precision" in cleaned:
        return "本曲展現對超高純度半導體級溶劑的極致工藝追求。從電子級無塵室的精密自動化分裝，到黃光區的晶圓清洗曝光，每一步都是對極致純淨與科技創新的承諾！"
    elif "攜手未來" in cleaned or "弈融" in cleaned:
        return "本曲展現團隊攜手共創永續未來的卓越力量。從港口的貨輪裝箱出海，到半導體晶片的智慧應用，勝一化學以專業與堅持，與您攜手同行，開創綠能永續的新時代！"
    else:
        return "勝一化學與鴻勝化學 AIGC 節能與永續發展主題歌曲，譜寫科技創新與環境友好的永續藍圖。"

def generate_youtube_assets(folder_path, folder, lyrics, style_desc, duration):
    # 1. lyrics.txt
    lyrics_txt_path = os.path.join(folder_path, "lyrics.txt")
    if not os.path.exists(lyrics_txt_path) and lyrics:
        with open(lyrics_txt_path, "w", encoding="utf-8") as f:
            f.write(lyrics)
            
    # 2. youtube_description.txt
    desc_path = os.path.join(folder_path, "youtube_description.txt")
    if not os.path.exists(desc_path) and lyrics:
        intro = generate_introduction(folder)
        style_clean = re.sub(r"^\*\s*\*\*.*?\*\*：\s*", "", style_desc).replace("`", "").strip()
        with open(desc_path, "w", encoding="utf-8") as f:
            f.write(f"《{folder}》 - {style_clean}\n")
            f.write("勝一與鴻勝化學 AIGC 節能與永續主題歌曲\n\n")
            f.write("🎬 影片介紹：\n")
            f.write(f"{intro}\n\n")
            if style_clean:
                f.write("🎵 歌曲曲風：\n")
                f.write(f"{style_clean}\n\n")
            f.write("📝 完整歌詞：\n")
            f.write(f"{lyrics}\n")
            
    # 3. {folder}.srt
    srt_path = os.path.join(folder_path, f"{folder}.srt")
    if not os.path.exists(srt_path) and lyrics and duration > 0:
        lines = []
        for line in lyrics.split("\n"):
            line = line.strip()
            if line and not line.startswith("[") and not line.endswith("]"):
                lines.append(line)
                
        if lines:
            duration_per_line = duration / len(lines)
            with open(srt_path, "w", encoding="utf-8") as f:
                for idx, line in enumerate(lines, 1):
                    start_s = (idx - 1) * duration_per_line
                    end_s = idx * duration_per_line - 0.2
                    if end_s < start_s:
                        end_s = start_s + 0.1
                    f.write(f"{idx}\n")
                    f.write(f"{format_srt_time(start_s)} --> {format_srt_time(end_s)}\n")
                    f.write(f"{line}\n\n")

def get_base_name(folder_name):
    # Strip trailing numbers like (1), (2), (3) or (Remove Section)
    name = re.sub(r"\s*\(\d+\)$", "", folder_name)
    name = re.sub(r"\s*\(Remove\s+Section\)$", "", name, flags=re.IGNORECASE)
    
    # Remove any (1), (2) anywhere in the name, e.g., "永續的交響 (1)-史詩交響流行風" -> "永續的交響-史詩交響流行風"
    name = re.sub(r"\s*\(\d+\)", "", name)
    name = name.strip()
    
    # See if there's a style separator like "-" or "—"
    for sep in ["-", "—"]:
        if sep in name:
            parts = name.split(sep)
            prefix = parts[0].strip()
            if prefix:
                return prefix
                
    return name

def parse_storyboard_md(md_path):
    if not os.path.exists(md_path):
        return []
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    scenes = []
    # Split by "### 📌 "
    parts = content.split("### 📌 ")
    for part in parts[1:]:
        lines = part.strip().split("\n")
        if not lines:
            continue
            
        header = lines[0] # e.g. "場景 01：廠區遠景"
        scene_id = ""
        scene_name = ""
        match = re.match(r"場景\s*(\d+)[：:](.*)", header)
        if match:
            scene_id = match.group(1)
            scene_name = match.group(2).strip()
            
        time_limit = ""
        status = "🔴"
        filename = ""
        image_prompt = ""
        motion_prompt = ""
        
        recording_image = False
        recording_motion = False
        
        for line in lines:
            if "建議播放長度" in line:
                time_match = re.search(r"`(.*?)`", line)
                if time_match:
                    time_limit = time_match.group(1)
            elif "🟢" in line:
                status = "🟢"
            elif "圖片檔名" in line or "本機對照圖片" in line:
                fn_match = re.search(r"`(.*?)`", line)
                if fn_match:
                    filename = fn_match.group(1)
            elif "1. 圖片" in line:
                recording_image = True
                recording_motion = False
            elif "2. 動態" in line or "2. 影片" in line:
                recording_image = False
                recording_motion = True
            elif "```" in line:
                continue
            elif recording_image and line.strip():
                image_prompt = line.strip()
                recording_image = False
            elif recording_motion and line.strip():
                motion_prompt = line.strip()
                recording_motion = False
                
        scenes.append({
            "id": scene_id,
            "name": scene_name,
            "time": time_limit,
            "status": status,
            "filename": filename,
            "image_prompt": image_prompt,
            "motion_prompt": motion_prompt
        })
    return scenes

def parse_all_lyrics(workspace_dir):
    songbook_path = os.path.join(workspace_dir, "創作庫", "勝一與鴻勝化學_AI主題歌曲合輯.md")
    if not os.path.exists(songbook_path):
        return {}
        
    with open(songbook_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    lyrics_map = {}
    # Split by ### 🎵 or #### 🎵
    sections = re.split(r"(?:###|####) 🎵 ", content)
    for section in sections[1:]:
        lines = section.split("\n")
        title_line = lines[0].strip()
        title_match = re.search(r"《(.*?)》", title_line)
        if not title_match:
            continue
        title = title_match.group(1).strip()
        
        full_title = title_line
        
        lyrics_text = ""
        in_block = False
        block_lines = []
        for line in lines[1:]:
            if line.strip().startswith("```"):
                if in_block:
                    in_block = False
                    lyrics_text = "\n".join(block_lines)
                    break
                else:
                    in_block = True
            elif in_block:
                block_lines.append(line)
                
        style_desc = ""
        for line in lines[1:]:
            if "曲風設定" in line:
                style_desc = line.strip()
                break
                
        lyrics_map[full_title] = {
            "title": title,
            "full_title": full_title,
            "lyrics": lyrics_text,
            "style": style_desc
        }
    return lyrics_map

def find_matching_lyrics(folder_name, lyrics_map):
    cleaned = folder_name.replace("《", "").replace("》", "").replace("—", "").replace("-", "")
    cleaned = re.sub(r"\s*\(.*?\)", "", cleaned).strip()
    
    if "彰濱先鋒" in cleaned:
        match_key = [k for k in lyrics_map if "2.6" in k]
        if match_key: return lyrics_map[match_key[0]]
        
    if "攜手未來" in cleaned or "共創未來" in cleaned:
        match_key = [k for k in lyrics_map if "3.3" in k]
        if match_key: return lyrics_map[match_key[0]]
        
    if "彰濱" in cleaned:
        if any(kw in cleaned for kw in ["中國風", "啟航", "二廠啟航"]):
            match_key = [k for k in lyrics_map if "2.3.1" in k]
            if match_key: return lyrics_map[match_key[0]]
        else:
            match_key = [k for k in lyrics_map if "2.3.2" in k]
            if match_key: return lyrics_map[match_key[0]]
            
    if "智慧流動" in cleaned or "虹昇" in cleaned:
        if "中國風" in cleaned or "古風" in cleaned:
            match_key = [k for k in lyrics_map if "2.1.1" in k]
            if match_key: return lyrics_map[match_key[0]]
        else:
            match_key = [k for k in lyrics_map if "2.1.2" in k]
            if match_key: return lyrics_map[match_key[0]]
            
    if "綠色循環" in cleaned or "純淨的脈動" in cleaned or "Purity" in cleaned:
        if "聖衣" in cleaned:
            match_key = [k for k in lyrics_map if "1.3" in k]
            if match_key: return lyrics_map[match_key[0]]
        else:
            match_key = [k for k in lyrics_map if "1.2" in k]
            if match_key: return lyrics_map[match_key[0]]
            
    if "網格交響" in cleaned or "雙端的呼喚" in cleaned:
        if "中國風" in cleaned or "古風" in cleaned:
            match_key = [k for k in lyrics_map if "2.2.1" in k]
            if match_key: return lyrics_map[match_key[0]]
        else:
            match_key = [k for k in lyrics_map if "2.2.2" in k]
            if match_key: return lyrics_map[match_key[0]]
            
    if "流動軌跡" in cleaned or "產品流向" in cleaned:
        if "中國風" in cleaned or "古風" in cleaned:
            match_key = [k for k in lyrics_map if "2.4.1" in k]
            if match_key: return lyrics_map[match_key[0]]
        else:
            match_key = [k for k in lyrics_map if "2.4.2" in k]
            if match_key: return lyrics_map[match_key[0]]
            
    if "安全去化" in cleaned or "格外久滯" in cleaned:
        if "中國風" in cleaned or "古風" in cleaned:
            match_key = [k for k in lyrics_map if "2.5.1" in k]
            if match_key: return lyrics_map[match_key[0]]
        else:
            match_key = [k for k in lyrics_map if "2.5.2" in k]
            if match_key: return lyrics_map[match_key[0]]
            
    if "純淨之光" in cleaned:
        match_key = [k for k in lyrics_map if "1.1" in k]
        if match_key: return lyrics_map[match_key[0]]
        
    for full_title, data in lyrics_map.items():
        title = data["title"]
        if title in cleaned or cleaned in title:
            return data
            
    return None

def main():
    if not os.path.exists(output_root):
        print(f"錯誤: 找不到創作庫資料夾: {output_root}")
        return

    lyrics_map = parse_all_lyrics(workspace_dir)
    print(f"已從合輯解析出 {len(lyrics_map)} 首歌曲的歌詞資料。")

    songs_data = []
    song_folders = sorted(os.listdir(output_root))
    
    print("正在掃描歌曲資料夾並解析故事板...")
    for folder in song_folders:
        folder_path = os.path.join(output_root, folder)
        if not os.path.isdir(folder_path):
            continue
            
        base_name = get_base_name(folder)
            
        # Find MP3 inside folder
        mp3_file = None
        for f in os.listdir(folder_path):
            if f.endswith(".mp3"):
                mp3_file = f
                break
                
        if not mp3_file:
            continue
            
        mp3_path = os.path.join(folder_path, mp3_file)
        duration = get_audio_duration(mp3_path)
        
        md_path = os.path.join(folder_path, "vids_storyboard_prompts.md")
        scenes = parse_storyboard_md(md_path)
        
        # Auto-detect generated image files inside "圖片" directory
        images_dir = os.path.join(folder_path, "圖片")
        existing_images = {}
        existing_filenames = set()
        if os.path.exists(images_dir) and os.path.isdir(images_dir):
            for f_name in os.listdir(images_dir):
                if f_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    existing_filenames.add(f_name)
                    # Match leading digits, e.g., "01_廠區遠景.png" -> "01"
                    match = re.match(r"^(\d+)_", f_name)
                    if match:
                        num_str = match.group(1)
                        # Normalize to 2-digit string
                        normalized_num = f"{int(num_str):02d}"
                        existing_images[normalized_num] = f_name

        for scene in scenes:
            scene_id = scene["id"]
            md_filename = scene.get("filename", "")
            
            # 1. Prefer matching by exact filename written in the Markdown if it exists locally in song's folder
            if md_filename and md_filename in existing_filenames:
                scene["status"] = "🟢"
                scene["image_url"] = f"創作庫/{folder}/圖片/{md_filename}"
            # 2. Check if the exact filename exists in the master "圖片" directory
            elif md_filename and os.path.exists(os.path.join(workspace_dir, "圖片", md_filename)):
                scene["status"] = "🟢"
                scene["image_url"] = f"圖片/{md_filename}"
            # 3. Fall back to prefix matching using the prefix from the markdown filename in song's folder
            else:
                prefix_matched = False
                if md_filename:
                    fn_match = re.match(r"^(\d+)_", md_filename)
                    if fn_match:
                        normalized_id = f"{int(fn_match.group(1)):02d}"
                        if normalized_id in existing_images:
                            scene["status"] = "🟢"
                            scene["filename"] = existing_images[normalized_id]
                            scene["image_url"] = f"創作庫/{folder}/圖片/{existing_images[normalized_id]}"
                            prefix_matched = True
                
                if not prefix_matched:
                    scene["status"] = "🔴"
                    scene["image_url"] = ""

        # relative paths for local HTML loading
        rel_mp3_path = f"創作庫/{folder}/{mp3_file}"
        
        # Check if local MV MP4 exists
        mp4_file = f"{folder}_MV.mp4"
        mp4_path = os.path.join(folder_path, mp4_file)
        rel_mp4_path = f"創作庫/{folder}/{mp4_file}" if os.path.exists(mp4_path) else ""
        
        # Match lyrics - check local lyrics.txt first
        local_lyrics_path = os.path.join(folder_path, "lyrics.txt")
        if os.path.exists(local_lyrics_path):
            matched = True
            with open(local_lyrics_path, 'r', encoding='utf-8') as lf:
                lyrics_text = lf.read().strip()
            style_desc = ""
            local_desc_path = os.path.join(folder_path, "youtube_description.txt")
            if os.path.exists(local_desc_path):
                with open(local_desc_path, 'r', encoding='utf-8') as df:
                    desc_lines = df.read().split("\n")
                    for line in desc_lines:
                        if "歌曲曲風" in line or "曲風" in line:
                            try:
                                style_idx = desc_lines.index(line) + 1
                                while style_idx < len(desc_lines) and not desc_lines[style_idx].strip():
                                    style_idx += 1
                                if style_idx < len(desc_lines):
                                    style_desc = f"* **曲風設定 (Style)**：`{desc_lines[style_idx].strip()}`"
                                    break
                            except Exception:
                                pass
        else:
            matched = find_matching_lyrics(folder, lyrics_map)
            lyrics_text = matched["lyrics"] if matched else ""
            style_desc = matched["style"] if matched else ""
        
        # Style overrides based on folder name keywords
        style_overrides = [
            ("古典中國風", "`Chinese traditional instruments, guzheng, erhu, bamboo flute, Chinese style pop, elegant, melodic, male and female duet` (優雅中國國樂流行)"),
            ("中國風", "`Chinese traditional instruments, guzheng, erhu, bamboo flute, Chinese style pop, elegant, melodic, male and female duet` (優雅中國國樂流行)"),
            ("史詩交響流行", "`epic orchestral pop, majestic, clean vocals, male and female duet, inspiring, cinematic, strings, brass, powerful drums, emotional build-up` (大氣壯麗交響樂流行)"),
            ("交響流行", "`epic orchestral pop, majestic, clean vocals, male and female duet, inspiring, cinematic, strings, brass, powerful drums, emotional build-up` (大氣壯麗交響樂流行)"),
            ("護國神山史詩電音", "`electronic pop, synth-pop, high-tech, futuristic, male and female duet, clean vocals, melodic, driving beat, inspiring` (護國神山史詩電音對唱)"),
            ("電音", "`electronic pop, synth-pop, high-tech, futuristic, male and female duet, clean vocals, melodic, driving beat, inspiring` (電音風)"),
            ("復古合成器", "`synthwave, retro 80s, electro-pop, driving bassline, male and female duet, melodic, energetic, catchy` (動感復古合成器流行)"),
            ("合成器", "`synthwave, retro 80s, electro-pop, driving bassline, male and female duet, melodic, energetic, catchy` (動感復古合成器流行)"),
            ("流行輕搖滾", "`modern pop rock, light rock, energetic, emotional, melodic pop, electric guitar, driving drums, male vocals` (流行輕搖滾)"),
            ("輕搖滾", "`modern pop rock, light rock, energetic, emotional, melodic pop, electric guitar, driving drums, male vocals` (流行輕搖滾)"),
            ("Cinematic Pop _ Anthem Rock", "`cinematic pop, stadium rock, anthemic, building up, inspiring, electric guitar, grand piano, driving beat, male vocals` (電影感與競技搖滾組合)"),
            ("Cinematic Pop", "`cinematic pop, epic orchestral build, anthemic chorus, inspiring, storytelling, male vocals` (電影感流行)"),
            ("電影感流行", "`cinematic pop, epic orchestral build, anthemic chorus, inspiring, storytelling, male vocals` (電影感流行)"),
            ("Anthem Rock", "`anthem rock, stadium rock, driving beat, electric guitar, energetic, soaring male vocals` (競技體育搖滾)"),
            ("勵志搖滾", "`anthem rock, stadium rock, driving beat, electric guitar, energetic, soaring male vocals` (競技體育搖滾)"),
        ]
        
        # If it is the original "攜手未來" without extra style suffix, give it the original rap-pop style
        is_original_future = "攜手未來" in folder and not any(kw in folder for kw in ["Cinematic", "Anthem", "搖滾", "組合", "輕搖滾", "流行"])
        if is_original_future:
            style_desc = "* **曲風設定 (Style)**：`emotional melodic rap, cinematic pop beat, grand piano, soaring strings, deep sub-bass, inspiring, dramatic male vocals, storytelling` (情感說唱流行)"
        else:
            for kw, tag in style_overrides:
                if kw in folder:
                    style_desc = f"* **曲風設定 (Style)**：{tag}"
                    break
        
        # Generate YouTube assets if missing
        generate_youtube_assets(folder_path, folder, lyrics_text, style_desc, duration)
        
        songs_data.append({
            "name": folder,
            "base_name": base_name,
            "mp3": rel_mp3_path,
            "mp4": rel_mp4_path,
            "duration": f"{duration:.2f} 秒" if duration else "未知",
            "scenes_count": len(scenes),
            "folder_path": f"file:///{folder_path.replace('\\', '/')}",
            "lyrics": lyrics_text,
            "style": style_desc,
            "scenes": scenes
        })
        print(f"  [✓] 已解析: {folder} ({len(scenes)} 個場景, 歌詞匹配: {'成功' if matched else '失敗'})")

    # Generate Dashboard HTML
    html_template = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIGC 音樂影片專案主控台</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+TC:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(22, 28, 45, 0.6);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --primary: #10b981;
            --primary-glow: rgba(16, 185, 129, 0.15);
            --accent: #06b6d4;
            --accent-glow: rgba(6, 182, 212, 0.15);
            --card-hover-border: rgba(6, 182, 212, 0.4);
        }

        .version-btn {
            background-color: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .version-btn:hover {
            background-color: rgba(255, 255, 255, 0.08);
            color: var(--text-primary);
        }
        .version-btn.active {
            background-color: var(--primary-glow);
            border-color: var(--primary);
            color: var(--primary);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: 'Outfit', 'Noto Sans TC', sans-serif;
            overflow-x: hidden;
            display: flex;
            height: 100vh;
        }

        /* Sidebar styling */
        .sidebar {
            width: 320px;
            background-color: rgba(17, 24, 39, 0.95);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            height: 100%;
            flex-shrink: 0;
        }

        .sidebar-header {
            padding: 24px;
            border-bottom: 1px solid var(--border-color);
        }

        .sidebar-header h1 {
            font-size: 1.25rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent), var(--primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }

        .sidebar-header p {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        .search-box {
            padding: 16px 24px;
            border-bottom: 1px solid var(--border-color);
        }

        .search-box input {
            width: 100%;
            padding: 10px 16px;
            border-radius: 8px;
            background-color: rgba(31, 41, 55, 0.5);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .search-box input:focus {
            border-color: var(--accent);
        }

        .song-list {
            flex-grow: 1;
            overflow-y: auto;
            padding: 16px;
        }

        .song-item {
            padding: 14px 18px;
            border-radius: 10px;
            background-color: transparent;
            border: 1px solid transparent;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .song-item:hover {
            background-color: rgba(31, 41, 55, 0.4);
            border-color: rgba(255, 255, 255, 0.05);
        }

        .song-item.active {
            background-color: var(--primary-glow);
            border-color: var(--primary);
        }

        .song-item h3 {
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 6px;
            text-overflow: ellipsis;
            white-space: nowrap;
            overflow: hidden;
        }

        .song-item-meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        .song-item-meta span.scenes-tag {
            background-color: rgba(6, 182, 212, 0.1);
            color: var(--accent);
            padding: 2px 6px;
            border-radius: 4px;
        }

        /* Main panel styling */
        .main-panel {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
            overflow-y: auto;
            background: radial-gradient(circle at 80% 20%, rgba(6, 182, 212, 0.03), transparent 40%),
                        radial-gradient(circle at 10% 80%, rgba(16, 185, 129, 0.03), transparent 40%);
        }

        .empty-state {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100%;
            color: var(--text-secondary);
        }

        .empty-state svg {
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            opacity: 0.2;
        }

        .song-detail {
            padding: 40px;
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            display: none;
        }

        .song-detail.active {
            display: block;
        }

        .detail-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 30px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 24px;
        }

        .header-left h2 {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 12px;
            background: linear-gradient(135deg, #fff, #a3e635);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-left-meta {
            display: flex;
            gap: 16px;
            align-items: center;
        }

        .meta-pill {
            background-color: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .meta-pill strong {
            color: var(--text-primary);
        }

        .header-right {
            display: flex;
            gap: 12px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
            border: 1px solid transparent;
        }

        .btn-primary {
            background-color: var(--accent);
            color: #fff;
        }

        .btn-primary:hover {
            background-color: #0891b2;
            box-shadow: 0 0 15px rgba(6, 182, 212, 0.4);
        }

        .btn-secondary {
            background-color: rgba(255, 255, 255, 0.04);
            border-color: var(--border-color);
            color: var(--text-primary);
        }

        .btn-secondary:hover {
            background-color: rgba(255, 255, 255, 0.08);
            border-color: var(--text-secondary);
        }

        /* Player & media preview section */
        .media-section {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 24px;
            margin-bottom: 40px;
        }

        .player-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(16px);
        }

        .player-card h4 {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 16px;
            color: var(--accent);
        }

        audio {
            width: 100%;
            margin-top: 10px;
        }

        .video-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            backdrop-filter: blur(16px);
        }

        .video-card svg {
            width: 48px;
            height: 48px;
            margin-bottom: 16px;
            color: var(--primary);
        }

        /* Storyboard Grid styling */
        .storyboard-title {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .storyboard-title span.badge {
            background-color: var(--primary);
            color: #0b0f19;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: 800;
        }

        .scenes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
            gap: 24px;
        }

        .scene-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }

        .scene-card:hover {
            transform: translateY(-4px);
            border-color: var(--card-hover-border);
            box-shadow: 0 10px 20px rgba(6, 182, 212, 0.1);
        }

        .scene-thumb {
            height: 180px;
            background-color: rgba(17, 24, 39, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            border-bottom: 1px solid var(--border-color);
            overflow: hidden;
        }

        .scene-thumb img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .scene-status-tag {
            position: absolute;
            top: 12px;
            left: 12px;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: 700;
            backdrop-filter: blur(8px);
        }

        .status-generated {
            background-color: rgba(16, 185, 129, 0.85);
            color: #fff;
        }

        .status-missing {
            background-color: rgba(239, 68, 68, 0.85);
            color: #fff;
        }

        .scene-duration-tag {
            position: absolute;
            bottom: 12px;
            right: 12px;
            background-color: rgba(15, 23, 42, 0.75);
            color: #fff;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-family: monospace;
        }

        .scene-card-body {
            padding: 20px;
        }

        .scene-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 14px;
        }

        .scene-number {
            font-weight: 800;
            color: var(--accent);
            font-family: monospace;
        }

        .scene-name {
            font-weight: 700;
            font-size: 1rem;
        }

        .prompt-block {
            margin-bottom: 12px;
        }

        .prompt-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .btn-copy {
            background: none;
            border: none;
            color: var(--accent);
            cursor: pointer;
            font-size: 0.75rem;
            font-weight: 600;
            outline: none;
        }

        .btn-copy:hover {
            color: #22d3ee;
            text-decoration: underline;
        }

        .prompt-content {
            background-color: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 0.8rem;
            line-height: 1.4;
            font-family: monospace;
            word-break: break-all;
            height: 52px;
            overflow-y: auto;
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.1);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        /* Toast notification styling */
        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background-color: var(--primary);
            color: #0b0f19;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 700;
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            z-index: 1000;
        }

        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
    </style>
</head>
<body>

    <!-- Sidebar with songs list -->
    <div class="sidebar">
        <div class="sidebar-header">
            <h1>AIGC 音樂影片主控台</h1>
            <p>勝一化學專案 • <span id="totalSongsText">--</span> 首歌曲</p>
        </div>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="搜尋歌曲名稱或風格..." onkeyup="filterSongs()">
        </div>
        <div class="song-list" id="songList">
            <!-- Song items injected here -->
        </div>
    </div>

    <!-- Main Panel -->
    <div class="main-panel">
        <!-- Empty State -->
        <div class="empty-state" id="emptyState">
            <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polygon points="10 8 16 12 10 16 10 8"></polygon></svg>
            <h2>請從左側選單選擇一首歌曲專案</h2>
            <p>可直接預覽音軌、複製 Vids 生成提示詞、瀏覽故事板</p>
        </div>

        <!-- Song Details View -->
        <div class="song-detail" id="songDetail">
            <div class="detail-header">
                <div class="header-left">
                    <h2 id="detailTitle">歌曲名稱</h2>
                    <div class="header-left-meta">
                        <div class="meta-pill">時長: <strong id="detailDuration">--</strong></div>
                        <div class="meta-pill">場景數: <strong id="detailScenesCount">--</strong></div>
                    </div>
                </div>
                <div class="header-right">
                    <a href="#" id="btnOpenFolder" class="btn btn-secondary" target="_blank">
                        <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                        開啟本機資料夾
                    </a>
                </div>
            </div>

            <!-- Version selector tabs -->
            <div id="versionSelector" style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 24px;"></div>

            <!-- Media Preview Section -->
            <div class="media-section">
                <!-- Audio Player -->
                <div class="player-card">
                    <h4>💿 音軌聆聽</h4>
                    <audio id="audioPlayer" controls></audio>
                </div>
                
                <!-- Video Status -->
                <div class="video-card">
                    <svg viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
                    <h4 id="videoStatusTitle" style="margin-bottom: 6px;">本機影片已渲染</h4>
                    <a href="#" id="btnPlayVideo" class="btn btn-primary" target="_blank">
                        播放 MV 影片
                    </a>
                </div>
            </div>

            <!-- Lyrics Section -->
            <div class="lyrics-section" id="lyricsSection" style="display:none; margin-top: 24px; padding: 24px; background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; backdrop-filter: blur(10px);">
                <h4 style="margin-bottom: 12px; font-weight: 600; display: flex; align-items: center; justify-content: space-between;">
                    <span style="display: flex; align-items: center; gap: 8px;">🎵 歌詞與曲風設定</span>
                    <button class="btn" style="font-size: 0.75rem; padding: 4px 10px; border-radius: 6px; cursor: pointer; background-color: rgba(255,255,255,0.05); color: var(--text-primary); border: 1px solid var(--border-color);" onclick="copyText(document.getElementById('lyricsContent').innerText)">複製完整歌詞</button>
                </h4>
                <div id="lyricsStyle" style="font-size: 0.85rem; color: var(--accent); margin-bottom: 12px; font-style: italic; line-height: 1.5; padding: 8px 12px; background-color: rgba(6, 182, 212, 0.05); border-radius: 6px; border: 1px solid rgba(6, 182, 212, 0.1);"></div>
                <div id="lyricsContent" style="font-size: 0.9rem; line-height: 1.8; white-space: pre-wrap; color: var(--text-primary); max-height: 250px; overflow-y: auto; padding: 16px; background-color: rgba(0,0,0,0.3); border-radius: 8px; border: 1px solid rgba(255,255,255,0.04); font-family: 'Noto Sans TC', sans-serif;"></div>
            </div>

            <!-- Storyboard section -->
            <div class="storyboard-title">
                <span>🎥 Vids 影像故事板</span>
                <span class="badge" id="badgeTotalScenes">26 頁</span>
            </div>

            <div class="scenes-grid" id="scenesGrid">
                <!-- Scenes card injected dynamically -->
            </div>
        </div>
    </div>

    <!-- Toast Notification -->
    <div class="toast" id="toast">已複製提示詞到剪貼簿！</div>

    <script>
        // Inject dynamic JSON data from Python
        const songs = __SONGS_DATA_JSON__;
        
        // Group songs by base_name
        const groups = {};
        const groupOrder = []; // maintain order of appearance of base names
        
        songs.forEach((song, idx) => {
            const base = song.base_name || song.name;
            if (!groups[base]) {
                groups[base] = [];
                groupOrder.push(base);
            }
            groups[base].push({ ...song, globalIndex: idx });
        });

        // Update total songs count dynamically
        document.getElementById('totalSongsText').innerText = songs.length;

        // Active state
        let activeBaseName = null;
        let activeVariantIndex = 0;

        // Initialize song list with base songs
        const songList = document.getElementById('songList');
        groupOrder.forEach((baseName) => {
            const variants = groups[baseName];
            const item = document.createElement('div');
            item.className = 'song-item';
            item.onclick = () => selectGroup(baseName);
            item.dataset.baseName = baseName;
            
            const mainSong = variants[0];
            
            item.innerHTML = `
                <h3>${baseName}</h3>
                <div class="song-item-meta">
                    <span>${variants.length} 個版本</span>
                    <span class="scenes-tag">${mainSong.scenes_count} 頁</span>
                </div>
            `;
            songList.appendChild(item);
        });

        // Filter Songs in list
        function filterSongs() {
            const input = document.getElementById('searchInput').value.toUpperCase();
            const items = songList.getElementsByClassName('song-item');
            
            for (let i = 0; i < items.length; i++) {
                const baseName = items[i].dataset.baseName;
                if (baseName.toUpperCase().indexOf(input) > -1) {
                    items[i].style.display = "";
                } else {
                    items[i].style.display = "none";
                }
            }
        }

        // Copy text to clipboard helper
        function copyText(text) {
            navigator.clipboard.writeText(text).then(() => {
                const toast = document.getElementById('toast');
                toast.classList.add('show');
                setTimeout(() => {
                    toast.classList.remove('show');
                }, 2000);
            });
        }
        
        // Select a song group
        function selectGroup(baseName) {
            activeBaseName = baseName;
            activeVariantIndex = 0;
            
            // Highlight sidebar item
            const items = songList.getElementsByClassName('song-item');
            for (let i = 0; i < items.length; i++) {
                if (items[i].dataset.baseName === baseName) {
                    items[i].classList.add('active');
                } else {
                    items[i].classList.remove('active');
                }
            }
            
            // Render version tabs and load default version
            renderVersionSelector();
            loadVariant(0);
        }
        
        // Render version buttons
        function renderVersionSelector() {
            const container = document.getElementById('versionSelector');
            container.innerHTML = '';
            
            const variants = groups[activeBaseName];
            if (variants.length <= 1) {
                container.style.display = 'none';
                return;
            }
            container.style.display = 'flex';
            
            variants.forEach((variant, index) => {
                const btn = document.createElement('button');
                btn.className = 'version-btn' + (index === activeVariantIndex ? ' active' : '');
                
                // Extract clean variant name
                let vName = variant.name;
                // If it starts with the base name, strip it
                if (vName.startsWith(activeBaseName)) {
                    vName = vName.substring(activeBaseName.length).replace(/^[-—\s]+/, '').trim();
                }
                // Fallback if empty
                if (!vName) {
                    vName = "原版";
                }
                
                btn.innerText = vName;
                btn.onclick = () => {
                    // Update active tab button classes
                    const btns = container.getElementsByClassName('version-btn');
                    for (let i = 0; i < btns.length; i++) {
                        btns[i].classList.remove('active');
                    }
                    btn.classList.add('active');
                    
                    activeVariantIndex = index;
                    loadVariant(index);
                };
                container.appendChild(btn);
            });
        }
        
        // Load details of specific variant
        function loadVariant(index) {
            const song = groups[activeBaseName][index];
            
            // Hide empty state and show details
            document.getElementById('emptyState').style.display = 'none';
            const detailPanel = document.getElementById('songDetail');
            detailPanel.classList.add('active');
            
            // Set details
            document.getElementById('detailTitle').innerText = song.name;
            document.getElementById('detailDuration').innerText = song.duration;
            document.getElementById('detailScenesCount').innerText = song.scenes_count + ' 頁';
            document.getElementById('badgeTotalScenes').innerText = song.scenes_count + ' 頁';
            
            // Open local folder link
            document.getElementById('btnOpenFolder').href = song.folder_path;
            
            // Play Audio
            const audio = document.getElementById('audioPlayer');
            audio.src = song.mp3;
            audio.load();
            
            // Play Video setup
            const videoBtn = document.getElementById('btnPlayVideo');
            const videoTitle = document.getElementById('videoStatusTitle');
            if (song.mp4) {
                videoBtn.href = song.mp4;
                videoBtn.style.display = 'inline-flex';
                videoTitle.innerText = "本機影片已渲染";
            } else {
                videoBtn.style.display = 'none';
                videoTitle.innerText = "尚未在本機渲染影片";
            }
            
            // Render lyrics
            const lyricsSec = document.getElementById('lyricsSection');
            const lyricsStyle = document.getElementById('lyricsStyle');
            const lyricsContent = document.getElementById('lyricsContent');
            if (song.lyrics) {
                lyricsStyle.innerHTML = song.style || '';
                lyricsContent.innerText = song.lyrics;
                lyricsSec.style.display = 'block';
            } else {
                lyricsSec.style.display = 'none';
            }
            
            // Render scenes grid
            const grid = document.getElementById('scenesGrid');
            grid.innerHTML = '';
            
            song.scenes.forEach((scene) => {
                const card = document.createElement('div');
                card.className = 'scene-card';
                
                let imageHtml = `<div class="scene-thumb"><span style="opacity: 0.3; font-size: 0.9rem;">需用提示詞生成</span></div>`;
                let statusClass = 'status-missing';
                let statusLabel = '🔴 Vids 生成';
                
                if (scene.status === '🟢') {
                    statusClass = 'status-generated';
                    statusLabel = '🟢 本機已生成';
                    const imgUrl = scene.image_url || `圖片/${scene.filename}`;
                    imageHtml = `
                        <div class="scene-thumb">
                            <img src="${imgUrl}" alt="${scene.name}" onerror="if(!this.dataset.triedFallback){this.dataset.triedFallback=true; this.src='圖片/${scene.filename}';}else{this.style.display='none';}">
                            <span class="scene-duration-tag">${scene.time}</span>
                        </div>
                    `;
                } else {
                    imageHtml = `
                        <div class="scene-thumb">
                            <div style="text-align: center; padding: 20px;">
                                <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" style="opacity: 0.3; margin-bottom: 6px;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                                <div style="font-size: 0.75rem; opacity: 0.5;">點擊下方複製提示詞生成</div>
                            </div>
                            <span class="scene-duration-tag">${scene.time}</span>
                        </div>
                    `;
                }
                
                card.innerHTML = `
                    ${imageHtml}
                    <div class="scene-status-tag ${statusClass}">${statusLabel}</div>
                    <div class="scene-card-body">
                        <div class="scene-header">
                            <span class="scene-number">#${scene.id}</span>
                            <span class="scene-name">${scene.name}</span>
                        </div>
                        <div class="prompt-block">
                            <div class="prompt-label">
                                <span>1. 圖片提示詞 (Text-to-Image)</span>
                                <button class="btn-copy" onclick="copyText('${scene.image_prompt.replace(/'/g, "\\'")}')">複製</button>
                            </div>
                            <div class="prompt-content" title="${scene.image_prompt}">${scene.image_prompt}</div>
                        </div>
                        <div class="prompt-block">
                            <div class="prompt-label">
                                <span>2. 動態提示詞 (Image-to-Video)</span>
                                <button class="btn-copy" onclick="copyText('${scene.motion_prompt.replace(/'/g, "\\'")}')">複製</button>
                            </div>
                            <div class="prompt-content" title="${scene.motion_prompt}">${scene.motion_prompt}</div>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });
        }
    </script>
</body>
</html>"""

    # Inject data into HTML
    json_data = json.dumps(songs_data, ensure_ascii=False)
    html_content = html_template.replace("__SONGS_DATA_JSON__", json_data)
    
    with open(dashboard_html_path, "w", encoding="utf-8") as out:
        out.write(html_content)
        
    print(f"\n🎉 音樂影片專案總覽主控台生成成功！")
    print(f"🎬 網頁已儲存至: {dashboard_html_path}")

if __name__ == "__main__":
    main()
