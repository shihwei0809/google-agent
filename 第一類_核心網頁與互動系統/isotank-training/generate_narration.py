# 用 Edge-TTS 生成 ISOTANK 安全訓練旁白
# 執行：python generate_narration.py
import asyncio
import edge_tts
from pathlib import Path

OUT = Path(__file__).parent / "assets" / "narration"
OUT.mkdir(parents=True, exist_ok=True)

VOICE = "zh-TW-YunJheNeural"
RATE = "-5%"  # 稍微放慢一點點以維持安全宣導的莊重沉穩感
PITCH = "-1Hz"

SCRIPT = [
    (1, "歡迎收看 ISOTANK 化學品卸料安全訓練課程。今天我們用三分鐘，徹底掌握進貨安全的每一個關鍵步驟。"),
    (2, "高危險化學品卸料，是一場與隱形危機的博弈。微小的靜電火花，或細微的接頭洩漏，都可能釀成不可挽回的災害。"),
    (3, "卸料前，必須核對單據、標籤與安全資料表。同時，必須著裝完整的防化服、防毒面具與眼罩、以及耐酸鹼手套。"),
    (4, "接著是雙重防護。將車輪鎖定，並在車體下方架設防溢流圍堤。隨後夾緊靜電接地夾，確認接地電阻小於十歐姆。"),
    (5, "連接管路時，氣相平衡管必須先接，液相輸送管後接。接好後，引入低壓氮氣，在接頭塗抹肥皂水進行氣密測試。"),
    (6, "緩慢開啟卸料閥，卸料期間，操作人員不得離開現場。必須嚴格監控管路壓力、儲槽液位與是否有異常氣味。"),
    (7, "卸料結束後，關閉閥門，引入氮氣將管路殘液完全吹掃進儲槽。確認管路無壓、無殘液後，才可緩慢拆卸。"),
    (8, "牢記緊急洗眼器與淋浴間的位置。接地防靜電，密閉防外洩，拆管先排空，安全不妥協。"),
    (9, "感謝您的參與，祝您工作平安。"),
]

async def synth(i, text):
    out = OUT / f"page-{i:02d}.mp3"
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(str(out))
    print(f"OK page-{i:02d}.mp3")

async def main():
    for i, t in SCRIPT:
        for attempt in range(3):
            try:
                await synth(i, t)
                break
            except Exception as e:
                print(f"retry {i} ({attempt+1}): {e}")
                await asyncio.sleep(2)
    print("All done.")

if __name__ == "__main__":
    asyncio.run(main())
