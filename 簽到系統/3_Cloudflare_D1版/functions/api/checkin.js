// Cloudflare Pages Function: /api/checkin
// 支援工號查詢 (GET ?empId=B0066) 與簽到提交 (POST)

function maskName(name) {
  const s = String(name || '').trim();
  if (s.length <= 1) return s;
  if (s.length === 2) return s[0] + '○';
  return s[0] + '○'.repeat(s.length - 2) + s[s.length - 1];
}

export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const raw = (url.searchParams.get('empId') || '').trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (!raw) return Response.json({ success: false, error: '請輸入員工編號' }, { status: 400 });

  const { results } = await env.DB.prepare('SELECT * FROM roster').all();
  let hit = results.find(r => r.emp_id.toUpperCase() === raw);

  if (!hit && /^\d+$/.test(raw)) {
    const qNum = raw.replace(/^0+/, '');
    const matches = results.filter(r => {
      const digits = r.emp_id.toUpperCase().replace(/^[A-Z]+/, '');
      return digits === raw || digits.replace(/^0+/, '') === qNum;
    });
    if (matches.length === 1) hit = matches[0];
    if (matches.length > 1) {
      return Response.json({ success: false, error: '簡碼對應多位同仁，請輸入完整工號' }, { status: 409 });
    }
  }

  if (!hit) return Response.json({ success: false, error: '查無此工號' }, { status: 404 });

  const deps = JSON.parse(hit.dependents_json || '[]').map(d => ({
    name: maskName(d.name),
    rawName: d.name,
    relation: d.relation || '眷屬'
  }));

  return Response.json({
    success: true,
    record: {
      id: hit.emp_id,
      dept: hit.dept,
      maskedName: maskName(hit.name),
      dependents: deps,
      checkedIn: Boolean(hit.checked_in),
      arrivedDependents: JSON.parse(hit.arrived_dependents_json || '[]'),
      extraCount: hit.extra_count || 0,
      totalArrived: hit.total_arrived || 0,
      checkinTime: hit.checkin_time,
      seq: hit.seq,
      verifyStatus: hit.verify_status,
      note: hit.note || ''
    }
  });
}

export async function onRequestPost({ request, env }) {
  const body = await request.json();
  const now = new Date().toISOString();

  if (body.manual) {
    const empId = (body.empId || `TEMP-${Date.now().toString().slice(-4)}`).toUpperCase();
    const depCount = Number(body.extraCount || 0);
    const maxRow = await env.DB.prepare('SELECT COALESCE(MAX(seq), 0) AS m FROM roster').first();
    const nextSeq = (maxRow?.m || 0) + 1;

    await env.DB.prepare(`
      INSERT INTO roster (emp_id, dept, name, checked_in, extra_count, total_arrived, checkin_time, seq, verify_status, note)
      VALUES (?, ?, ?, 1, ?, ?, ?, ?, 'pending', ?)
    `).bind(empId, body.dept, body.name, depCount, 1 + depCount, now, nextSeq, body.note || '[手動補簽]').run();

    return Response.json({ success: true, seq: nextSeq, checkinTime: now });
  }

  const empId = String(body.empId || '').toUpperCase();
  const existing = await env.DB.prepare('SELECT * FROM roster WHERE emp_id = ?').bind(empId).first();
  if (!existing) return Response.json({ success: false, error: '查無此工號' }, { status: 404 });

  const arrivedDeps = Array.isArray(body.arrivedDependents) ? body.arrivedDependents : [];
  const extraCount = Number(body.extraCount || 0);
  const totalArrived = 1 + arrivedDeps.length + extraCount;

  let seq = existing.seq;
  let checkinTime = existing.checkin_time;
  if (!existing.checked_in) {
    const maxRow = await env.DB.prepare('SELECT COALESCE(MAX(seq), 0) AS m FROM roster').first();
    seq = (maxRow?.m || 0) + 1;
    checkinTime = now;
  }

  await env.DB.prepare(`
    UPDATE roster
    SET checked_in = 1,
        arrived_dependents_json = ?,
        extra_count = ?,
        total_arrived = ?,
        checkin_time = ?,
        seq = ?,
        note = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE emp_id = ?
  `).bind(JSON.stringify(arrivedDeps), extraCount, totalArrived, checkinTime, seq, body.note || '', empId).run();

  return Response.json({ success: true, seq, checkinTime, totalArrived });
}
