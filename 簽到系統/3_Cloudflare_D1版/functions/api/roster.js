// Cloudflare Pages Function: /api/roster (管理後台名單讀取與核准)

export async function onRequestGet({ env }) {
  const { results } = await env.DB.prepare('SELECT * FROM roster ORDER BY seq DESC, emp_id ASC').all();
  return Response.json({ success: true, items: results });
}

export async function onRequestPatch({ request, env }) {
  const { empId, action } = await request.json();
  if (action === 'approve') {
    await env.DB.prepare("UPDATE roster SET verify_status = 'verified' WHERE emp_id = ?").bind(empId).run();
  } else if (action === 'undo') {
    await env.DB.prepare(`
      UPDATE roster SET checked_in = 0, arrived_dependents_json = '[]', extra_count = 0, total_arrived = 0, checkin_time = NULL, seq = NULL
      WHERE emp_id = ?
    `).bind(empId).run();
  }
  return Response.json({ success: true });
}
