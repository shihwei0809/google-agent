export async function onRequestPost(context) {
  const { message, customKey } = await context.request.json();
  const env = context.env;
  
  // Rule 7: Multi-key support & Fallback
  let keys = (env.GEMINI_KEYS || "").split(",").filter(k => k);
  if (customKey) {
    keys = [customKey, ...keys]; // 優先使用前端傳來的金鑰
  }
  if (keys.length === 0) return new Response(JSON.stringify({reply: "未設定 API Key"}), {status: 200});

  let reply = "所有金鑰皆已超限或失效";
  
  for (let key of keys) {
    try {
      const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key=${key}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contents: [{ parts: [{ text: `你是一位化工廠製程專家，請用繁體中文回答：${message}` }] }] })
      });
      
      if (resp.ok) {
        const data = await resp.json();
        reply = data.candidates[0].content.parts[0].text;
        break; // Success, break fallback loop
      }
    } catch (e) {
      console.error(e);
      // Fallback to next key
    }
  }
  
  return new Response(JSON.stringify({ reply }), {headers: {'Content-Type': 'application/json'}});
}