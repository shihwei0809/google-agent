import os
import re

for folder in ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Add onchange to select
    text = text.replace(
        '<select id="modalResult" style="margin-bottom:15px; font-size:1.1rem; color:#059669; font-weight:bold;">',
        '<select id="modalResult" onchange="handleResultChange()" style="margin-bottom:15px; font-size:1.1rem; color:#059669; font-weight:bold;">'
    )

    # 2. Add handleResultChange function
    new_func = """
  function handleResultChange() {
    const sel = document.getElementById('modalResult');
    const note = document.getElementById('modalNote');
    if (sel.value === 'FAIL') {
      sel.style.color = '#dc2626'; // Red
      if (note.value === '合格放行') note.value = '';
    } else {
      sel.style.color = '#059669'; // Green
      if (note.value === '') note.value = '合格放行';
    }
  }
"""
    if 'function handleResultChange' not in text:
        text = text.replace(
            "function submitJudge() {",
            new_func + "\n  function submitJudge() {"
        )

    # 3. Update openJudge to reset select
    old_openJudge = re.search(r'function openJudge\(id\) \{.*?(?=const approverText)', text, re.DOTALL)
    if old_openJudge:
        new_top = old_openJudge.group(0)
        if "document.getElementById('modalResult').value = 'PASS';" not in new_top:
            new_top = new_top.replace(
                "document.getElementById('modalNote').value = '合格放行';",
                "document.getElementById('modalNote').value = '合格放行'; \n    document.getElementById('modalResult').value = 'PASS';\n    handleResultChange();"
            )
            text = text.replace(old_openJudge.group(0), new_top)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

print("Patched handleResultChange")
