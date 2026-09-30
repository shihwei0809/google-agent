import re
import os

html_path = r"d:\GOOGLE ANGET\製程流程圖\public\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update renderWires() to support label offset and dragging
old_wire_label = """        if (wire.label) {
          const midX = (p1.x + p2.x) / 2;
          const midY = (p1.y + p2.y) / 2;
          const text = document.createElementNS(SVG_NS, 'text');
          text.setAttribute('x', midX);
          text.setAttribute('y', midY - 6);
          text.setAttribute('fill', labelColor);
          text.setAttribute('font-size', '10');
          text.setAttribute('font-weight', 'bold');
          text.setAttribute('text-anchor', 'middle');
          text.setAttribute('class', 'select-none pointer-events-none');
          text.textContent = wire.label;
          g.appendChild(text);
        }"""

new_wire_label = """        if (wire.label) {
          const midX = (p1.x + p2.x) / 2;
          const midY = (p1.y + p2.y) / 2;
          const offsetX = wire.labelOffsetX || 0;
          const offsetY = wire.labelOffsetY || 0;
          
          const text = document.createElementNS(SVG_NS, 'text');
          text.setAttribute('x', midX + offsetX);
          text.setAttribute('y', midY - 6 + offsetY);
          text.setAttribute('fill', labelColor);
          text.setAttribute('font-size', '10');
          text.setAttribute('font-weight', 'bold');
          text.setAttribute('text-anchor', 'middle');
          text.setAttribute('class', 'select-none cursor-move');
          text.textContent = wire.label;
          
          // 讓文字可以被拖曳
          text.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            startDragWireLabel(wire.id, e);
          });
          
          g.appendChild(text);
        }"""

if old_wire_label in html:
    html = html.replace(old_wire_label, new_wire_label)
else:
    print("WARNING: Could not find old_wire_label string to replace.")

# 2. Add startDragWireLabel function near startDragNode
script_insert_target = """    function startDragNode(id, e) {"""

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
else:
    print("WARNING: Could not find script_insert_target string to replace.")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Update applied successfully for wire label drag.")
