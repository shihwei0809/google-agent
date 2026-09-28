path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Extract the skipSample function block
m = re.search(r'  function skipSample\(\) \{.*?\n  \}\n', text, re.DOTALL)
if m:
    skip_fn = m.group(0)
    # Remove it from the incorrect location
    text = text.replace(skip_fn, '')
    
    # Insert it properly AFTER submitForm() ends
    text = text.replace('    } else {\n      setTimeout(() => {\n        allData.unshift(payload);\n        localStorage.setItem(\'HS_QC_SAMPLES\', JSON.stringify(allData));\n        resetForm();\n        btn.disabled = false;\n        btn.innerText = "確認提交送樣 🚀";\n        showToast("⚠️ 已暫存於本機！");\n        render();\n      }, 500);\n    }\n  }', '    } else {\n      setTimeout(() => {\n        allData.unshift(payload);\n        localStorage.setItem(\'HS_QC_SAMPLES\', JSON.stringify(allData));\n        resetForm();\n        btn.disabled = false;\n        btn.innerText = "確認提交送樣 🚀";\n        showToast("⚠️ 已暫存於本機！");\n        render();\n      }, 500);\n    }\n  }\n\n' + skip_fn)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed skipSample placement")
else:
    print("Not found")
