import os

src = "c:/GOOGLE ANGET/溫度通報/scratch/recovered_fish_0.py"
with open(src, "r", encoding="utf-8") as f:
    c = f.read()

print("Length:", len(c))
print("Last 200 repr:", repr(c[-200:]))
