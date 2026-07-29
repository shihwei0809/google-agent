import os
import sys
import json
import uuid
import socket
import itertools
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from docx_generator import generate_interview_report_docx

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

app = FastAPI(title="AI Voice Interview Analyzer for Materials & Supply Chain HR")

DATA_DIR = "data"
AUDIO_DIR = os.path.join(DATA_DIR, "audios")
DB_FILE = os.path.join(DATA_DIR, "db.json")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs("static", exist_ok=True)
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

FLASH_MODELS_CASCADE = [
    'gemini-3.6-flash',
    'gemini-3.5-flash',
    'gemini-3.1-flash-lite',
    'gemini-3-flash',
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-1.5-flash',
]

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port: int = 8000, max_attempts: int = 50) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port

class APIKeyPool:
    def __init__(self, req_keys: Optional[str] = None):
        raw_keys = req_keys or os.environ.get("GEMINI_API_KEYS", os.environ.get("GEMINI_API_KEY", ""))
        self.keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        self._iterator = itertools.cycle(self.keys) if self.keys else None

    def get_client_for_key(self, key: str) -> genai.Client:
        return genai.Client(api_key=key)

    def execute_with_retry(self, action_func):
        if not self.keys:
            raise HTTPException(
                status_code=400, 
                detail="未設定 API Key。請點擊右上角「🔑 API Key 管理」輸入 Key。"
            )
        
        last_error = None
        for _ in range(len(self.keys)):
            key = next(self._iterator)
            try:
                client = self.get_client_for_key(key)
                return action_func(client)
            except Exception as e:
                err_str = str(e)
                last_error = e
                if any(kw in err_str for kw in ["401", "UNAUTHENTICATED", "invalid authentication"]):
                    print(f"[KeyPool Warning] Key {key[:8]}... 401 Invalid: {err_str[:80]}")
                    continue
                if any(kw in err_str for kw in ["429", "RESOURCE_EXHAUSTED", "Quota", "rate limit"]):
                    print(f"[KeyPool Warning] Key {key[:8]}... 額度耗盡，自動切換下一組...")
                    continue
                raise HTTPException(status_code=500, detail=f"Gemini API 處理失敗: {err_str[:150]}")
                
        raise HTTPException(
            status_code=400, 
            detail=f"API 呼叫失敗 (錯誤: {str(last_error)[:120]})。"
        )

def call_gemini_with_model_cascade(client: genai.Client, contents: list, response_schema):
    last_exception = None
    for model_name in FLASH_MODELS_CASCADE:
        try:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.2
            )
            res = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            print(f"[Model Cascade Success] 採用模型: {model_name}")
            return res.parsed, model_name
        except Exception as e:
            last_exception = e
            print(f"[Model Cascade Warning] 模型 {model_name} 限制: {str(e)[:80]}，嘗試下一階...")
            continue
    raise last_exception

class BigFive(BaseModel):
    openness: int = Field(description="經驗開放性 (1-100)")
    conscientiousness: int = Field(description="盡責性/盡職度 (1-100)")
    extraversion: int = Field(description="外向性 (1-100)")
    agreeableness: int = Field(description="宜人性/親和力 (1-100)")
    emotional_stability: int = Field(description="情緒穩定度 (1-100)")

class JobMatch(BaseModel):
    title: str = Field(description="職缺名稱")
    score: int = Field(description="契合度評分 (1-100)")
    reason: str = Field(description="原因")

class InterviewReport(BaseModel):
    transcript: str = Field(description="完整的語音轉文字逐字稿 (Transcript)")
    candidate_summary: str = Field(description="對話核心摘要")
    communication_style: str = Field(description="溝通風格與語調表達特徵")
    acoustic_observation: str = Field(description="聲學與語速觀察（節奏、停頓、情緒波動）")
    disc_type: str = Field(description="DISC 人格類型")
    big_five: BigFive
    recommended_jobs: List[JobMatch]
    unsuitable_jobs: List[JobMatch]
    management_advice: str
    followup_questions: List[str]

class PureTranscriptResponse(BaseModel):
    transcript: str = Field(description="語音轉譯出的文字內容")

def load_records():
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_records(records):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/audios", StaticFiles(directory=AUDIO_DIR), name="audios")

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

@app.get("/api/records")
async def get_records():
    return load_records()

# 匯出 Word 評估報告 (.docx)
@app.get("/api/export-docx/{record_id}")
async def export_docx(record_id: str):
    records = load_records()
    rec = next((r for r in records if r["id"] == record_id), None)
    if not rec:
        raise HTTPException(status_code=404, detail="找不到該筆紀錄")

    if rec.get("status") != "analyzed" or not rec.get("report"):
        raise HTTPException(status_code=400, detail="該筆紀錄尚未完成 AI 特質分析，無法匯出 Word 報告")

    filename = f"面試特質評估報告_{rec['created_at'].replace(' ', '_').replace(':', '-')}.docx"
    output_path = os.path.join(DATA_DIR, f"export_{record_id}.docx")

    generate_interview_report_docx(rec, output_path)

    return FileResponse(
        path=output_path, 
        filename=filename, 
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# 刪除紀錄
@app.delete("/api/records/{record_id}")
async def delete_record(record_id: str):
    records = load_records()
    rec = next((r for r in records if r["id"] == record_id), None)
    if not rec:
        raise HTTPException(status_code=404, detail="找不到該筆紀錄")

    if "audio_path" in rec and os.path.exists(rec["audio_path"]):
        try: os.remove(rec["audio_path"])
        except: pass

    export_path = os.path.join(DATA_DIR, f"export_{record_id}.docx")
    if os.path.exists(export_path):
        try: os.remove(export_path)
        except: pass

    records = [r for r in records if r["id"] != record_id]
    save_records(records)

    return {"message": "紀錄已成功刪除", "remaining_count": len(records)}

# 1. 開始新的面試 Session
@app.post("/api/start-session")
async def start_session(target_dept: str = Query("資材部 (現場助理工程師/工程師/行政)")):
    rec_id = str(uuid.uuid4())
    audio_filename = f"{rec_id}.webm"
    saved_path = os.path.join(AUDIO_DIR, audio_filename)

    with open(saved_path, "wb") as f:
        pass

    new_record = {
        "id": rec_id,
        "target_dept": target_dept,
        "audio_url": f"/audios/{audio_filename}",
        "audio_path": saved_path,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transcript": "",
        "chunks_count": 0,
        "status": "recording",
        "used_model": None,
        "report": None
    }

    records = load_records()
    records.insert(0, new_record)
    save_records(records)

    return new_record

# 2. 每 5 分鐘背景拋送 Chunk 追加
@app.post("/api/append-chunk")
async def append_chunk(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    x_gemini_api_keys: Optional[str] = Header(None)
):
    key_pool = APIKeyPool(x_gemini_api_keys)
    records = load_records()
    rec = next((r for r in records if r["id"] == session_id), None)
    if not rec:
        raise HTTPException(status_code=404, detail="Session 不存在")

    chunk_bytes = await file.read()
    if not chunk_bytes:
        return rec

    with open(rec["audio_path"], "ab") as f:
        f.write(chunk_bytes)

    mime_type = file.content_type or "audio/webm"

    def do_transcribe_chunk(client: genai.Client):
        audio_part = types.Part.from_bytes(data=chunk_bytes, mime_type=mime_type)
        prompt = "請精準轉譯這小段錄音內容為繁體中文逐字稿，不需結尾標點以外的多餘說明。"
        parsed_res, used_model = call_gemini_with_model_cascade(
            client=client,
            contents=[audio_part, prompt],
            response_schema=PureTranscriptResponse
        )
        return parsed_res.transcript, used_model

    try:
        chunk_text, used_model = key_pool.execute_with_retry(do_transcribe_chunk)
        if chunk_text and chunk_text.strip():
            existing = rec["transcript"].strip()
            rec["transcript"] = (existing + "\n" + chunk_text.strip()).strip()
            rec["used_model"] = used_model
    except Exception as e:
        print(f"[Chunk Warning] 分段轉寫錯誤: {e}")

    rec["chunks_count"] = rec.get("chunks_count", 0) + 1
    save_records(records)

    return rec

# 3. 結束 Session 並發起分析
@app.post("/api/finish-session/{session_id}")
async def finish_session(
    session_id: str,
    analyze: bool = Query(True),
    x_gemini_api_keys: Optional[str] = Header(None)
):
    key_pool = APIKeyPool(x_gemini_api_keys)
    records = load_records()
    rec = next((r for r in records if r["id"] == session_id), None)
    if not rec:
        raise HTTPException(status_code=404, detail="Session 不存在")

    if not analyze:
        rec["status"] = "transcribed"
        save_records(records)
        return rec

    with open(rec["audio_path"], "rb") as f:
        full_audio_bytes = f.read()

    ext = os.path.splitext(rec["audio_path"])[1]
    mime_type = "audio/webm" if "webm" in ext else "audio/wav"
    target_dept = rec.get("target_dept", "資材部 (現場助理工程師/工程師/行政)")

    def do_final_analysis(client: genai.Client):
        contents = []
        if len(full_audio_bytes) <= 20 * 1024 * 1024:
            contents.append(types.Part.from_bytes(data=full_audio_bytes, mime_type=mime_type))

        prompt = f"""
        你是一位頂尖組織心理學家與 HR 顧問。
        應徵目標部門與職務為：【{target_dept}】。

        （特別評估注意事項：若目標為資材部現場助理工程師/工程師，黃金 DISC 為 C型(分析) + S型(穩健) CS型，著重高精準度、料號與SOP細節敏感度；若為資材行政，著重 S型(支援) + C型(分析) SC型）。

        這段長時間面試對話的完整逐字稿為：
        "{rec['transcript']}"

        請綜合對話內容與聲音風格，進行全方位特質與【{target_dept}】職務適性評估報告。
        """
        contents.append(prompt)

        parsed_res, used_model = call_gemini_with_model_cascade(
            client=client,
            contents=contents,
            response_schema=InterviewReport
        )
        return parsed_res.model_dump(), used_model

    report_data, used_model = key_pool.execute_with_retry(do_final_analysis)

    rec["status"] = "analyzed"
    rec["used_model"] = used_model
    if not report_data.get("transcript"):
        report_data["transcript"] = rec["transcript"]
    rec["report"] = report_data

    save_records(records)
    return rec

@app.post("/api/analyze-record/{record_id}")
async def analyze_existing_record(
    record_id: str,
    target_dept: Optional[str] = Query(None),
    x_gemini_api_keys: Optional[str] = Header(None)
):
    key_pool = APIKeyPool(x_gemini_api_keys)
    records = load_records()
    rec = next((r for r in records if r["id"] == record_id), None)
    if not rec:
        raise HTTPException(status_code=404, detail="找不到該筆面試紀錄")

    if target_dept:
        rec["target_dept"] = target_dept
    dept_name = rec.get("target_dept", "資材部 (現場助理工程師/工程師/行政)")

    saved_path = rec["audio_path"]
    if not os.path.exists(saved_path):
        raise HTTPException(status_code=404, detail="音訊檔案已遺失")

    with open(saved_path, "rb") as f:
        audio_bytes = f.read()

    ext = os.path.splitext(saved_path)[1]
    mime_type = "audio/webm" if "webm" in ext else "audio/wav"

    def do_analyze(client: genai.Client):
        contents = []
        if len(audio_bytes) <= 20 * 1024 * 1024:
            contents.append(types.Part.from_bytes(data=audio_bytes, mime_type=mime_type))

        prompt = f"""
        你是一位頂尖組織心理學家與 HR 顧問。
        應徵目標部門與職務為：【{dept_name}】。

        （特別評估注意事項：若目標為資材部現場助理工程師/工程師，黃金 DISC 為 C型(分析) + S型(穩健) CS型，著重高精準度、料號與SOP細節敏感度；若為資材行政，著重 S型(支援) + C型(分析) SC型）。

        這段錄音的語音轉寫文字為：
        "{rec['transcript']}"

        請結合聲音風格與對話內容，針對【{dept_name}】進行深度特質與職務契合度評估。
        """
        contents.append(prompt)

        parsed_res, used_model = call_gemini_with_model_cascade(
            client=client,
            contents=contents,
            response_schema=InterviewReport
        )
        return parsed_res.model_dump(), used_model

    report_data, used_model = key_pool.execute_with_retry(do_analyze)

    rec["status"] = "analyzed"
    rec["used_model"] = used_model
    rec["report"] = report_data
    save_records(records)

    return rec

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    local_ip = get_local_ip()
    port = find_available_port(8000)
    url = f"http://localhost:{port}"
    lan_url = f"http://{local_ip}:{port}"
    
    print("========================================================")
    print("  AI 面試語音與資材特質分析系統 - 伺服器啟動成功！")
    print(f"  -> 本機網址: {url}")
    print(f"  -> 區網網址: {lan_url}")
    print("========================================================")
    
    try:
        webbrowser.open(url)
    except:
        pass
        
    uvicorn.run(app, host="0.0.0.0", port=port)
