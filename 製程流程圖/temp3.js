
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
          body: JSON.stringify({ message: text, customKey: localStorage.getItem('chemflow_gemini_key') })
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
          body: JSON.stringify({ prompt, customKey: localStorage.getItem('chemflow_openai_key') })
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
  