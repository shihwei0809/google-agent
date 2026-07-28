import os

src = "c:/GOOGLE ANGET/溫度通報/scratch/recovered_gdrive_0.py"
with open(src, "r", encoding="utf-8") as f:
    c = f.read()

print("Length:", len(c))
print("Repr:", repr(c[:200]))
