"""
批次生成投影片 MP3 旁白
使用 edge-tts（免費，微軟 Azure Neural TTS 品質）

安裝：pip install edge-tts
執行：python generate_mp3.py

輸出：slides/slide_01.mp3 ~ slide_20.mp3
"""

import asyncio
import edge_tts
import os
import csv
import sys

# ── 設定區 ─────────────────────────────────────────────────
ENGINE = "microsoft"              # 配音引擎："microsoft" (使用 edge-tts) 或 "google" (使用 Gemini TTS)

# 微軟設定 (ENGINE = "microsoft")
VOICE = "zh-TW-HsiaoChenNeural"   # 女聲（自然）
# VOICE = "zh-TW-YunJheNeural"    # 男聲
RATE  = "+0%"    # 語速 例如 +10% 加快 / -10% 放慢

# Google 設定 (ENGINE = "google")
# 可選聲音如："Kore" (女聲), "Zephyr" (男聲), "Aoede", "Puck", "Fenrir" 等
GEMINI_VOICE = "Kore"

OUTPUT_DIR = "slides"             # 輸出資料夾（與 index_with_mp3.html 同目錄）

# ── 朗讀文字 ─────────────────────────────────────────────────
# 方式一：直接在這裡填寫每頁旁白（最簡單）
# 格式：("輸出檔名", "朗讀文字")
NARRATIONS = [
    ("slide_01", "第一頁旁白：歡迎參加員工教育訓練測驗，請仔細聆聽每一頁的說明。"),
    ("slide_02", "第二頁旁白：請在此填入第二頁的朗讀內容。"),
    # ... 依序填到 slide_20
    # 可以直接從 Google Sheet「語音朗讀內容」欄位複製貼上
]

# 方式二：從 CSV 讀取（若你已從 Google Sheet 匯出 CSV）
# CSV 格式：檔名, 朗讀文字
# 例如：slide_01,"歡迎參加員工教育訓練..."
CSV_FILE = "narrations.csv"  # 若此檔案存在則自動改用 CSV 模式

# ─────────────────────────────────────────────────────────────

def load_from_csv(csv_path):
    items = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2 and row[0].strip():
                items.append((row[0].strip(), row[1].strip()))
    return items

async def generate_one(name, text, idx, total):
    ext = "wav" if ENGINE == "google" else "mp3"
    output_path = os.path.join(OUTPUT_DIR, f"{name}.{ext}")
    print(f"[{idx}/{total}] 生成 {name}.{ext} ...", end=" ", flush=True)
    
    if not text.strip():
        print("⚠ 文字為空，跳過")
        return
        
    if ENGINE == "google":
        try:
            from google import genai
        except ImportError:
            print("\n❌ 未偵測到 google-genai 套件。請在本機安裝：pip install google-genai")
            sys.exit(1)
            
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("\n❌ 未偵測到 GEMINI_API_KEY 環境變數。請在終端機設定它（例如 $env:GEMINI_API_KEY='你的金鑰'）")
            sys.exit(1)
            
        try:
            client = genai.Client(api_key=api_key)
            interaction = client.interactions.create(
                model="gemini-3.1-flash-tts-preview",
                input=text,
                response_format={"type": "audio"},
                generation_config={"speech_config": [{"voice": GEMINI_VOICE}]}
            )
            
            import base64
            import wave
            
            pcm_data = base64.b64decode(interaction.output_audio.data)
            with wave.open(output_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(pcm_data)
                
            size = os.path.getsize(output_path)
            print(f"✓ ({size/1024:.0f} KB)")
        except Exception as e:
            print(f"❌ 失敗: {e}")
    else:
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
        await communicate.save(output_path)
        size = os.path.getsize(output_path)
        print(f"✓ ({size/1024:.0f} KB)")

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 決定使用哪種資料來源
    if os.path.exists(CSV_FILE):
        print(f"📄 從 CSV 讀取：{CSV_FILE}")
        items = load_from_csv(CSV_FILE)
    else:
        print(f"📝 使用腳本內建文字（共 {len(NARRATIONS)} 頁）")
        items = NARRATIONS
    
    if not items:
        print("❌ 沒有任何旁白文字，請先填寫 NARRATIONS 或提供 narrations.csv")
        sys.exit(1)
    
    if ENGINE == "google":
        print(f"🎙  引擎：Google Gemini TTS  聲音：{GEMINI_VOICE}")
    else:
        print(f"🎙  引擎：Microsoft edge-tts  聲音：{VOICE}  語速：{RATE}")
    print(f"📁 輸出目錄：{os.path.abspath(OUTPUT_DIR)}")
    print("-" * 50)
    
    for i, (name, text) in enumerate(items, 1):
        await generate_one(name, text, i, len(items))
    
    print("-" * 50)
    ext = "wav" if ENGINE == "google" else "mp3"
    print(f"✅ 完成！共生成 {len(items)} 個 {ext.upper()} 檔案")
    print(f"   請將 slides/ 資料夾與 index_with_mp3.html 放在同一目錄後開啟")

if __name__ == "__main__":
    asyncio.run(main())
