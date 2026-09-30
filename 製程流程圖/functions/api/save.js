export async function onRequestPost(context) {
  const req = await context.request.json();
  const db = context.env.DB;
  const jsonData = JSON.stringify(req);
  await db.prepare('INSERT OR REPLACE INTO flow_data (id, json_data) VALUES (?, ?)').bind('default_save', jsonData).run();
  return new Response(JSON.stringify({success: true}), {headers: {'Content-Type': 'application/json'}});
}