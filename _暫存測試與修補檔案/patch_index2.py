path = r'D:\GOOGLE ANGET\三合一單網頁架機伺服器\static\index.html'
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
m = re.search(r'(<th style="width: 170px;">批號.*?</th>)\s*(<th style="width: 90px;">槽號.*?</th>)\s*(<th style="width: 120px;">地點.*?</th>)\s*(<th style="width: 220px;">長代號.*?</th>)', text)
if m:
    new_headers = f'{m.group(1)}\n                    {m.group(2)}\n                    <th style="width: 100px;">出貨區 (貼上)</th>\n                    {m.group(3)}\n                    <th style="width: 120px;">料號 (自動)</th>\n                    {m.group(4)}'
    text = text[:m.start()] + new_headers + text[m.end():]

# 4. row HTML
m = re.search(r'(<td><input type="text" class="read-only" id="tank_\$\{rowIdx\}".*?</td>)\s*(<td><input type="text" id="loc_\$\{rowIdx\}".*?</td>)\s*(<td><input type="text" class="read-only long-code" id="long_\$\{rowIdx\}".*?</td>)', text)
if m:
    new_row = f'''{m.group(1)}
            <td><input type="text" id="origin_${{rowIdx}}" placeholder="崙尾/彰濱" oninput="onOriginChange(${{rowIdx}})" onpaste="onPasteHandler(event, ${{rowIdx}})"></td>
            {m.group(2)}
            <td><input type="text" class="read-only part-no" id="part_${{rowIdx}}" readonly placeholder="自動料號" style="color:#D32F2F; font-weight:bold;"></td>
            {m.group(3)}'''
    text = text[:m.start()] + new_row + text[m.end():]

# 5. onLocChange
if 'function onOriginChange' not in text:
    text = text.replace(
        'function onLocChange(rowIdx) {',
        'function onOriginChange(rowIdx) {\n            onLocChange(rowIdx);\n        }\n\n        function onLocChange(rowIdx) {'
    )

onloc_old = r'''            let locVal = document\.getElementById\(`loc_\$\{rowIdx\}`\)\.value\.toUpperCase\(\)\.trim\(\);
            let longField = document\.getElementById\(`long_\$\{rowIdx\}`\);
            if \(locVal\) \{
                longField\.value = SERVER_MAPPING\[locVal\] \|\| "";
            \} else \{
                longField\.value = "";
            \}'''
onloc_new = r'''            let locVal = document.getElementById(`loc_${rowIdx}`).value.toUpperCase().trim();
            let originVal = (document.getElementById(`origin_${rowIdx}`) ? document.getElementById(`origin_${rowIdx}`).value.trim().toUpperCase() : "");
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
                        if (originVal && originVal.includes(key.toUpperCase())) {
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

# 6. onPasteHandler extraction
if 'let originVal = "";' not in text:
    text = text.replace('let dateVal = "";\n            let timeVal = "";', 'let dateVal = "";\n            let timeVal = "";\n            let originVal = "";')

onpaste_check_old = '''                        dateVal = upper;
                    } else if (upper.length === 10 && !batchVal && /[A-Z]/.test(upper) && /\\d/.test(upper)) {
                        batchVal = upper;
                    } else if ((SERVER_MAPPING[upper] || upper.includes('18P') || upper.includes('15P') || upper.includes('P3') || upper.length <= 6) && !locVal && upper !== batchVal && !upper.includes('/')) {
                        locVal = upper;
                    }'''
onpaste_check_new = '''                        dateVal = upper;
                    } else if (upper.length === 10 && !batchVal && /[A-Z]/.test(upper) && /\\d/.test(upper)) {
                        batchVal = upper;
                    } else if (!originVal && (upper.includes('崙尾') || upper.includes('彰濱') || upper.includes('L1') || upper.includes('L2'))) {
                        originVal = upper;
                    } else if ((SERVER_MAPPING[upper] || upper.includes('18P') || upper.includes('15P') || upper.includes('P3') || upper.length <= 6) && !locVal && upper !== batchVal && !upper.includes('/')) {
                        locVal = upper;
                    }'''
text = text.replace(onpaste_check_old, onpaste_check_new)

# block replacement
text = re.sub(
    r'if \(batchVal \|\| locVal \|\| dateVal \|\| timeVal\) \{',
    r'if (batchVal || locVal || dateVal || timeVal || originVal) {',
    text
)

text = text.replace(
    'if (locVal) {\n                    document.getElementById(`loc_${currentIdx}`).value = locVal;',
    'if (originVal) {\n                    if (document.getElementById(`origin_${currentIdx}`)) document.getElementById(`origin_${currentIdx}`).value = originVal;\n                }\n                if (locVal) {\n                    document.getElementById(`loc_${currentIdx}`).value = locVal;'
)

# 7. Add origin to records sent to backend
collect_old = r'''                    let locVal = document\.getElementById\(`loc_\$\{rowIdx\}`\)\.value\.toUpperCase\(\)\.trim\(\);
                    let longVal = document\.getElementById\(`long_\$\{rowIdx\}`\)\.value\.trim\(\);
                    let dateVal = document\.getElementById\(`date_\$\{rowIdx\}`\)\.value;
                    let poVal = document\.getElementById\(`po_\$\{rowIdx\}`\)\.value\.trim\(\);'''
collect_new = r'''                    let locVal = document.getElementById(`loc_${rowIdx}`).value.toUpperCase().trim();
                    let originVal = (document.getElementById(`origin_${rowIdx}`) ? document.getElementById(`origin_${rowIdx}`).value.trim() : "");
                    let longVal = document.getElementById(`long_${rowIdx}`).value.trim();
                    let dateVal = document.getElementById(`date_${rowIdx}`).value;
                    let poVal = document.getElementById(`po_${rowIdx}`).value.trim();'''
text = re.sub(collect_old, collect_new, text)

push_old = r'''                        loc: locVal,
                        long_code: longVal,
                        date: dateVal,'''
push_new = r'''                        loc: locVal,
                        origin: originVal,
                        long_code: longVal,
                        date: dateVal,'''
text = re.sub(push_old, push_new, text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Patched successfully!')
