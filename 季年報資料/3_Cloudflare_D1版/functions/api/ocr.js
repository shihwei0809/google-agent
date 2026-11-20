const GEMINI_MODELS = [
  'gemini-3.8-flash',
  'gemini-3.7-flash',
  'gemini-3.6-flash',
  'gemini-2.5-flash',
  'gemini-1.5-flash',
];

export async function onRequestPost({ request, env }) {
  const apiKey = env.GEMINI_API_KEY;
  if (!apiKey) {
    return Response.json(
      { error: 'Cloudflare Pages 尚未設定環境變數 GEMINI_API_KEY' },
      { status: 400 }
    );
  }
  const { images = [], prompt = '' } = await request.json();
  const imageParts = (Array.isArray(images) ? images : []).map((item) => {
    if (item && typeof item === 'object' && item.data) {
      return { inline_data: { mime_type: item.mime_type || 'image/jpeg', data: item.data } };
    }
    return { inline_data: { mime_type: 'image/jpeg', data: item } };
  });
  const parts = [{ text: prompt }, ...imageParts];

  let lastError = '所有模型皆無法回應';
  for (const model of GEMINI_MODELS) {
    try {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(apiKey)}`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contents: [{ parts }], generationConfig: { temperature: 0.1 } }),
      });
      if (!res.ok) {
        const errText = await res.text();
        lastError = `[${model}] HTTP ${res.status}: ${errText.slice(0, 200)}`;
        continue;
      }
      const data = await res.json();
      const raw = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
      const cleaned = raw.replace(/```json|```/g, '').trim();
      let jsonStr = cleaned;
      const startIdx = cleaned.indexOf('[');
      const endIdx = cleaned.lastIndexOf(']');
      if (startIdx !== -1 && endIdx > startIdx) {
        jsonStr = cleaned.slice(startIdx, endIdx + 1);
      }
      const records = JSON.parse(jsonStr);
      return Response.json({ ok: true, model, records });
    } catch (e) {
      lastError = `[${model}] ${e.message}`;
    }
  }
  return Response.json(
    { error: `Gemini Vision OCR 降級鏈耗盡：${lastError}` },
    { status: 502 }
  );
}
