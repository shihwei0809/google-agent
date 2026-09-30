import re

html_path = r"d:\GOOGLE ANGET\製程流程圖\public\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Remove the old dblclick event on `g` (we don't need it if we have midpoint handles, or we can keep it as a fallback. Let's keep it but just in case, let's remove the clunky g.addEventListener('dblclick'))
# Wait, let's just replace the whole block from `g.addEventListener('click'` to `wiresLayer.appendChild(g);`
old_events_block = """        g.addEventListener('click', (e) => {
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
        });

        wiresLayer.appendChild(g);"""

new_events_block = """        g.addEventListener('mousedown', (e) => {
          // 支援直接按住管線拖曳新增折點
          e.stopPropagation();
          if (state.selectedWireId !== wire.id) {
            selectWire(wire.id);
          } else {
            // 已選取狀態下，直接按住線段拖曳產生新折點
            const mouse = getCanvasMousePos(e);
            if (!wire.waypoints) wire.waypoints = [];
            
            const p1Pos = getNodePortPos(wire.from.id, wire.from.port);
            const p2Pos = getNodePortPos(wire.to.id, wire.to.port);
            const pts = [p1Pos, ...wire.waypoints, p2Pos];
            let minIndex = 0;
            let minDist = Infinity;
            const dist2 = (p, v, w) => {
              let l2 = (v.x - w.x)**2 + (v.y - w.y)**2;
              if (l2 === 0) return (p.x - v.x)**2 + (p.y - v.y)**2;
              let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
              t = Math.max(0, Math.min(1, t));
              return (p.x - (v.x + t * (w.x - v.x)))**2 + (p.y - (v.y + t * (w.y - v.y)))**2;
            };
            for(let i=0; i<pts.length-1; i++) {
              let d = dist2(mouse, pts[i], pts[i+1]);
              if (d < minDist) { minDist = d; minIndex = i; }
            }
            
            wire.waypoints.splice(minIndex, 0, { x: mouse.x, y: mouse.y });
            startDragWaypoint(wire, minIndex, e);
          }
        });

        wiresLayer.appendChild(g);"""

if old_events_block in html:
    html = html.replace(old_events_block, new_events_block)
else:
    print("WARNING: old_events_block not found.")
    
# 2. Add midpoint handles in the `if (isSelected)` block
old_is_selected_block = """          // 折點控制點
          if (wire.waypoints) {
            wire.waypoints.forEach((wp, idx) => {
              const wpHandle = createWireHandle(wp.x, wp.y, '#0ea5e9');
              wpHandle.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                startDragWaypoint(wire, idx, e);
              });
              wpHandle.addEventListener('dblclick', (e) => {
                e.stopPropagation();
                wire.waypoints.splice(idx, 1);
                saveHistory();
                renderAll();
              });
              wiresLayer.appendChild(wpHandle);
            });
          }
        }
      });
    }"""

new_is_selected_block = """          // 折點控制點
          if (wire.waypoints) {
            wire.waypoints.forEach((wp, idx) => {
              const wpHandle = createWireHandle(wp.x, wp.y, '#0ea5e9');
              wpHandle.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                startDragWaypoint(wire, idx, e);
              });
              wpHandle.addEventListener('dblclick', (e) => {
                e.stopPropagation();
                wire.waypoints.splice(idx, 1);
                saveHistory();
                renderAll();
              });
              wiresLayer.appendChild(wpHandle);
            });
          }
          
          // 中點虛擬控制點 (輔助提示，點擊拖曳即可新增)
          const pts = [p1, ...(wire.waypoints || []), p2];
          for(let i=0; i<pts.length-1; i++) {
             const midX = (pts[i].x + pts[i+1].x) / 2;
             const midY = (pts[i].y + pts[i+1].y) / 2;
             const midHandle = createWireHandle(midX, midY, '#bae6fd');
             midHandle.setAttribute('r', '4');
             midHandle.style.opacity = '0.8';
             midHandle.style.cursor = 'crosshair';
             midHandle.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                if (!wire.waypoints) wire.waypoints = [];
                wire.waypoints.splice(i, 0, { x: midX, y: midY });
                startDragWaypoint(wire, i, e);
             });
             wiresLayer.appendChild(midHandle);
          }
        }
      });
    }"""

if old_is_selected_block in html:
    html = html.replace(old_is_selected_block, new_is_selected_block)
else:
    print("WARNING: old_is_selected_block not found.")
    
# 3. Modify startDragWaypoint to optionally accept remove on click
# If startX == endX and startY == endY on mouseup, it means it was just a click.
# We can remove the waypoint if it was just a click, avoiding accidental clicks generating many points.
old_start_drag_wp = """    function startDragWaypoint(wire, idx, e) {
      const startX = e.clientX;
      const startY = e.clientY;
      const wp = wire.waypoints[idx];
      const startWpX = wp.x;
      const startWpY = wp.y;
      
      const onMouseMove = (moveEvent) => {
        wp.x = startWpX + (moveEvent.clientX - startX) / state.zoom;
        wp.y = startWpY + (moveEvent.clientY - startY) / state.zoom;
        renderWires();
      };
      
      const onMouseUp = () => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        saveHistory();
      };
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    }"""

new_start_drag_wp = """    function startDragWaypoint(wire, idx, e) {
      const startX = e.clientX;
      const startY = e.clientY;
      const wp = wire.waypoints[idx];
      const startWpX = wp.x;
      const startWpY = wp.y;
      let hasMoved = false;
      
      const onMouseMove = (moveEvent) => {
        hasMoved = true;
        wp.x = startWpX + (moveEvent.clientX - startX) / state.zoom;
        wp.y = startWpY + (moveEvent.clientY - startY) / state.zoom;
        renderWires();
      };
      
      const onMouseUp = () => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        // 如果沒有移動，代表只是誤點，把剛新增的節點刪除
        if (!hasMoved && wire.waypoints.length > 0) {
           // wire.waypoints.splice(idx, 1);
           // 不要隨便刪除，這可能讓使用者原本的點消失。我們在這裡不做任何事，維持雙擊刪除的邏輯即可。
        }
        saveHistory();
        renderAll();
      };
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    }"""
    
if old_start_drag_wp in html:
    html = html.replace(old_start_drag_wp, new_start_drag_wp)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
    
print("Updated to support click-and-drag midpoints.")
