import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add to NODE_TEMPLATES
template_str = '''    const NODE_TEMPLATES = {
      custom_block: {
        width: 100, height: 100,
        title: '自訂設備',
        tag: 'EQ-001',
        bgColor: '#ffffff',
        ports: [
          { x: 50, y: 0, name: 'Top' },
          { x: 100, y: 50, name: 'Right' },
          { x: 50, y: 100, name: 'Bottom' },
          { x: 0, y: 50, name: 'Left' },
          { x: 25, y: 0, name: 'Top-L' },
          { x: 75, y: 0, name: 'Top-R' },
          { x: 100, y: 25, name: 'Right-T' },
          { x: 100, y: 75, name: 'Right-B' },
          { x: 0, y: 25, name: 'Left-T' },
          { x: 0, y: 75, name: 'Left-B' },
          { x: 25, y: 100, name: 'Bottom-L' },
          { x: 75, y: 100, name: 'Bottom-R' }
        ],
        render: (n) => {
          const bg = n.bgColor || '#ffffff';
          const img = n.imageUrl ? <image href=" + n.imageUrl + " x="5" y="5" width="90" height="90" preserveAspectRatio="xMidYMid meet" /> : '';
          const textY = n.imageUrl ? 115 : 55;
          return <g>
            <rect x="0" y="0" width="100" height="100" rx="8" fill=" + bg + " stroke="#1e293b" stroke-width="2.5" />
             + img + 
            <text x="50" y=" + textY + " font-size="12" font-weight="bold" fill="#1e293b" text-anchor="middle"> + n.title + </text>
            <text x="50" y=" + (textY + 16) + " font-size="10" fill="#64748b" text-anchor="middle"> + (n.tag || '') + </text>
          </g>;
        }
      },'''

content = content.replace('const NODE_TEMPLATES = {', template_str)

# 2. Add Button in Sidebar
btn_str = '''<!-- 自訂設備 -->
              <button class="add-node-btn p-2 rounded-lg border border-slate-200 hover:border-sky-500 hover:bg-sky-50/50 flex flex-col items-center gap-1 text-center transition col-span-2" data-type="custom_block">
                <i class="fa-solid fa-image text-2xl text-purple-500 mb-1"></i>
                <span class="font-medium text-slate-700">通用自訂設備 (支援上傳圖片)</span>
              </button>
            </div>
          </div>'''

content = re.sub(r'</div>\s*</div>\s*<!-- 標註、備註卡片與儀表 -->', btn_str + '\n\n          <!-- 標註、備註卡片與儀表 -->', content)

# 3. Add Property Panel HTML
prop_html = '''          <div>
            <label class="block font-bold text-slate-700 mb-1">設備尺寸縮放</label>
            <div class="flex items-center gap-2">
              <input type="range" id="node-prop-scale" min="0.6" max="2" step="0.1" value="1" class="w-full" />
              <span id="node-scale-val" class="font-mono text-slate-500">1.0x</span>
            </div>
          </div>

          <!-- 自訂設備專用屬性 -->
          <div id="prop-custom-block-fields" class="hidden space-y-4 pt-2 border-t border-slate-200">
            <div>
              <label class="block font-bold text-slate-700 mb-1">上傳專屬圖片/Icon (選填)</label>
              <input type="file" id="node-prop-image" accept="image/*" class="w-full text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-sky-50 file:text-sky-700 hover:file:bg-sky-100" />
              <p class="text-[10px] text-slate-500 mt-1">選取電腦中的圖片，作為此設備的外觀</p>
            </div>
            <div>
              <label class="block font-bold text-slate-700 mb-1">設備底色</label>
              <input type="color" id="node-prop-bgcolor" class="w-8 h-8 rounded border border-slate-300 cursor-pointer p-0.5" />
            </div>
          </div>'''

content = re.sub(r'<div>\s*<label class="block font-bold text-slate-700 mb-1">設備尺寸縮放</label>.*?</div>\s*</div>', prop_html, content, flags=re.DOTALL)

# 4. Add JS logic to show/hide and handle inputs
select_node_js = '''document.getElementById('node-prop-tag').value = node.tag || '';
        document.getElementById('node-prop-temp').value = node.temp || '';
        document.getElementById('node-prop-press').value = node.press || '';
        document.getElementById('node-prop-scale').value = node.scaleX || node.scale || 1;
        document.getElementById('node-scale-val').textContent = (node.scaleX || node.scale || 1) + 'x';
        
        const customFields = document.getElementById('prop-custom-block-fields');
        if (customFields) {
          if (node.type === 'custom_block') {
            customFields.classList.remove('hidden');
            document.getElementById('node-prop-bgcolor').value = node.bgColor || '#ffffff';
          } else {
            customFields.classList.add('hidden');
          }
        }'''

content = re.sub(r"document\.getElementById\('node-prop-tag'\)\.value = node\.tag \|\| '';\s*document\.getElementById\('node-prop-temp'\)\.value = node\.temp \|\| '';\s*document\.getElementById\('node-prop-press'\)\.value = node\.press \|\| '';\s*document\.getElementById\('node-prop-scale'\)\.value = node\.scale \|\| 1;\s*document\.getElementById\('node-scale-val'\)\.textContent = \(node\.scale \|\| 1\) \+ 'x';", select_node_js, content)

event_listeners = '''    document.getElementById('node-prop-scale').addEventListener('input', (e) => {
      const node = state.nodes.find(n => n.id === state.selectedNodeId);
      if (node) {
        const val = parseFloat(e.target.value);
        node.scale = val;
        node.scaleX = val;
        node.scaleY = val;
        document.getElementById('node-scale-val').textContent = val + 'x';
        renderAll();
      }
    });

    const customImgInput = document.getElementById('node-prop-image');
    if (customImgInput) {
      customImgInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (event) => {
          const node = state.nodes.find(n => n.id === state.selectedNodeId);
          if (node && node.type === 'custom_block') {
            node.imageUrl = event.target.result;
            renderNodes();
            saveHistory();
          }
        };
        reader.readAsDataURL(file);
      });
    }

    const customBgInput = document.getElementById('node-prop-bgcolor');
    if (customBgInput) {
      customBgInput.addEventListener('input', (e) => {
        const node = state.nodes.find(n => n.id === state.selectedNodeId);
        if (node && node.type === 'custom_block') {
          node.bgColor = e.target.value;
          renderNodes();
        }
      });
      customBgInput.addEventListener('change', saveHistory);
    }'''

content = re.sub(r"    document\.getElementById\('node-prop-scale'\)\.addEventListener\('input', \(e\) => \{.*?renderAll\(\);\s*\}\s*\}\);", event_listeners, content, flags=re.DOTALL)

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added custom block builder")
