/**
 * Cloudflare Pages Functions API for 鴻勝產銷動態計畫系統
 * Routes: /api/health, /api/plan, /api/logs, /api/archives, /api/archives/:id
 */

function jsonRes(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store, no-cache, must-revalidate',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}

async function ensureSchema(db) {
  await db.batch([
    db.prepare(`CREATE TABLE IF NOT EXISTS sp_plan_state (
      id TEXT PRIMARY KEY,
      plan_json TEXT NOT NULL,
      version INTEGER NOT NULL DEFAULT 1,
      updated_by TEXT DEFAULT '系統',
      updated_at TEXT NOT NULL
    )`),
    db.prepare(`CREATE TABLE IF NOT EXISTS sp_plan_archives (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      description TEXT DEFAULT '',
      plan_json TEXT NOT NULL,
      created_by TEXT DEFAULT '系統',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )`),
    db.prepare(`CREATE TABLE IF NOT EXISTS sp_change_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      action TEXT NOT NULL,
      actor TEXT NOT NULL,
      summary TEXT NOT NULL,
      created_at TEXT NOT NULL
    )`)
  ]);
}

export async function onRequest(context) {
  const { request, env } = context;
  if (request.method === 'OPTIONS') {
    return jsonRes({ ok: true }, 204);
  }

  const db = env.sales_planner_db || env.DB;
  if (!db) {
    return jsonRes({ ok: false, error: 'D1 binding sales_planner_db is missing' }, 500);
  }

  const url = new URL(request.url);
  const path = url.pathname.replace(/\/+$/, '');
  const method = request.method.toUpperCase();

  try {
    await ensureSchema(db);

    if (path === '/api/health' && method === 'GET') {
      const row = await db.prepare(`SELECT COUNT(*) AS cnt FROM sp_plan_archives`).first();
      return jsonRes({
        ok: true,
        mode: 'cloudflare-d1',
        db: 'sales-planner-db',
        archiveCount: row ? row.cnt : 0,
        timestamp: new Date().toISOString()
      });
    }

    if (path === '/api/plan' && method === 'GET') {
      const row = await db.prepare(`SELECT plan_json, version, updated_by, updated_at FROM sp_plan_state WHERE id = 'current'`).first();
      if (!row) {
        return jsonRes({ ok: true, exists: false, version: 0, updatedBy: null, updatedAt: null, plan: null });
      }
      return jsonRes({
        ok: true,
        exists: true,
        version: row.version,
        updatedBy: row.updated_by,
        updatedAt: row.updated_at,
        plan: JSON.parse(row.plan_json)
      });
    }

    if (path === '/api/plan' && method === 'POST') {
      const body = await request.json();
      const planObj = body && body.plan;
      if (!planObj || !Array.isArray(planObj.items)) {
        return jsonRes({ ok: false, error: 'Invalid plan payload' }, 400);
      }

      const clientVersion = Number(body.version || 0);
      const force = !!body.force;
      const updatedBy = String(body.updatedBy || '線上人員').slice(0, 50);
      const summary = String(body.summary || '更新產銷計畫').slice(0, 200);
      const nowIso = new Date().toISOString();

      const cur = await db.prepare(`SELECT plan_json, version, updated_by, updated_at FROM sp_plan_state WHERE id = 'current'`).first();
      if (cur && !force && clientVersion > 0 && cur.version > clientVersion) {
        return jsonRes({
          ok: false,
          error: 'conflict',
          message: `雲端版本 (v${cur.version} 由「${cur.updated_by}」更新) 較新於您的版本 (v${clientVersion})`,
          serverVersion: cur.version,
          serverUpdatedBy: cur.updated_by,
          serverUpdatedAt: cur.updated_at,
          serverPlan: JSON.parse(cur.plan_json)
        }, 409);
      }

      const nextVer = cur ? cur.version + 1 : 1;
      const serialized = JSON.stringify(planObj);
      await db.batch([
        db.prepare(`INSERT INTO sp_plan_state (id, plan_json, version, updated_by, updated_at)
          VALUES ('current', ?, ?, ?, ?)
          ON CONFLICT(id) DO UPDATE SET
            plan_json = excluded.plan_json,
            version = excluded.version,
            updated_by = excluded.updated_by,
            updated_at = excluded.updated_at`)
          .bind(serialized, nextVer, updatedBy, nowIso),
        db.prepare(`INSERT INTO sp_change_logs (action, actor, summary, created_at) VALUES (?, ?, ?, ?)`)
          .bind(force ? 'FORCE_SAVE' : 'SAVE', updatedBy, `${summary} (v${nextVer})`, nowIso),
        db.prepare(`DELETE FROM sp_change_logs WHERE id NOT IN (SELECT id FROM sp_change_logs ORDER BY id DESC LIMIT 200)`)
      ]);

      return jsonRes({
        ok: true,
        version: nextVer,
        updatedBy,
        updatedAt: nowIso
      });
    }

    if (path === '/api/logs' && method === 'GET') {
      const { results } = await db.prepare(
        `SELECT id, action, actor, summary, created_at FROM sp_change_logs ORDER BY id DESC LIMIT 40`
      ).all();
      return jsonRes({ ok: true, logs: results || [] });
    }

    if (path === '/api/archives' && method === 'GET') {
      const { results } = await db.prepare(
        `SELECT id, name, description, created_by, created_at, updated_at FROM sp_plan_archives ORDER BY updated_at DESC, id DESC`
      ).all();
      return jsonRes({ ok: true, archives: results || [] });
    }

    if (path === '/api/archives' && method === 'POST') {
      const body = await request.json();
      const planObj = body && body.plan;
      const name = String(body && body.name ? body.name : '').trim().slice(0, 100);
      if (!name || !planObj) {
        return jsonRes({ ok: false, error: 'Snapshot name and plan required' }, 400);
      }
      const desc = String(body.description || '').slice(0, 200);
      const actor = String(body.created_by || '線上人員').slice(0, 50);
      const nowIso = new Date().toISOString();
      const serialized = JSON.stringify(planObj);

      if (body.overwrite_id) {
        const owId = Number(body.overwrite_id);
        await db.batch([
          db.prepare(`UPDATE sp_plan_archives SET name = ?, description = ?, plan_json = ?, created_by = ?, updated_at = ? WHERE id = ?`)
            .bind(name, desc, serialized, actor, nowIso, owId),
          db.prepare(`INSERT INTO sp_change_logs (action, actor, summary, created_at) VALUES ('ARCHIVE_OVERWRITE', ?, ?, ?)`)
            .bind(actor, `覆蓋快照「${name}」`, nowIso)
        ]);
        return jsonRes({ ok: true, id: owId, updated_at: nowIso });
      }

      const res = await db.prepare(
        `INSERT INTO sp_plan_archives (name, description, plan_json, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)`
      ).bind(name, desc, serialized, actor, nowIso, nowIso).run();
      await db.prepare(`INSERT INTO sp_change_logs (action, actor, summary, created_at) VALUES ('ARCHIVE_SAVE', ?, ?, ?)`)
        .bind(actor, `建立快照「${name}」`, nowIso).run();

      return jsonRes({ ok: true, id: res.meta ? res.meta.last_row_id : null, created_at: nowIso });
    }

    const archiveMatch = path.match(/^\/api\/archives\/(\d+)$/);
    if (archiveMatch) {
      const archId = Number(archiveMatch[1]);
      if (method === 'GET') {
        const row = await db.prepare(`SELECT id, name, description, plan_json, created_by, created_at, updated_at FROM sp_plan_archives WHERE id = ?`).bind(archId).first();
        if (!row) return jsonRes({ ok: false, error: 'Archive not found' }, 404);
        return jsonRes({
          ok: true,
          archive: {
            id: row.id,
            name: row.name,
            description: row.description,
            created_by: row.created_by,
            created_at: row.created_at,
            updated_at: row.updated_at,
            plan: JSON.parse(row.plan_json)
          }
        });
      }
      if (method === 'PUT') {
        const body = await request.json();
        const newName = String(body.name || '').trim().slice(0, 100);
        const newDesc = String(body.description || '').slice(0, 200);
        if (!newName) return jsonRes({ ok: false, error: 'Name required' }, 400);
        const nowIso = new Date().toISOString();
        await db.prepare(`UPDATE sp_plan_archives SET name = ?, description = ?, updated_at = ? WHERE id = ?`)
          .bind(newName, newDesc, nowIso, archId).run();
        return jsonRes({ ok: true, id: archId, updated_at: nowIso });
      }
      if (method === 'DELETE') {
        let pwd = url.searchParams.get('password') || '';
        if (!pwd) {
          try {
            const b = await request.json();
            pwd = String((b && b.password) || '');
          } catch (_) {}
        }
        if (pwd !== '8888') {
          return jsonRes({ ok: false, error: '刪除密碼錯誤（預設 8888）' }, 403);
        }
        await db.prepare(`DELETE FROM sp_plan_archives WHERE id = ?`).bind(archId).run();
        return jsonRes({ ok: true, deletedId: archId });
      }
    }

    return jsonRes({ ok: false, error: 'Not found: ' + path }, 404);
  } catch (err) {
    return jsonRes({ ok: false, error: String(err && err.message ? err.message : err) }, 500);
  }
}
