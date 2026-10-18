import os
import shutil
import uuid
import socket
import json
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from video_generator import render_multi_scene_video

app = FastAPI(title="AI 影音自動剪輯工作站")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def generate_storyboard(topic: str, prompt: str) -> list:
    """
    依據使用者輸入的主題與概念，自動構建 4 個連續鏡頭的劇本與對應的精確圖片檢索關鍵字
    """
    if "倒掛" in prompt or "特斯拉" in prompt or "車" in prompt:
        return [
            {
                "title": "第一幕：驚人現象",
                "highlight": "0.81s 加速與倒掛？",
                "subtitle": "傳統輪胎極限真的能突破嗎",
                "search_keyword": "Tesla Roadster sports car red 4k",
                "script": "特斯拉 Roadster 宣稱零到一百只要 0.81 秒，甚至還能倒掛行駛，這到底怎麼做到的？"
            },
            {
                "title": "第二幕：氣動力學下壓力",
                "highlight": "下壓力 > 車身重",
                "subtitle": "伯努利定律與負壓效應",
                "search_keyword": "racing car aerodynamic wind tunnel airflow",
                "script": "首先是倒掛行駛！當車速夠快，空氣動力學產生巨大的下壓力超過車重，就能吸附在隧道頂端！"
            },
            {
                "title": "第三幕：太空火箭推進",
                "highlight": "SpaceX 冷氣推進器",
                "subtitle": "突破橡膠摩擦力係數上限",
                "search_keyword": "SpaceX rocket thruster nozzle fire",
                "script": "至於零點八一秒的恐怖加速，則是靠十個冷氣火箭噴嘴直接噴射，打破輪胎抓地力的物理極限！"
            },
            {
                "title": "第四幕：科學總結",
                "highlight": "國中理化完美驗證",
                "subtitle": "作用力與反作用力的極致展現",
                "search_keyword": "supercar futuristic speeding highway",
                "script": "看似科幻的神話，背後其實就是牛頓第三運動定律！你學會了嗎？"
            }
        ]
    elif any(k in topic or k in prompt for k in ["化", "工廠", "實驗", "產線", "加班", "廢液", "工程"]):
        return [
            {
                "title": "第一幕：現場直擊",
                "highlight": topic,
                "subtitle": "化工產業前線現場",
                "search_keyword": "chemical industry plant workers control room",
                "script": f"走進化工產業最真實的現場，{topic}其實藏著許多不為人知的專業與堅持！"
            },
            {
                "title": "第二幕：關鍵製程與難題",
                "highlight": "嚴謹工藝與挑戰",
                "subtitle": "精密反應與安全控制",
                "search_keyword": "chemical plant refinery pipes distillation towers",
                "script": "從複雜的化學反應槽到管線監控，每一個環節都必須精準掌握溫度與壓力，絕不容許任何差錯！"
            },
            {
                "title": "第三幕：專業與默默付出",
                "highlight": "守護生產穩定運行",
                "subtitle": "全天候數據監控",
                "search_keyword": "chemical engineer in protective suit laboratory testing",
                "script": "無論日夜交替，專業人員隨時監測化驗數據與產線進耗存，確保製程安全與高效穩定。"
            },
            {
                "title": "第四幕：產業基石",
                "highlight": "致敬每一位幕後推手",
                "subtitle": "推動現代科技不可或缺的力量",
                "search_keyword": "modern petrochemical industry factory dramatic sunset",
                "script": "正是這群默默付出的工程師與技術員，撐起了整個現代科技製造業的基石！"
            }
        ]
    else:
        # 通用精確語意配圖
        clean_text = prompt.replace("隨便幫我產生一段二三十秒的短影片", "").strip() or topic
        return [
            {
                "title": "引言導入",
                "highlight": topic,
                "subtitle": "AI 探索世界",
                "search_keyword": f"{topic} professional photography",
                "script": f"今天我們就來聊聊這個超熱門話題：{topic}！"
            },
            {
                "title": "深入剖析",
                "highlight": "核心關鍵解析",
                "subtitle": "隱藏在背後的關鍵細節",
                "search_keyword": f"{topic} high tech precision concept",
                "script": f"很多人不知道，其實這背後最關鍵的因素，就是科學與數據的精準結合。"
            },
            {
                "title": "實務應用",
                "highlight": "突破傳統想像",
                "subtitle": "效率與體驗全面進化",
                "search_keyword": f"{topic} modern application future",
                "script": f"當我們理解了其中的原理，就能掌握未來的趨勢與方向！"
            },
            {
                "title": "結論總結",
                "highlight": "立即跟上趨勢",
                "subtitle": "關注我們獲取更多知識",
                "search_keyword": f"{topic} success breakthrough",
                "script": "這就是今天的超精彩解析！喜歡的話記得點讚收藏，我們下期見！"
            }
        ]

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    local_ip = get_local_ip()
    return templates.TemplateResponse(request=request, name="index.html", context={"local_ip": local_ip})

@app.post("/api/generate")
async def api_generate(
    file: UploadFile = File(None),
    title: str = Form("AI 智能短影音"),
    text_script: str = Form(...),
    voice: str = Form("zh-TW-YunJheNeural"),
    accent_color: str = Form("#FF7A1A")
):
    try:
        req_id = str(uuid.uuid4())[:8]
        saved_media = None

        if file and file.filename:
            saved_media = os.path.join(UPLOAD_DIR, f"{req_id}_{file.filename}")
            with open(saved_media, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        output_filename = f"story_reel_{req_id}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        # 1. 自動拆解為 4 幕連續分鏡
        scenes = generate_storyboard(topic=title, prompt=text_script)

        # 2. 進行多鏡頭合成（第 1 鏡使用使用者素材，後續 3 鏡 AI 自動補齊圖卡素材）
        await render_multi_scene_video(
            user_media=saved_media,
            topic=title,
            scenes=scenes,
            output_video_path=output_path,
            voice=voice,
            accent_color=accent_color
        )

        return JSONResponse({
            "status": "success",
            "video_url": f"/outputs/{output_filename}",
            "filename": output_filename,
            "scene_count": len(scenes)
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8050, reload=False)
