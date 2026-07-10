import os
import sys
import json
import uuid
import shutil
import subprocess
import argparse
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
import edge_tts

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 初始化 FastAPI app
app = FastAPI(title="PDF to Voiceover Video Web App")

# 啟用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 建立基礎工作目錄
WORKSPACE_DIR = "video_web_workspace"
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# 掛載靜態檔案路由，方便瀏覽器載入投影片圖片與影片
app.mount("/workspace", StaticFiles(directory=WORKSPACE_DIR), name="workspace")

# 初始化 EasyOCR 模型 (只載入一次，加速辨識)
print("[*] 正在載入 EasyOCR 繁體中文與英文模型...")
import easyocr
reader = easyocr.Reader(['ch_tra', 'en'], gpu=False)
print("[+] EasyOCR 模型載入完成！")

# ====== 語音與音訊處理輔助函式 ======

def create_silence_mp3(filepath, duration_sec):
    """使用 ffmpeg 建立無聲 MP3 檔案"""
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
    """使用 ffmpeg 讀取音訊長度（秒）"""
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
    """使用 ffmpeg concat 功能快速無損合併 MP3 檔案"""
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

# ====== Web App API 路由 ======

# 1. 首頁
@app.get("/")
async def get_index():
    if os.path.exists("video_index.html"):
        return FileResponse("video_index.html")
    return JSONResponse(status_code=404, content={"message": "video_index.html not found"})

# 2. 語音試聽介面 (即時生成並回傳 MP3)
@app.get("/api/preview_audio")
async def preview_audio(text: str, voice: str = "zh-TW-HsiaoChenNeural", speed: str = "+0%"):
    if not text.strip():
        raise HTTPException(status_code=400, detail="文字內容不可為空")
        
    temp_dir = os.path.join(WORKSPACE_DIR, "temp_previews")
    os.makedirs(temp_dir, exist_ok=True)
    temp_filename = f"preview_{uuid.uuid4().hex}.mp3"
    temp_filepath = os.path.join(temp_dir, temp_filename)
    
    try:
        communicate = edge_tts.Communicate(text, voice, rate=speed)
        await communicate.save(temp_filepath)
        return FileResponse(temp_filepath, media_type="audio/mpeg", filename=temp_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"語音生成失敗: {e}")

# 3. 第一階段：上傳 PDF 並執行 OCR 提取
@app.post("/api/prepare")
async def prepare_pdf(file: UploadFile = File(...)):
    filename = file.filename
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="僅支援 PDF 檔案上傳")
        
    # 建立唯一的 Session 工作目錄
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(WORKSPACE_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    pdf_path = os.path.join(session_dir, "input.pdf")
    with open(pdf_path, "wb") as f:
        f.write(await file.read())
        
    try:
        # PDF 轉圖片
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        pages_data = []
        
        for i in range(total_pages):
            page = doc[i]
            # 1.2x 解析度即可，避免 CPU OCR 過慢
            mat = fitz.Matrix(1.2, 1.2)
            pix = page.get_pixmap(matrix=mat)
            img_filename = f"page_{i+1:03d}.png"
            img_path = os.path.join(session_dir, img_filename)
            pix.save(img_path)
            
            # OCR 辨識
            pil_img = Image.open(img_path)
            img_array = np.array(pil_img)
            ocr_results = reader.readtext(img_array, detail=0, paragraph=True)
            text = "\n".join(ocr_results).strip()
            
            pages_data.append({
                "page_num": i + 1,
                "img_url": f"/workspace/{session_id}/{img_filename}",
                "text": text
            })
            print(f"  [Prepare Session {session_id}] Page {i+1}/{total_pages} OCR finished.")
            
        doc.close()
        
        # 儲存初始的 narration.json
        narration = {str(item["page_num"]): item["text"] for item in pages_data}
        with open(os.path.join(session_dir, "narration.json"), "w", encoding="utf-8") as f:
            json.dump(narration, f, ensure_ascii=False, indent=2)
            
        return {
            "success": True,
            "session_id": session_id,
            "pdf_name": os.path.splitext(filename)[0],
            "pages": pages_data
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# 定義生成影片之 JSON 資料格式
class GenerateRequest(BaseModel):
    session_id: str
    voice: str = "zh-TW-HsiaoChenNeural"
    speed: str = "+0%"
    narration: dict  # 鍵為字串格式的頁碼，值為修改後的旁白文字

# 4. 第二階段：使用更新後的旁白資料生成簡報影片
@app.post("/api/generate")
async def generate_video(req: GenerateRequest):
    session_dir = os.path.join(WORKSPACE_DIR, req.session_id)
    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail="Session 不存在或已過期")
        
    try:
        # 將更新後的旁白寫入 narration.json
        narration_path = os.path.join(session_dir, "narration.json")
        with open(narration_path, "w", encoding="utf-8") as f:
            json.dump(req.narration, f, ensure_ascii=False, indent=2)
            
        from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
        
        total_pages = len(req.narration)
        clips = []
        audio_paths = []
        
        print(f"[*] [Session {req.session_id}] 正在為每頁投影片合成語音...")
        
        for i in range(total_pages):
            page_num = i + 1
            text = req.narration.get(str(page_num), "").strip()
            img_path = os.path.join(session_dir, f"page_{page_num:03d}.png")
            audio_path = os.path.join(session_dir, f"page_{page_num:03d}.mp3")
            
            if not os.path.exists(img_path):
                raise HTTPException(status_code=400, detail=f"找不到投影片圖片 page_{page_num:03d}.png")
                
            # 1. 生成語音
            if not text:
                print(f"  [{page_num}/{total_pages}] 無旁白，生成 3 秒靜音...")
                create_silence_mp3(audio_path, 3.0)
            else:
                print(f"  [{page_num}/{total_pages}] 正在生成語音：{text[:20]}...")
                try:
                    communicate = edge_tts.Communicate(text, req.voice, rate=req.speed)
                    await communicate.save(audio_path)
                except Exception as e:
                    print(f"    [-] edge-tts 失敗：{e}")
                    print(f"    [*] 降級使用 3 秒靜音...")
                    create_silence_mp3(audio_path, 3.0)
            
            # 2. 讀取長度並建立片段
            duration = get_audio_duration(audio_path)
            img_clip = ImageClip(img_path).with_duration(duration)
            clips.append(img_clip)
            audio_paths.append(audio_path)
            
        # 3. 合併所有音軌
        final_audio_path = os.path.join(session_dir, "final_narration.mp3")
        print(f"[*] [Session {req.session_id}] 正在合併音訊...")
        concat_mp3s(audio_paths, final_audio_path, session_dir)
        
        # 4. 合成影片與音軌
        print(f"[*] [Session {req.session_id}] 正在合併影片片段與音軌...")
        video_track = concatenate_videoclips(clips, method="compose")
        audio_clip = AudioFileClip(final_audio_path)
        final_video = video_track.with_audio(audio_clip)
        
        # 輸出影片檔名
        output_filename = "output_video.mp4"
        output_filepath = os.path.join(session_dir, output_filename)
        
        # 5. 影片渲染 (fps=5 + ultrafast 加速 50 倍)
        print(f"[*] [Session {req.session_id}] 正在渲染導出 MP4...")
        final_video.write_videofile(
            output_filepath,
            fps=5,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger=None  # Web 環境下關閉控制台進度條避免卡住
        )
        
        # 關閉並釋放資源
        for clip in clips:
            clip.close()
        audio_clip.close()
        final_video.close()
        
        print(f"[+] [Session {req.session_id}] 影片合成成功！")
        
        return {
            "success": True,
            "video_url": f"/workspace/{req.session_id}/{output_filename}"
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF to Video Web Server")
    parser.add_argument("--port", type=int, default=8000, help="Web app port (default: 8000)")
    args = parser.parse_args()
    
    # 啟動 Uvicorn 伺服器
    uvicorn.run(app, host="127.0.0.1", port=args.port)
