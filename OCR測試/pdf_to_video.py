import os
import sys
import json
import subprocess
import wave
import argparse
import fitz  # PyMuPDF
from PIL import Image

def create_silence_wav(filepath, duration_sec):
    """建立指定秒數的無聲 WAV 檔案，確保無文字的頁面也有音軌以防影音同步失敗。"""
    sample_rate = 24000
    channels = 1
    sample_width = 2  # 16-bit
    num_frames = int(sample_rate * duration_sec)
    
    with wave.open(filepath, 'wb') as w:
        w.setnchannels(channels)
        w.setsampwidth(sample_width)
        w.setframerate(sample_rate)
        # 16-bit PCM 靜音為全 0
        w.writeframes(b'\x00' * (num_frames * channels * sample_width))

def get_wav_duration(filepath):
    """讀取 WAV 檔案的總長度（秒）。"""
    with wave.open(filepath, 'rb') as wf:
        return wf.getnframes() / wf.getframerate()

def concat_wavs(wav_paths, output_path):
    """將多個 WAV 檔案合併成一個單一的 WAV 檔案。"""
    with wave.open(wav_paths[0], 'rb') as w:
        params = w.getparams()
    
    with wave.open(output_path, 'wb') as out_w:
        out_w.setparams(params)
        for path in wav_paths:
            with wave.open(path, 'rb') as in_w:
                out_w.writeframes(in_w.readframes(in_w.getnframes()))

def extract_pdf_pages_and_text(pdf_path, workspace_dir):
    """
    第一階段：從 PDF 中提取每一頁為 PNG 圖片，並偵測/辨識文字
    """
    os.makedirs(workspace_dir, exist_ok=True)
    
    print(f"[*] 正在開啟 PDF 檔案：{pdf_path}")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"[+] 成功開啟 PDF！共 {total_pages} 頁")
    
    # 延遲載入 EasyOCR，僅在 PyMuPDF 無法提取文字時作為 OCR 後備方案
    reader = None
    
    narration_data = {}
    
    for i in range(total_pages):
        page_num = i + 1
        page = doc[i]
        
        # 1. 導出圖片 (150 DPI)
        pix = page.get_pixmap(dpi=150)
        img_filename = f"page_{page_num:03d}.png"
        img_path = os.path.join(workspace_dir, img_filename)
        pix.save(img_path)
        print(f"  [{page_num}/{total_pages}] 已導出圖片 -> {img_filename}")
        
        # 2. 提取文字 (優先使用內嵌文字，若無則用 EasyOCR)
        text = page.get_text().strip()
        
        # 檢查提取出的文字長度，太短可能表示此頁面是純圖片 PDF
        if len(text) < 2:
            if reader is None:
                print("  [*] 偵測到部分頁面無內嵌文字，正在初始化 EasyOCR 模型...")
                import easyocr
                reader = easyocr.Reader(['ch_tra', 'en'], gpu=False)
            
            print(f"  [*] 頁面 {page_num} 無內嵌文字，執行 OCR 辨識中...")
            try:
                # 讀取剛剛保存的圖片來進行 OCR
                ocr_results = reader.readtext(img_path, detail=0)
                text = " ".join(ocr_results).strip()
            except Exception as e:
                print(f"  [-] OCR 辨識失敗: {e}")
                text = ""
        
        # 清理文字中的多餘換行
        clean_text = " ".join(text.split())
        narration_data[str(page_num)] = clean_text
        print(f"  [文字預覽] {clean_text[:60]}...")
        
    # 保存文字稿為 JSON，供使用者編輯
    json_path = os.path.join(workspace_dir, "narration.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(narration_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n[+] 準備工作完成！")
    print(f"[*] 投影片圖片已儲存至：{workspace_dir}/")
    print(f"[*] 語音說明草稿已儲存至：{json_path}")
    print(f"[!] 提示：您可以手動編輯 `narration.json`，修改每一頁的旁白內容，修改完後再執行生成影片。")

def generate_video(pdf_path, workspace_dir, voice="zh-TW-HsiaoChenNeural", speed="+0%"):
    """
    第二階段：根據 JSON 旁白生成語音，並使用 moviepy 合成影片
    """
    json_path = os.path.join(workspace_dir, "narration.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"找不到語音說明稿 {json_path}，請先執行 --prepare 階段！")
        
    with open(json_path, "r", encoding="utf-8") as f:
        narration_data = json.load(f)
        
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
    
    total_pages = len(narration_data)
    clips = []
    audio_paths = []
    
    print("[*] 正在為每一頁投影片生成語音並建立影片剪輯...")
    
    for i in range(total_pages):
        page_num = i + 1
        page_str = str(page_num)
        text = narration_data.get(page_str, "").strip()
        
        img_path = os.path.join(workspace_dir, f"page_{page_num:03d}.png")
        audio_path = os.path.join(workspace_dir, f"page_{page_num:03d}.wav")
        
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"找不到投影片圖片 {img_path}，請確認工作目錄完整性。")
            
        # 1. 生成語音 (使用 edge-tts)
        if not text:
            print(f"  [{page_num}/{total_pages}] 旁白為空，生成 2 秒靜音...")
            create_silence_wav(audio_path, 2.0)
        else:
            print(f"  [{page_num}/{total_pages}] 正在生成語音：\"{text[:30]}...\"")
            # 呼叫 edge-tts 命令列工具
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
                print(f"  [-] edge-tts 執行失敗，錯誤訊息：{e.stderr.decode('utf-8', errors='ignore')}")
                print("  [*] 降級生成 3 秒靜音替代...")
                create_silence_wav(audio_path, 3.0)
        
        # 2. 建立無聲音的投影片片段 (避免同時開啟多個 ffmpeg 子進程)
        try:
            duration = get_wav_duration(audio_path)
            img_clip = ImageClip(img_path).with_duration(duration)
            clips.append(img_clip)
            audio_paths.append(audio_path)
        except Exception as e:
            print(f"  [-] 讀取音訊長度或建立片段失敗 (第 {page_num} 頁): {e}")
            
    if not clips:
        print("[-] 沒有成功的影片片段可以合併！")
        return
        
    # 3. 合併所有的音軌為單一 WAV 檔 (極速，免開子進程)
    final_audio_path = os.path.join(workspace_dir, "final_narration.wav")
    print("\n[*] 正在合併音軌為單一無損 WAV 檔...")
    try:
        concat_wavs(audio_paths, final_audio_path)
    except Exception as e:
        print(f"[-] 合併音軌失敗: {e}")
        return
        
    # 4. 串接影像片段並疊加合併後的音軌
    print("[*] 正在串接投影片片段並疊加音軌...")
    video_track = concatenate_videoclips(clips, method="compose")
    
    # 開啟單一 AudioFileClip 進程
    audio_clip = AudioFileClip(final_audio_path)
    final_video = video_track.with_audio(audio_clip)
    
    # 產出影片名稱
    pdf_base = os.path.splitext(os.path.basename(pdf_path))[0]
    output_mp4 = f"{pdf_base}_導覽影片.mp4"
    
    # 5. 導出為 MP4
    print("[*] 正在渲染並導出最終影片...")
    final_video.write_videofile(
        output_mp4,
        fps=5,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        logger="bar"
    )
    
    print(f"\n[+] 轉換完成！最終影片已儲存至：{os.path.abspath(output_mp4)}")
    
    # 6. 釋放與關閉資源
    for clip in clips:
        clip.close()
    audio_clip.close()
    final_video.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF 轉簡報語音說明影片工具")
    parser.add_argument("--pdf", type=str, default="轉PDF檔.pdf", help="要轉換的 PDF 檔案路徑")
    parser.add_argument("--prepare", action="store_true", help="執行第一階段：導出圖片並提取/辨識文字草稿")
    parser.add_argument("--generate", action="store_true", help="執行第二階段：將旁白轉換為語音並合成 MP4 影片")
    parser.add_argument("--voice", type=str, default="zh-TW-HsiaoChenNeural", help="edge-tts 語音角色 (例如 zh-TW-HsiaoChenNeural, zh-TW-YunJheNeural)")
    parser.add_argument("--speed", type=str, default="+0%", help="語速調整，例如 +5% 或 -10%")
    parser.add_argument("--dir", type=str, default="video_workspace", help="暫存與工作檔案的目錄名稱")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf):
        print(f"[-] 錯誤：找不到 PDF 檔案 '{args.pdf}'")
        sys.exit(1)
        
    if not args.prepare and not args.generate:
        print("[!] 請指定執行階段！")
        print("  步驟 1：python pdf_to_video.py --prepare  (提取圖片與文字稿)")
        print("  步驟 2：(可選) 編輯 video_workspace/narration.json 潤飾旁白")
        print("  步驟 3：python pdf_to_video.py --generate  (生成語音並導出影片)")
        sys.exit(0)
        
    if args.prepare:
        extract_pdf_pages_and_text(args.pdf, args.dir)
        
    if args.generate:
        generate_video(args.pdf, args.dir, args.voice, args.speed)
