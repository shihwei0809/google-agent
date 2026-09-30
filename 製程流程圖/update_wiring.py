import re

html_path = r"d:\GOOGLE ANGET\製程流程圖\public\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update path generation to support waypoints
old_generate = """    function generateOrthoPath(p1, p2) {
      const dx = p2.x - p1.x;
      const dy = p2.y - p1.y;
      if (Math.abs(dx) > Math.abs(dy)) {
        const midX = p1.x + dx * 0.5;
        return `M ${p1.x} ${p1.y} L ${midX} ${p1.y} L ${midX} ${p2.y} L ${p2.x} ${p2.y}`;
      } else {
        const midY = p1.y + dy * 0.5;
        return `M ${p1.x} ${p1.y} L ${p1.x} ${midY} L ${p2.x} ${midY} L ${p2.x} ${p2.y}`;
      }
    }"""

new_generate = """    function generatePath(wire, p1, p2) {
      if (wire.waypoints && wire.waypoints.length > 0) {
        let path = `M ${p1.x} ${p1.y}`;
        wire.waypoints.forEach(wp => {
          path += ` L ${wp.x} ${wp.y}`;
        });
        path += ` L ${p2.x} ${p2.y}`;
        return path;
      }
      return generateOrthoPath(p1, p2);
    }
    
    function generateOrthoPath(p1, p2) {
      const dx = p2.x - p1.x;
      const dy = p2.y - p1.y;
      if (Math.abs(dx) > Math.abs(dy)) {
        const midX = p1.x + dx * 0.5;
        return `M ${p1.x} ${p1.y} L ${midX} ${p1.y} L ${midX} ${p2.y} L ${p2.x} ${p2.y}`;
      } else {
        const midY = p1.y + dy * 0.5;
        return `M ${p1.x} ${p1.y} L ${p1.x} ${midY} L ${p2.x} ${midY} L ${p2.x} ${p2.y}`;
      }
    }"""

if old_generate in html:
    html = html.replace(old_generate, new_generate)
else:
    print("Warning: old_generate not found")

# 2. Update renderWires to use generatePath and add handles/events
old_render = """        const p1 = getNodePortPos(wire.from.id, wire.from.port);
        const p2 = getNodePortPos(wire.to.id, wire.to.port);
        const pathData = generateOrthoPath(p1, p2);"""

new_render = """        const p1 = getNodePortPos(wire.from.id, wire.from.port);
        const p2 = getNodePortPos(wire.to.id, wire.to.port);
        const pathData = generatePath(wire, p1, p2);"""

if old_render in html:
    html = html.replace(old_render, new_render)

old_hitpath = """        // 點擊判定區（透明）
        const hitPath = document.createElementNS(SVG_NS, 'path');
        hitPath.setAttribute('d', pathData);
        hitPath.setAttribute('fill', 'none');
        hitPath.setAttribute('stroke', 'transparent');
        hitPath.setAttribute('stroke-width', '16');"""

new_hitpath = """        // 點擊判定區（透明）
        const hitPath = document.createElementNS(SVG_NS, 'path');
        hitPath.setAttribute('d', pathData);
        hitPath.setAttribute('fill', 'none');
        hitPath.setAttribute('stroke', 'transparent');
        hitPath.setAttribute('stroke-width', '20');
        
        // 雙擊線段新增折點 (Waypoint)
        hitPath.addEventListener('dblclick', (e) => {
          e.stopPropagation();
          const mouse = getCanvasMousePos(e);
          if (!wire.waypoints) wire.waypoints = [];
          wire.waypoints.push({ x: mouse.x, y: mouse.y });
          selectWire(wire.id);
          saveHistory();
        });"""

if old_hitpath in html:
    html = html.replace(old_hitpath, new_hitpath)

# 3. Add Handles when selected
old_wire_end = """        g.addEventListener('click', (e) => {
          e.stopPropagation();
          selectWire(wire.id);
        });

        wiresLayer.appendChild(g);
      });
    }"""

new_wire_end = """        g.addEventListener('click', (e) => {
          e.stopPropagation();
          selectWire(wire.id);
        });

        wiresLayer.appendChild(g);
        
        // 如果被選取，繪製重新連接與折點控制點
        if (isSelected) {
          // 起點重新連接控制點
          const p1Handle = createWireHandle(p1.x, p1.y, '#eab308');
          p1Handle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            startReconnectWire(wire, 'from', e);
          });
          wiresLayer.appendChild(p1Handle);
          
          // 終點重新連接控制點
          const p2Handle = createWireHandle(p2.x, p2.y, '#eab308');
          p2Handle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            startReconnectWire(wire, 'to', e);
          });
          wiresLayer.appendChild(p2Handle);
          
          // 折點控制點
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
    }
    
    function createWireHandle(x, y, color) {
      const circle = document.createElementNS(SVG_NS, 'circle');
      circle.setAttribute('cx', x);
      circle.setAttribute('cy', y);
      circle.setAttribute('r', '6');
      circle.setAttribute('fill', color);
      circle.setAttribute('stroke', '#ffffff');
      circle.setAttribute('stroke-width', '2');
      circle.setAttribute('class', 'cursor-move');
      return circle;
    }
    
    function startDragWaypoint(wire, idx, e) {
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
    }
    
    // 用於記錄目前正在重新連接的線段資訊
    let reconnectingData = null;

    function startReconnectWire(wire, endType, e) {
      reconnectingData = { wireId: wire.id, endType: endType };
      
      // 模擬進入連線狀態，讓其他設備的 Port 顯示出來
      state.connectingStart = { 
        nodeId: wire[endType === 'from' ? 'to' : 'from'].id, // 防止連向自己
        portIndex: wire[endType === 'from' ? 'to' : 'from'].port 
      };
      
      const pos = getNodePortPos(wire[endType].id, wire[endType].port);
      tempWire.setAttribute('x1', pos.x);
      tempWire.setAttribute('y1', pos.y);
      tempWire.setAttribute('x2', pos.x);
      tempWire.setAttribute('y2', pos.y);
      tempWire.classList.remove('hidden');
      connHint.classList.remove('hidden');
      
      renderPorts(); // 顯示所有可連接的目標點
      
      const onMouseMove = (moveEvent) => {
        const mouse = getCanvasMousePos(moveEvent);
        tempWire.setAttribute('x2', mouse.x);
        tempWire.setAttribute('y2', mouse.y);
      };
      
      const onMouseUp = (upEvent) => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        
        // 如果沒有在 port 上觸發 finishReconnect (mouseup)，則取消
        // finishReconnect 會在 port 的 mouseup 處理
        setTimeout(() => {
          if (reconnectingData) {
            cancelConnect();
            reconnectingData = null;
          }
        }, 50);
      };
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    }
"""

if old_wire_end in html:
    html = html.replace(old_wire_end, new_wire_end)

# 4. Modify ports mouseup to handle finish reconnect
old_port_mouseup = """          circle.addEventListener('mouseup', (e) => {
            e.stopPropagation();
            finishConnect(node.id, idx);
          });"""

new_port_mouseup = """          circle.addEventListener('mouseup', (e) => {
            e.stopPropagation();
            if (reconnectingData) {
              finishReconnect(node.id, idx);
            } else {
              finishConnect(node.id, idx);
            }
          });"""

if old_port_mouseup in html:
    html = html.replace(old_port_mouseup, new_port_mouseup)

# 5. Add finishReconnect function
insert_reconnect = """    function finishConnect(targetNodeId, targetPortIdx) {"""

finish_reconnect_func = """    function finishReconnect(targetNodeId, targetPortIdx) {
      if (!reconnectingData) return;
      
      const wire = state.wires.find(w => w.id === reconnectingData.wireId);
      if (wire) {
        saveHistory();
        wire[reconnectingData.endType] = { id: targetNodeId, port: targetPortIdx };
      }
      
      reconnectingData = null;
      cancelConnect();
      renderAll();
    }

"""

if insert_reconnect in html:
    html = html.replace(insert_reconnect, finish_reconnect_func + insert_reconnect)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Update applied for wire reconnect and waypoints.")
