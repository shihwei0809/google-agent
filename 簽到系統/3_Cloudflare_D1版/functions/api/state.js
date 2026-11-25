// Cloudflare Pages Function: /api/state
// 統一同步活動設定 (event_settings)、簽到名單 (roster)、滿意度問卷 (surveys) 至 Cloudflare D1

const JSON_HEADERS = {
  'Content-Type': 'application/json; charset=utf-8',
  'Cache-Control': 'no-store'
};

function formatTaiwanNow() {
  const parts = new Intl.DateTimeFormat('zh-TW', {
    timeZone: 'Asia/Taipei',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).formatToParts(new Date());
  const get = t => (parts.find(p => p.type === t) || {}).value || '00';
  return `${get('year')}/${get('month')}/${get('day')} ${get('hour')}:${get('minute')}:${get('second')}`;
}

function ok(data, status = 200) {
  return new Response(JSON.stringify({ success: true, serverTimeMs: Date.now(), ...data }), { status, headers: JSON_HEADERS });
}

function fail(error, status = 500) {
  return new Response(JSON.stringify({ success: false, error: String(error) }), { status, headers: JSON_HEADERS });
}

function rowToRosterItem(r) {
  let dependents = [];
  let arrivedDependents = [];
  try { dependents = JSON.parse(r.dependents_json || '[]'); } catch {}
  try { arrivedDependents = JSON.parse(r.arrived_dependents_json || '[]'); } catch {}
  return {
    id: r.emp_id,
    dept: r.dept,
    name: r.name,
    dependents,
    checkedIn: Boolean(r.checked_in),
    arrivedDependents,
    extraCount: Number(r.extra_count || 0),
    totalArrived: Number(r.total_arrived || 0),
    checkinTime: r.checkin_time || null,
    seq: r.seq != null ? Number(r.seq) : null,
    verifyStatus: r.verify_status || 'verified',
    note: r.note || ''
  };
}

function rowToSurveyItem(r) {
  let favorites = [];
  try { favorites = JSON.parse(r.favorites_json || '[]'); } catch {}
  return {
    id: r.id,
    empId: r.emp_id,
    name: r.name,
    dept: r.dept,
    overall: Number(r.overall || 5),
    venue: Number(r.venue || 5),
    activity: Number(r.activity || 5),
    service: Number(r.service || 5),
    favorites,
    comment: r.comment || '',
    submittedAt: r.submitted_at
  };
}

export async function onRequestGet({ env }) {
  try {
    if (!env.DB) return fail('D1 binding DB not configured', 500);

    const [settingsRow, rosterRes, surveyRes] = await Promise.all([
      env.DB.prepare("SELECT value FROM event_settings WHERE key = 'main'").first(),
      env.DB.prepare('SELECT * FROM roster ORDER BY COALESCE(seq, 999999) ASC, emp_id ASC').all(),
      env.DB.prepare('SELECT * FROM surveys ORDER BY id DESC').all()
    ]);

    let settings = null;
    if (settingsRow && settingsRow.value) {
      try { settings = JSON.parse(settingsRow.value); } catch {}
    }

    const roster = (rosterRes.results || []).map(rowToRosterItem);
    const surveys = (surveyRes.results || []).map(rowToSurveyItem);
    const initialized = Boolean(settingsRow) || roster.length > 0;

    return ok({ initialized, settings, roster, surveys });
  } catch (err) {
    return fail(err.message || err, 500);
  }
}

export async function onRequestPost({ request, env }) {
  try {
    if (!env.DB) return fail('D1 binding DB not configured', 500);
    const body = await request.json();
    const action = body.action;

    if (action === 'save_settings') {
      await env.DB.prepare(`
        INSERT INTO event_settings (key, value, updated_at)
        VALUES ('main', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
      `).bind(JSON.stringify(body.settings || {})).run();
      return ok({ action });
    }

    if (action === 'checkin') {
      const empId = String(body.empId || '').trim().toUpperCase();
      if (!empId) return fail('Missing empId', 400);
      const arrivedDeps = Array.isArray(body.arrivedDependents) ? body.arrivedDependents : [];
      const extraCount = Number(body.extraCount || 0);
      const totalArrived = 1 + arrivedDeps.length + extraCount;
      const checkinTime = String(body.checkinTime || formatTaiwanNow());
      const note = String(body.note || '');

      const updated = await env.DB.prepare(`
        UPDATE roster
        SET checked_in = 1,
            arrived_dependents_json = ?,
            extra_count = ?,
            total_arrived = ?,
            checkin_time = COALESCE(checkin_time, ?),
            seq = COALESCE(seq, (SELECT COALESCE(MAX(seq), 0) + 1 FROM roster)),
            note = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE UPPER(emp_id) = ?
        RETURNING emp_id, seq, checkin_time, total_arrived
      `).bind(
        JSON.stringify(arrivedDeps),
        extraCount,
        totalArrived,
        checkinTime,
        note,
        empId
      ).first();

      if (!updated) return fail(`Roster record not found: ${empId}`, 404);
      return ok({
        action,
        empId: updated.emp_id,
        seq: Number(updated.seq),
        checkinTime: updated.checkin_time,
        totalArrived: Number(updated.total_arrived)
      });
    }

    if (action === 'manual_checkin') {
      const empId = String(body.empId || `TEMP-${Date.now().toString().slice(-4)}`).trim().toUpperCase();
      const dept = String(body.dept || '');
      const name = String(body.name || '');
      const extraCount = Number(body.extraCount || 0);
      const totalArrived = 1 + extraCount;
      const checkinTime = String(body.checkinTime || formatTaiwanNow());
      const note = String(body.note || '[手動補簽]');

      const inserted = await env.DB.prepare(`
        INSERT INTO roster (
          emp_id, dept, name, dependents_json, checked_in,
          arrived_dependents_json, extra_count, total_arrived,
          checkin_time, seq, verify_status, note, updated_at
        ) VALUES (
          ?, ?, ?, '[]', 1, '[]', ?, ?, ?,
          (SELECT COALESCE(MAX(seq), 0) + 1 FROM roster),
          'pending', ?, CURRENT_TIMESTAMP
        )
        ON CONFLICT(emp_id) DO UPDATE SET
          dept = excluded.dept,
          name = excluded.name,
          checked_in = 1,
          extra_count = excluded.extra_count,
          total_arrived = excluded.total_arrived,
          checkin_time = COALESCE(roster.checkin_time, excluded.checkin_time),
          seq = COALESCE(roster.seq, (SELECT COALESCE(MAX(seq), 0) + 1 FROM roster)),
          verify_status = 'pending',
          note = excluded.note,
          updated_at = CURRENT_TIMESTAMP
        RETURNING emp_id, seq, checkin_time, total_arrived
      `).bind(empId, dept, name, extraCount, totalArrived, checkinTime, note).first();

      return ok({
        action,
        empId: inserted.emp_id,
        seq: Number(inserted.seq),
        checkinTime: inserted.checkin_time,
        totalArrived: Number(inserted.total_arrived)
      });
    }

    if (action === 'approve') {
      const empId = String(body.empId || '').trim().toUpperCase();
      if (!empId) return fail('Missing empId', 400);
      await env.DB.prepare(`
        UPDATE roster SET verify_status = 'verified', updated_at = CURRENT_TIMESTAMP
        WHERE UPPER(emp_id) = ?
      `).bind(empId).run();
      return ok({ action, empId });
    }

    if (action === 'undo_checkin') {
      const empId = String(body.empId || '').trim().toUpperCase();
      if (!empId) return fail('Missing empId', 400);
      await env.DB.prepare(`
        UPDATE roster
        SET checked_in = 0,
            arrived_dependents_json = '[]',
            extra_count = 0,
            total_arrived = 0,
            checkin_time = NULL,
            seq = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE UPPER(emp_id) = ?
      `).bind(empId).run();
      return ok({ action, empId });
    }

    if (action === 'sync_roster') {
      const list = Array.isArray(body.roster) ? body.roster : [];
      const stmts = [env.DB.prepare('DELETE FROM roster')];
      for (const item of list) {
        if (!item || !item.id) continue;
        stmts.push(
          env.DB.prepare(`
            INSERT INTO roster (
              emp_id, dept, name, dependents_json, checked_in,
              arrived_dependents_json, extra_count, total_arrived,
              checkin_time, seq, verify_status, note, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
          `).bind(
            String(item.id),
            String(item.dept || ''),
            String(item.name || ''),
            JSON.stringify(Array.isArray(item.dependents) ? item.dependents : []),
            item.checkedIn ? 1 : 0,
            JSON.stringify(Array.isArray(item.arrivedDependents) ? item.arrivedDependents : []),
            Number(item.extraCount || 0),
            Number(item.totalArrived || 0),
            item.checkinTime || null,
            item.seq != null ? Number(item.seq) : null,
            String(item.verifyStatus || 'verified'),
            String(item.note || '')
          )
        );
      }
      await env.DB.batch(stmts);
      return ok({ action, count: list.length });
    }

    if (action === 'submit_survey') {
      const s = body.survey || {};
      await env.DB.prepare(`
        INSERT INTO surveys (
          emp_id, name, dept, overall, venue, activity, service,
          favorites_json, comment, submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        String(s.empId || '匿名'),
        String(s.name || '匿名填答'),
        String(s.dept || '未指定'),
        Number(s.overall || 5),
        Number(s.venue || 5),
        Number(s.activity || 5),
        Number(s.service || 5),
        JSON.stringify(Array.isArray(s.favorites) ? s.favorites : []),
        String(s.comment || ''),
        String(s.submittedAt || formatTaiwanNow())
      ).run();
      return ok({ action });
    }

    if (action === 'seed_or_reset') {
      const stmts = [
        env.DB.prepare('DELETE FROM roster'),
        env.DB.prepare('DELETE FROM surveys'),
        env.DB.prepare(`
          INSERT INTO event_settings (key, value, updated_at)
          VALUES ('main', ?, CURRENT_TIMESTAMP)
          ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        `).bind(JSON.stringify(body.settings || {}))
      ];
      for (const item of (Array.isArray(body.roster) ? body.roster : [])) {
        if (!item || !item.id) continue;
        stmts.push(
          env.DB.prepare(`
            INSERT INTO roster (
              emp_id, dept, name, dependents_json, checked_in,
              arrived_dependents_json, extra_count, total_arrived,
              checkin_time, seq, verify_status, note, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
          `).bind(
            String(item.id),
            String(item.dept || ''),
            String(item.name || ''),
            JSON.stringify(Array.isArray(item.dependents) ? item.dependents : []),
            item.checkedIn ? 1 : 0,
            JSON.stringify(Array.isArray(item.arrivedDependents) ? item.arrivedDependents : []),
            Number(item.extraCount || 0),
            Number(item.totalArrived || 0),
            item.checkinTime || null,
            item.seq != null ? Number(item.seq) : null,
            String(item.verifyStatus || 'verified'),
            String(item.note || '')
          )
        );
      }
      for (const s of (Array.isArray(body.surveys) ? body.surveys : [])) {
        stmts.push(
          env.DB.prepare(`
            INSERT INTO surveys (
              emp_id, name, dept, overall, venue, activity, service,
              favorites_json, comment, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            String(s.empId || '匿名'),
            String(s.name || '匿名填答'),
            String(s.dept || '未指定'),
            Number(s.overall || 5),
            Number(s.venue || 5),
            Number(s.activity || 5),
            Number(s.service || 5),
            JSON.stringify(Array.isArray(s.favorites) ? s.favorites : []),
            String(s.comment || ''),
            String(s.submittedAt || formatTaiwanNow())
          )
        );
      }
      await env.DB.batch(stmts);
      return ok({ action });
    }

    return fail(`Unknown action: ${action}`, 400);
  } catch (err) {
    return fail(err.message || err, 500);
  }
}
