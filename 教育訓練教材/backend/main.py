import os
import sys
import time
import datetime
import asyncio
import shutil
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI 訓練平台 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載 materials 目錄為靜態資料夾，用來提供圖片等檔案
MATERIALS_DIR = "materials"
os.makedirs(MATERIALS_DIR, exist_ok=True)
app.mount("/materials_static", StaticFiles(directory=MATERIALS_DIR), name="materials_static")

from fastapi import FastAPI, UploadFile, File, HTTPException

def get_api_keys():
    """動態讀取最新 .env 中的 GEMINI_API_KEY，支援熱更新與多組輪詢"""
    load_dotenv(override=True)
    raw = os.getenv("GEMINI_API_KEY", "")
    return [k.strip() for k in raw.split(",") if k.strip()]

# 優先使用官方最新支援的模型
MODEL_FALLBACKS = [
    'gemini-2.5-flash',
    'gemini-3.5-flash',
    'gemini-3-flash-preview',
    'gemini-2.5-pro'
]

def call_gemini_with_fallback(prompt_or_list):
    """共用的 Gemini API 呼叫函數，支援多組 API Key 與多模型自動降級 (Fallback) 機制"""
    keys = get_api_keys()
    if not keys:
        raise Exception("系統尚未設定任何有效的 GEMINI_API_KEY，請至 backend/.env 填入金鑰")
        
    last_err = None
    for key in keys:
        genai.configure(api_key=key)
        for model_name in MODEL_FALLBACKS:
            try:
                model = genai.GenerativeModel(model_name)
                res = model.generate_content(prompt_or_list)
                return res
            except Exception as e:
                last_err = e
                print(f"[Fallback] 模型 {model_name} (Key: {key[:6]}...) 呼叫失敗: {e}")
                continue
    raise Exception(f"所有模型與 API Key 皆無法順利回應: {last_err}")

class ChatRequest(BaseModel):
    message: str
    context: str = ""
    material_name: str = "未知教材"

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI 訓練平台 API 運作中"}

# --- 教材管理 API ---

@app.get("/materials")
def list_materials():
    files = [f for f in os.listdir(MATERIALS_DIR) if f.endswith('.md') or f.endswith('.txt')]
    return {"materials": files}

@app.get("/materials/{filename}")
def get_material(filename: str):
    filepath = os.path.join(MATERIALS_DIR, filename)
    if not os.path.exists(filepath):
        return {"error": "找不到該教材"}
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return {"content": content}

import fitz  # PyMuPDF
import docx
import pandas as pd
from pptx import Presentation

@app.post("/materials")
async def upload_material(file: UploadFile = File(...)):
    filename = file.filename
    ext = filename.lower().split('.')[-1]
    
    # 讀取檔案內容至記憶體
    content_bytes = await file.read()
    
    # 若是 md 或 txt，直接存檔
    if ext in ['md', 'txt']:
        filepath = os.path.join(MATERIALS_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(content_bytes)
        return {"message": "上傳成功", "filename": filename}
    
    # 若是其他格式，進行文字萃取並轉為 md
    extracted_text = f"# {filename} (系統自動轉換)\n\n"
    new_filename = filename.rsplit('.', 1)[0] + ".md"
    filepath = os.path.join(MATERIALS_DIR, new_filename)
    
    try:
        if ext == 'pdf':
            doc = fitz.open(stream=content_bytes, filetype="pdf")
            for page in doc:
                extracted_text += page.get_text() + "\n\n"
                
        elif ext == 'docx':
            doc_file = io.BytesIO(content_bytes)
            doc = docx.Document(doc_file)
            for para in doc.paragraphs:
                extracted_text += para.text + "\n\n"
                
        elif ext == 'xlsx':
            excel_file = io.BytesIO(content_bytes)
            # 讀取所有 sheet
            xl = pd.ExcelFile(excel_file)
            for sheet_name in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet_name)
                extracted_text += f"## {sheet_name}\n\n"
                extracted_text += df.to_markdown(index=False) + "\n\n"
                
        elif ext == 'pptx':
            ppt_file = io.BytesIO(content_bytes)
            prs = Presentation(ppt_file)
            from pptx.enum.shapes import MSO_SHAPE_TYPE
            for i, slide in enumerate(prs.slides):
                extracted_text += f"## 第 {i+1} 頁\n\n"
                for j, shape in enumerate(slide.shapes):
                    if hasattr(shape, "text") and shape.text.strip():
                        extracted_text += shape.text + "\n"
                    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                        img_bytes = shape.image.blob
                        img_ext = shape.image.ext
                        img_filename = f"{filename.rsplit('.', 1)[0]}_p{i+1}_{j+1}.{img_ext}"
                        img_filepath = os.path.join(MATERIALS_DIR, img_filename)
                        with open(img_filepath, "wb") as img_f:
                            img_f.write(img_bytes)
                        
                        import urllib.parse
                        safe_img_filename = urllib.parse.quote(img_filename)
                        extracted_text += f"\n![圖片]({safe_img_filename})\n\n"
                extracted_text += "\n"
        elif ext in ['mp4', 'mov', 'avi', 'webm']:
            import time
            import requests
            import subprocess
            import tempfile
            import re
            
            keys = get_api_keys()
            if not keys:
                raise HTTPException(status_code=400, detail="尚未設定 GEMINI_API_KEY，請至 backend/.env 填入")
            
            base_clean_name = filename.rsplit('.', 1)[0]
            
            # 1. 儲存暫存影片供 ffmpeg 截圖
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_v:
                tmp_v.write(content_bytes)
                tmp_video_path = tmp_v.name
                
            captured_images = []
            try:
                # 2. 自動擷取影片真實操作截圖
                video_duration = 30
                try:
                    probe_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{tmp_video_path}"'
                    d_out = subprocess.check_output(probe_cmd, shell=True, text=True).strip()
                    video_duration = max(5, int(float(d_out)))
                except Exception as e:
                    print(f"[截圖提示] 無法取得影片時長: {e}")
                
                # 在影片時間軸依序擷取 5 個時間點的代表性真實畫面
                sample_fractions = [0.15, 0.35, 0.55, 0.75, 0.90]
                for idx, frac in enumerate(sample_fractions):
                    sec = max(1, int(video_duration * frac))
                    img_filename = f"{base_clean_name}_step_{idx+1}.jpg"
                    img_filepath = os.path.join(MATERIALS_DIR, img_filename)
                    ff_cmd = f'ffmpeg -y -ss {sec} -i "{tmp_video_path}" -vframes 1 -q:v 2 "{img_filepath}"'
                    subprocess.run(ff_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if os.path.exists(img_filepath) and os.path.getsize(img_filepath) > 1000:
                        captured_images.append(img_filename)
                        print(f"[畫面擷取] 成功擷取第 {sec} 秒操作畫面: {img_filename}")
            finally:
                if os.path.exists(tmp_video_path):
                    try:
                        os.remove(tmp_video_path)
                    except Exception:
                        pass
            
            # 依序輪詢金鑰進行上傳與分析
            analysis_success = False
            last_error = None
            
            mime_map = {
                'mp4': 'video/mp4',
                'mov': 'video/quicktime',
                'avi': 'video/x-msvideo',
                'webm': 'video/webm'
            }
            mime_type = mime_map.get(ext, 'video/mp4')
            
            for key in keys:
                try:
                    print(f"[影片解析] 透過 REST API 上傳影片至 Google: {filename} (Key: {key[:8]}...)...")
                    upload_url = "https://generativelanguage.googleapis.com/upload/v1beta/files"
                    upload_headers = {
                        "x-goog-api-key": key,
                        "X-Goog-Upload-Command": "start, upload, finalize",
                        "X-Goog-Upload-Header-Content-Length": str(len(content_bytes)),
                        "X-Goog-Upload-Header-Content-Type": mime_type,
                        "Content-Type": mime_type
                    }
                    
                    up_resp = requests.post(upload_url, headers=upload_headers, data=content_bytes, timeout=300)
                    if up_resp.status_code != 200:
                        raise Exception(f"Google 檔案上傳失敗 ({up_resp.status_code}): {up_resp.text}")
                    
                    file_info = up_resp.json().get("file", {})
                    file_uri = file_info.get("uri")
                    file_name = file_info.get("name")
                    print(f"[影片解析] 上傳成功: {file_name}，等待雲端解碼中...")
                    
                    # 輪詢等待檔案狀態變成 ACTIVE
                    check_url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}"
                    check_headers = {"x-goog-api-key": key}
                    
                    wait_count = 0
                    while True:
                        c_resp = requests.get(check_url, headers=check_headers, timeout=30)
                        if c_resp.status_code == 200:
                            state = c_resp.json().get("state")
                            if state == "ACTIVE":
                                print(f"[影片解析] 影片解碼就緒，共耗時 {wait_count} 秒")
                                break
                            elif state == "FAILED":
                                raise Exception("影片在 Google 雲端解碼處理失敗")
                        time.sleep(3)
                        wait_count += 3
                        print(f"       雲端解碼中 ({wait_count} 秒)...")
                        if wait_count > 300:
                            raise Exception("影片處理超時 (>300 秒)")
                    
                    img_list_str = "\n".join([f"- {img}" for img in captured_images])
                    print("[影片解析] 開始透過 Gemini 生成繁體中文 SOP 與 Mermaid 流程圖...")
                    prompt = f"""你是一個專業的教育訓練教材撰寫專家。
請仔細觀看這段系統操作影片，將人員的操作流程轉化為一份高品質的繁體中文 Markdown 圖文教學教材。
請嚴格包含以下區塊：
1. 💡 教材核心重點 (Key Takeaways)：提煉出這個影片中最核心的 3 個作業重點或防呆注意事項。
2. 🖼️ 系統流程圖：請根據影片的操作邏輯，使用 Mermaid 語法繪製一段精簡的流程圖 (graph TD)。
3. 📖 步驟解析：詳細記錄每個重要的點擊位置與欄位輸入，並使用要點式 (bullet points) 條列說明。

【重要：真實操作截圖嵌入指引】
系統已為這段影片自動擷取了真實的操作截圖檔名清單如下：
{img_list_str}

請將上述截圖檔名，依序分配插入在對應的步驟下方！
語法嚴格規定為：`![操作畫面](截圖檔名)`（例如：`![操作畫面]({captured_images[0] if captured_images else "screenshot.jpg"})`）。
請務必使用上方真實存在的檔名，絕不可在括號內填入自創文字！
"""
                    # 輪詢模型
                    generated_text = None
                    for model_name in MODEL_FALLBACKS:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
                        headers = {
                            "x-goog-api-key": key,
                            "Content-Type": "application/json"
                        }
                        body = {
                            "contents": [{
                                "parts": [
                                    {"file_data": {"mime_type": mime_type, "file_uri": file_uri}},
                                    {"text": prompt}
                                ]
                            }]
                        }
                        try:
                            g_resp = requests.post(url, headers=headers, json=body, timeout=180)
                            if g_resp.status_code == 200:
                                res_json = g_resp.json()
                                generated_text = res_json['candidates'][0]['content']['parts'][0]['text']
                                print(f"[影片解析] 模型 {model_name} 分析成功！")
                                break
                            else:
                                print(f"[Fallback] 模型 {model_name} 失敗: {g_resp.text[:120]}")
                        except Exception as m_err:
                            print(f"[Fallback] 模型 {model_name} 異常: {m_err}")
                            continue
                            
                    if not generated_text:
                        raise Exception("所有 Gemini 模型均無法回應分析請求")
                    
                    # 後處理防呆：若 Gemini 仍產生非圖片檔名的括號，依序補上真實截圖
                    if captured_images:
                        def replace_img_tag(match):
                            nonlocal captured_images
                            alt_text = match.group(1)
                            src_val = match.group(2)
                            # 如果不是已知圖檔
                            if not any(src_val.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                                chosen_img = captured_images.pop(0) if captured_images else ""
                                if chosen_img:
                                    return f"![{alt_text}]({chosen_img})"
                            return match.group(0)
                        
                        generated_text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_img_tag, generated_text)
                        
                    extracted_text = f"# 🎥 {filename.rsplit('.', 1)[0]} (影片SOP教學)\n\n" + generated_text
                    analysis_success = True
                    
                    # 清理雲端空間
                    try:
                        requests.delete(f"https://generativelanguage.googleapis.com/v1beta/{file_name}", headers=check_headers, timeout=10)
                    except Exception:
                        pass
                        
                    break # 成功即退出金鑰迴圈
                    
                except Exception as err:
                    print(f"[金鑰切換] 使用金鑰 {key[:8]}... 失敗: {err}")
                    last_error = err
                    continue
                    
            if not analysis_success:
                raise HTTPException(status_code=500, detail=f"影片解析失敗: {last_error}")
        else:
            raise HTTPException(status_code=400, detail=f"不支援的檔案格式: .{ext}")
            
        # ==========================================
        # AI 重寫與精煉 (適用於 PDF, DOCX, PPTX 等靜態文件)
        # ==========================================
        if ext not in ['mp4', 'mov', 'avi', 'webm', 'md', 'txt']:
            print(f"原始文件萃取完成，開始使用 AI 提煉精華與重寫版面 ({ext})...")
            rewrite_prompt = f"""你是一個專業的教育訓練教材撰寫專家。
以下是從原始文件中萃取出來的文字（以及保留的圖片標籤）。請仔細閱讀並理解內容，重新排版並提煉精華，產出一份給基層員工閱讀的高品質繁體中文 Markdown 圖文教學教材。
請嚴格包含以下區塊：
1. 💡 教材核心重點 (Key Takeaways)：提煉出這份教材最核心的 3 個重點。
2. 🖼️ 系統流程圖：請根據內容邏輯，使用 Mermaid 語法繪製精簡的流程圖 (graph TD)。
3. 📖 步驟解析：將原本的內容有邏輯地分章節列出，文字敘述必須簡單易懂。**重要：請務必保留原文中所有的圖片標籤 `![圖片](...)` 不可刪除，將它們安插在適合的步驟段落中，以便員工圖文對照學習**。

原始內容如下：
{extracted_text}
"""
            try:
                res = call_gemini_with_fallback(rewrite_prompt)
                extracted_text = res.text
            except Exception as e:
                print(f"AI 提煉失敗，退回原始萃取文字: {e}")
                # 若 AI 提煉失敗，保留原本原始萃取的 extracted_text

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(extracted_text)
            
        print(f"[教材儲存] 成功寫入教材檔案: {new_filename}")
        return {"message": "轉換並上傳成功", "filename": new_filename}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"轉換失敗: {e}")
        raise HTTPException(status_code=500, detail=f"檔案解析失敗: {str(e)}")

@app.delete("/materials/{filename}")
def delete_material(filename: str):
    filepath = os.path.join(MATERIALS_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return {"message": "刪除成功"}
    return {"error": "檔案不存在"}

from pydantic import BaseModel

class UpdateMaterialRequest(BaseModel):
    content: str

@app.put("/materials/{filename}")
def update_material(filename: str, req: UpdateMaterialRequest):
    filepath = os.path.join(MATERIALS_DIR, filename)
    if not os.path.exists(filepath):
        return {"error": "找不到該教材"}
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"message": "更新成功"}
    except Exception as e:
        return {"error": f"更新失敗: {str(e)}"}

class GenerateImageRequest(BaseModel):
    prompt: str

import urllib.request
import urllib.parse
import time

@app.post("/generate_image")
def generate_image(req: GenerateImageRequest):
    if not API_KEYS:
        return {"error": "未設定 API Key"}
    try:
        # 1. 將使用者的中文提示翻譯成精準的英文繪圖提示詞 (使用 Gemini 自動降級機制)
        prompt = f"Translate this image generation prompt to English. Just output the English text, add details if needed to make it look professional, no extra words: {req.prompt}"
        trans_res = call_gemini_with_fallback(prompt)
        eng_prompt = trans_res.text.strip()
        
        # 2. 呼叫外部免金鑰 AI 繪圖 API (Pollinations) 進行繪圖
        safe_prompt = urllib.parse.quote(eng_prompt)
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}?nologo=true&width=800&height=600"
        
        # 3. 將生成的圖片下載並存入系統的教材圖片庫
        timestamp = int(time.time())
        filename = f"ai_img_{timestamp}.jpg"
        filepath = os.path.join(MATERIALS_DIR, filename)
        
        req_img = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req_img) as response, open(filepath, 'wb') as out_file:
            out_file.write(response.read())
        
        return {"filename": filename}
    except Exception as e:
        return {"error": str(e)}

@app.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    """專門處理前端貼上 (Paste) 截圖的 API"""
    try:
        ext = file.filename.split('.')[-1].lower()
        if ext not in ['png', 'jpg', 'jpeg', 'gif']:
            ext = 'png' # 預設副檔名
            
        content_bytes = await file.read()
        timestamp = int(time.time())
        filename = f"screenshot_{timestamp}.{ext}"
        filepath = os.path.join(MATERIALS_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(content_bytes)
            
        return {"url": filename}
    except Exception as e:
        return {"error": str(e)}

# --- AI 問答 API ---

import asyncio

@app.post("/chat")
async def chat_with_ai(req: ChatRequest):
    keys = get_api_keys()
    if not keys:
        return JSONResponse(content={"response": "系統尚未設定任何 GEMINI_API_KEY，請至 backend/.env 填入金鑰。"})
    
    # 優先使用當前教材內容，若不足則輔以其他教材摘錄
    current_ctx = req.context or ""
    materials_summary = ""
    if os.path.exists(MATERIALS_DIR):
        for fname in os.listdir(MATERIALS_DIR):
            if fname.endswith(".md") and fname != req.material_name:
                try:
                    fpath = os.path.join(MATERIALS_DIR, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        content_sample = f.read(300).replace("\n", " ")
                        materials_summary += f"\n- 教材【{fname}】：{content_sample}..."
                except Exception:
                    pass

    prompt = f"""你是一個專業的企業內訓 AI 助教。
請根據學員當前正在研讀的教材內容，親切且專業地回答學員的提問。
如果問題跨越了其他教材，請參考下方相關教材摘要做統整回答。

【當前研讀教材: {req.material_name}】
{current_ctx[:4000]}

【系統其他相關教材目錄與摘要】
{materials_summary}

【學員問題】
{req.message}

請以繁體中文回答，條列分明，若有具體操作步驟請給出要點。"""

    for key_idx, current_key in enumerate(keys):
        genai.configure(api_key=current_key)
        for model_name in MODEL_FALLBACKS:
            try:
                model = genai.GenerativeModel(model_name)
                # 使用非同步線程池執行，防止阻塞主伺服器事件循環
                res = await asyncio.to_thread(model.generate_content, prompt)
                ans_text = res.text or "很抱歉，無法生成該問題的回答。"
                
                # 背景記錄 Excel
                try:
                    import openpyxl
                    log_file = "chat_logs.xlsx"
                    now = datetime.datetime.now()
                    month_str = now.strftime("%Y-%m")
                    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                    if os.path.exists(log_file):
                        wb = openpyxl.load_workbook(log_file)
                    else:
                        wb = openpyxl.Workbook()
                        if "Sheet" in wb.sheetnames:
                            del wb["Sheet"]
                    if month_str not in wb.sheetnames:
                        ws = wb.create_sheet(title=month_str)
                        ws.append(["時間", "當前檢視教材", "學員提問", "AI回覆"])
                    else:
                        ws = wb[month_str]
                    ws.append([timestamp, req.material_name, req.message, ans_text])
                    wb.save(log_file)
                except Exception as log_e:
                    print(f"記錄對話失敗: {log_e}")
                
                # 非同步打字機串流回傳給前端
                async def stream_output():
                    chunk_size = 20
                    for i in range(0, len(ans_text), chunk_size):
                        yield ans_text[i:i+chunk_size]
                        await asyncio.sleep(0.015)
                    footer = f"\n\n*(Powered by {model_name})*"
                    yield footer
                    
                return StreamingResponse(stream_output(), media_type="text/plain; charset=utf-8")
            except Exception as e:
                print(f"[Chat Fallback] Key({key_idx+1}) 模型 {model_name} 呼叫失敗: {e}")
                continue
                
    return JSONResponse(content={"response": "所有 AI 模型皆暫時無法回應，請檢查 API Key 或稍後再試。"})
