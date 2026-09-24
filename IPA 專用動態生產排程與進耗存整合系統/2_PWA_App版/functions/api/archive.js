// 取得備份紀錄清單
export async function onRequestGet(context) {
  const { env } = context;
  try {
    const { results } = await env.DB.prepare("SELECT id, timestamp, data_json FROM ipa_archives ORDER BY timestamp DESC").all();
    const list = results.map(row => ({
      id: row.id,
      time: row.timestamp,
      dataStr: row.data_json
    }));
    return new Response(JSON.stringify(list), { headers: { 'Content-Type': 'application/json' } });
  } catch (err) {
    return new Response(JSON.stringify([]));
  }
}

// 新增備份紀錄
export async function onRequestPost(context) {
  const { request, env } = context;
  try {
    const { archiveName, payload } = await request.json();
    
    // 產生台灣時區的 timestamp
    const now = new Date();
    const twTime = new Date(now.getTime() + 8 * 60 * 60 * 1000);
    const timestamp = twTime.toISOString().replace('T', ' ').substring(0, 19); 
    
    const dataJSON = JSON.stringify(payload);
    
    await env.DB.prepare("INSERT INTO ipa_archives (id, timestamp, data_json) VALUES (?1, ?2, ?3)")
      .bind(String(archiveName), timestamp, dataJSON)
      .run();
      
    return new Response("SUCCESS");
  } catch (err) {
    return new Response("ERROR: " + err.toString(), { status: 500 });
  }
}
