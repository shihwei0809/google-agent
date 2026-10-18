import os
import sys
import json
import asyncio
import subprocess
import urllib.request
import urllib.parse
import re
import io
import random
import edge_tts
from PIL import Image, ImageDraw, ImageFont

DEFAULT_VOICE = "zh-TW-YunJheNeural"

async def generate_tts(text: str, output_audio_path: str, voice: str = DEFAULT_VOICE) -> float:
    """使用 Edge-TTS 產生語音並回傳長度(秒)"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_audio_path)
    
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", output_audio_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return float(result.stdout.strip())

def search_semantic_images(query: str, count: int = 3) -> list:
    """
    透過搜尋引擎精準檢索與文字語意高度匹配的 4K/HD 實景照片
    """
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.bing.com/images/async?q={encoded}&first=1&count=15&mmasync=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", errors="ignore")
        murls = re.findall(r'murl&quot;:&quot;(https?://[^&]+?\.(?:jpg|jpeg|png))', html)
        return murls[:count]
    except Exception as e:
        print(f"[!] 語意圖片搜尋異常: {e}")
        return []

def download_and_crop_semantic_photo(image_url: str, output_path: str) -> bool:
    """
    下載指定語意照片並精確裁切為 1080x1920 (9:16)，套用電影感暗角
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        req = urllib.request.Request(image_url, headers=headers)
        raw_data = urllib.request.urlopen(req, timeout=8).read()
        img = Image.open(io.BytesIO(raw_data)).convert("RGB")
        
        target_w, target_h = 1080, 1920
        orig_w, orig_h = img.size
        scale = max(target_w / orig_w, target_h / orig_h)
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        img = img.crop((left, top, left + target_w, top + target_h))

        # 電影暗角與底部黑色漸層
        overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for y in range(0, 360):
            alpha = int(140 * (1 - (y / 360.0)))
            draw.line([(0, y), (target_w, y)], fill=(0, 0, 0, alpha))
        for y in range(960, target_h):
            alpha = int(230 * ((y - 960) / 960.0))
            draw.line([(0, y), (target_w, y)], fill=(0, 0, 0, alpha))

        final = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        final.save(output_path, "JPEG", quality=95)
        return True
    except Exception as e:
        print(f"[!] 下載或裁切語意照片失敗 ({image_url[:40]}...): {e}")
        return False

def make_text_overlay(text: str, width: int, height: int, output_img_path: str, title: str = "", accent_color: str = "#FF7A1A"):
    """使用 PIL 繪製透明字幕字卡與強調框"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    font_path = "C:/Windows/Fonts/msjhbd.ttc"
    if not os.path.exists(font_path):
        font_path = "C:/Windows/Fonts/simhei.ttf"
        
    try:
        title_font = ImageFont.truetype(font_path, 52)
        body_font = ImageFont.truetype(font_path, 42)
    except:
        title_font = body_font = ImageFont.load_default()

    # 頂部主題膠囊
    if title:
        pill_w, pill_h = 620, 84
        pill_x = (width - pill_w) // 2
        pill_y = 180
        draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=42, fill=(18, 18, 22, 235), outline=(255, 122, 26, 255), width=3)
        draw.text((width // 2, pill_y + pill_h // 2), title, font=title_font, fill="#FFFFFF", anchor="mm")

    # 底部字幕卡
    card_margin = 50
    card_w = width - (card_margin * 2)
    card_h = 280
    card_x = card_margin
    card_y = height - card_h - 160

    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=24,
        fill=(12, 12, 16, 225),
        outline=(255, 255, 255, 45),
        width=2
    )

    draw.rounded_rectangle(
        [card_x + 30, card_y + 20, card_x + 90, card_y + 26],
        radius=3,
        fill=accent_color
    )

    max_chars_per_line = 18
    lines = []
    for i in range(0, len(text), max_chars_per_line):
        lines.append(text[i:i+max_chars_per_line])

    text_y_start = card_y + 68
    line_spacing = 60
    for idx, line in enumerate(lines[:3]):
        draw.text(
            (width // 2, text_y_start + (idx * line_spacing)),
            line,
            font=body_font,
            fill="#F2F0EA",
            anchor="mm"
        )

    img.save(output_img_path, "PNG")

async def render_single_clip(
    media_path: str,
    script_text: str,
    output_clip_path: str,
    title: str = "",
    voice: str = DEFAULT_VOICE,
    accent_color: str = "#FF7A1A"
) -> str:
    """渲染單一鏡頭片段 (包含語音與字幕)"""
    work_dir = os.path.dirname(output_clip_path)
    base_name = os.path.splitext(os.path.basename(output_clip_path))[0]
    audio_path = os.path.join(work_dir, f"{base_name}_audio.mp3")
    overlay_path = os.path.join(work_dir, f"{base_name}_overlay.png")

    duration = await generate_tts(script_text, audio_path, voice)
    duration += 0.4

    make_text_overlay(script_text, 1080, 1920, overlay_path, title=title, accent_color=accent_color)

    ext = os.path.splitext(media_path)[1].lower()
    is_image = ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']

    if is_image:
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"zoompan=z='min(zoom+0.0009,1.15)':d={int(duration*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920[bg];"
            f"[bg][1:v]overlay=0:0[outv]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", media_path,
            "-i", overlay_path,
            "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "2:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration),
            output_clip_path
        ]
    else:
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
            f"[bg][1:v]overlay=0:0[outv]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", media_path,
            "-i", overlay_path,
            "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "2:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration),
            output_clip_path
        ]

    subprocess.run(cmd, check=True)
    return output_clip_path

async def render_multi_scene_video(
    user_media: str,
    topic: str,
    scenes: list,
    output_video_path: str,
    voice: str = DEFAULT_VOICE,
    accent_color: str = "#FF7A1A"
) -> str:
    """
    多分鏡自動剪輯：
    - 依據每一幕的 keywords 自動檢索 100% 吻合主題的真實 4K 照片素材！
    - 自動分別配音、上字幕，最後無縫合併為 20~30 秒精美短影音。
    """
    work_dir = os.path.dirname(output_video_path)
    os.makedirs(work_dir, exist_ok=True)
    clip_files = []

    for idx, sc in enumerate(scenes):
        clip_path = os.path.join(work_dir, f"scene_{idx}.mp4")
        
        # 決定素材
        if idx == 0 and user_media and os.path.exists(user_media):
            media_to_use = user_media
        else:
            # 依據關鍵字進行精確語意配圖
            keyword = sc.get("search_keyword", f"{topic} professional photo")
            print(f"[*] 分鏡 {idx+1}: 正在搜尋並下載符合語意的素材: '{keyword}'...")
            photo_file = os.path.join(work_dir, f"semantic_photo_{idx}.jpg")
            
            urls = search_semantic_images(keyword, count=3)
            success = False
            for u in urls:
                if download_and_crop_semantic_photo(u, photo_file):
                    success = True
                    break
            
            if not success:
                # 備用純色質感底
                img = Image.new("RGB", (1080, 1920), (18, 22, 32))
                img.save(photo_file, "JPEG")

            media_to_use = photo_file

        print(f"[*] 正在剪輯分鏡 {idx+1}/{len(scenes)}: {sc['script'][:15]}...")
        await render_single_clip(
            media_path=media_to_use,
            script_text=sc["script"],
            output_clip_path=clip_path,
            title=topic,
            voice=voice,
            accent_color=accent_color
        )
        clip_files.append(clip_path)

    # 寫入 concat 清單進行 FFmpeg 無縫串接
    concat_txt = os.path.join(work_dir, "concat_list.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for cf in clip_files:
            clean_p = os.path.abspath(cf).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")

    print("[*] 正在無縫合併所有分鏡...")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_txt,
        "-c", "copy",
        output_video_path
    ]
    subprocess.run(concat_cmd, check=True)
    print(f"[SUCCESS] 短影音輸出成功: {output_video_path}")
    return output_video_path
