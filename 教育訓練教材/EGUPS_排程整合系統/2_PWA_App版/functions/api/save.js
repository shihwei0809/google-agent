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
        env.DB.prepare('INSERT INTO DataStore (key, value) VALUES (?1, ?2) ON CONFLICT(key) DO UPDATE SET value = ?2')
          .bind(key, String(value))
      );
    }

    if (stmts.length > 0) {
      await env.DB.batch(stmts);
    }
    
    return new Response("SUCCESS", { status: 200 });
  } catch (err) {
    return new Response("ERROR: " + err.toString(), { status: 500 });
  }
}
