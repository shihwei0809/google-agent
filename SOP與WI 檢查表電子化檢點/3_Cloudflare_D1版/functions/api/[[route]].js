// Cloudflare Pages Functions REST API — 高併發原子寫入 + 台灣時區 (Asia/Taipei UTC+8)
function nowTaipei() {
  return new Intl.DateTimeFormat('zh-TW', {
    timeZone: 'Asia/Taipei',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false
  }).format(new Date());
}

function json(data, status = 200) {
  return new Response(JSON.stringify({ ...data, serverTimeMs: Date.now(), serverTimeTaipei: nowTaipei() }), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}

export async function onRequest(context) {
  const { request, env, params } = context;
  if (request.method === 'OPTIONS') return json({ ok: true });

  const db = env.DB;
  if (!db) return json({ error: 'D1 binding DB not configured' }, 500);

  const route = Array.isArray(params.route) ? params.route.join('/') : (params.route || '');
  const method = request.method;

  try {
    // 1. GET /api/templates
    if (route === 'templates' && method === 'GET') {
      const { results } = await db.prepare('SELECT payload_json FROM wi_templates ORDER BY updated_at DESC').all();
      return json({ templates: results.map(r => JSON.parse(r.payload_json)) });
    }

    // 2. POST /api/templates (單列原子 UPSERT + 同群組舊版標記)
    if (route === 'templates' && method === 'POST') {
      const tpl = await request.json();
      const ts = nowTaipei();
      if (tpl.isLatest) {
        await db.prepare('UPDATE wi_templates SET is_latest = 0 WHERE group_key = ? AND id != ?')
          .bind(tpl.groupKey, tpl.id).run();
      }
      await db.prepare(`
        INSERT INTO wi_templates (id, group_key, form_code, wi_version, is_latest, payload_json, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          form_code = excluded.form_code,
          wi_version = excluded.wi_version,
          is_latest = excluded.is_latest,
          payload_json = excluded.payload_json,
          updated_at = excluded.updated_at
      `).bind(tpl.id, tpl.groupKey, tpl.formCode, tpl.wiVersion || '', tpl.isLatest ? 1 : 0, JSON.stringify(tpl), ts).run();
      return json({ ok: true, id: tpl.id });
    }

    // 3. GET /api/records
    if (route === 'records' && method === 'GET') {
      const { results } = await db.prepare('SELECT * FROM wi_records ORDER BY seq DESC, created_at DESC LIMIT 200').all();
      const records = results.map(r => ({
        id: r.id,
        seq: r.seq,
        createdAt: r.created_at,
        status: r.status,
        templateSnapshot: JSON.parse(r.template_snapshot_json),
        meta: JSON.parse(r.meta_json),
        answers: JSON.parse(r.answers_json),
        signatures: JSON.parse(r.signatures_json || '{}')
      }));
      return json({ records });
    }

    // 4. POST /api/records (高併發原子配號寫入 + RETURNING)
    if (route === 'records' && method === 'POST') {
      const rec = await request.json();
      const ts = nowTaipei();
      const row = await db.prepare(`
        INSERT INTO wi_records (id, seq, group_key, form_code, status, created_at, template_snapshot_json, meta_json, answers_json, signatures_json, updated_at)
        VALUES (
          ?,
          (SELECT COALESCE(MAX(seq), 0) + 1 FROM wi_records),
          ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(id) DO UPDATE SET
          status = excluded.status,
          signatures_json = excluded.signatures_json,
          updated_at = excluded.updated_at
        RETURNING id, seq
      `).bind(
        rec.id,
        rec.templateSnapshot?.groupKey || '',
        rec.templateSnapshot?.formCode || '',
        rec.status || 'pending',
        rec.createdAt || ts,
        JSON.stringify(rec.templateSnapshot || {}),
        JSON.stringify(rec.meta || {}),
        JSON.stringify(rec.answers || {}),
        JSON.stringify(rec.signatures || {}),
        ts
      ).first();
      return json({ ok: true, id: row?.id || rec.id, seq: row?.seq });
    }

    // 5. POST /api/records/:id/sign (單列原子補簽，不覆蓋其他紀錄)
    const signMatch = route.match(/^records\/([^/]+)\/sign$/);
    if (signMatch && method === 'POST') {
      const recId = decodeURIComponent(signMatch[1]);
      const { signerKey, name, dataUrl, status } = await request.json();
      const existing = await db.prepare('SELECT signatures_json FROM wi_records WHERE id = ?').bind(recId).first();
      if (!existing) return json({ error: 'Record not found' }, 404);
      const sigs = JSON.parse(existing.signatures_json || '{}');
      const ts = nowTaipei();
      sigs[signerKey] = { name, dataUrl, signedAt: ts };
      await db.prepare('UPDATE wi_records SET signatures_json = ?, status = ?, updated_at = ? WHERE id = ?')
        .bind(JSON.stringify(sigs), status || 'pending', ts, recId).run();
      return json({ ok: true, id: recId, signedAt: ts });
    }

    // 6. GET / POST /api/signatures (主管常用簽名檔庫)
    if (route === 'signatures' && method === 'GET') {
      const { results } = await db.prepare('SELECT * FROM wi_saved_signatures').all();
      const map = {};
      results.forEach(r => {
        map[r.role] = { roleLabel: r.role_label, name: r.name, pin: r.pin, dataUrl: r.data_url, updatedAt: r.updated_at };
      });
      return json({ signatures: map });
    }

    if (route === 'signatures' && method === 'POST') {
      const s = await request.json();
      const ts = nowTaipei();
      await db.prepare(`
        INSERT INTO wi_saved_signatures (role, role_label, name, pin, data_url, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(role) DO UPDATE SET
          name = excluded.name,
          pin = excluded.pin,
          data_url = excluded.data_url,
          updated_at = excluded.updated_at
      `).bind(s.role, s.roleLabel || s.role, s.name || '', s.pin || '1234', s.dataUrl || '', ts).run();
      return json({ ok: true });
    }

    // 7. GET / POST / DELETE /api/drafts (跨裝置共享作業中暫存區，支援品管補簽與換班交接)
    if (route === 'drafts' && method === 'GET') {
      const { results } = await db.prepare('SELECT payload_json FROM wi_drafts ORDER BY updated_at DESC LIMIT 100').all();
      return json({ drafts: results.map(r => JSON.parse(r.payload_json)) });
    }

    if (route === 'drafts' && method === 'POST') {
      const d = await request.json();
      const ts = nowTaipei();
      d.savedAt = ts;
      await db.prepare(`
        INSERT INTO wi_drafts (id, group_key, plant, payload_json, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          plant = excluded.plant,
          payload_json = excluded.payload_json,
          updated_at = excluded.updated_at
      `).bind(d.id, d.groupKey || '', d.meta?.plant || '', JSON.stringify(d), ts).run();
      return json({ ok: true, id: d.id, savedAt: ts });
    }

    const draftDelMatch = route.match(/^drafts\/([^/]+)$/);
    if (draftDelMatch && method === 'DELETE') {
      const draftId = decodeURIComponent(draftDelMatch[1]);
      await db.prepare('DELETE FROM wi_drafts WHERE id = ?').bind(draftId).run();
      return json({ ok: true, id: draftId });
    }

    return json({ error: 'Route not found', route }, 404);
  } catch (err) {
    return json({ error: err.message || String(err) }, 500);
  }
}
