import re
import os

html_path = r"d:\GOOGLE ANGET\製程流程圖\public\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update getNodePortPos
port_pos_old = """    function getNodePortPos(nodeId, portIndex) {
      const node = state.nodes.find(n => n.id === nodeId);
      if (!node) return { x: 0, y: 0 };
      const tpl = NODE_TEMPLATES[node.type];
      const scale = node.scale || 1;
      const port = (tpl.ports && tpl.ports[portIndex]) ? tpl.ports[portIndex] : { x: tpl.width / 2, y: tpl.height / 2 };
      return {
        x: node.x + port.x * scale,
        y: node.y + port.y * scale
      };
    }"""

port_pos_new = """    function getNodePortPos(nodeId, portIndex) {
      const node = state.nodes.find(n => n.id === nodeId);
      if (!node) return { x: 0, y: 0 };
      const tpl = NODE_TEMPLATES[node.type];
      const scaleX = node.scaleX || node.scale || 1;
      const scaleY = node.scaleY || node.scale || 1;
      const port = (tpl.ports && tpl.ports[portIndex]) ? tpl.ports[portIndex] : { x: tpl.width / 2, y: tpl.height / 2 };
      return {
        x: node.x + port.x * scaleX,
        y: node.y + port.y * scaleY
      };
    }"""

if port_pos_old in html:
    html = html.replace(port_pos_old, port_pos_new)


# 2. Update renderNodes (scaleX/Y and text dragging)
render_nodes_old = """        const g = document.createElementNS(SVG_NS, 'g');
        g.dataset.id = node.id;
        const scale = node.scale || 1;
        g.setAttribute('transform', `translate(${node.x}, ${node.y}) scale(${scale})`);
        g.className = 'cursor-move';

        // 渲染設備與標註
        g.innerHTML = tpl.render(node);

        // 選取高亮外框
        if (isSelected) {"""

render_nodes_new = """        const g = document.createElementNS(SVG_NS, 'g');
        g.dataset.id = node.id;
        const scaleX = node.scaleX || node.scale || 1;
        const scaleY = node.scaleY || node.scale || 1;
        g.setAttribute('transform', `translate(${node.x}, ${node.y}) scale(${scaleX}, ${scaleY})`);
        g.className = 'cursor-move';

        // 渲染設備與標註
        g.innerHTML = tpl.render(node);
        
        // 賦予節點內文字可拖曳的能力 (解決文字重疊問題)
        const textElements = g.querySelectorAll('text');
        textElements.forEach(t => {
          t.style.cursor = 'move';
          t.classList.add('select-none');
          if (node.textOffsetX || node.textOffsetY) {
            t.setAttribute('transform', `translate(${node.textOffsetX || 0}, ${node.textOffsetY || 0})`);
          }
          t.addEventListener('mousedown', (e) => {
            e.stopPropagation(); // 阻止觸發移動整個節點
            startDragNodeText(node.id, e);
          });
        });

        // 選取高亮外框
        if (isSelected) {"""

if render_nodes_old in html:
    html = html.replace(render_nodes_old, render_nodes_new)


# 3. Update startResizeNode
start_resize_old = """    function startResizeNode(nodeId, e) {
      const node = state.nodes.find(n => n.id === nodeId);
      if (!node) return;
      const tpl = NODE_TEMPLATES[node.type];
      
      const startX = e.clientX;
      const startScale = node.scale || 1;
      
      const onMouseMove = (moveEvent) => {
        const dx = (moveEvent.clientX - startX) / state.zoom;
        // 依照 X 軸位移比例計算縮放，提升操作直覺度
        const scaleChange = dx / (tpl.width || 100) * 1.5; 
        let newScale = startScale + scaleChange;
        newScale = Math.max(0.4, Math.min(newScale, 4.0)); // 限制縮放範圍 0.4x ~ 4.0x
        node.scale = Math.round(newScale * 10) / 10;
        
        // 同步更新右側屬性面板的滑桿
        if (state.selectedNodeId === node.id) {
          const scaleInput = document.getElementById('node-prop-scale');
          if (scaleInput) {
            scaleInput.value = node.scale;
            document.getElementById('node-scale-val').textContent = node.scale + 'x';
          }
        }
        renderAll();
      };
      
      const onMouseUp = () => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        saveHistory();
      };
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    }"""

start_resize_new = """    function startResizeNode(nodeId, e) {
      const node = state.nodes.find(n => n.id === nodeId);
      if (!node) return;
      const tpl = NODE_TEMPLATES[node.type];
      
      const startX = e.clientX;
      const startY = e.clientY;
      const startScaleX = node.scaleX || node.scale || 1;
      const startScaleY = node.scaleY || node.scale || 1;
      
      const onMouseMove = (moveEvent) => {
        const dx = (moveEvent.clientX - startX) / state.zoom;
        const dy = (moveEvent.clientY - startY) / state.zoom;
        
        let newScaleX = startScaleX + dx / (tpl.width || 100);
        let newScaleY = startScaleY + dy / (tpl.height || 100);
        
        node.scaleX = Math.max(0.2, Math.min(newScaleX, 5.0));
        node.scaleY = Math.max(0.2, Math.min(newScaleY, 5.0));
        
        renderAll();
      };
      
      const onMouseUp = () => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        saveHistory();
      };
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    }"""

if start_resize_old in html:
    html = html.replace(start_resize_old, start_resize_new)


# 4. Add startDragNodeText
drag_text_func = """    function startDragNodeText(nodeId, e) {
      const node = state.nodes.find(n => n.id === nodeId);
      if (!node) return;
      
      selectNode(nodeId);
      
      const startX = e.clientX;
      const startY = e.clientY;
      // 注意：文字是在節點內部被 scale 的，所以位移需反向除以 scale
      const scaleX = node.scaleX || node.scale || 1;
      const scaleY = node.scaleY || node.scale || 1;
      
      const initialOffsetX = node.textOffsetX || 0;
      const initialOffsetY = node.textOffsetY || 0;
      
      const onMouseMove = (moveEvent) => {
        const dx = (moveEvent.clientX - startX) / state.zoom / scaleX;
        const dy = (moveEvent.clientY - startY) / state.zoom / scaleY;
        node.textOffsetX = initialOffsetX + dx;
        node.textOffsetY = initialOffsetY + dy;
        renderNodes();
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

script_insert_target = """    function startDragNode(nodeId, e) {"""
if script_insert_target in html:
    html = html.replace(script_insert_target, drag_text_func + script_insert_target)


# 5. Fix slider to set both scaleX and scaleY uniformly (reset stretch)
slider_old = """    document.getElementById('node-prop-scale').addEventListener('input', (e) => {
      const node = state.nodes.find(n => n.id === state.selectedNodeId);
      if (node) {
        node.scale = parseFloat(e.target.value);
        document.getElementById('node-scale-val').textContent = node.scale + 'x';
        renderAll();
      }
    });"""

slider_new = """    document.getElementById('node-prop-scale').addEventListener('input', (e) => {
      const node = state.nodes.find(n => n.id === state.selectedNodeId);
      if (node) {
        const val = parseFloat(e.target.value);
        node.scale = val;
        node.scaleX = val; // 滑桿操作時會將拉伸比例重置為等比例
        node.scaleY = val;
        document.getElementById('node-scale-val').textContent = val + 'x';
        renderAll();
      }
    });"""

if slider_old in html:
    html = html.replace(slider_old, slider_new)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Update applied for node text dragging and non-uniform stretching.")
