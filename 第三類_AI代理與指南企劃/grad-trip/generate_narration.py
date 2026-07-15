# 用 Edge-TTS 生成畢業旅行回憶錄音檔
import asyncio, edge_tts, os
from pathlib import Path

OUT = Path(__file__).parent / "assets" / "narration"
OUT.mkdir(parents=True, exist_ok=True)

VOICE = "zh-TW-HsiaoChenNeural"  # 用溫柔的女聲來呈現畢旅的溫馨與懷舊感
RATE = "-8%"  # 稍微慢速，帶有情感起伏
PITCH = "-1Hz"

SCRIPT = [
    (1, "在沒人看見的清晨，大巴已經靜候著我們。這是我們，小學五年級的畢業旅行。"),
    (2, "提著滿滿的行李，揮手告別爸媽。我們的笑臉，在晨光中肆意綻放。"),
    (3, "大巴緩緩駛上高速公路，兩旁的青山向後飛退，帶我們駛向夢想的遊樂園。"),
    (4, "終於抵達樂園的大門！大家笑著、鬧著，留下了第一張充滿朝氣的合照。"),
    (5, "坐在旋轉木馬和雲霄飛車上，風在耳邊呼嘯，這一刻，是純粹的快樂與驚呼。"),
    (6, "隨著夜幕低垂，營火在草地上高高堆起。微涼的晚風中，期待在悄悄蔓延。"),
    (7, "手拉著手，圍繞著熊熊烈火唱歌跳舞。火光映紅了每一張真摯而無憂的臉龐。"),
    (8, "營火的火星飛向浩瀚的星空，像繁星般耀眼。這個夜晚，註定會被永遠記得。"),
    (9, "回到旅館，穿上睡衣圍坐在床邊聊天。那些小秘密，在溫暖的燈光下流淌。"),
    (10, "第二天清晨，把行李重新收好。看著窗外的晨光，心中有一點小小的捨不得。"),
    (11, "來到最後的沙灘，我們一起把帽子拋向天空。這段青春，有你同行，真好。"),
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
