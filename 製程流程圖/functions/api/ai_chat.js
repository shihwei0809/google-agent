export async function onRequestPost(context) {
  const { message, customKey } = await context.request.json();
  const env = context.env;
  
  let keys = (env.GEMINI_KEYS || env.GEMINI_API_KEYS || "").split(",").filter(k => k);
  if (customKey) {
    keys = [customKey, ...keys];
  }
  if (keys.length === 0) return new Response(JSON.stringify({reply: "未設定 API Key"}), {status: 200});

  let reply = "所有金鑰皆已超限或失效";
  let lastError = null;
  let attempted = [];
  
  for (let key of keys) {
    // 1. Get available models dynamically to avoid guessing exact string names (like -latest, -001, etc.)
    let validModels = [];
    try {
      const listResp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${key}`);
      const listData = await listResp.json();
      if (listData.models) {
        // Filter models that support generateContent and contain "gemini" and "flash" or "pro"
        validModels = listData.models
          .filter(m => m.supportedGenerationMethods && m.supportedGenerationMethods.includes("generateContent"))
          .map(m => m.name.replace("models/", ""))
          .filter(name => name.includes("gemini"));
          
        // Sort them descending to prefer newest versions (e.g. 3.8 > 3.7 > 2.5 > 1.5)
        validModels.sort((a, b) => b.localeCompare(a));
      }
    } catch (e) {
      console.error("ListModels failed", e);
    }
    
    // If ListModels failed or returned empty, fallback to a predefined robust list
    if (validModels.length === 0) {
      validModels = [
        "gemini-3.8-flash", "gemini-3.8-flash-latest", "gemini-3.8-flash-001",
        "gemini-3.7-flash", "gemini-3.5-flash", 
        "gemini-2.5-flash", 
        "gemini-1.5-flash", "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest", "gemini-pro"
      ];
    }
    
    // 2. Try models in order
    for (let model of validModels) {
      // Prioritize flash/pro, skip embeddings or experimental weird ones if possible
      if (model.includes("embedding") || model.includes("vision") || model.includes("tts")) continue;
      
      attempted.push(model);
      try {
        let resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${key}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ contents: [{ parts: [{ text: `你是一位化工廠設備專家，請回答中文：${message}` }] }] })
        });
        
        let data = await resp.json();
        if (resp.ok && data.candidates) {
          reply = data.candidates[0].content.parts[0].text;
          return new Response(JSON.stringify({ reply }), {headers: {'Content-Type': 'application/json'}});
        } else {
          lastError = data.error?.message || "未知錯誤";
          // If the key is totally invalid, break to the next key.
          if (data.error?.code === 400 && data.error?.message.includes("API key not valid")) {
            break; 
          }
        }
      } catch (e) {
        lastError = e.message;
      }
    }
  }
  
  if (lastError) {
    reply = `❌ API 呼叫失敗！系統已動態抓取您的可用模型清單，並依序嘗試以下模型皆被拒絕：\n${attempted.slice(0, 10).join(' ➡️ ')}${attempted.length > 10 ? ' ...等' : ''}\n\n(最後一個錯誤訊息：${lastError})`;
  }
  
  return new Response(JSON.stringify({ reply }), {headers: {'Content-Type': 'application/json'}});
}
