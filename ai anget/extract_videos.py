import yt_dlp
import json
import os
import sys

# Set output encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.youtube.com/@sensebar/videos"
ydl_opts = {
    'extract_flat': True,
    'skip_download': True,
    'quiet': True,
}

# Targeted keywords as requested
keywords = ["claude", "codex", "antigravity", "opencode", "agent"]

print("Extracting videos from sensebar YouTube channel...")
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
except Exception as e:
    print(f"Error extracting channel info: {e}")
    sys.exit(1)

entries = info.get('entries', [])
print(f"Total videos found on channel: {len(entries)}")

matches = []
for entry in entries:
    title = entry.get('title', '')
    video_url = entry.get('url', '')
    # If the URL is just the video ID, format it
    if video_url and not video_url.startswith('http'):
        video_url = f"https://www.youtube.com/watch?v={video_url}"
    elif not video_url:
        video_id = entry.get('id', '')
        if video_id:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            continue
            
    title_lower = title.lower()
    matched_kws = []
    
    for kw in keywords:
        if kw in title_lower:
            matched_kws.append(kw)
            
    if matched_kws:
        matches.append({
            'title': title,
            'url': video_url,
            'matched': matched_kws
        })

print(f"Matched {len(matches)} videos.")

# Generate markdown content
md_content = "# @sensebar AI Agent 相關影片清單\n\n"
md_content += f"此清單篩選自 YouTube 頻道 [@sensebar](https://www.youtube.com/@sensebar) 中與 **Claude AI**、**Codex**、**AntiGravity**、**OpenCode** 及 **AI Agent** 相關的影片。\n\n"
md_content += f"**篩選關鍵字：** `{', '.join(keywords)}`\n\n"
md_content += "| 影片標題 | 網址 | 匹配關鍵字 |\n"
md_content += "| --- | --- | --- |\n"

for m in matches:
    # Escape pipe characters in titles to not break markdown table
    escaped_title = m['title'].replace('|', '\\|')
    md_content += f"| {escaped_title} | [{m['url']}]({m['url']}) | {', '.join(m['matched'])} |\n"

output_path = "sensebar_ai_videos.md"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(md_content)

print(f"成功儲存影片清單至：{output_path}")

# Also output the URLs to sensebar_ai_urls.txt
urls_path = "sensebar_ai_urls.txt"
with open(urls_path, "w", encoding="utf-8") as f:
    for m in matches:
        f.write(f"{m['url']}\n")
print(f"成功更新影片網址清單至：{urls_path}")


