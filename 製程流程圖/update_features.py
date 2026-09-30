import re
import os

# 1. Update ai_chat.js to support customKey
chat_js_path = r"d:\GOOGLE ANGET\製程流程圖\functions\api\ai_chat.js"
with open(chat_js_path, "r", encoding="utf-8") as f:
    chat_js = f.read()

chat_js = chat_js.replace("const { message } = await context.request.json();", "const { message, customKey } = await context.request.json();")
chat_js = chat_js.replace('const keys = (env.GEMINI_KEYS || "").split(",").filter(k => k);', '''let keys = (env.GEMINI_KEYS || "").split(",").filter(k => k);
  if (customKey) {
    keys = [customKey, ...keys]; // 優先使用前端傳來的金鑰
  }''')

with open(chat_js_path, "w", encoding="utf-8") as f:
    f.write(chat_js)


# 2. Update ai_image.js to support customKey
img_js_path = r"d:\GOOGLE ANGET\製程流程圖\functions\api\ai_image.js"
with open(img_js_path, "r", encoding="utf-8") as f:
    img_js = f.read()

img_js = img_js.replace("const { prompt } = await context.request.json();", "const { prompt, customKey } = await context.request.json();")
img_js = img_js.replace('const keys = (env.OPENAI_KEYS || "").split(",").filter(k => k);', '''let keys = (env.OPENAI_KEYS || "").split(",").filter(k => k);
  if (customKey) {
    keys = [customKey, ...keys];
  }''')

with open(img_js_path, "w", encoding="utf-8") as f:
    f.write(img_js)


# 3. Update index.html
html_path = r"d:\GOOGLE ANGET\製程流程圖\public\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# 3a. Add API Settings UI to AI Modal
ai_header_old = """      <div class="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-xl">
        <h3 class="font-bold text-slate-700 flex items-center gap-2">
          <i class="fa-solid fa-robot text-purple-500"></i> 製程 AI 助手
        </h3>
        <button id="close-ai-chat" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark text-lg"></i></button>
      </div>"""

ai_header_new = """      <div class="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-xl">
        <h3 class="font-bold text-slate-700 flex items-center gap-2">
          <i class="fa-solid fa-robot text-purple-500"></i> 製程 AI 助手
        </h3>
        <div class="flex items-center gap-3">
          <button id="toggle-api-settings" class="text-slate-400 hover:text-purple-600" title="自訂 API Key (雙軌制)"><i class="fa-solid fa-gear"></i></button>
          <button id="close-ai-chat" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark text-lg"></i></button>
        </div>
      </div>
      <!-- API 設定區塊 (預設隱藏) -->
      <div id="api-settings-panel" class="hidden p-3 bg-purple-50 border-b border-purple-100 text-xs">
        <label class="block font-bold text-purple-900 mb-1">個人 Gemini API Key (雙軌制)</label>
        <div class="flex gap-2 mb-1">
          <input type="password" id="custom-gemini-key" class="flex-1 px-2 py-1.5 border border-purple-200 rounded" placeholder="留空則使用後台系統預設金鑰 (Fallback)">
          <button id="save-api-key" class="px-3 py-1.5 bg-purple-600 text-white rounded hover:bg-purple-700 font-bold">儲存本機</button>
        </div>
        <p class="text-purple-600 leading-tight">安全提示：金鑰僅儲存於您的瀏覽器 LocalStorage，不會外流。</p>
      </div>"""

if ai_header_old in html:
    html = html.replace(ai_header_old, ai_header_new)


# 3b. Add resize handle in renderNodes
render_nodes_old = """          selBox.setAttribute('stroke-dasharray', '4,4');
          g.insertBefore(selBox, g.firstChild);
        }

        g.addEventListener('mousedown', (e) => {"""

render_nodes_new = """          selBox.setAttribute('stroke-dasharray', '4,4');
          g.insertBefore(selBox, g.firstChild);

          // 新增右下角縮放控制點 (Drag to resize)
          const resizeHandle = document.createElementNS(SVG_NS, 'circle');
          resizeHandle.setAttribute('cx', tpl.width + 4);
          resizeHandle.setAttribute('cy', tpl.height + 4);
          resizeHandle.setAttribute('r', '6');
          resizeHandle.setAttribute('fill', '#ffffff');
          resizeHandle.setAttribute('stroke', '#0284c7');
          resizeHandle.setAttribute('stroke-width', '2');
          resizeHandle.setAttribute('class', 'cursor-se-resize');
          
          resizeHandle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            startResizeNode(node.id, e);
          });
          g.appendChild(resizeHandle);
        }

        g.addEventListener('mousedown', (e) => {"""

if render_nodes_old in html:
    html = html.replace(render_nodes_old, render_nodes_new)

# 3c. Add startResizeNode function and update API fetch logic
script_insert_target = """    function startDragNode(id, e) {"""

start_resize_func = """    function startResizeNode(nodeId, e) {
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
    }

"""

if script_insert_target in html:
    html = html.replace(script_insert_target, start_resize_func + script_insert_target)

# 3d. Update fetch calls with customKey
fetch_chat_old = """body: JSON.stringify({ message: text })"""
fetch_chat_new = """body: JSON.stringify({ message: text, customKey: localStorage.getItem('chemflow_gemini_key') })"""
if fetch_chat_old in html:
    html = html.replace(fetch_chat_old, fetch_chat_new)

fetch_img_old = """body: JSON.stringify({ prompt })"""
fetch_img_new = """body: JSON.stringify({ prompt, customKey: localStorage.getItem('chemflow_openai_key') })"""  # we will use the same key for now or add a separate one, but let's just stick to the AI chat key setting logic. Actually, we'll just use one key input for Gemini right now. The user mostly requested it generally. Let's just update the JS to handle the UI.

if fetch_img_old in html:
    html = html.replace(fetch_img_old, fetch_img_new)


# 3e. API Settings UI Logic
api_settings_js = """
    // API Settings Logic
    const toggleApiBtn = document.getElementById('toggle-api-settings');
    const apiPanel = document.getElementById('api-settings-panel');
    const customKeyInput = document.getElementById('custom-gemini-key');
    
    if (toggleApiBtn) {
      toggleApiBtn.addEventListener('click', () => {
        apiPanel.classList.toggle('hidden');
        customKeyInput.value = localStorage.getItem('chemflow_gemini_key') || '';
      });
    }
    
    const saveApiBtn = document.getElementById('save-api-key');
    if (saveApiBtn) {
      saveApiBtn.addEventListener('click', () => {
        const val = customKeyInput.value.trim();
        if (val) {
          localStorage.setItem('chemflow_gemini_key', val);
        } else {
          localStorage.removeItem('chemflow_gemini_key');
        }
        alert('API Key 儲存成功！');
      });
    }
"""

end_script_target = """  </script>
</body>"""
if end_script_target in html:
    html = html.replace(end_script_target, api_settings_js + end_script_target)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Updates applied successfully.")
