import re

file_path = 'C:/GOOGLE ANGET/IPAHQ排程/server.js'
with open(file_path, 'r', encoding='utf-8') as f:
    js = f.read()

old_download_pattern = r"const safeId = \(order\.id && order\.id !== '無' && order\.id !== 'null'\) \? order\.id : \(order\.batch \|\| '未知'\);\s*res\.download\(outFile, `三合一單-\$\{safeId\}\.xlsx`\);"

new_download = """      // 檔名格式: 2026.8.29. 20P1_S382_台積電槽車barcode三合一單.xlsx
      let dateStr = "";
      if (order.expected_date) {
          let parts = order.expected_date.split('-');
          if (parts.length === 3) {
              dateStr = `${parseInt(parts[0], 10)}.${parseInt(parts[1], 10)}.${parseInt(parts[2], 10)}. `;
          }
      }

      let tankNo = "";
      if (order.batch) {
          let m = order.batch.match(/(S\\d+)/i);
          if (m) tankNo = m[1].toUpperCase();
          else tankNo = order.batch;
      }

      let locShort = "";
      const locFile = require('path').join(__dirname, '地點代號對照表.xlsx');
      if (require('fs').existsSync(locFile)) {
          const xlsxLocal = require('xlsx');
          const wbLoc = xlsxLocal.readFile(locFile);
          const sheetLoc = wbLoc.Sheets[wbLoc.SheetNames[0]];
          const rows = xlsxLocal.utils.sheet_to_json(sheetLoc, { header: 1, range: 1 });
          const destUpper = (order.destination || '').toUpperCase();
          for (let r of rows) {
              const sn = String(r[0] || '').trim();
              const fn = String(r[1] || '').trim();
              if (sn && (destUpper === sn.toUpperCase() || destUpper === fn.toUpperCase() || destUpper.includes(sn.toUpperCase()))) {
                  locShort = sn;
                  break;
              }
          }
      }
      if (!locShort) {
          let match = (order.destination||'').match(/([A-Z0-9]+)$/i);
          if(match) locShort = match[1];
          else locShort = order.destination || '未知';
      }

      const finalFileName = `${dateStr}${locShort}_${tankNo}_台積電槽車barcode三合一單.xlsx`;
      res.download(outFile, finalFileName);"""

if re.search(old_download_pattern, js):
    # Pass a lambda to avoid backslash escaping issues in replacement string
    js = re.sub(old_download_pattern, lambda m: new_download.replace('\\\\', '\\'), js)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print("Patched filename format successfully.")
else:
    print("Failed to find download pattern.")
