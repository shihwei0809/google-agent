import re

file_path = 'C:/GOOGLE ANGET/IPAHQ排程/server.js'
with open(file_path, 'r', encoding='utf-8') as f:
    js = f.read()

old_logic = """app.get('/api/orders/:id/tsmc-3in1', (req, res) => {
  try {
    const orderId = req.params.id;
    const db = getDB();
    const order = db.orders.find(o => o.id === orderId);
    if (!order) return res.status(404).json({ success: false, message: '找不到訂單' });"""

new_logic = """app.get('/api/orders/:id/tsmc-3in1', (req, res) => {
  try {
    const orderId = req.params.id;
    const db = getDB();
    let order = null;
    
    if (orderId.startsWith('batch:')) {
      const batch = orderId.replace('batch:', '');
      order = db.orders.find(o => o.batch === batch);
    } else {
      order = db.orders.find(o => o.id === orderId);
    }
    
    if (!order) return res.status(404).json({ success: false, message: '找不到訂單' });"""

if old_logic in js:
    js = js.replace(old_logic, new_logic)
    print("Patched server API logic.")
else:
    # Use regex
    js = re.sub(
        r"app\.get\('/api/orders/:id/tsmc-3in1',\s*\(req,\s*res\)\s*=>\s*\{\s*try\s*\{\s*const\s*orderId\s*=\s*req\.params\.id;\s*const\s*db\s*=\s*getDB\(\);\s*const\s*order\s*=\s*db\.orders\.find\(o\s*=>\s*o\.id\s*===\s*orderId\);\s*if\s*\(!order\)\s*return\s*res\.status\(404\)\.json\(\{ success: false, message: '找不到訂單' \}\);",
        r"app.get('/api/orders/:id/tsmc-3in1', (req, res) => {\n  try {\n    const orderId = req.params.id;\n    const db = getDB();\n    let order = null;\n    if (orderId.startsWith('batch:')) {\n      const batch = orderId.replace('batch:', '');\n      order = db.orders.find(o => o.batch === batch);\n    } else {\n      order = db.orders.find(o => o.id === orderId);\n    }\n    if (!order) return res.status(404).json({ success: false, message: '找不到訂單' });",
        js
    )
    print("Patched server API logic via regex.")

# Change the filename output
# res.download(outFile, `三合一單-${orderId}.xlsx`);
# Should be: 
# const safeId = order.id && order.id !== '無' && order.id !== 'null' ? order.id : order.batch;
# res.download(outFile, `三合一單-${safeId}.xlsx`);
js = re.sub(
    r"res\.download\(outFile,\s*`三合一單-\$\{orderId\}\.xlsx`\);",
    r"const safeId = (order.id && order.id !== '無' && order.id !== 'null') ? order.id : (order.batch || '未知');\n        res.download(outFile, `三合一單-${safeId}.xlsx`);",
    js
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("Regex replace for server.js applied.")
