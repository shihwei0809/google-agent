export async function onRequestGet({ env }) {
  return new Response(
    JSON.stringify({
      ok: true,
      mode: 'CLOUDFLARE_D1',
      hasDb: Boolean(env.DB),
      hasGeminiKey: Boolean(env.GEMINI_API_KEY),
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
}
