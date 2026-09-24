path = r'D:\GOOGLE ANGET\三合一單網頁架機伺服器\static\index.html'

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Globals
text = text.replace(
    'let SERVER_MAPPING = {};',
    'let SERVER_MAPPING = {};\nlet SERVER_PART_MAPPING = {};'
)

# 2. fetchMapping
text = text.replace(
    'SERVER_MAPPING = Object.assign({}, DEFAULT_FALLBACK_MAPPING, res.data);',
    'SERVER_MAPPING = Object.assign({}, DEFAULT_FALLBACK_MAPPING, res.data);\n                    if (res.parts) SERVER_PART_MAPPING = res.parts;'
)

# 3. Table Headers
headers_old = '''                    <th style="width: 170px;">批號 (請輸入10 碼)</th>
                    <th style="width: 90px;">槽號 (自動)</th>
                    <th style="width: 120px;">地點 (如18P3B)</th>
                    <th style="width: 220px;">長代號 (自動)</th>'''
headers_new = '''                    <th style="width: 170px;">批號 (請輸入10 碼)</th>
                    <th style="width: 90px;">槽號 (自動)</th>
                    <th style="width: 100px;">出貨區 (貼上)</th>
                    <th style="width: 110px;">地點 (如18P3B)</th>
                    <th style="width: 120px;">料號 (自動)</th>
                    <th style="width: 220px;">長代號 (自動)</th>'''
text = text.replace(headers_old, headers_new)

# 4. row HTML
row_old = '''            <td><input type="text" class="read-only" id="tank_${rowIdx}" readonly placeholder="自動槽號"></td>
            <td><input type="text" id="loc_${rowIdx}" placeholder="18P3B" oninput="onLocChange(${rowIdx})"></td>
            <td><input type="text" class="read-only long-code" id="long_${rowIdx}" readonly placeholder="自動長碼" onclick="handleLongCodeClick(${rowIdx})"></td>'''
row_new = '''            <td><input type="text" class="read-only" id="tank_${rowIdx}" readonly placeholder="自動槽號"></td>
            <td><input type="text" id="origin_${rowIdx}" placeholder="崙尾/彰濱" oninput="onOriginChange(${rowIdx})" onpaste="onPasteHandler(event, ${rowIdx})"></td>
            <td><input type="text" id="loc_${rowIdx}" placeholder="18P3B" oninput="onLocChange(${rowIdx})"></td>
            <td><input type="text" class="read-only part-no" id="part_${rowIdx}" readonly placeholder="自動料號" style="color:#D32F2F; font-weight:bold;"></td>
            <td><input type="text" class="read-only long-code" id="long_${rowIdx}" readonly placeholder="自動長碼" onclick="handleLongCodeClick(${rowIdx})"></td>'''
text = text.replace(row_old, row_new)

# 5. onLocChange
text = text.replace(
    'function onLocChange(rowIdx) {',
    'function onOriginChange(rowIdx) {\n            onLocChange(rowIdx);\n        }\n\n        function onLocChange(rowIdx) {'
)

onloc_old = '''            let locVal = document.getElementById(`loc_${rowIdx}`).value.toUpperCase().trim();
            let longField = document.getElementById(`long_${rowIdx}`);
            if (locVal) {
                longField.value = SERVER_MAPPING[locVal] || "";
            } else {
                longField.value = "";
            }'''
onloc_new = '''            let locVal = document.getElementById(`loc_${rowIdx}`).value.toUpperCase().trim();
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
text = text.replace(onloc_old, onloc_new)

# 6. onPasteHandler extraction
onpaste_old = '''let dateVal = "";
            let timeVal = "";'''
onpaste_new = '''let dateVal = "";
            let timeVal = "";
            let originVal = "";'''
text = text.replace(onpaste_old, onpaste_new)

onpaste_check_old = '''                        dateVal = upper;
                    } else if (upper.length === 10 && !batchVal && /[A-Z]/.test(upper) && /\d/.test(upper)) {
                        batchVal = upper;
                    } else if ((SERVER_MAPPING[upper] || upper.includes('18P') || upper.includes('15P') || upper.includes('P3') || upper.length <= 6) && !locVal && upper !== batchVal && !upper.includes('/')) {
                        locVal = upper;
                    }'''
onpaste_check_new = '''                        dateVal = upper;
                    } else if (upper.length === 10 && !batchVal && /[A-Z]/.test(upper) && /\d/.test(upper)) {
                        batchVal = upper;
                    } else if (!originVal && (upper.includes('崙尾') || upper.includes('彰濱') || upper.includes('L1') || upper.includes('L2'))) {
                        originVal = upper;
                    } else if ((SERVER_MAPPING[upper] || upper.includes('18P') || upper.includes('15P') || upper.includes('P3') || upper.length <= 6) && !locVal && upper !== batchVal && !upper.includes('/')) {
                        locVal = upper;
                    }'''
text = text.replace(onpaste_check_old, onpaste_check_new)

# Find and replace the if (batchVal || ...) block
start_idx = text.find('if (batchVal || locVal || dateVal || timeVal) {')
end_idx = text.find('if (locVal) {', start_idx) + 100
end_idx = text.find('}', end_idx) + 1
old_block = text[start_idx:end_idx]

new_block = old_block.replace(
    'if (batchVal || locVal || dateVal || timeVal) {',
    'if (batchVal || locVal || dateVal || timeVal || originVal) {'
).replace(
    'if (locVal) {',
    'if (originVal) {\n                    if (document.getElementById(`origin_${currentIdx}`)) document.getElementById(`origin_${currentIdx}`).value = originVal;\n                }\n                if (locVal) {'
)
text = text.replace(old_block, new_block)

# 7. Add origin to records sent to backend
collect_old = '''                    let locVal = document.getElementById(`loc_${rowIdx}`).value.toUpperCase().trim();
                    let longVal = document.getElementById(`long_${rowIdx}`).value.trim();
                    let dateVal = document.getElementById(`date_${rowIdx}`).value;
                    let poVal = document.getElementById(`po_${rowIdx}`).value.trim();'''
collect_new = '''                    let locVal = document.getElementById(`loc_${rowIdx}`).value.toUpperCase().trim();
                    let originVal = (document.getElementById(`origin_${rowIdx}`) ? document.getElementById(`origin_${rowIdx}`).value.trim() : "");
                    let longVal = document.getElementById(`long_${rowIdx}`).value.trim();
                    let dateVal = document.getElementById(`date_${rowIdx}`).value;
                    let poVal = document.getElementById(`po_${rowIdx}`).value.trim();'''
text = text.replace(collect_old, collect_new)

push_old = '''                        loc: locVal,
                        long_code: longVal,
                        date: dateVal,'''
push_new = '''                        loc: locVal,
                        origin: originVal,
                        long_code: longVal,
                        date: dateVal,'''
text = text.replace(push_old, push_new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
