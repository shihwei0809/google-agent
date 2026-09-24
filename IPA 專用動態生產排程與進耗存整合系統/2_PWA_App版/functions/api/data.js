// 讀取主資料
export async function onRequestGet(context) {
  const { env } = context;
  try {
    const { results } = await env.DB.prepare("SELECT * FROM ipa_data").all();
    const data = {};
    for (const row of results) {
      try {
        if (typeof row.value === 'string' && (row.value.startsWith('{') || row.value.startsWith('['))) {
          data[row.key] = JSON.parse(row.value);
        } else {
          data[row.key] = row.value;
        }
      } catch (e) {
        data[row.key] = row.value;
      }
    }
    return new Response(JSON.stringify(data), { headers: { 'Content-Type': 'application/json' } });
  } catch (err) {
    return new Response(JSON.stringify({ _error: err.toString() }), { status: 500 });
  }
}

// 儲存主資料
export async function onRequestPost(context) {
  const { request, env } = context;
  try {
    const payload = await request.json();
    const stmts = [];
    
    for (const key of Object.keys(payload)) {
      let value = payload[key];
      if (value === undefined || value === null) value = '';
      if (typeof value === 'number' && isNaN(value)) value = '';
      if (typeof value === 'object') value = JSON.stringify(value);

      stmts.push(
        env.DB.prepare("INSERT INTO ipa_data (key, value) VALUES (?1, ?2) ON CONFLICT(key) DO UPDATE SET value=?2")
          .bind(key, String(value))
      );
    }
    
    if (stmts.length > 0) {
      await env.DB.batch(stmts);
    }
    
    return new Response("SUCCESS");
  } catch (err) {
    return new Response("ERROR: " + err.toString(), { status: 500 });
  }
}
