import sys
import codecs
import re

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

with open('static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Title
content = re.sub(
    r'<title>.*</title>',
    '<title>【V4更新版】台積電槽車 Barcode 三合一單與運輸通知表</title>',
    content
)

# 2. Table Header
content = content.replace(
    '<th style="width: 170px;">批號 (請輸入 10~11 碼)</th>\n                    <th style="width: 90px;">槽號 (自動)</th>',
    '<th style="width: 170px;">批號 (請輸入 11 碼)</th>\n                    <th style="width: 90px;">槽號 (自動)</th>\n                    <th style="width: 150px;">品名 (產品)</th>'
)

# 3. Table Body Template
content = content.replace(
    '<td><input type="text" class="read-only" id="tank_${rowIdx}" readonly placeholder="自動槽號"></td>\n                <td><input type="text" id="loc_${rowIdx}" placeholder="18P3B" oninput="onLocChange(${rowIdx})"></td>',
    '<td><input type="text" class="read-only" id="tank_${rowIdx}" readonly placeholder="自動槽號"></td>\n                <td><input type="text" id="prod_${rowIdx}" placeholder="產品名稱"></td>\n                <td><input type="text" id="loc_${rowIdx}" placeholder="18P3B" oninput="onLocChange(${rowIdx})"></td>'
)

# 4. generateAllZip logic
content = content.replace('if (batch.length !== 10 && batch.length !== 11)', 'if (batch.length !== 11)')

content = re.sub(
    r'const poVal = document\.getElementById\(`po_\$\{i\}`\) \? document\.getElementById\(`po_\$\{i\}`\)\.value\.trim\(\) : "";',
    'const poVal = document.getElementById(`po_${i}`) ? document.getElementById(`po_${i}`).value.trim() : "";\n            const prodVal = document.getElementById(`prod_${i}`) ? document.getElementById(`prod_${i}`).value.trim() : "";',
    content
)

content = re.sub(
    r'po: poVal\n\s+\}\);',
    'po: poVal,\n                    prod: prodVal\n                });',
    content
)

# 5. Excel Parser logic
content = content.replace('let custVal = custCol !== -1 ? String(row[custCol] || "").trim() : "";', 'let custVal = custCol !== -1 ? String(row[custCol] || "").trim() : "";\n                        let prodVal = prodCol !== -1 ? String(row[prodCol] || "").trim() : "";')
content = content.replace(
    'po: poVal\n                        });',
    'po: poVal,\n                            prod: prodVal\n                        });'
)

# 6. modal logic confirmImport
content = content.replace(
    'if (rec.po) {\n                document.getElementById(`po_${rowIdx}`).value = rec.po;\n            }',
    'if (rec.po) {\n                document.getElementById(`po_${rowIdx}`).value = rec.po;\n            }\n            if (rec.prod && document.getElementById(`prod_${rowIdx}`)) {\n                document.getElementById(`prod_${rowIdx}`).value = rec.prod;\n            }'
)

# 7. modal text
content = content.replace(
    'label.innerText = `[${(idx+1).toString().padStart(2, \'0\')}] ${sheetTag}${dateStr}${timeStr} | 批號: ${rec.batch.padEnd(11, \' \')} | 槽號: ${(rec.tank || \'無\').padEnd(5, \' \')} | 地點: ${rec.loc || \'無\'}`;',
    'label.innerText = `[${(idx+1).toString().padStart(2, \'0\')}] ${sheetTag}${dateStr}${timeStr} | 批號: ${rec.batch.padEnd(11, \' \')} | 槽號: ${(rec.tank || \'無\').padEnd(5, \' \')} | 地點: ${rec.loc || \'無\'} | 品名: ${rec.prod || \'無\'}`;'
)

# 8. Add Toast CSS & Element & JS
toast_css = '''
        .success-box { background: #d4edda; color: #155724; border-left: 5px solid #28a745; padding: 10px; margin-bottom: 20px; border-radius: 5px; display: flex; align-items: center; justify-content: space-between; font-weight: bold;}
        #toast { visibility: hidden; min-width: 250px; background-color: #333; color: #fff; text-align: center; border-radius: 8px; padding: 16px; position: fixed; z-index: 1000; left: 50%; bottom: 30px; transform: translateX(-50%); font-size: 16px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); opacity: 0; transition: opacity 0.5s, visibility 0.5s; }
        #toast.show { visibility: visible; opacity: 1; }
'''
content = content.replace('</style>', toast_css + '</style>')
content = content.replace('</div>\n</body>', '<div id="toast"></div>\n</div>\n</body>')

toast_js = '''
    function showToast(message, duration=3000) {
        const toast = document.getElementById("toast");
        toast.innerText = message;
        toast.className = "show";
        setTimeout(() => { toast.className = toast.className.replace("show", ""); }, duration);
    }
'''
content = content.replace('function loadLocationMapping() {', toast_js + '\n    function loadLocationMapping() {')
content = re.sub(
    r'alert\(`✔️ 已成功更新伺服器對照表！最新共匯入 \$\{newCount\} 筆對照碼。`\);',
    'showToast(`✔️ 已成功更新伺服器對照表！最新共匯入 ${newCount} 筆對照碼。`);',
    content
)
content = re.sub(
    r'alert\("讀取 Excel 成功.*?"\);',
    'showToast("讀取 Excel 成功...");',
    content
)
content = content.replace('alert("✔️ 資料處理完成！");', 'showToast("✔️ 資料處理完成！");')

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
