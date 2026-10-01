import re

html_path = r"d:\GOOGLE ANGET\製程流程圖\public\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

old_code = """        g.addEventListener('click', (e) => {
          e.stopPropagation();
          selectWire(wire.id);
        });"""

new_code = """        g.addEventListener('click', (e) => {
          e.stopPropagation();
          selectWire(wire.id);
        });

        g.addEventListener('dblclick', (e) => {
          e.stopPropagation();
          const mouse = getCanvasMousePos(e);
          if (!wire.waypoints) wire.waypoints = [];
          wire.waypoints.push({ x: mouse.x, y: mouse.y });
          selectWire(wire.id);
          saveHistory();
          renderAll(); // 重新渲染以顯示新折點
        });"""

if old_code in html:
    html = html.replace(old_code, new_code)
    print("Successfully injected dblclick event.")
else:
    print("WARNING: old_code not found.")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
