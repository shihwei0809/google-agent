path = r'D:\GOOGLE ANGET\勝一三合一單網頁架機伺服器\static\index.html'
import re

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Globals
if 'let SERVER_PART_MAPPING' not in text:
    text = text.replace(
        'let SERVER_MAPPING = {};',
        'let SERVER_MAPPING = {};\nlet SERVER_PART_MAPPING = {};'
    )

# 2. fetchMapping
if 'SERVER_PART_MAPPING = res.parts;' not in text:
    text = text.replace(
        'SERVER_MAPPING = Object.assign({}, DEFAULT_FALLBACK_MAPPING, res.data);',
        'SERVER_MAPPING = Object.assign({}, DEFAULT_FALLBACK_MAPPING, res.data);\n                    if (res.parts) SERVER_PART_MAPPING = res.parts;'
    )

# 3. Table Headers
m = re.search(r'(<th style="width: 220px;">長代號.*?</th>)', text)
if m:
    new_headers = f'{m.group(1)}\n                    <th style="width: 120px;">料號 (自動)</th>'
    text = text[:m.start()] + new_headers + text[m.end():]

# 4. row HTML
m = re.search(r'(<td><input type="text" class="read-only long-code" id="long_\$\{rowIdx\}".*?</td>)', text)
if m:
    new_row = f'''{m.group(1)}
            <td><input type="text" class="read-only part-no" id="part_${{rowIdx}}" readonly placeholder="自動料號" style="color:#D32F2F; font-weight:bold;"></td>'''
    text = text[:m.start()] + new_row + text[m.end():]

# 5. onLocChange
onloc_old = r'''            let locVal = document\.getElementById\(`loc_\$\{rowIdx\}`\)\.value\.toUpperCase\(\)\.trim\(\);
            let longField = document\.getElementById\(`long_\$\{rowIdx\}`\);
            if \(locVal\) \{
                longField\.value = SERVER_MAPPING\[locVal\] \|\| "";
            \} else \{
                longField\.value = "";
            \}'''
onloc_new = r'''            let locVal = document.getElementById(`loc_${rowIdx}`).value.toUpperCase().trim();
            let prodVal = (document.getElementById(`prod_${rowIdx}`) ? document.getElementById(`prod_${rowIdx}`).value.trim().toUpperCase() : "");
            let longField = document.getElementById(`long_${rowIdx}`);
            let partField = document.getElementById(`part_${rowIdx}`);
            if (locVal) {
                longField.value = SERVER_MAPPING[locVal] || "";
                if (partField) {
                    let info = SERVER_PART_MAPPING[locVal] || {};
                    let origins = info.origins || {};
                    let defaultPart = info.default || "";
                    let finalPart = "";
                    for (let key in origins) {
                        if (prodVal && prodVal.includes(key.toUpperCase())) {
                            finalPart = origins[key];
                            break;
                        }
                    }
                    if (!finalPart) finalPart = defaultPart;
                    if (!finalPart) finalPart = "L12C53161";
                    partField.value = "4" + finalPart;
                }
            } else {
                longField.value = "";
                if (partField) partField.value = "";
            }'''
text = re.sub(onloc_old, onloc_new, text)

# hook prod to locChange
prod_change_old = r'''        function onProdChange\(rowIdx\) \{
            // 目前不需特別連動
        \}'''
prod_change_new = r'''        function onProdChange(rowIdx) {
            onLocChange(rowIdx);
        }'''
text = re.sub(prod_change_old, prod_change_new, text)

# 7. Add prod to records sent to backend
# Wait, Sheng Yi already sends prod to backend!
# Let's check collectTableData
if 'prod: prodVal' not in text:
    collect_old = r'''                    let prodVal = document\.getElementById\(`prod_\$\{rowIdx\}`\)\.value\.trim\(\);'''
    # we don't need to change collect if it already collects prod!
    pass

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Patched SY index successfully!')
