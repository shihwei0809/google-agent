path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

get_orders = '''    if (action === "getOrders") {
      const { results } = await env.DB.prepare("SELECT * FROM Orders ORDER BY createdAt DESC LIMIT 100").all();
      return new Response(JSON.stringify(results), { headers: h });
    }'''

new_orders = '''    if (action === "saveOrders" && request.method === "POST") {
      // 確保資料表存在
      await env.DB.prepare(CREATE TABLE IF NOT EXISTS T100_Orders (id INTEGER PRIMARY KEY AUTOINCREMENT, doc_no TEXT, flowType TEXT, productName TEXT, tankNo TEXT, container TEXT, quantity TEXT, customer TEXT, grade TEXT, targetDate TEXT, createdAt DATETIME DEFAULT CURRENT_TIMESTAMP)).run();
      
      // 清空舊排程
      await env.DB.prepare(DELETE FROM T100_Orders).run();
      
      // 批次寫入新排程
      const orders = payload.orders || [];
      if (orders.length > 0) {
        const stmt = env.DB.prepare(INSERT INTO T100_Orders (doc_no, flowType, productName, tankNo, container, quantity, customer, grade, targetDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?));
        const batchStmts = orders.map(o => stmt.bind(o.doc_no||'', o.flowType||'', o.productName||'', o.tankNo||'', o.container||'', o.quantity||'', o.customer||'', o.grade||'', o.targetDate||''));
        await env.DB.batch(batchStmts);
      }
      return new Response(JSON.stringify({ success: true, count: orders.length, importedAt: new Date().toISOString() }), { headers: h });
    }

    if (action === "getOrders") {
      // 確保資料表存在以防尚未初始化
      await env.DB.prepare(CREATE TABLE IF NOT EXISTS T100_Orders (id INTEGER PRIMARY KEY AUTOINCREMENT, doc_no TEXT, flowType TEXT, productName TEXT, tankNo TEXT, container TEXT, quantity TEXT, customer TEXT, grade TEXT, targetDate TEXT, createdAt DATETIME DEFAULT CURRENT_TIMESTAMP)).run();
      const { results } = await env.DB.prepare("SELECT * FROM T100_Orders ORDER BY targetDate DESC, createdAt DESC LIMIT 200").all();
      return new Response(JSON.stringify(results), { headers: h });
    }'''

text = text.replace(get_orders, new_orders)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
