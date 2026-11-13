export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const path = url.pathname;
  const db = env.DB;

  const json = (data, status = 200) =>
    new Response(JSON.stringify(data), {
      status,
      headers: { "Content-Type": "application/json; charset=utf-8" }
    });

  const normalizeLots = (raw) => {
    const parts = (raw || "").split(/[,，、;\n\r]+/).map(s => s.trim()).filter(Boolean);
    return [...new Set(parts)].join("\n");
  };

  const hashPw = async (pw) => {
    const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`storage_pwa::${pw}`));
    return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
  };

  const ensureDefaultUsers = async () => {
    const cnt = await db.prepare("SELECT COUNT(*) AS c FROM users").first();
    if (!cnt || Number(cnt.c) === 0) {
      const h = await hashPw("1234");
      await db.prepare("INSERT OR IGNORE INTO users (username, display_name, password_hash, role, enabled) VALUES (?, ?, ?, ?, 1)").bind("admin", "管理員", h, "admin").run();
      await db.prepare("INSERT OR IGNORE INTO users (username, display_name, password_hash, role, enabled) VALUES (?, ?, ?, ?, 1)").bind("staff1", "現場人員1", h, "staff").run();
    }
  };

  if (path === "/api/login" && request.method === "POST") {
    await ensureDefaultUsers();
    const p = await request.json();
    const uname = (p.username || "").trim();
    const pwHash = await hashPw(p.password || "");
    const u = await db.prepare("SELECT username, display_name, password_hash, role, enabled FROM users WHERE username = ?").bind(uname).first();
    if (!u || u.password_hash !== pwHash) return json({ detail: "帳號或密碼錯誤" }, 401);
    if (!u.enabled) return json({ detail: "此帳號已被停用" }, 403);
    return json({ ok: true, user: { username: u.username, display_name: u.display_name, role: u.role } });
  }

  if (path === "/api/users") {
    await ensureDefaultUsers();
    if (request.method === "GET") {
      const rows = (await db.prepare("SELECT username, display_name, role, enabled FROM users ORDER BY role, username").all()).results || [];
      return json({ users: rows.map(u => ({ ...u, enabled: Boolean(u.enabled) })) });
    }
    if (request.method === "POST") {
      const p = await request.json();
      const uname = (p.username || "").trim();
      const existing = await db.prepare("SELECT username FROM users WHERE username = ?").bind(uname).first();
      if (existing) {
        if ((p.password || "").trim()) {
          const h = await hashPw(p.password.trim());
          await db.prepare("UPDATE users SET display_name=?, role=?, enabled=?, password_hash=? WHERE username=?")
            .bind(p.display_name.trim(), p.role || "staff", p.enabled !== false ? 1 : 0, h, uname).run();
        } else {
          await db.prepare("UPDATE users SET display_name=?, role=?, enabled=? WHERE username=?")
            .bind(p.display_name.trim(), p.role || "staff", p.enabled !== false ? 1 : 0, uname).run();
        }
      } else {
        if (!(p.password || "").trim()) return json({ detail: "新增帳號必須設定密碼" }, 400);
        const h = await hashPw(p.password.trim());
        await db.prepare("INSERT INTO users (username, display_name, password_hash, role, enabled) VALUES (?, ?, ?, ?, ?)")
          .bind(uname, p.display_name.trim(), h, p.role || "staff", p.enabled !== false ? 1 : 0).run();
      }
      return json({ ok: true, message: `已儲存帳號 ${uname}` });
    }
  }

  if (path.startsWith("/api/users/") && request.method === "DELETE") {
    const uname = decodeURIComponent(path.split("/")[3]);
    if (uname === "admin") return json({ detail: "不可刪除預設管理員帳號 admin" }, 400);
    await db.prepare("DELETE FROM users WHERE username = ?").bind(uname).run();
    return json({ ok: true });
  }

  if (path === "/api/network-info") {
    return json({ local_url: url.origin, lan_url: url.origin, ip: "Cloudflare D1", port: 443 });
  }

  if (path.startsWith("/api/warehouse/") && path.endsWith("/settings")) {
    const whId = path.split("/")[3];
    if (request.method === "GET") {
      const row = await db.prepare("SELECT items_json, packages_json FROM warehouse_settings WHERE wh_id = ?").bind(whId).first();
      if (row) {
        return json({
          wh_id: whId,
          items: JSON.parse(row.items_json || "[]"),
          packages: JSON.parse(row.packages_json || "[]")
        });
      }
      return json({ wh_id: whId, items: [], packages: ["200L", "20L", "GAL", "1M", "pallet"] });
    }
    if (request.method === "POST") {
      const p = await request.json();
      await db.prepare(
        `INSERT INTO warehouse_settings (wh_id, items_json, packages_json, updated_at)
         VALUES (?, ?, ?, datetime('now'))
         ON CONFLICT(wh_id) DO UPDATE SET
           items_json=excluded.items_json, packages_json=excluded.packages_json, updated_at=datetime('now')`
      ).bind(whId, JSON.stringify(p.items || []), JSON.stringify(p.packages || [])).run();
      return json({ ok: true, message: `已儲存 ${whId === "lunwei" ? "崙尾倉儲" : "鴻勝倉庫"} 的品名與包材設定` });
    }
  }

  if (path.startsWith("/api/warehouse/") && path.endsWith("/data")) {
    const whId = path.split("/")[3];
    const rows = await db.prepare("SELECT * FROM locations WHERE wh_id = ? ORDER BY location").bind(whId).all();
    const locs = (rows.results || []).map(l => ({
      ...l,
      occupied: Boolean(l.item_name || l.lot_no || Number(l.qty || 0) > 0)
    }));
    const zones = [...new Set(locs.map(l => l.zone).filter(Boolean))];
    const lots = [...new Set(locs.map(l => l.lot_no).filter(Boolean))];

    const cfgRow = await db.prepare("SELECT items_json, packages_json FROM warehouse_settings WHERE wh_id = ?").bind(whId).first();
    let catalog = [];
    let packages = ["200L", "20L", "GAL", "1M", "pallet"];
    if (cfgRow) {
      const allItems = JSON.parse(cfgRow.items_json || "[]");
      catalog = allItems.filter(it => it.enabled !== false);
      const pkgs = JSON.parse(cfgRow.packages_json || "[]");
      if (pkgs.length) packages = pkgs;
    }

    // 計算即時看板（只顯示架上有貨品名 + 依備註動態抓取異常品）
    const qtyByItem = {};
    const palletsByItem = {};
    const abnormalByKey = {};
    const abKeywords = ["HOLD", "異常", "不良", "後助", "侯住"];
    for (const l of locs) {
      const name = (l.item_name || "").trim();
      const note = (l.note || "").trim();
      const q = Number(l.qty || 0);
      if (name && (q > 0 || l.occupied)) {
        qtyByItem[name] = (qtyByItem[name] || 0) + q;
        palletsByItem[name] = (palletsByItem[name] || 0) + 1;
      }
      const nu = note.toUpperCase();
      const nmu = name.toUpperCase();
      if (abKeywords.some(k => nu.includes(k) || nmu.includes(k)) && (q > 0 || name)) {
        let lbl = name || "(未填品名)";
        if (note && !abKeywords.some(k => nmu.includes(k))) lbl = `${lbl} (${note})`;
        abnormalByKey[lbl] = (abnormalByKey[lbl] || 0) + q;
      }
    }

    const product_totals = Object.entries(qtyByItem)
      .filter(([, v]) => v > 0)
      .sort((a, b) => b[1] - a[1])
      .map(([k, v]) => ({ item_name: k, total_qty: v, pallets: palletsByItem[k] || 0 }));

    const abnormal_totals = Object.entries(abnormalByKey)
      .filter(([, v]) => v > 0)
      .sort((a, b) => b[1] - a[1])
      .map(([k, v]) => ({ item_name: k, total_qty: v }));

    let zone_empty = [];
    let total_empty_summary_count = 0;
    if (whId === "lunwei") {
      for (const [zi, zlbl] of [[1, "第一區空儲位\n1~4層"], [2, "第二區空儲位\n1~4層"], [3, "第三區空儲位\n1~4層"], [4, "第四區空儲位\n1~4層"]]) {
        const targets = new Set([1, 2, 3, 4].map(ly => `${zi}區${ly}層`));
        const zl = locs.filter(l => targets.has(l.zone));
        const ec = zl.filter(l => !l.occupied).length;
        total_empty_summary_count += ec;
        zone_empty.push({ label: `${zlbl}(${zl.length})`, empty_count: ec, total_count: zl.length });
      }
    } else {
      const zm = {};
      for (const l of locs) {
        const z = l.zone || "未分類";
        if (!zm[z]) zm[z] = { total: 0, empty: 0 };
        zm[z].total++;
        if (!l.occupied) zm[z].empty++;
      }
      zone_empty = Object.entries(zm).map(([z, c]) => ({ label: `${z} (${c.total})`, empty_count: c.empty, total_count: c.total }));
      total_empty_summary_count = Object.values(zm).reduce((s, c) => s + c.empty, 0);
    }

    return json({
      warehouse: { id: whId, name: whId === "lunwei" ? "崙尾倉儲" : "鴻勝倉庫" },
      zones,
      locations: locs,
      catalog,
      packages,
      existing_lots: lots,
      summary: {
        total_locations: locs.length,
        occupied_locations: locs.filter(l => l.occupied).length,
        empty_locations: locs.filter(l => !l.occupied).length,
        total_qty: locs.reduce((s, l) => s + Number(l.qty || 0), 0)
      },
      dashboard: {
        product_totals,
        zone_empty,
        total_empty_summary_label: whId === "lunwei" ? "崙尾倉貨架板數" : "鴻勝倉空儲位合計",
        total_empty_summary_count,
        abnormal_totals
      }
    });
  }

  if (path === "/api/record" && request.method === "POST") {
    const p = await request.json();
    const now = new Date();
    const logDate = now.toISOString().slice(0, 10);
    const logTime = now.toTimeString().slice(0, 8);
    const id = crypto.randomUUID().replace(/-/g, "").slice(0, 12);

    const existing = await db.prepare("SELECT * FROM locations WHERE wh_id = ? AND location = ?")
      .bind(p.wh_id, p.location).first();
    const beforeQty = existing ? Number(existing.qty || 0) : 0;
    const opQty = Number(p.qty || 0);
    const inLot = normalizeLots(p.lot_no || "");
    let afterQty = opQty;
    let nextLot = inLot || (existing?.lot_no || "");
    let nextName = (p.item_name || "").trim() || (existing?.item_name || "");
    let nextNo = (p.item_no || "").trim() || (existing?.item_no || "");
    let nextPkg = (p.package || "").trim() || (existing?.package || "");
    let nextNote = (p.note || "").trim() || (existing?.note || "");

    if (p.action === "in") {
      if (p.in_mode === "replace") {
        afterQty = opQty;
        nextLot = inLot;
        nextName = (p.item_name || "").trim();
        nextNo = (p.item_no || "").trim();
        nextPkg = (p.package || "").trim();
        nextNote = (p.note || "").trim();
      } else {
        afterQty = beforeQty + opQty;
        if (existing && (existing.item_name || existing.lot_no || beforeQty > 0)) {
          nextLot = normalizeLots(`${existing.lot_no || ""}\n${inLot}`);
        }
      }
    } else if (p.action === "out") {
      afterQty = Math.max(0, beforeQty - opQty);
    } else {
      afterQty = opQty;
      nextLot = inLot;
      nextName = (p.item_name || "").trim();
      nextNo = (p.item_no || "").trim();
      nextPkg = (p.package || "").trim();
      nextNote = (p.note || "").trim();
    }

    const clear = afterQty <= 0 && p.clear_on_zero !== false;
    await db.prepare(
      `INSERT INTO locations (wh_id, location, zone, item_no, item_name, lot_no, package, qty, note)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(wh_id, location) DO UPDATE SET
         item_no=excluded.item_no, item_name=excluded.item_name, lot_no=excluded.lot_no,
         package=excluded.package, qty=excluded.qty, note=excluded.note, updated_at=datetime('now')`
    ).bind(
      p.wh_id, p.location, existing?.zone || "",
      clear ? "" : nextNo, clear ? "" : nextName,
      clear ? "" : nextLot, clear ? "" : nextPkg,
      clear ? 0 : afterQty, clear ? "" : nextNote
    ).run();

    await db.prepare(
      `INSERT OR IGNORE INTO daily_logs
       (id, client_tx_id, log_date, log_time, wh_id, wh_name, zone, location, action, item_no, item_name, lot_no, package, before_qty, op_qty, after_qty, pallets, note, operator)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      id, p.client_tx_id || null, logDate, logTime, p.wh_id,
      p.wh_id === "lunwei" ? "崙尾倉儲" : "鴻勝倉庫",
      existing?.zone || "", p.location, p.action, nextNo, nextName,
      nextLot, nextPkg, beforeQty, opQty, afterQty, p.pallets ?? 1, nextNote, p.operator || "現場人員"
    ).run();

    return json({
      ok: true,
      message: `已同步雲端 D1 儲位 ${p.location}`,
      updated_location: {
        wh_id: p.wh_id,
        zone: existing?.zone || "",
        location: p.location,
        item_no: clear ? "" : nextNo,
        item_name: clear ? "" : nextName,
        lot_no: clear ? "" : nextLot,
        package: clear ? "" : nextPkg,
        qty: clear ? 0 : afterQty,
        note: clear ? "" : nextNote,
        occupied: !clear && Boolean(nextName || nextLot || afterQty > 0)
      }
    });
  }

  if (path.startsWith("/api/record/") && request.method === "DELETE") {
    const logId = path.split("/")[3];
    await db.prepare("DELETE FROM daily_logs WHERE id = ?").bind(logId).run();
    return json({ ok: true });
  }

  if (path === "/api/daily-stats") {
    const dt = url.searchParams.get("date") || new Date().toISOString().slice(0, 10);
    const rows = (await db.prepare("SELECT * FROM daily_logs WHERE log_date = ? ORDER BY log_time DESC").bind(dt).all()).results || [];
    let inP = 0, outP = 0, setP = 0, inQ = 0, outQ = 0;
    const bMap = new Map();
    for (const r of rows) {
      const key = `${r.lot_no}||${r.item_name}`;
      if (!bMap.has(key)) bMap.set(key, {
        lot_no: r.lot_no || "(無批號)", item_name: r.item_name || "(未填)",
        in_pallets: 0, in_qty: 0, in_count: 0,
        out_pallets: 0, out_qty: 0, out_count: 0,
        set_pallets: 0, record_count: 0
      });
      const b = bMap.get(key);
      b.record_count++;
      if (r.action === "in") { inP += r.pallets; inQ += r.op_qty; b.in_pallets += r.pallets; b.in_qty += r.op_qty; b.in_count++; }
      else if (r.action === "out") { outP += r.pallets; outQ += r.op_qty; b.out_pallets += r.pallets; b.out_qty += r.op_qty; b.out_count++; }
      else { setP += r.pallets; b.set_pallets += r.pallets; }
    }
    return json({
      date: dt,
      total_records: rows.length,
      total_pallets: inP + outP + setP,
      in_pallets: inP, out_pallets: outP, set_pallets: setP,
      in_qty: inQ, out_qty: outQ, net_qty: inQ - outQ,
      by_batch: [...bMap.values()],
      records: rows.map(r => ({ ...r, time: r.log_time, wh_name: r.wh_name }))
    });
  }

  return json({ error: "Not found" }, 404);
}
