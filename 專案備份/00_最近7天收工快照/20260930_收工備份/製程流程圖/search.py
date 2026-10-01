import os

target = "液相/氣相/蒸汽多相流動可視化與自訂色彩標註系統"
base_dir = r"C:\GOOGLE ANGET"

for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith(".html"):
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    if target in file.read():
                        print(path)
            except Exception:
                pass
