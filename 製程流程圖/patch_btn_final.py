import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r"(<span class=\"font-medium text-slate-700\">控制閥 \(Valve\)</span>\n\s*</button>\n\s*</div>\n\s*</div>)"

replacement = r"""<span class="font-medium text-slate-700">控制閥 (Valve)</span>
              </button>

              <!-- 自訂設備 -->
              <button class="add-node-btn p-2 rounded-lg border border-slate-200 hover:border-sky-500 hover:bg-sky-50/50 flex flex-col items-center gap-1 text-center transition col-span-2" data-type="custom_block">
                <div class="px-2 py-1 bg-purple-50 border border-purple-300 rounded text-[11px] font-bold text-purple-900"><i class="fa-solid fa-image mr-1"></i>通用設備</div>
                <span class="font-medium text-slate-700">自訂設備 (支援圖片)</span>
              </button>
            </div>
          </div>"""

content = re.sub(pattern, replacement, content)

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Button injected!")
