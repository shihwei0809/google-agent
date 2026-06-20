import os
import re
import json
import sys
import subprocess

# Configure sys.stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

workspace_dir = r"c:\GOOGLE ANGET\ai anget"
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
            elif "圖片檔名" in line:
                fn_match = re.search(r"`(.*?)`", line)
                if fn_match:
                    filename = fn_match.group(1)
            elif "1. 圖片生成提示詞" in line:
                recording_image = True
                recording_motion = False
            elif "2. 動態生成提示詞" in line:
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
        
        # relative paths for local HTML loading
        rel_mp3_path = f"創作庫/{folder}/{mp3_file}"
        
        # Check if local MV MP4 exists
        mp4_file = f"{folder}_MV.mp4"
        mp4_path = os.path.join(folder_path, mp4_file)
        rel_mp4_path = f"創作庫/{folder}/{mp4_file}" if os.path.exists(mp4_path) else ""
        
        # Match lyrics
        matched = find_matching_lyrics(folder, lyrics_map)
        lyrics_text = matched["lyrics"] if matched else ""
        style_desc = matched["style"] if matched else ""
        
        songs_data.append({
            "name": folder,
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
        
        // Update total songs count dynamically
        document.getElementById('totalSongsText').innerText = songs.length;

        // Initialize song list
        const songList = document.getElementById('songList');
        songs.forEach((song, index) => {
            const item = document.createElement('div');
            item.className = 'song-item';
            item.onclick = () => selectSong(index);
            
            // Generate clean name
            let displayName = song.name;
            
            item.innerHTML = `
                <h3>${displayName}</h3>
                <div class="song-item-meta">
                    <span>${song.duration}</span>
                    <span class="scenes-tag">${song.scenes_count} 頁</span>
                </div>
            `;
            songList.appendChild(item);
        });

        // Filter Songs in list
        function filterSongs() {
            const input = document.getElementById('searchInput').value.toUpperCase();
            const items = songList.getElementsByClassName('song-item');
            
            for (let i = 0; i < items.length; i++) {
                const title = items[i].getElementsByTagName('h3')[0].innerText;
                if (title.toUpperCase().indexOf(input) > -1) {
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

        // Handle song selection
        function selectSong(index) {
            // Remove active classes
            const items = songList.getElementsByClassName('song-item');
            for (let i = 0; i < items.length; i++) {
                items[i].classList.remove('active');
            }
            
            // Add active to current
            items[index].classList.add('active');
            
            const song = songs[index];
            
            // Hide empty state and show details
            document.getElementById('emptyState').style.display = 'none';
            const detailPanel = document.getElementById('songDetail');
            detailPanel.classList.add('active');
            
            // Set basic details
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
                    // Load relative local image path
                    const imgUrl = `圖片/${scene.filename}`;
                    imageHtml = `
                        <div class="scene-thumb">
                            <img src="${imgUrl}" alt="${scene.name}" onerror="this.style.display='none'">
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
