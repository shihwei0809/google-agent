export async function onRequestGet({ env }) {
  try {
    const { results } = await env.DB.prepare(
      'SELECT * FROM monthly_metrics ORDER BY ym ASC'
    ).all();
    const data = (results || []).map((r) => ({
      ym: r.ym,
      category: r.category,
      source: r.source,
      mt: r.mt,
      trips: r.trips,
      pallets: r.pallets,
      rows: r.rows_count,
      breakdown: JSON.parse(r.breakdown_json || '{}'),
    }));
    return Response.json({ ok: true, data });
  } catch (err) {
    return Response.json({ ok: false, error: err.message }, { status: 500 });
  }
}

export async function onRequestPost({ request, env }) {
  try {
    const body = await request.json();
    if (body.action === 'delete_many' && Array.isArray(body.keys)) {
      const stmts = body.keys.map((k) =>
        env.DB.prepare(
          'DELETE FROM monthly_metrics WHERE ym = ?1 AND category = ?2 AND source = ?3'
        ).bind(k.ym, k.category, k.source)
      );
      if (stmts.length) await env.DB.batch(stmts);
      return Response.json({ ok: true, deleted: stmts.length });
    }
    const records = body.records || [];
    const fname = body.filename || '';
    const stmts = records.map((r) => {
      const bd = { ...(r.breakdown || {}) };
      if (r.filename || fname) bd._filename = r.filename || fname;
      return env.DB.prepare(
        `INSERT INTO monthly_metrics (ym, category, source, mt, trips, pallets, rows_count, breakdown_json, updated_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, CURRENT_TIMESTAMP)
         ON CONFLICT(ym, category, source) DO UPDATE SET
           mt = excluded.mt,
           trips = excluded.trips,
           pallets = excluded.pallets,
           rows_count = excluded.rows_count,
           breakdown_json = excluded.breakdown_json,
           updated_at = CURRENT_TIMESTAMP`
      ).bind(
        r.ym,
        r.category,
        r.source || 'BI_EXCEL',
        r.mt ?? null,
        r.trips ?? null,
        r.pallets ?? null,
        r.rows ?? 0,
        JSON.stringify(bd)
      );
    });
    if (stmts.length) await env.DB.batch(stmts);
    return Response.json({ ok: true, saved: records.length });
  } catch (err) {
    return Response.json({ ok: false, error: err.message }, { status: 500 });
  }
}

export async function onRequestDelete({ request, env }) {
  try {
    const url = new URL(request.url);
    const ym = url.searchParams.get('ym');
    const category = url.searchParams.get('category');
    const source = url.searchParams.get('source');
    if (!ym || !category || !source) {
      return Response.json({ ok: false, error: '缺少 ym / category / source 參數' }, { status: 400 });
    }
    await env.DB.prepare(
      'DELETE FROM monthly_metrics WHERE ym = ?1 AND category = ?2 AND source = ?3'
    )
      .bind(ym, category, source)
      .run();
    return Response.json({ ok: true, deleted: 1 });
  } catch (err) {
    return Response.json({ ok: false, error: err.message }, { status: 500 });
  }
}
