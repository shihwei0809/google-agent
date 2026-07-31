import base64
import io
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PIL import Image
import easyocr

app = FastAPI(title="Local OCR Server")

# 啟用 CORS 跨來源資源共享，允許手機瀏覽器連線呼叫
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 EasyOCR (載入繁體中文與英文模型)
print("[*] 正在載入 EasyOCR 繁體中文與英文模型...")
reader = easyocr.Reader(['ch_tra', 'en'], gpu=False)
print("[+] OCR 模型已成功載入，伺服器準備就緒！")

class OCRRequest(BaseModel):
    image_base64: str

# 提供靜態首頁，讓手機能直接連線開啟網頁
@app.get("/")
async def read_index():
    return FileResponse("Index.html")

@app.post("/ocr")
async def perform_ocr(req: OCRRequest):
    try:
        # 解析 Base64 字串並轉換為 PIL 圖片
        header, encoded = req.image_base64.split(",", 1) if "," in req.image_base64 else ("", req.image_base64)
        image_data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_data))
        
        # 轉成 JPEG 格式 bytes 傳入 EasyOCR
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        # 執行文字辨識
        results = reader.readtext(img_bytes, detail=0)
        full_text = "\n".join(results)
        return {"text": full_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 監聽 0.0.0.0 埠口 8000，允許同網域下的手機或設備連線
    uvicorn.run(app, host="0.0.0.0", port=8000)
