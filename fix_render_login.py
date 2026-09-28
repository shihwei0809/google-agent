path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Add loggedInUser check in render()
if "const loggedInUser = sessionStorage.getItem('QC_LOGGED_IN_USER');" not in text:
    text = text.replace("  function render() {\n    const kw =", "  function render() {\n    const loggedInUser = sessionStorage.getItem('QC_LOGGED_IN_USER');\n    const kw =")

# Adaptive replacement
old_adaptive = """<button class="btn-action btn-print" onclick="printLabelById('${s.id}')" style="width:100%; padding:4px 0; font-size:0.75rem; margin:0;">列印</button>
            <button class="btn-action btn-judge" onclick="openJudge('${s.id}')" style="width:100%; padding:4px 0; font-size:0.75rem; margin:0;">判定</button>"""
new_adaptive = """<button class="btn-action btn-print" onclick="printLabelById('${s.id}')" style="width:100%; padding:4px 0; font-size:0.75rem; margin:0;">列印</button>
            ${loggedInUser ? `<button class="btn-action btn-judge" onclick="openJudge('${s.id}')" style="width:100%; padding:4px 0; font-size:0.75rem; margin:0;">判定</button>` : `<div style="text-align:center; color:#94a3b8; font-size:0.75rem; margin-top:8px; border: 1px dashed #cbd5e1; border-radius: 4px; padding: 2px;">登入後判定</div>`}"""
text = text.replace(old_adaptive, new_adaptive)

# Traditional replacement
old_trad = """<button class="btn-action btn-print" onclick="printLabelById('${s.id}')">列印</button>
          <button class="btn-action btn-judge" onclick="openJudge('${s.id}')">判定</button>"""
new_trad = """<button class="btn-action btn-print" onclick="printLabelById('${s.id}')">列印</button>
          ${loggedInUser ? `<button class="btn-action btn-judge" onclick="openJudge('${s.id}')">判定</button>` : `<div style="text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:5px; border: 1px dashed #cbd5e1; border-radius: 4px; padding: 2px;">登入後判定</div>`}"""
text = text.replace(old_trad, new_trad)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
