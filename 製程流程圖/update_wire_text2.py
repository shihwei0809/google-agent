import re
import os

html_path = r"d:\GOOGLE ANGET\製程流程圖\public\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# Add startDragWireLabel function near startDragNode
script_insert_target = """    function startDragNode(nodeId, e) {"""

start_drag_label_func = """    function startDragWireLabel(wireId, e) {
      const wire = state.wires.find(w => w.id === wireId);
      if (!wire) return;
      
      selectWire(wireId); // 選取該線段
      
      const startX = e.clientX;
      const startY = e.clientY;
      const initialOffsetX = wire.labelOffsetX || 0;
      const initialOffsetY = wire.labelOffsetY || 0;
      
      const onMouseMove = (moveEvent) => {
        const dx = (moveEvent.clientX - startX) / state.zoom;
        const dy = (moveEvent.clientY - startY) / state.zoom;
        wire.labelOffsetX = initialOffsetX + dx;
        wire.labelOffsetY = initialOffsetY + dy;
        renderWires();
      };
      
      const onMouseUp = () => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        saveHistory();
      };
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    }

"""

if script_insert_target in html:
    html = html.replace(script_insert_target, start_drag_label_func + script_insert_target)
    print("Function added.")
else:
    print("WARNING: Could not find script_insert_target string to replace.")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
