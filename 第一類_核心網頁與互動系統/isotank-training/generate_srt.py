# generate_srt.py
import os

PAGES = [
    { "i": 1, "dur": 12.9, "sub": "歡迎收看 ISOTANK 化學品卸料安全訓練課程。今天我們用三分鐘，徹底掌握進貨安全的每一個關鍵步驟。" },
    { "i": 2, "dur": 14.3, "sub": "高危險化學品卸料，是一場與隱形危機的博弈。微小的靜電火花，或細微的接頭洩漏，都可能釀成不可挽回的災害。" },
    { "i": 3, "dur": 13.8, "sub": "卸料前，必須核對單據、標籤與安全資料表。同時，必須著裝完整的防化服、防毒面具與眼罩、以及耐酸鹼手套。" },
    { "i": 4, "dur": 15.6, "sub": "接著是雙重防護。將車輪鎖定，並在車體下方架設防溢流圍堤。隨後夾緊靜電接地夾，確認接地電阻小於十歐姆。" },
    { "i": 5, "dur": 14.7, "sub": "連接管路時，氣相平衡管必須先接，液相輸送管後接。接好後，引入低壓氮氣，在接頭塗抹肥皂水進行氣密測試。" },
    { "i": 6, "dur": 14.0, "sub": "緩慢開啟卸料閥，卸料期間，操作人員不得離開現場。必須嚴格監控管路壓力、儲槽液位與是否有異常氣味。" },
    { "i": 7, "dur": 14.2, "sub": "卸料結束後，關閉閥門，引入氮氣將管路殘液完全吹掃進儲槽。確認管路無壓、無殘液後，才可緩慢拆卸。" },
    { "i": 8, "dur": 12.6, "sub": "牢記緊急洗眼器與淋浴間的位置。接地防靜電，密閉防外洩，拆管先排空，安全不妥協。" },
    { "i": 9, "dur": 6.7,  "sub": "感謝您的參與，祝您工作平安。" },
]

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    if ms >= 1000:
        ms -= 1000
        s += 1
        if s >= 60:
            s -= 60
            m += 1
            if m >= 60:
                m -= 60
                h += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

dir_path = os.path.dirname(__file__)
renders_dir = os.path.join(dir_path, "renders")
srt_path = os.path.join(renders_dir, "ISOTANK_卸料安全訓練影片.srt")

current_time = 0.0
with open(srt_path, "w", encoding="utf-8") as f:
    for idx, p in enumerate(PAGES):
        start_str = format_time(current_time)
        end_time = current_time + p["dur"]
        end_str = format_time(end_time)
        
        f.write(f"{p['i']}\n")
        f.write(f"{start_str} --> {end_str}\n")
        f.write(f"{p['sub']}\n\n")
        
        current_time = end_time

print(f"[OK] SRT subtitle file generated at: {srt_path}")
