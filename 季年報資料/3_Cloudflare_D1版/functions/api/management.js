export async function onRequestGet({ env }) {
  const { results } = await env.DB.prepare(
    'SELECT * FROM daily_management ORDER BY id DESC'
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
        `INSERT INTO daily_management (id, period, date, type, content, status)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)
         ON CONFLICT(id) DO UPDATE SET
           period = excluded.period, date = excluded.date,
           type = excluded.type, content = excluded.content, status = excluded.status`
      ).bind(
        Number(r.id) || baseId + idx,
        String(r.period || '未指定'),
        String(r.date || ''),
        String(r.type || '其他管理'),
        String(r.content || ''),
        String(r.status || '記錄中')
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
  await env.DB.prepare('DELETE FROM daily_management WHERE id = ?1').bind(id).run();
  return Response.json({ ok: true });
}
