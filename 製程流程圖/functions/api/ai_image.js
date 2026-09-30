export async function onRequestPost(context) {
  const { prompt, customKey } = await context.request.json();
  const env = context.env;
  let keys = (env.OPENAI_KEYS || "").split(",").filter(k => k);
  if (customKey) {
    keys = [customKey, ...keys];
  }
  if (keys.length === 0) return new Response(JSON.stringify({error: "未設定 API Key"}), {status: 200});

  let imageUrl = null;
  
  for (let key of keys) {
    try {
      const resp = await fetch("https://api.openai.com/v1/images/generations", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${key}`
        },
        body: JSON.stringify({
          model: "dall-e-3",
          prompt: `一個工業製程圖/設備：${prompt}。專業、清晰、工業風。`,
          n: 1,
          size: "1024x1024"
        })
      });
      
      if (resp.ok) {
        const data = await resp.json();
        imageUrl = data.data[0].url;
        break;
      }
    } catch (e) {
      // Fallback
    }
  }
  
  return new Response(JSON.stringify({ imageUrl }), {headers: {'Content-Type': 'application/json'}});
}