path = r'D:\GOOGLE ANGET\三合一單網頁架機伺服器\static\index.html'

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace onLocChange(idx) definition
old_func = '''function onLocChange(idx) {
            let locVal = document.getElementById(`loc_${idx}`).value.toUpperCase().trim();
            let longField = document.getElementById(`long_${idx}`);
            if (locVal) {
                longField.value = SERVER_MAPPING[locVal] || "";
            } else {
                longField.value = "";
            }
        }'''

new_func = '''function onOriginChange(idx) {
            onLocChange(idx);
        }

        function onLocChange(idx) {
            let locVal = document.getElementById(`loc_${idx}`).value.toUpperCase().trim();
            let originVal = (document.getElementById(`origin_${idx}`) ? document.getElementById(`origin_${idx}`).value.trim().toUpperCase() : "");
            let longField = document.getElementById(`long_${idx}`);
            let partField = document.getElementById(`part_${idx}`);
            
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
            }
        }'''

if 'function onOriginChange' not in text:
    text = text.replace(old_func, new_func)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Fixed index.html!')
