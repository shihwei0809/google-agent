export async function onRequestPost(context) {
  const { prompt, customKey } = await context.request.json();
  const env = context.env;
  let keys = (env.GEMINI_API_KEYS || env.OPENAI_KEYS || "").split(",").filter(k => k);
  if (customKey) {
    keys = [customKey, ...keys];
  }
  if (keys.length === 0) return new Response(JSON.stringify({error: "未設定 Gemini API Key"}), {status: 200});

  let imageUrl = null;
  let lastError = null;
  let attempted = [];
  
  for (let key of keys) {
    let validModels = [];
    try {
      const listResp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${key}`);
      const listData = await listResp.json();
      if (listData.models) {
        validModels = listData.models
          .filter(m => m.supportedGenerationMethods && (m.supportedGenerationMethods.includes("generateContent") || m.supportedGenerationMethods.includes("predict")))
          .map(m => m.name.replace("models/", ""))
          // Check for image, vision, or banana (new codename for Gemini Image models)
          .filter(name => name.includes("image") || name.includes("vision") || name.includes("banana") || name.includes("imagen"));
          
        validModels.sort((a, b) => b.localeCompare(a));
      }
    } catch (e) {}
    
    // Always append our robust fallback list just in case
    const hardcodedFallbacks = [
      "nano-banana-2",
      "nano-banana-pro",
      "nano-banana",
      "gemini-3.8-flash-image",
      "gemini-3.1-flash-image",
      "gemini-1.5-flash-image",
      "imagen-3.0-generate-001"
    ];
    
    for (let h of hardcodedFallbacks) {
      if (!validModels.includes(h)) validModels.push(h);
    }
    
    for (let model of validModels) {
      attempted.push(model);
      try {
        if (model.includes("imagen")) {
          let resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:predict?key=${key}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              instances: [{ prompt: `一個化工廠設備的設計圖：${prompt}。必須是白底無文字` }],
              parameters: { sampleCount: 1 }
            })
          });
          
          let data = await resp.json();
          if (resp.ok && data.predictions?.[0]?.bytesBase64) {
            const mime = data.predictions[0].mimeType || 'image/jpeg';
            imageUrl = `data:${mime};base64,${data.predictions[0].bytesBase64}`;
            return new Response(JSON.stringify({ imageUrl }), {headers: {'Content-Type': 'application/json'}});
          } else {
            lastError = data.error?.message || '生成失敗';
          }
        } else {
          // Standard generateContent for Nano Banana
          let resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${key}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              contents: [{ parts: [{ text: `一個化工廠設備的設計圖：${prompt}。必須是白底無文字` }] }]
            })
          });
          
          let data = await resp.json();
          if (resp.ok) {
            if (data.candidates?.[0]?.content?.parts?.[0]?.inlineData) {
              const inline = data.candidates[0].content.parts[0].inlineData;
              imageUrl = `data:${inline.mimeType};base64,${inline.data}`;
              return new Response(JSON.stringify({ imageUrl }), {headers: {'Content-Type': 'application/json'}});
            } else if (data.candidates?.[0]?.content?.parts?.[0]?.text) {
              // It returned text instead of an image! This means it's not an image model.
              lastError = "這個模型返回了純文字而不是圖片，請更換模型代號。";
            }
          } else {
            lastError = data.error?.message || '生成失敗';
          }
        }
      } catch (e) {
        lastError = e.message;
      }
    }
  }
  
  if (lastError) {
    return new Response(JSON.stringify({ error: `嘗試過 ${attempted.slice(0, 5).join(', ')} 皆失敗。\n最後錯誤：${lastError}` }), {headers: {'Content-Type': 'application/json'}});
  }
}
