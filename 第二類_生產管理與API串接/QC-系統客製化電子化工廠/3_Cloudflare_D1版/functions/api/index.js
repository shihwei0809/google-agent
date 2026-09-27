export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  if (request.method === "OPTIONS") return new Response(null, { headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type" } });
  const h = { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" };
  
  try {
    let action = url.searchParams.get("action");
    let payload = null;
    if (request.method === "POST") { 
      try { payload = await request.json(); action = payload.action || action; } catch(e) {} 
    }
    
    // --- Authentication ---
    if (action === "verifyLogin" && request.method === "POST") {
      const row = await env.DB.prepare("SELECT username, role FROM Accounts WHERE username = ? AND password_hash = ?").bind(payload.username, payload.password).first();
      if (row) return new Response(JSON.stringify({ success: true, username: row.username, role: row.role }), { headers: h });
      else return new Response(JSON.stringify({ error: "Invalid credentials" }), { headers: h, status: 401 });
    }
    
    // --- System Config ---
    if (action === "getConfig") {
      const { results } = await env.DB.prepare("SELECT * FROM System_Config").all();
      let configMap = {}; results.forEach(r => { configMap[r.config_key] = r.config_value; });
      return new Response(JSON.stringify(configMap), { headers: h });
    }
    if (action === "fixDatabase") {
      await env.DB.prepare('DELETE FROM System_Config').run();
      const stmt = env.DB.prepare('INSERT INTO System_Config (config_key, config_value) VALUES (?, ?)');
      const defaults = [
        ['QC_PIN', '8888'],
        ['TEAMS_MANAGER_WEBHOOK', ''],
        ['TEAMS_WEBHOOK_資材課', ''],
        ['TEAMS_WEBHOOK_二部一課', ''],
        ['TEAMS_WEBHOOK_二部二課', ''],
        ['TEAMS_WEBHOOK_一部一課', ''],
        ['TEAMS_WEBHOOK_一部二課', ''],
        ['PWA_URL', 'https://google-agent.pages.dev/qc-system'],
        ['OPTIONS_FLOW_TYPES', '出貨, 進料, 補料, 委託'],
        ['OPTIONS_GRADES', '工業級, 電子級, IF'],
        ['OPTIONS_DEPTS', '資材課, 二部一課, 二部二課, 一部一課, 一部二課'],
        ['OPTIONS_PRODUCTS', 'IPA, IPAUPS, IPAHQ, CPNE3(T), CPNE4, CPN-P1R, EBR, EBR-P1R, NBAC, NBAC-P1R, CPN, EG, NMP, GAA, ACT, PM, PMA98, heavy-R, DPM, DPM-B1, SEP73, Anone, GBL, PG, EBRR'],
        ['OPTIONS_PRODUCT_GRADES_MAP', 'EBR-P1R:電子級, IPAUPS:UPS']
      ];
      await env.DB.batch(defaults.map(d => stmt.bind(d[0], d[1])));
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }

    if (action === "updateConfig" && request.method === "POST") {
      const configs = payload.configs || {};
      for (const key of Object.keys(configs)) await env.DB.prepare("INSERT INTO System_Config (config_key, config_value) VALUES (?, ?) ON CONFLICT(config_key) DO UPDATE SET config_value=excluded.config_value").bind(key, configs[key]).run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    
    // --- Accounts Management ---
    if (action === "getAccounts") {
      const { results } = await env.DB.prepare("SELECT id, username, role, created_at FROM Accounts").all();
      return new Response(JSON.stringify({ success: true, count: results.length, data: results }), { headers: h });
    }
    if (action === "createAccount" && request.method === "POST") {
      await env.DB.prepare("INSERT INTO Accounts (username, password_hash, role) VALUES (?, ?, ?)").bind(payload.username, payload.password, payload.role || 'user').run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    if (action === "changePassword" && request.method === "POST") {
      await env.DB.prepare("UPDATE Accounts SET password_hash = ? WHERE id = ?").bind(payload.newPassword, payload.id).run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    if (action === "deleteAccount" && request.method === "POST") {
      await env.DB.prepare("DELETE FROM Accounts WHERE id = ?").bind(payload.id).run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }

    // --- Core QC Business Logic ---
    if (action === "getSamples") {
      const { results } = await env.DB.prepare("SELECT * FROM QC_Samples ORDER BY createdAt DESC LIMIT 100").all();
      return new Response(JSON.stringify(results), { headers: h });
    }
    
    if ((action === "submitSample" || action === "createSample") && request.method === "POST") {
      // payload expects: id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade
      const data = payload.payload || payload;
      const { id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade, remark } = data;
      await env.DB.prepare("ALTER TABLE QC_Samples ADD COLUMN remark TEXT").run().catch(e=>{});
      await env.DB.prepare("INSERT INTO QC_Samples (id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade, remark, status, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now', '+8 hours'))")
        .bind(id||null, barcode||null, productName||null, tankNo||null, customer||null, quantity||null, flowType||null, dept||null, requester||null, grade||null, remark||null).run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }

    if (action === "updateSample" && request.method === "POST") {
      // QC Approvals and Judgements
      // payload expects: id, result, note, approver
      const { id, result, note, approver } = payload;
      let status = "completed";
      if (result === "退件" || result === "重取樣") status = "failed";
      
      await env.DB.prepare("UPDATE QC_Samples SET status = ?, qcResult = ?, qcNote = ?, qcApprover = ?, completedAt = datetime('now', '+8 hours') WHERE id = ?")
        .bind(status||null, result||null, note||null, approver||null, id||null).run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }
    
    if (action === "deleteSample" && request.method === "POST") {
      await env.DB.prepare("DELETE FROM QC_Samples WHERE id = ?").bind(payload.id).run();
      return new Response(JSON.stringify({ success: true }), { headers: h });
    }

    if (action === "saveOrders" && request.method === "POST") {
      // 確保資料表存在並自動更新結構
      await env.DB.prepare("CREATE TABLE IF NOT EXISTS T100_Orders (id INTEGER PRIMARY KEY AUTOINCREMENT, doc_no TEXT, flowType TEXT, productName TEXT, tankNo TEXT, container TEXT, quantity TEXT, customer TEXT, grade TEXT, targetDate TEXT, date TEXT, time TEXT, note TEXT, createdAt DATETIME DEFAULT CURRENT_TIMESTAMP)").run();
      await env.DB.prepare("ALTER TABLE T100_Orders ADD COLUMN date TEXT").run().catch(e=>{});
      await env.DB.prepare("ALTER TABLE T100_Orders ADD COLUMN time TEXT").run().catch(e=>{});
      await env.DB.prepare("ALTER TABLE T100_Orders ADD COLUMN note TEXT").run().catch(e=>{});
      
      // 清空舊排程
      await env.DB.prepare("DELETE FROM T100_Orders").run();
      
      // 批次寫入新排程
      const orders = payload.orders || [];
      if (orders.length > 0) {
        const stmt = env.DB.prepare("INSERT INTO T100_Orders (doc_no, flowType, productName, tankNo, container, quantity, customer, grade, targetDate, date, time, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
        const batchStmts = orders.map(o => stmt.bind(o.doc_no||'', o.flowType||'', o.productName||'', o.tankNo||'', o.container||'', o.quantity||'', o.customer||'', o.grade||'', o.targetDate||'', o.date||'', o.time||'', o.note||''));
        await env.DB.batch(batchStmts);
      }
      return new Response(JSON.stringify({ success: true, count: orders.length, importedAt: new Date().toISOString() }), { headers: h });
    }

    if (action === "getOrders") {
      // 確保資料表存在以防尚未初始化
      await env.DB.prepare("CREATE TABLE IF NOT EXISTS T100_Orders (id INTEGER PRIMARY KEY AUTOINCREMENT, doc_no TEXT, flowType TEXT, productName TEXT, tankNo TEXT, container TEXT, quantity TEXT, customer TEXT, grade TEXT, targetDate TEXT, date TEXT, time TEXT, note TEXT, createdAt DATETIME DEFAULT CURRENT_TIMESTAMP)").run();
      const { results } = await env.DB.prepare("SELECT * FROM T100_Orders ORDER BY targetDate DESC, createdAt DESC LIMIT 200").all();
      return new Response(JSON.stringify({ success: true, count: results.length, orders: results }), { headers: h });
    }

    if (action === "getEmployees") {
      const { results } = await env.DB.prepare("SELECT * FROM Employees").all();
      return new Response(JSON.stringify({ success: true, data: results }), { headers: h });
    }

    return new Response(JSON.stringify({ error: "Unknown action" }), { headers: h, status: 400 });
  } catch (err) { 
    return new Response(JSON.stringify({ error: err.message }), { headers: h, status: 500 }); 
  }
}


