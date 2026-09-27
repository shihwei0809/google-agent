import re
path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix getOrders
text = re.sub(
    r'(if \(action === "getOrders"\) \{.*?const \{ results \} = await env\.DB\.prepare\(.*?\.all\(\);\n\s+)return new Response\(JSON\.stringify\(results\), \{ headers: h \}\);',
    r'\1return new Response(JSON.stringify({ success: true, count: results.length, orders: results }), { headers: h });',
    text,
    flags=re.DOTALL
)

# Fix getEmployees
text = re.sub(
    r'(if \(action === "getEmployees"\) \{.*?const \{ results \} = await env\.DB\.prepare\(.*?\.all\(\);\n\s+)return new Response\(JSON\.stringify\(results\), \{ headers: h \}\);',
    r'\1return new Response(JSON.stringify({ success: true, data: results }), { headers: h });',
    text,
    flags=re.DOTALL
)

# Fix getAccounts
text = re.sub(
    r'(if \(action === "getAccounts"\) \{.*?const \{ results \} = await env\.DB\.prepare\(.*?\.all\(\);\n\s+)return new Response\(JSON\.stringify\(results\), \{ headers: h \}\);',
    r'\1return new Response(JSON.stringify({ success: true, count: results.length, data: results }), { headers: h });',
    text,
    flags=re.DOTALL
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
