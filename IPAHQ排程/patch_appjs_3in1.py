import re

file_path = 'C:/GOOGLE ANGET/IPAHQ排程/public/app.js'
with open(file_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Replace the 3-in-1 printCell generation logic
old_printCell = """      // 三合一單獨立一欄
      let printLink = '-';
      if (o.client && (o.client.includes('台積') || o.client.includes('TSMC'))) {
        printLink = `<button class="btn btn-primary btn-sm" onclick="download3in1('${o.id}')" style="padding: 2px 8px; font-size: 0.85rem;">🖨️ 下載</button>`;
      }
      const printCell = `<td>${printLink}</td>`;"""

new_printCell = """      // 三合一單獨立一欄 (無批號不顯示)
      let printLink = '-';
      if (o.client && (o.client.includes('台積') || o.client.includes('TSMC')) && o.batch && o.batch.trim() !== '' && o.batch !== '-' && o.batch !== 'null') {
        const safeId = o.id || '';
        printLink = `<button class="btn btn-primary btn-sm" onclick="download3in1('${safeId}', '${o.batch}')" style="padding: 2px 8px; font-size: 0.85rem;">🖨️ 下載</button>`;
      }
      const printCell = `<td>${printLink}</td>`;"""

if old_printCell in js:
    js = js.replace(old_printCell, new_printCell)
    print("Replaced printCell block.")
else:
    # Use regex
    js = re.sub(
        r'// 三合一單獨立一欄[\s\S]*?const printCell = `<td>\$\{printLink\}</td>`;',
        new_printCell,
        js
    )
    print("Replaced printCell block via regex.")

# Replace download3in1 function
old_download = """window.download3in1 = async function(id) {
    try {
      const res = await fetch(`/api/orders/${id}/tsmc-3in1`);"""

new_download = """window.download3in1 = async function(id, batch) {
    if (id === 'null' || !id) {
        id = 'batch:' + batch;
    }
    try {
      const res = await fetch(`/api/orders/${encodeURIComponent(id)}/tsmc-3in1`);"""

if old_download in js:
    js = js.replace(old_download, new_download)
    print("Replaced download3in1 function.")
else:
    print("Could not find download3in1 function to replace.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(js)
