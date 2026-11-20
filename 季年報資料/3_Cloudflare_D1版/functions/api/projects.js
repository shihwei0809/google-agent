export async function onRequestGet({ env }) {
  const { results } = await env.DB.prepare(
    'SELECT * FROM key_projects ORDER BY id ASC'
  ).all();
  return Response.json({ ok: true, data: results || [] });
}

export async function onRequestPost({ request, env }) {
  try {
    const body = await request.json();
    const list = Array.isArray(body.records) ? body.records : [body];
    const baseId = Date.now();
    const stmts = list.map((r, idx) =>
      env.DB.prepare(
        `INSERT INTO key_projects (id, title, desc, effect, eta, status)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)
         ON CONFLICT(id) DO UPDATE SET
           title = excluded.title, desc = excluded.desc,
           effect = excluded.effect, eta = excluded.eta, status = excluded.status`
      ).bind(
        Number(r.id) || baseId + idx,
        String(r.title || '未命名工作項目'),
        String(r.desc || ''),
        String(r.effect || ''),
        String(r.eta || ''),
        String(r.status || '進行中')
      )
    );
    if (stmts.length) await env.DB.batch(stmts);
    return Response.json({ ok: true, saved: stmts.length });
  } catch (err) {
    return Response.json({ ok: false, error: err.message }, { status: 500 });
  }
}

export async function onRequestDelete({ request, env }) {
  const url = new URL(request.url);
  const id = Number(url.searchParams.get('id'));
  await env.DB.prepare('DELETE FROM key_projects WHERE id = ?1').bind(id).run();
  return Response.json({ ok: true });
}
