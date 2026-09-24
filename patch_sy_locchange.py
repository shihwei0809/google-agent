path = r'D:\GOOGLE ANGET\勝一三合一單網頁架機伺服器\static\index.html'

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace function onLocChange(idx) {
new_func = '''    function onLocChange(idx) {'''

old_logic = '''        } else {
            longEl.value = "";
            longEl.style.color = "#7B1FA2";
            longEl.style.cursor = "default";
            longEl.title = "";
        }
    }'''

new_logic = '''        } else {
            longEl.value = "";
            longEl.style.color = "#7B1FA2";
            longEl.style.cursor = "default";
            longEl.title = "";
        }
        
        let partField = document.getElementById(`part_${idx}`);
        let prodVal = (document.getElementById(`prod_${idx}`) ? document.getElementById(`prod_${idx}`).value.trim().toUpperCase() : "");
        if (locVal && partField) {
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
        } else if (partField) {
            partField.value = "";
        }
    }'''

if 'partField.value = "4" + finalPart;' not in text:
    text = text.replace(old_logic, new_logic)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
