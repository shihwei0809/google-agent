import yt_dlp
import os
import re
import glob
import time
import sys

# Reconfigure stdout to use UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Paths
urls_file = "sensebar_ai_urls.txt"
sub_dir = "Clipping"
os.makedirs(sub_dir, exist_ok=True)



# Read URLs
with open(urls_file, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

def make_safe_filename(title):
    # Remove characters that are illegal in Windows filenames
    # Also remove any non-ascii or special symbols if they could cause path issues,
    # but keeping Chinese/Unicode is fine.
    safe = re.sub(r'[\\/*?:"<>|]', "_", title)
    # Strip leading/trailing spaces/dots
    safe = safe.strip().strip('.')
    return safe

def parse_vtt(vtt_path):
    with open(vtt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    cleaned = []
    last_line = ""
    for line in lines:
        line = line.strip()
        # Skip VTT headers and timestamp lines
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:") or "-->" in line:
            continue
        # Remove tags
        line = re.sub(r'<[^>]+>', '', line)
        line = line.strip()
        if not line:
            continue
        # Deduplicate consecutive identical lines
        if line == last_line:
            continue
        cleaned.append(line)
        last_line = line
        
    return "\n".join(cleaned)

# yt-dlp configurations
ydl_opts = {
    'skip_download': True,
    'writesubtitles': True,
    'writeautomaticsubtitles': True,
    'subtitleslangs': ['zh-Hant', 'zh-TW', 'zh', 'en'],
    'subtitlesformat': 'vtt',
    'outtmpl': os.path.join(sub_dir, 'temp_sub.%(ext)s'),
    'quiet': True,
    'no_warnings': True,
}

print(f"Total videos to process: {len(urls)}")

for idx, url in enumerate(urls):
    print(f"[{idx+1}/{len(urls)}] Fetching metadata for {url}...")
    
    # 1. Get Title first to check if we already have the md file (resumable)
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            title = info_dict.get('title', f"video_{idx+1}")
    except Exception as e:
        print(f"  Error fetching metadata for {url}: {e}")
        continue

    safe_title = make_safe_filename(title)
    out_md_path = os.path.join(sub_dir, f"{safe_title}.md")
    
    if os.path.exists(out_md_path):
        print(f"  [Skip] Already exists: {safe_title}.md")
        continue

    # 2. Clean up old temp files
    for f in glob.glob(os.path.join(sub_dir, "temp_sub.*")):
        try:
            os.remove(f)
        except:
            pass

    # 3. Download subtitles
    print(f"  Downloading subtitles for: {title}...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
            
        sub_files = glob.glob(os.path.join(sub_dir, "temp_sub.*.vtt"))
        
        if not sub_files:
            print("  No subtitles found.")
            md_content = f"# {title}\n\n- 影片網址: {url}\n\n*(此影片未提供字幕)*\n"
            with open(out_md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            continue
            
        # Parse and save
        sub_file = sub_files[0]
        cleaned_text = parse_vtt(sub_file)
        
        md_content = f"# {title}\n\n"
        md_content += f"- 影片網址: {url}\n\n"
        md_content += "---\n\n"
        md_content += cleaned_text + "\n"
        
        with open(out_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"  [Success] Saved to: {safe_title}.md")
        
    except Exception as e:
        print(f"  Error downloading subtitles for {title}: {e}")
        
    # Clean up temp files
    for f in glob.glob(os.path.join(sub_dir, "temp_sub.*")):
        try:
            os.remove(f)
        except:
            pass

    # Polite sleep to avoid rate limits
    time.sleep(2)

print("\nAll tasks completed!")
