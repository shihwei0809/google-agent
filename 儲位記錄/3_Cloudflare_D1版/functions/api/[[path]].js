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

  // 台灣時區 (UTC+8) 日期時間工具
  const getTaiwanNowParts = () => {
    const now = new Date();
    const fmt = new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Taipei",
      year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", second: "2-digit",
      hour12: false
    });
    const parts = Object.fromEntries(fmt.formatToParts(now).map(p => [p.type, p.value]));
    const hh = parts.hour === "24" ? "00" : parts.hour;
    return {
      date: `${parts.year}-${parts.month}-${parts.day}`,
      time: `${hh}:${parts.minute}:${parts.second}`,
      datetime: `${parts.year}-${parts.month}-${parts.day} ${hh}:${parts.minute}:${parts.second}`
    };
  };

  const validateYMD = (yy, mm, dd) => {
    if (yy < 2015 || yy > 2099 || mm < 1 || mm > 12 || dd < 1 || dd > 31) return null;
    const d = new Date(Date.UTC(yy, mm - 1, dd));
    if (d.getUTCFullYear() !== yy || d.getUTCMonth() !== mm - 1 || d.getUTCDate() !== dd) return null;
    return `${yy}-${String(mm).padStart(2, "0")}-${String(dd).padStart(2, "0")}`;
  };

  // 解析批號內含日期：規則 年月日，如 26b26 = 2026-11-26 (a=10, b=11, c=12)、25729M5001 = 2025-07-29
  const parseLotDate = (lotRaw) => {
    const s = String(lotRaw || "").trim();
    if (!s) return null;
    // 1) 5碼 YYMDD，月份為 a/b/c (10/11/12月)，如 26b26、26A05M01
    const mAlpha = s.match(/^(\d{2})([a-cA-C])(\d{2})/);
    if (mAlpha) {
      const mmMap = { a: 10, b: 11, c: 12 };
      const res = validateYMD(2000 + parseInt(mAlpha[1], 10), mmMap[mAlpha[2].toLowerCase()], parseInt(mAlpha[3], 10));
      if (res) return res;
    }
    // 2) 5碼 YYMDD，月份為 1~9 且第6碼非數字，如 25729M5001、26905
    const m5 = s.match(/^(\d{2})([1-9])(\d{2})(?!\d)/);
    if (m5) {
      const res = validateYMD(2000 + parseInt(m5[1], 10), parseInt(m5[2], 10), parseInt(m5[3], 10));
      if (res) return res;
    }
    // 3) 6碼 YYMMDD，如 261126、260915-01
    const m6 = s.match(/^(\d{2})(0[1-9]|1[0-2])(\d{2})(?!\d)/);
    if (m6) {
      const res = validateYMD(2000 + parseInt(m6[1], 10), parseInt(m6[2], 10), parseInt(m6[3], 10));
      if (res) return res;
    }
    // 4) 8碼 YYYYMMDD，如 20261126
    const m8 = s.match(/^(20\d{2})(0[1-9]|1[0-2])(\d{2})(?!\d)/);
    if (m8) {
      const res = validateYMD(parseInt(m8[1], 10), parseInt(m8[2], 10), parseInt(m8[3], 10));
      if (res) return res;
    }
    // 5) 5碼 YYMDD 後接數字流水號（最後嘗試）
    const m5Any = s.match(/^(\d{2})([1-9])(\d{2})/);
    if (m5Any) {
      const res = validateYMD(2000 + parseInt(m5Any[1], 10), parseInt(m5Any[2], 10), parseInt(m5Any[3], 10));
      if (res) return res;
    }
    return null;
  };

  const calcAgeDays = (dateStr, todayStr) => {
    if (!dateStr || !todayStr) return 0;
    const d1 = Date.parse(`${String(dateStr).slice(0, 10)}T00:00:00Z`);
    const d2 = Date.parse(`${String(todayStr).slice(0, 10)}T00:00:00Z`);
    if (Number.isNaN(d1) || Number.isNaN(d2)) return 0;
    return Math.max(0, Math.floor((d2 - d1) / 86400000));
  };

  const safeParseJson = (raw, fallback) => {
    try { return JSON.parse(raw || ""); } catch { return fallback; }
  };

  const enrichLocationAging = (loc, alertDays, todayStr) => {
    const occupied = Boolean(loc.item_name || loc.lot_no || Number(loc.qty || 0) > 0);
    const warnDays = Math.max(1, alertDays - 15);
    if (!occupied) {
      return {
        ...loc,
        occupied: false,
        lot_ages: [],
        max_age_days: 0,
        age_level: "empty",
        oldest_lot: "",
        oldest_date: ""
      };
    }
    const lotDatesMap = safeParseJson(loc.lot_dates_json, {});
    const lots = String(loc.lot_no || "").split(/[,，、;\n\r]+/).map(s => s.trim()).filter(Boolean);
    const targetLots = lots.length ? lots : ["(無批號)"];
    const fallbackDate = String(loc.updated_at || todayStr).slice(0, 10);

    const lot_ages = targetLots.map(lot => {
      const parsed = lot === "(無批號)" ? null : parseLotDate(lot);
      let placed_date = fallbackDate;
      let date_source = "updated_at";
      if (parsed) {
        placed_date = parsed;
        date_source = "lot";
      } else if (lotDatesMap && lotDatesMap[lot]) {
        placed_date = String(lotDatesMap[lot]).slice(0, 10);
        date_source = "recorded";
      }
      const days = calcAgeDays(placed_date, todayStr);
      const level = days >= alertDays ? "danger" : (days >= warnDays ? "warning" : "ok");
      return { lot_no: lot, placed_date, date_source, days, level };
    });

    lot_ages.sort((a, b) => b.days - a.days);
    const oldest = lot_ages[0];
    return {
      ...loc,
      occupied: true,
      lot_ages,
      max_age_days: oldest ? oldest.days : 0,
      age_level: oldest ? oldest.level : "ok",
      oldest_lot: oldest ? oldest.lot_no : "",
      oldest_date: oldest ? oldest.placed_date : ""
    };
  };

  const ensureAgingColumns = async () => {
    try {
      await db.prepare("ALTER TABLE locations ADD COLUMN lot_dates_json TEXT NOT NULL DEFAULT '{}'").run();
    } catch (_) {}
    try {
      await db.prepare("ALTER TABLE warehouse_settings ADD COLUMN alert_days INTEGER NOT NULL DEFAULT 60").run();
    } catch (_) {}
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

  if (path === "/api/users/import" && request.method === "POST") {
    await ensureDefaultUsers();
    const p = await request.json();
    const list = Array.isArray(p.users) ? p.users : [];
    if (!list.length) return json({ detail: "匯入帳號清單為空" }, 400);
    const existingRows = (await db.prepare("SELECT username FROM users").all()).results || [];
    const existingSet = new Set(existingRows.map(r => r.username));
    const stmts = [];
    let count = 0;
    for (const u of list) {
      const uname = String(u.username || "").trim();
      if (!uname) continue;
      const dn = String(u.display_name || uname).trim() || uname;
      const role = u.role === "admin" ? "admin" : "staff";
      const enabled = u.enabled !== false ? 1 : 0;
      const pw = String(u.password || "").trim();
      if (existingSet.has(uname)) {
        if (pw) {
          const h = await hashPw(pw);
          stmts.push(db.prepare("UPDATE users SET display_name=?, role=?, enabled=?, password_hash=? WHERE username=?").bind(dn, role, enabled, h, uname));
        } else {
          stmts.push(db.prepare("UPDATE users SET display_name=?, role=?, enabled=? WHERE username=?").bind(dn, role, enabled, uname));
        }
      } else {
        const h = await hashPw(pw || "1234");
        stmts.push(db.prepare("INSERT INTO users (username, display_name, password_hash, role, enabled) VALUES (?, ?, ?, ?, ?)").bind(uname, dn, h, role, enabled));
        existingSet.add(uname);
      }
      count++;
    }
    if (stmts.length) await db.batch(stmts);
    return json({ ok: true, count, message: `已匯入更新 ${count} 筆人員帳號` });
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

  const ensureDefaultWarehouses = async () => {
    const cnt = await db.prepare("SELECT COUNT(*) AS c FROM warehouses").first();
    if (!cnt || Number(cnt.c) === 0) {
      await db.prepare("INSERT OR IGNORE INTO warehouses (id, name, icon, sort_order) VALUES (?, ?, ?, ?)").bind("lunwei", "崙尾倉儲", "🏭", 1).run();
      await db.prepare("INSERT OR IGNORE INTO warehouses (id, name, icon, sort_order) VALUES (?, ?, ?, ?)").bind("hongsheng", "鴻勝倉庫", "🏢", 2).run();
    }
  };

  if (path === "/api/warehouses") {
    await ensureDefaultWarehouses();
    if (request.method === "GET") {
      const rows = (await db.prepare("SELECT id, name, icon, sort_order FROM warehouses ORDER BY sort_order, created_at").all()).results || [];
      return json({ warehouses: rows.map(w => ({ ...w, exists: true })) });
    }
    if (request.method === "POST") {
      const p = await request.json();
      const wid = (p.id || "").trim();
      const wname = (p.name || "").trim();
      if (!wid || !wname) return json({ detail: "請填寫倉庫代碼與名稱" }, 400);
      await db.prepare(
        `INSERT INTO warehouses (id, name, icon, sort_order) VALUES (?, ?, ?, 10)
         ON CONFLICT(id) DO UPDATE SET name=excluded.name, icon=excluded.icon`
      ).bind(wid, wname, p.icon || "🏬").run();
      const rows = (await db.prepare("SELECT id, name, icon, sort_order FROM warehouses ORDER BY sort_order, created_at").all()).results || [];
      return json({ ok: true, message: `已儲存倉庫 ${wname}`, warehouses: rows.map(w => ({ ...w, exists: true })) });
    }
  }

  if (path.startsWith("/api/warehouses/") && request.method === "DELETE") {
    const wid = decodeURIComponent(path.split("/")[3]);
    if (wid === "lunwei" || wid === "hongsheng") return json({ detail: "不可刪除預設倉庫" }, 400);
    await db.prepare("DELETE FROM warehouses WHERE id = ?").bind(wid).run();
    return json({ ok: true });
  }

  if (path.startsWith("/api/warehouse/") && path.endsWith("/settings")) {
    await ensureAgingColumns();
    const whId = path.split("/")[3];
    if (request.method === "GET") {
      const row = await db.prepare("SELECT items_json, packages_json, alert_days FROM warehouse_settings WHERE wh_id = ?").bind(whId).first();
      if (row) {
        const alertDays = Math.max(16, Math.min(3650, Number(row.alert_days || 60)));
        return json({
          wh_id: whId,
          items: JSON.parse(row.items_json || "[]"),
          packages: JSON.parse(row.packages_json || "[]"),
          alert_days: alertDays,
          warn_days: Math.max(1, alertDays - 15)
        });
      }
      return json({ wh_id: whId, items: [], packages: ["200L", "20L", "GAL", "1M", "pallet"], alert_days: 60, warn_days: 45 });
    }
    if (request.method === "POST") {
      const p = await request.json();
      const alertDays = Math.max(16, Math.min(3650, parseInt(p.alert_days, 10) || 60));
      await db.prepare(
        `INSERT INTO warehouse_settings (wh_id, items_json, packages_json, alert_days, updated_at)
         VALUES (?, ?, ?, ?, datetime('now'))
         ON CONFLICT(wh_id) DO UPDATE SET
           items_json=excluded.items_json, packages_json=excluded.packages_json, alert_days=excluded.alert_days, updated_at=datetime('now')`
      ).bind(whId, JSON.stringify(p.items || []), JSON.stringify(p.packages || []), alertDays).run();
      return json({ ok: true, alert_days: alertDays, warn_days: Math.max(1, alertDays - 15), message: `已儲存 ${whId === "lunwei" ? "崙尾倉儲" : "鴻勝倉庫"} 的品名、包材與久置警示設定` });
    }
  }

  if (path.startsWith("/api/warehouse/") && path.endsWith("/data")) {
    await ensureAgingColumns();
    const whId = path.split("/")[3];
    const twNow = getTaiwanNowParts();
    const cfgRow = await db.prepare("SELECT items_json, packages_json, alert_days FROM warehouse_settings WHERE wh_id = ?").bind(whId).first();
    const alertDays = Math.max(16, Math.min(3650, Number(cfgRow?.alert_days || 60)));
    const warnDays = Math.max(1, alertDays - 15);

    const rows = await db.prepare("SELECT * FROM locations WHERE wh_id = ? ORDER BY location").bind(whId).all();
    const natCmp = (a, b) => String(a || "").localeCompare(String(b || ""), "zh-Hant", { numeric: true });
    const locs = (rows.results || [])
      .map(l => enrichLocationAging(l, alertDays, twNow.date))
      .sort((a, b) => natCmp(a.location, b.location));
    const zones = [...new Set(locs.map(l => l.zone).filter(Boolean))].sort(natCmp);
    const lots = [...new Set(locs.map(l => l.lot_no).filter(Boolean))];

    let catalog = [];
    let packages = ["200L", "20L", "GAL", "1M", "pallet"];
    if (cfgRow) {
      const allItems = JSON.parse(cfgRow.items_json || "[]");
      catalog = allItems.filter(it => it.enabled !== false);
      const pkgs = JSON.parse(cfgRow.packages_json || "[]");
      if (pkgs.length) packages = pkgs;
    }

    // 計算即時看板（只顯示架上有貨品名，依 品名+包材 細分 + 依備註動態抓取異常品）
    const itemPkgMap = {};
    const pkgSummaryMap = {};
    const abnormalByKey = {};
    const abKeywords = ["HOLD", "異常", "不良", "後助", "侯住"];
    for (const l of locs) {
      const name = (l.item_name || "").trim();
      const pkg = (l.package || "").trim() || "(未指定)";
      const note = (l.note || "").trim();
      const q = Number(l.qty || 0);
      if (name && (q > 0 || l.occupied)) {
        const key = `${name}||${pkg}`;
        if (!itemPkgMap[key]) itemPkgMap[key] = { item_name: name, package: pkg, total_qty: 0, pallets: 0 };
        itemPkgMap[key].total_qty += q;
        itemPkgMap[key].pallets += 1;
      }
      if (q > 0 || l.occupied) {
        if (!pkgSummaryMap[pkg]) pkgSummaryMap[pkg] = { package: pkg, total_qty: 0, pallets: 0 };
        pkgSummaryMap[pkg].total_qty += q;
        pkgSummaryMap[pkg].pallets += 1;
      }
      const nu = note.toUpperCase();
      const nmu = name.toUpperCase();
      if (abKeywords.some(k => nu.includes(k) || nmu.includes(k)) && (q > 0 || name)) {
        let lbl = name || "(未填品名)";
        if (note && !abKeywords.some(k => nmu.includes(k))) lbl = `${lbl} (${note})`;
        abnormalByKey[lbl] = (abnormalByKey[lbl] || 0) + q;
      }
    }

    const product_totals = Object.values(itemPkgMap)
      .filter(v => v.total_qty > 0)
      .sort((a, b) => b.total_qty - a.total_qty);

    const package_totals = Object.values(pkgSummaryMap)
      .filter(v => v.total_qty > 0)
      .sort((a, b) => b.total_qty - a.total_qty);

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

    await ensureDefaultWarehouses();
    const whRow = await db.prepare("SELECT name FROM warehouses WHERE id = ?").bind(whId).first();
    const whName = whRow ? whRow.name : whId;
    const dangerCount = locs.filter(l => l.age_level === "danger").length;
    const warningCount = locs.filter(l => l.age_level === "warning").length;
    const okCount = locs.filter(l => l.age_level === "ok").length;
    return json({
      warehouse: { id: whId, name: whName },
      zones,
      locations: locs,
      catalog,
      packages,
      existing_lots: lots,
      alert_days: alertDays,
      warn_days: warnDays,
      server_date: twNow.date,
      aging_summary: {
        alert_days: alertDays,
        warn_days: warnDays,
        danger_count: dangerCount,
        warning_count: warningCount,
        ok_count: okCount
      },
      summary: {
        total_locations: locs.length,
        occupied_locations: locs.filter(l => l.occupied).length,
        empty_locations: locs.filter(l => !l.occupied).length,
        total_qty: locs.reduce((s, l) => s + Number(l.qty || 0), 0)
      },
      dashboard: {
        product_totals,
        package_totals,
        zone_empty,
        total_empty_summary_label: whId === "lunwei" ? "崙尾倉貨架板數" : "鴻勝倉空儲位合計",
        total_empty_summary_count,
        abnormal_totals
      }
    });
  }

  if (path === "/api/record" && request.method === "POST") {
    await ensureAgingColumns();
    const p = await request.json();
    const twNow = getTaiwanNowParts();
    const logDate = twNow.date;
    const logTime = twNow.time;
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
    const prevLotDates = safeParseJson(existing?.lot_dates_json, {});
    const prevFallback = existing?.updated_at ? String(existing.updated_at).slice(0, 10) : logDate;
    const nextLotDates = {};
    if (!clear) {
      const nextLotList = String(nextLot || "").split("\n").map(s => s.trim()).filter(Boolean);
      const isReplace = p.action === "in" && p.in_mode === "replace";
      const prevLotSet = new Set(String(existing?.lot_no || "").split("\n").map(s => s.trim()).filter(Boolean));
      for (const lot of nextLotList) {
        const parsed = parseLotDate(lot);
        if (parsed) {
          nextLotDates[lot] = parsed;
        } else if (!isReplace && prevLotDates[lot]) {
          nextLotDates[lot] = prevLotDates[lot];
        } else if (!isReplace && prevLotSet.has(lot)) {
          nextLotDates[lot] = prevFallback;
        } else {
          nextLotDates[lot] = logDate;
        }
      }
    }
    const nextLotDatesJson = JSON.stringify(nextLotDates);

    await db.prepare(
      `INSERT INTO locations (wh_id, location, zone, item_no, item_name, lot_no, package, qty, note, lot_dates_json, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(wh_id, location) DO UPDATE SET
         item_no=excluded.item_no, item_name=excluded.item_name, lot_no=excluded.lot_no,
         package=excluded.package, qty=excluded.qty, note=excluded.note,
         lot_dates_json=excluded.lot_dates_json, updated_at=excluded.updated_at`
    ).bind(
      p.wh_id, p.location, existing?.zone || "",
      clear ? "" : nextNo, clear ? "" : nextName,
      clear ? "" : nextLot, clear ? "" : nextPkg,
      clear ? 0 : afterQty, clear ? "" : nextNote,
      nextLotDatesJson, twNow.datetime
    ).run();

    await ensureDefaultWarehouses();
    const whRow = await db.prepare("SELECT name FROM warehouses WHERE id = ?").bind(p.wh_id).first();
    const whName = whRow ? whRow.name : p.wh_id;
    const cfgRow = await db.prepare("SELECT alert_days FROM warehouse_settings WHERE wh_id = ?").bind(p.wh_id).first();
    const alertDays = Math.max(16, Math.min(3650, Number(cfgRow?.alert_days || 60)));

    await db.prepare(
      `INSERT OR IGNORE INTO daily_logs
       (id, client_tx_id, log_date, log_time, wh_id, wh_name, zone, location, action, item_no, item_name, lot_no, package, before_qty, op_qty, after_qty, pallets, note, operator)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      id, p.client_tx_id || null, logDate, logTime, p.wh_id,
      whName,
      existing?.zone || "", p.location, p.action, nextNo, nextName,
      nextLot, nextPkg, beforeQty, opQty, afterQty, p.pallets ?? 1, nextNote, p.operator || "現場人員"
    ).run();

    const updatedLoc = enrichLocationAging({
      wh_id: p.wh_id,
      zone: existing?.zone || "",
      location: p.location,
      item_no: clear ? "" : nextNo,
      item_name: clear ? "" : nextName,
      lot_no: clear ? "" : nextLot,
      package: clear ? "" : nextPkg,
      qty: clear ? 0 : afterQty,
      note: clear ? "" : nextNote,
      lot_dates_json: nextLotDatesJson,
      updated_at: twNow.datetime
    }, alertDays, logDate);

    return json({
      ok: true,
      message: `已同步雲端 D1 儲位 ${p.location}`,
      updated_location: updatedLoc
    });
  }

  if (path.startsWith("/api/record/") && request.method === "DELETE") {
    const logId = path.split("/")[3];
    await db.prepare("DELETE FROM daily_logs WHERE id = ?").bind(logId).run();
    return json({ ok: true });
  }

  if (path === "/api/daily-stats") {
    const dt = url.searchParams.get("date") || getTaiwanNowParts().date;
    const whId = (url.searchParams.get("wh_id") || "").trim();
    const rows = (whId && whId !== "ALL"
      ? await db.prepare("SELECT * FROM daily_logs WHERE log_date = ? AND wh_id = ? ORDER BY log_time DESC").bind(dt, whId).all()
      : await db.prepare("SELECT * FROM daily_logs WHERE log_date = ? ORDER BY log_time DESC").bind(dt).all()
    ).results || [];
    let inP = 0, outP = 0, setP = 0, inQ = 0, outQ = 0;
    const bMap = new Map();
    const pkgMap = new Map();
    for (const r of rows) {
      const pkg = (r.package || "").trim() || "(未指定)";
      const key = `${r.lot_no}||${r.item_name}||${pkg}`;
      if (!bMap.has(key)) bMap.set(key, {
        lot_no: r.lot_no || "(無批號)", item_name: r.item_name || "(未填)", package: pkg,
        in_pallets: 0, in_qty: 0, in_count: 0,
        out_pallets: 0, out_qty: 0, out_count: 0,
        set_pallets: 0, record_count: 0
      });
      if (!pkgMap.has(pkg)) pkgMap.set(pkg, {
        package: pkg, in_qty: 0, out_qty: 0, net_qty: 0, in_pallets: 0, out_pallets: 0
      });
      const b = bMap.get(key);
      const pm = pkgMap.get(pkg);
      b.record_count++;
      if (r.action === "in") {
        inP += r.pallets; inQ += r.op_qty;
        b.in_pallets += r.pallets; b.in_qty += r.op_qty; b.in_count++;
        pm.in_pallets += r.pallets; pm.in_qty += r.op_qty; pm.net_qty += r.op_qty;
      } else if (r.action === "out") {
        outP += r.pallets; outQ += r.op_qty;
        b.out_pallets += r.pallets; b.out_qty += r.op_qty; b.out_count++;
        pm.out_pallets += r.pallets; pm.out_qty += r.op_qty; pm.net_qty -= r.op_qty;
      } else {
        setP += r.pallets; b.set_pallets += r.pallets;
      }
    }
    const by_package = [...pkgMap.values()].sort((a, b) => (b.in_qty + b.out_qty) - (a.in_qty + a.out_qty));
    return json({
      date: dt,
      wh_id: whId || "ALL",
      total_records: rows.length,
      total_pallets: inP + outP + setP,
      in_pallets: inP, out_pallets: outP, set_pallets: setP,
      in_qty: inQ, out_qty: outQ, net_qty: inQ - outQ,
      by_package,
      by_batch: [...bMap.values()],
      records: rows.map(r => ({ ...r, time: r.log_time, wh_name: r.wh_name }))
    });
  }

  if (path === "/api/daily-export") {
    const dt = url.searchParams.get("date") || getTaiwanNowParts().date;
    const whId = (url.searchParams.get("wh_id") || "").trim();
    const rows = (whId && whId !== "ALL"
      ? await db.prepare("SELECT * FROM daily_logs WHERE log_date = ? AND wh_id = ? ORDER BY log_time DESC").bind(dt, whId).all()
      : await db.prepare("SELECT * FROM daily_logs WHERE log_date = ? ORDER BY log_time DESC").bind(dt).all()
    ).results || [];
    let whLabel = "全部倉庫";
    if (whId && whId !== "ALL") {
      const whRow = await db.prepare("SELECT name FROM warehouses WHERE id = ?").bind(whId).first();
      whLabel = whRow ? whRow.name : whId;
    }
    const actMap = { in: "入庫", out: "出庫", set: "盤點覆寫" };
    const esc = (v) => {
      const s = String(v ?? "");
      return /[,"\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    };
    const headers = ["日期", "時間", "倉庫", "區域", "儲位", "動作", "品號", "品名", "批號", "包材", "異動前數量", "異動數量", "異動後數量", "板數", "備註", "操作人員"];
    const lines = [headers.join(",")].concat(rows.map(r => [
      r.log_date, r.log_time, r.wh_name, r.zone, r.location, actMap[r.action] || r.action,
      r.item_no, r.item_name, r.lot_no, r.package, r.before_qty, r.op_qty, r.after_qty,
      r.pallets, r.note, r.operator
    ].map(esc).join(",")));
    const filename = encodeURIComponent(`${whLabel}_每日作業明細_${dt}.csv`);
    return new Response("\uFEFF" + lines.join("\r\n"), {
      status: 200,
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": `attachment; filename="${filename}"; filename*=UTF-8''${filename}`,
        "Cache-Control": "no-cache, no-store"
      }
    });
  }

  if (path.startsWith("/api/warehouse/") && path.endsWith("/import") && request.method === "POST") {
    await ensureAgingColumns();
    const whId = path.split("/")[3];
    const body = await request.json();
    const rows = body.rows || [];
    if (!Array.isArray(rows) || rows.length === 0) {
      return json({ error: "未接收到任何儲位資料" }, 400);
    }

    const twNow = getTaiwanNowParts();
    const updatedTime = twNow.datetime;
    const todayDate = twNow.date;

    // 分批寫入 D1 (每批 80 筆，避開 D1 batch statement 數量上限)
    const chunkSize = 80;
    for (let i = 0; i < rows.length; i += chunkSize) {
      const chunk = rows.slice(i, i + chunkSize);
      const stmts = chunk.map(r => {
        const loc = String(r.location || "").trim();
        const zone = String(r.zone || "").trim();
        const itemNo = String(r.item_no || "").trim();
        const itemName = String(r.item_name || "").trim();
        const lotNo = normalizeLots(String(r.lot_no || "").trim());
        const pkg = String(r.package || "").trim();
        const qty = Number(r.qty || 0);
        const note = String(r.note || "").trim();
        const lotDates = {};
        if (lotNo) {
          for (const lt of lotNo.split("\n").filter(Boolean)) {
            const pd = parseLotDate(lt);
            if (pd) lotDates[lt] = pd;
          }
        }
        const lotDatesJson = JSON.stringify(lotDates);

        return db.prepare(`
          INSERT INTO locations (wh_id, location, zone, item_no, item_name, lot_no, package, qty, note, lot_dates_json, updated_at)
          VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)
          ON CONFLICT(wh_id, location) DO UPDATE SET
            zone = excluded.zone,
            item_no = excluded.item_no,
            item_name = excluded.item_name,
            lot_no = excluded.lot_no,
            package = excluded.package,
            qty = excluded.qty,
            note = excluded.note,
            lot_dates_json = excluded.lot_dates_json,
            updated_at = excluded.updated_at
        `).bind(whId, loc, zone, itemNo, itemName, lotNo, pkg, qty, note, lotDatesJson, updatedTime);
      });
      await db.batch(stmts);
    }

    return json({ ok: true, count: rows.length, message: `成功匯入更新 ${rows.length} 筆儲位資料！` });
  }

  if (path.startsWith("/api/warehouse/") && path.endsWith("/download")) {
    const whId = path.split("/")[3];
    const isCsv = url.searchParams.get("format") === "csv";

    // 預設下載完整版 .xlsm（包含 40~26 個各區各層儲位平面圖分頁與公式連動）
    if (!isCsv) {
      const fileName = whId === "lunwei" ? "崙尾倉儲儲位表_儲位專用.xlsm" : "鴻勝儲位表_儲位專用.xlsm";
      return Response.redirect(`${url.origin}/downloads/${encodeURIComponent(fileName)}`, 302);
    }

    const whInfo = await db.prepare("SELECT name FROM warehouses WHERE id = ?").bind(whId).first();
    const whName = whInfo ? whInfo.name : whId;
    const rows = (await db.prepare("SELECT * FROM locations WHERE wh_id = ? ORDER BY location").bind(whId).all()).results || [];
    
    // 輸出 UTF-8 CSV (附帶 BOM，讓 Excel 預設直接開不會亂碼)
    const bom = "\uFEFF";
    const headers = ["儲位", "區域", "料號", "品名", "批號", "數量", "包材", "備註", "更新時間"];
    const csvLines = [headers.join(",")];
    for (const r of rows) {
      const escapeCsv = (val) => {
        const s = String(val === undefined || val === null ? "" : val);
        if (s.includes(",") || s.includes('"') || s.includes("\n") || s.includes("\r")) {
          return '"' + s.replace(/"/g, '""') + '"';
        }
        return s;
      };
      csvLines.push([
        escapeCsv(r.location),
        escapeCsv(r.zone),
        escapeCsv(r.item_no),
        escapeCsv(r.item_name),
        escapeCsv(r.lot_no),
        escapeCsv(r.qty),
        escapeCsv(r.package),
        escapeCsv(r.note),
        escapeCsv(r.updated_at)
      ].join(","));
    }
    const csvContent = bom + csvLines.join("\r\n");
    const filename = encodeURIComponent(whName + "_最新儲位表.csv");
    return new Response(csvContent, {
      status: 200,
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": 'attachment; filename="' + filename + '"; filename*=UTF-8\'\'' + filename,
        "Cache-Control": "no-cache, no-store"
      }
    });
  }

  return json({ error: "Not found" }, 404);
}
