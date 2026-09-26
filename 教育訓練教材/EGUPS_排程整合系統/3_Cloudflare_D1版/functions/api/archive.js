export async function onRequestPost(context) {
  const { request, env } = context;
  try {
    const { payload, archiveName } = await request.json();
    
    const d = new Date();
    // Format to yyyy/MM/dd HH:mm:ss in GMT+8 manually for simplicity, or just use ISO
    const timestamp = d.toISOString().replace('T', ' ').substring(0, 19);
    const dataJSON = JSON.stringify(payload);
    
    await env.DB.prepare('INSERT INTO ArchiveStore (id, timestamp, dataJSON) VALUES (?1, ?2, ?3)')
      .bind(String(archiveName), timestamp, dataJSON)
      .run();
    
    return new Response("SUCCESS", { status: 200 });
  } catch (err) {
    return new Response("ERROR: " + err.toString(), { status: 500 });
  }
}
