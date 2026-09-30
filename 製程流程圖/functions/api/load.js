export async function onRequestGet(context) {
  const db = context.env.DB;
  const result = await db.prepare('SELECT json_data FROM flow_data WHERE id = ?').bind('default_save').first();
  if (result) {
    return new Response(result.json_data, {headers: {'Content-Type': 'application/json'}});
  }
  return new Response(JSON.stringify({nodes: [], wires: []}), {headers: {'Content-Type': 'application/json'}});
}