import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

target_html = """          <div>
            <label class="block font-bold text-slate-700 mb-1 text-sm">描述您想生成的化工設備或製程圖</label>
            <textarea id="ai-image-prompt" rows="3" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-pink-500 outline-none text-sm" placeholder="例如：一個具有未來科技感的高效能精餾塔..."></textarea>
          </div>"""

injection_html = """          <div>
            <label class="block font-bold text-slate-700 mb-1 text-sm">描述您想生成的化工設備或製程圖</label>
            <textarea id="ai-image-prompt" rows="3" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-pink-500 outline-none text-sm" placeholder="例如：一個具有未來科技感的高效能精餾塔..."></textarea>
          </div>
          <div>
            <label class="block font-bold text-slate-700 mb-1 text-sm text-pink-600">OpenAI API Key (必填，您的金鑰僅儲存於本機)</label>
            <input type="password" id="ai-api-key" class="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-pink-500 outline-none text-xs" placeholder="sk-proj-..." />
          </div>"""

content = content.replace(target_html, injection_html)

target_js = """    document.getElementById('generate-ai-image').addEventListener('click', async () => {
      const prompt = document.getElementById('ai-image-prompt').value.trim();
      if(!prompt) return;"""

injection_js = """    const initKey = localStorage.getItem('chemflow_openai_key') || '';
    if(document.getElementById('ai-api-key')) document.getElementById('ai-api-key').value = initKey;

    document.getElementById('generate-ai-image').addEventListener('click', async () => {
      const prompt = document.getElementById('ai-image-prompt').value.trim();
      if(!prompt) return;
      const customKeyInput = document.getElementById('ai-api-key');
      const customKey = customKeyInput ? customKeyInput.value.trim() : '';
      if(customKey) localStorage.setItem('chemflow_openai_key', customKey);"""

content = content.replace(target_js, injection_js)

error_target = """        } else {
          resContainer.innerHTML = `<span class="text-red-500">生成失敗</span>`;
        }
      } catch(e) {"""

error_injection = """        } else {
          resContainer.innerHTML = `<span class="text-red-500 text-center px-4">生成失敗：<br/>${data.error || '請檢查您的 API Key 是否正確或額度是否足夠'}</span>`;
        }
      } catch(e) {"""

content = content.replace(error_target, error_injection)

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Injected API Key UI")
