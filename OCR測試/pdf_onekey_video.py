"""
PDF 一鍵轉語音導覽影片工具
直接讀取 PDF 每頁圖片 → OCR 辨識中文 → edge-tts 台灣女聲語音 → 合成 MP4 影片
"""
import os
import sys
import json
import subprocess
import wave
import argparse
import fitz  # PyMuPDF
from PIL import Image
import io

# ====== 輔助函式 ======

def create_silence_mp3(filepath, duration_sec):
    """使用 ffmpeg 建立指定秒數的無聲 MP3 檔案"""
    from moviepy.config import FFMPEG_BINARY
    cmd = [
        FFMPEG_BINARY, "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=24000:cl=mono",
        "-t", str(duration_sec),
        "-c:a", "libmp3lame",
        "-b:a", "64k",
        filepath
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def get_audio_duration(filepath):
    """使用 ffmpeg 讀取音訊檔案的總長度（秒）"""
    from moviepy.config import FFMPEG_BINARY
    cmd = [FFMPEG_BINARY, "-i", filepath]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
    raise ValueError(f"無法讀取音訊長度：{filepath}")

def concat_mp3s(mp3_paths, output_path, workspace):
    """使用 ffmpeg concat 功能快速合併多個 MP3 檔案"""
    from moviepy.config import FFMPEG_BINARY
    list_path = os.path.join(workspace, "file_list.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for path in mp3_paths:
            safe_path = os.path.abspath(path).replace("\\", "/")
            f.write(f"file '{safe_path}'\n")
            
    cmd = [
        FFMPEG_BINARY, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def ocr_image(img_path, reader):
    """使用 EasyOCR 辨識圖片中的中文文字（透過 numpy 陣列避免路徑編碼問題）"""
    import numpy as np
    pil_img = Image.open(img_path)
    img_array = np.array(pil_img)
    results = reader.readtext(img_array, detail=0, paragraph=True)
    return "\n".join(results).strip()

# ====== 主流程 ======

def pdf_to_video(pdf_path, voice="zh-TW-HsiaoChenNeural", speed="+0%", prepare_only=False, generate_only=False):
    """
    一鍵將 PDF 轉換為語音導覽影片 (支援兩階段流程)
    """
    if not os.path.exists(pdf_path):
        print(f"[-] 找不到 PDF 檔案：{pdf_path}")
        return
    
    pdf_base = os.path.splitext(os.path.basename(pdf_path))[0]
    # 使用純英文工作目錄避免 OpenCV 路徑編碼問題
    workspace = "video_output"
    os.makedirs(workspace, exist_ok=True)
    json_path = os.path.join(workspace, "narration.json")
    
    # 決定是否執行匯出與 OCR (只要不是單獨執行 generate 階段就要執行)
    if not generate_only:
        # --- 步驟 1：PDF 轉圖片 ---
        print(f"[*] 正在開啟 PDF：{pdf_path}")
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"[*] 共 {total_pages} 頁，正在匯出圖片...")
        
        img_paths = []
        for i in range(total_pages):
            page = doc[i]
            # 1.2x 解析度即可，避免解析度過大導致 CPU OCR 極慢
            mat = fitz.Matrix(1.2, 1.2)
            pix = page.get_pixmap(matrix=mat)
            img_path = os.path.join(workspace, f"page_{i+1:03d}.png")
            pix.save(img_path)
            img_paths.append(img_path)
            print(f"  [{i+1}/{total_pages}] 已匯出 page_{i+1:03d}.png")
        doc.close()
        
        # --- 步驟 2：OCR 辨識文字 ---
        if os.path.exists(json_path):
            print(f"\n[+] 偵測到已存在的 OCR 結果 {json_path}，直接載入跳過 OCR 辨識！")
            with open(json_path, "r", encoding="utf-8") as f:
                narration = json.load(f)
        else:
            print("\n[*] 正在載入 EasyOCR 引擎（首次可能需要下載模型）...")
            import easyocr
            reader = easyocr.Reader(['ch_tra', 'en'], gpu=False)
            
            narration = {}
            for i, img_path in enumerate(img_paths):
                page_num = i + 1
                print(f"  [{page_num}/{total_pages}] 正在 OCR 辨識第 {page_num} 頁...")
                text = ocr_image(img_path, reader)
                if text:
                    narration[str(page_num)] = text
                    print(f"    → 辨識到 {len(text)} 字元")
                else:
                    narration[str(page_num)] = ""
                    print(f"    → 未辨識到文字")
            
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(narration, f, ensure_ascii=False, indent=2)
            print(f"[+] OCR 結果已儲存至：{json_path}")
            
        if prepare_only:
            print(f"\n{'='*60}")
            print(f"[+] 準備階段（第一階段）完成！")
            print(f"    文字旁白草稿已儲存至：{os.path.abspath(json_path)}")
            print(f"\n    【修正提示】：")
            print(f"    請使用文字編輯器打開此 json 檔案，修改或刪除不必要的文字（如頁碼、廣告字）。")
            print(f"    編輯完成並儲存後，執行以下指令生成最終影片：")
            print(f"    python pdf_onekey_video.py --pdf \"{pdf_path}\" --generate")
            print(f"{'='*60}")
            return
            
    else:
        # 單獨執行 generate 階段
        if not os.path.exists(json_path):
            print(f"[-] 錯誤：找不到說明稿 {json_path}！請先以 `--prepare` 執行第一階段。")
            return
        print(f"[+] 偵測到編輯好的說明稿：{json_path}，載入中...")
        with open(json_path, "r", encoding="utf-8") as f:
            narration = json.load(f)
        total_pages = len(narration)
        img_paths = [os.path.join(workspace, f"page_{i+1:03d}.png") for i in range(total_pages)]
        # 檢查圖片完整性
        for img_path in img_paths:
            if not os.path.exists(img_path):
                print(f"[-] 錯誤：找不到投影片圖片 {img_path}，請重新執行 `--prepare`！")
                return

    # --- 步驟 3：生成語音 ---
    print("\n[*] 正在為每頁生成台灣女聲語音...")
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
    
    clips = []
    audio_paths = []
    
    for i in range(total_pages):
        page_num = i + 1
        text = narration.get(str(page_num), "").strip()
        img_path = img_paths[i]
        audio_path = os.path.join(workspace, f"page_{page_num:03d}.mp3")
        
        if not text:
            print(f"  [{page_num}/{total_pages}] 無文字，生成 3 秒靜音...")
            create_silence_mp3(audio_path, 3.0)
        else:
            print(f"  [{page_num}/{total_pages}] 生成語音：「{text[:30]}...」")
            cmd = [
                "edge-tts",
                "--voice", voice,
                "--text", text,
                "--write-media", audio_path,
                "--rate", speed
            ]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else ''
                print(f"    [-] edge-tts 失敗：{err_msg[:100]}")
                print(f"    [*] 降級使用 3 秒靜音...")
                create_silence_mp3(audio_path, 3.0)
        
        # 建立影片片段（僅圖片，不在此處載入音軌）
        try:
            duration = get_audio_duration(audio_path)
            img_clip = ImageClip(img_path).with_duration(duration)
            clips.append(img_clip)
            audio_paths.append(audio_path)
        except Exception as e:
            print(f"    [-] 建立片段失敗 (第 {page_num} 頁): {e}")
    
    if not clips:
        print("[-] 沒有成功的影片片段！")
        return
    
    # --- 步驟 4：合併音軌 ---
    final_audio_path = os.path.join(workspace, "final_narration.mp3")
    print("\n[*] 正在合併所有音軌...")
    concat_mp3s(audio_paths, final_audio_path, workspace)
    
    # --- 步驟 5：合成影片 ---
    print("[*] 正在串接影片片段並疊加音軌...")
    video_track = concatenate_videoclips(clips, method="compose")
    audio_clip = AudioFileClip(final_audio_path)
    final_video = video_track.with_audio(audio_clip)
    
    output_mp4 = f"{pdf_base}_導覽影片.mp4"
    print(f"[*] 正在渲染影片：{output_mp4}")
    final_video.write_videofile(
        output_mp4,
        fps=5,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        logger="bar"
    )
    
    print(f"\n{'='*60}")
    print(f"[+] 轉換完成！影片已儲存至：{os.path.abspath(output_mp4)}")
    print(f"{'='*60}")
    
    # 釋放資源
    for clip in clips:
        clip.close()
    audio_clip.close()
    final_video.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF 一鍵轉語音導覽影片")
    parser.add_argument("--pdf", type=str, default="線上宣導教材-1-認識職場霸凌.pdf",
                        help="要轉換的 PDF 檔案路徑")
    parser.add_argument("--voice", type=str, default="zh-TW-HsiaoChenNeural",
                        help="語音名稱（預設：zh-TW-HsiaoChenNeural 台灣女聲）")
    parser.add_argument("--speed", type=str, default="+0%",
                        help="語速調整（如 +10%% 加速，-10%% 減速）")
    parser.add_argument("--prepare", action="store_true",
                        help="僅執行第一階段：匯出投影片圖片與辨識 OCR 文字草稿")
    parser.add_argument("--generate", action="store_true",
                        help="僅執行第二階段：使用現有（已編輯）的文字草稿生成影片")
    
    args = parser.parse_args()
    pdf_to_video(args.pdf, voice=args.voice, speed=args.speed, prepare_only=args.prepare, generate_only=args.generate)
