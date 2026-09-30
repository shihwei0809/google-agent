import re
import sys

def modify_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add manifest and sw registration
    head_addition = """
  <link rel="manifest" href="manifest.json">
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js');
      });
    }
  </script>
"""
    content = content.replace('</head>', head_addition + '</head>')

    # Add AI and Save Buttons to header
    header_addition = """
      <div class="h-5 w-px bg-slate-200 mx-1"></div>
      <button id="btn-cloud-save" class="px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 border border-slate-300 rounded flex items-center gap-1">
        <i class="fa-solid fa-cloud-arrow-up text-blue-500"></i> 雲端存檔
      </button>
      <button id="btn-cloud-load" class="px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 border border-slate-300 rounded flex items-center gap-1">
        <i class="fa-solid fa-cloud-arrow-down text-green-500"></i> 讀取雲端
      </button>
      <button id="btn-ai-chat" class="px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 border border-slate-300 rounded flex items-center gap-1">
        <i class="fa-solid fa-robot text-purple-500"></i> AI 助手
      </button>
      <button id="btn-ai-image" class="px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 border border-slate-300 rounded flex items-center gap-1">
        <i class="fa-solid fa-wand-magic-sparkles text-pink-500"></i> AI 建圖
      </button>
"""
    # Find the place to insert buttons (before the export buttons)
    content = content.replace('<!-- 匯入 / 匯出功能 -->', '<!-- 匯入 / 匯出功能 -->' + header_addition)

    # Add PWA Install Banner, AI Chat Modal, and AI Image Modal
    body_addition = """
  <!-- PWA 安裝橫幅 -->
  <div id="pwa-install-banner" class="hidden fixed top-0 left-0 w-full bg-indigo-600 text-white p-3 z-50 flex justify-between items-center shadow-md">
    <div class="flex items-center gap-2">
      <i class="fa-solid fa-mobile-screen-button text-xl"></i>
      <div>
        <div class="font-bold text-sm">安裝 ChemFlow Pro App</div>
        <div class="text-xs text-indigo-200">獲得全螢幕與離線體驗</div>
      </div>
    </div>
    <div class="flex gap-2">
      <button id="btn-pwa-install" class="px-4 py-1.5 bg-white text-indigo-700 font-bold text-sm rounded shadow hover:bg-indigo-50">立即安裝</button>
      <button id="btn-pwa-close" class="px-3 py-1.5 bg-indigo-700 text-indigo-100 font-bold text-sm rounded hover:bg-indigo-800">稍後</button>
    </div>
  </div>

  <!-- AI 助手 Modal -->
  <div id="ai-chat-modal" class="hidden fixed inset-0 bg-black/50 z-50 flex justify-center items-center backdrop-blur-sm">
    <div class="bg-white w-[500px] h-[600px] rounded-xl shadow-2xl flex flex-col border border-slate-200">
      <div class="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-xl">
        <h3 class="font-bold text-slate-700 flex items-center gap-2">
          <i class="fa-solid fa-robot text-purple-500"></i> 製程 AI 助手
        </h3>
        <button id="close-ai-chat" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark text-lg"></i></button>
      </div>
      <div id="ai-chat-messages" class="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50/50">
        <div class="bg-purple-50 text-purple-900 p-3 rounded-lg text-sm rounded-tl-none border border-purple-100 self-start w-fit max-w-[85%]">
          您好！我是 ChemFlow Pro AI 助手。您可以問我關於化工製程、設備參數或系統操作的問題。
        </div>
      </div>
      <div class="p-4 border-t border-slate-100 bg-white rounded-b-xl flex gap-2">
        <input type="text" id="ai-chat-input" class="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none text-sm" placeholder="輸入您的問題...">
        <button id="send-ai-chat" class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition flex items-center justify-center">
          <i class="fa-solid fa-paper-plane"></i>
        </button>
      </div>
    </div>
  </div>

  <!-- AI 建圖 Modal -->
  <div id="ai-image-modal" class="hidden fixed inset-0 bg-black/50 z-50 flex justify-center items-center backdrop-blur-sm">
    <div class="bg-white w-[600px] rounded-xl shadow-2xl flex flex-col border border-slate-200">
      <div class="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-xl">
        <h3 class="font-bold text-slate-700 flex items-center gap-2">
          <i class="fa-solid fa-wand-magic-sparkles text-pink-500"></i> AI 設備建圖
        </h3>
        <button id="close-ai-image" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark text-lg"></i></button>
      </div>
      <div class="p-4 space-y-4">
        <div>
          <label class="block font-bold text-slate-700 mb-1 text-sm">描述您想生成的化工設備或製程圖</label>
          <textarea id="ai-image-prompt" rows="3" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-pink-500 outline-none text-sm" placeholder="例如：一個具有未來科技感的高效能精餾塔..."></textarea>
        </div>
        <button id="generate-ai-image" class="w-full py-2.5 bg-pink-600 text-white rounded-lg hover:bg-pink-700 transition font-bold flex items-center justify-center gap-2">
          <i class="fa-solid fa-image"></i> 開始生成圖片
        </button>
        <div id="ai-image-result" class="min-h-[300px] bg-slate-100 rounded-lg border border-slate-200 flex items-center justify-center overflow-hidden relative">
          <span class="text-slate-400 text-sm">生成的圖片將顯示於此</span>
        </div>
      </div>
    </div>
  </div>

  <script>
    // 雲端存取 API
    document.getElementById('btn-cloud-save').addEventListener('click', async () => {
      const btn = document.getElementById('btn-cloud-save');
      const originalHtml = btn.innerHTML;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 儲存中...';
      try {
        const payload = { nodes: state.nodes, wires: state.wires };
        const res = await fetch('/api/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) alert('雲端存檔成功！');
        else alert('存檔失敗');
      } catch(e) {
        alert('連線錯誤');
      }
      btn.innerHTML = originalHtml;
    });

    document.getElementById('btn-cloud-load').addEventListener('click', async () => {
      const btn = document.getElementById('btn-cloud-load');
      const originalHtml = btn.innerHTML;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 讀取中...';
      try {
        const res = await fetch('/api/load');
        if (res.ok) {
          const data = await res.json();
          if (data && data.nodes) {
             state.nodes = data.nodes;
             state.wires = data.wires || [];
             saveHistory();
             renderAll();
             alert('雲端讀取成功！');
          }
        } else alert('讀取失敗');
      } catch(e) {
        alert('連線錯誤');
      }
      btn.innerHTML = originalHtml;
    });

    // AI Chat API
    const aiChatModal = document.getElementById('ai-chat-modal');
    document.getElementById('btn-ai-chat').addEventListener('click', () => aiChatModal.classList.remove('hidden'));
    document.getElementById('close-ai-chat').addEventListener('click', () => aiChatModal.classList.add('hidden'));
    
    document.getElementById('send-ai-chat').addEventListener('click', async () => {
      const input = document.getElementById('ai-chat-input');
      const text = input.value.trim();
      if (!text) return;
      
      const msgs = document.getElementById('ai-chat-messages');
      msgs.innerHTML += `<div class="bg-blue-500 text-white p-3 rounded-lg text-sm rounded-tr-none self-end w-fit max-w-[85%] ml-auto">${text}</div>`;
      input.value = '';
      msgs.scrollTop = msgs.scrollHeight;

      // Loading state
      const loadingId = 'loading-' + Date.now();
      msgs.innerHTML += `<div id="${loadingId}" class="bg-purple-50 text-purple-900 p-3 rounded-lg text-sm rounded-tl-none border border-purple-100 self-start w-fit max-w-[85%]"><i class="fa-solid fa-spinner fa-spin"></i> 思考中...</div>`;
      msgs.scrollTop = msgs.scrollHeight;

      try {
        const res = await fetch('/api/ai_chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        document.getElementById(loadingId).remove();
        msgs.innerHTML += `<div class="bg-purple-50 text-purple-900 p-3 rounded-lg text-sm rounded-tl-none border border-purple-100 self-start w-fit max-w-[85%]">${data.reply || '發生錯誤'}</div>`;
      } catch(e) {
        document.getElementById(loadingId).remove();
        msgs.innerHTML += `<div class="bg-red-50 text-red-900 p-3 rounded-lg text-sm rounded-tl-none border border-red-100 self-start w-fit max-w-[85%]">連線失敗</div>`;
      }
      msgs.scrollTop = msgs.scrollHeight;
    });

    // AI Image API
    const aiImageModal = document.getElementById('ai-image-modal');
    document.getElementById('btn-ai-image').addEventListener('click', () => aiImageModal.classList.remove('hidden'));
    document.getElementById('close-ai-image').addEventListener('click', () => aiImageModal.classList.add('hidden'));

    document.getElementById('generate-ai-image').addEventListener('click', async () => {
      const prompt = document.getElementById('ai-image-prompt').value.trim();
      if(!prompt) return;
      const resContainer = document.getElementById('ai-image-result');
      resContainer.innerHTML = '<div class="text-pink-600 flex flex-col items-center gap-2"><i class="fa-solid fa-wand-magic-sparkles fa-bounce text-3xl"></i><span>AI 正在為您生成圖片，請稍候...</span></div>';
      
      try {
        const res = await fetch('/api/ai_image', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt })
        });
        const data = await res.json();
        if(data.imageUrl) {
          resContainer.innerHTML = `<img src="${data.imageUrl}" class="w-full h-full object-contain">`;
        } else {
          resContainer.innerHTML = `<span class="text-red-500">生成失敗</span>`;
        }
      } catch(e) {
        resContainer.innerHTML = `<span class="text-red-500">連線錯誤</span>`;
      }
    });

    // PWA Install Logic
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      document.getElementById('pwa-install-banner').classList.remove('hidden');
    });
    
    document.getElementById('btn-pwa-close').addEventListener('click', () => {
      document.getElementById('pwa-install-banner').classList.add('hidden');
    });

    document.getElementById('btn-pwa-install').addEventListener('click', async () => {
      document.getElementById('pwa-install-banner').classList.add('hidden');
      if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        deferredPrompt = null;
      }
    });
  </script>
</body>"""
    content = content.replace('</body>', body_addition)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

modify_html(r'd:\GOOGLE ANGET\製程流程圖\public\index.html')
