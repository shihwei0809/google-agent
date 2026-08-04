import re
from pathlib import Path

durs   = [19,20,21,20,20,20,22,19,19,22,21,23]
starts = [sum(durs[:i]) for i in range(12)]
total  = sum(durs)

f = Path(r"C:\GOOGLE ANGET\isotank-hf-demo\index.html")
html = f.read_text(encoding="utf-8")

# root duration
html = re.sub(
    r'(data-composition-id="main"[^>]*data-duration=")\d+(")',
    lambda m: m.group(1) + str(total) + m.group(2),
    html
)
# fallback pattern
html = re.sub(r'data-duration="\d{3}"', f'data-duration="{total}"', html)

# each clip
for i in range(12):
    pid = i + 1
    html = re.sub(
        r'(id="p' + str(pid) + r'" class="slide clip" data-start=")\d+(" data-duration=")\d+(")',
        f'id="p{pid}" class="slide clip" data-start="{starts[i]}" data-duration="{durs[i]}"',
        html
    )
    print(f"p{pid}: start={starts[i]} dur={durs[i]}")

# GSAP offsets — replace old start values with new ones
old_starts = [0, 11, 24, 37, 51, 64, 76, 89, 100, 122, 144, 169]
for old, new in zip(old_starts, starts):
    if old != new:
        html = html.replace(f", {old}+", f", {new}+")

f.write_text(html, encoding="utf-8")
print(f"\nTotal: {total}s ({total/60:.1f} min)  — index.html saved")
