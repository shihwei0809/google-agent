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

// 新增或覆蓋備份紀錄 (ON CONFLICT DO UPDATE)
export async function onRequestPost(context) {
  const { request, env } = context;
  try {
    const { archiveName, archiveId, payload } = await request.json();
    const finalId = String(archiveId || archiveName);
    
    // 產生台灣時區的 timestamp
    const now = new Date();
    const twTime = new Date(now.getTime() + 8 * 60 * 60 * 1000);
    const timestamp = twTime.toISOString().replace('T', ' ').substring(0, 19); 
    
    const dataJSON = JSON.stringify(payload);
    
    await env.DB.prepare("INSERT INTO ipa_archives (id, timestamp, data_json) VALUES (?1, ?2, ?3) ON CONFLICT(id) DO UPDATE SET timestamp=?2, data_json=?3")
      .bind(finalId, timestamp, dataJSON)
      .run();
      
    return new Response("SUCCESS");
  } catch (err) {
    return new Response("ERROR: " + err.toString(), { status: 500 });
  }
}

// 修改備份紀錄名稱 (Rename)
export async function onRequestPut(context) {
  const { request, env } = context;
  try {
    const { oldId, newId } = await request.json();
    await env.DB.prepare("UPDATE ipa_archives SET id = ?1 WHERE id = ?2")
      .bind(String(newId), String(oldId))
      .run();
    return new Response("SUCCESS");
  } catch (err) {
    return new Response("ERROR: " + err.toString(), { status: 500 });
  }
}

// 刪除備份紀錄
export async function onRequestDelete(context) {
  const { request, env } = context;
  try {
    const { archiveId } = await request.json();
    await env.DB.prepare("DELETE FROM ipa_archives WHERE id = ?1")
      .bind(String(archiveId))
      .run();
    return new Response("SUCCESS");
  } catch (err) {
    return new Response("ERROR: " + err.toString(), { status: 500 });
  }
}
