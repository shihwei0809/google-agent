path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix getSamples response format
text = text.replace(
    'return new Response(JSON.stringify({ success: true, count: results.length, orders: results }), { headers: h });',
    'return new Response(JSON.stringify(results), { headers: h });'
)

# Fix submitSample status
text = text.replace(
    ", '待檢驗', datetime('now', 'localtime'))\"",
    ", 'pending', datetime('now', 'localtime'))\""
)

# Fix updateSample status
old_update = """      let status = "已檢驗";
      if (result === "退件") status = "退件";
      if (result === "重取樣") status = "重取樣";"""
new_update = """      let status = "completed";
      if (result === "退件" || result === "重取樣") status = "failed";"""
text = text.replace(old_update, new_update)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
