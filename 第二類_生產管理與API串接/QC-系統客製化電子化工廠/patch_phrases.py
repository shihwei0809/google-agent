import os
import re

CSS = """
    .phrase-tag {
      background: #f1f5f9;
      color: #475569;
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 0.75rem;
      cursor: pointer;
      border: 1px solid #cbd5e1;
      transition: all 0.2s;
      user-select: none;
    }
    .phrase-tag:hover {
      background: #e2e8f0;
      color: #0f172a;
      border-color: #94a3b8;
    }
"""

for folder in ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Add CSS
    if '.phrase-tag {' not in text:
        text = text.replace("</style>", CSS + "</style>")

    # 2. Add containers in HTML
    text = text.replace(
        '<textarea id="modalNote"',
        '<div id="modalPhraseContainer" style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px;"></div>\n    <textarea id="modalNote"'
    )
    text = text.replace(
        '<textarea id="returnResampleNote"',
        '<div id="returnResamplePhraseContainer" style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px; margin-top:4px;"></div>\n    <textarea id="returnResampleNote"'
    )

    # 3. Add logic in openJudge
    judge_logic = """
    const cfgStr = localStorage.getItem('HS_QC_DYNAMIC_OPTIONS');
    const phrasesStr = cfgStr ? (JSON.parse(cfgStr)['OPTIONS_PHRASES'] || '合格放行, 水分偏高, 金屬異常, 微粒超標, 外觀異常, 其他') : '合格放行, 水分偏高, 金屬異常, 微粒超標, 外觀異常, 其他';
    const phrases = phrasesStr.split(',').map(s=>s.trim()).filter(Boolean);
    const container = document.getElementById('modalPhraseContainer');
    if (container) {
      container.innerHTML = phrases.map(p => `<span class="phrase-tag" onclick="document.getElementById('modalNote').value = this.innerText">${p}</span>`).join('');
    }
    """
    if 'document.getElementById(\'modalPhraseContainer\')' not in text:
        text = text.replace(
            "document.getElementById('judgeModal').style.display = 'flex';",
            judge_logic + "\n    document.getElementById('judgeModal').style.display = 'flex';"
        )

    # 4. Add logic in openReturnResample
    resample_logic = """
    const cfgStr = localStorage.getItem('HS_QC_DYNAMIC_OPTIONS');
    const phrasesStr = cfgStr ? (JSON.parse(cfgStr)['OPTIONS_PHRASES'] || '合格放行, 水分偏高, 金屬異常, 微粒超標, 外觀異常, 其他') : '合格放行, 水分偏高, 金屬異常, 微粒超標, 外觀異常, 其他';
    const phrases = phrasesStr.split(',').map(s=>s.trim()).filter(Boolean).filter(p => p !== '合格放行');
    const container = document.getElementById('returnResamplePhraseContainer');
    if (container) {
      container.innerHTML = phrases.map(p => `<span class="phrase-tag" onclick="document.getElementById('returnResampleNote').value = this.innerText">${p}</span>`).join('');
    }
    """
    if 'document.getElementById(\'returnResamplePhraseContainer\')' not in text:
        text = text.replace(
            "document.getElementById('returnResampleModal').style.display = 'flex';",
            resample_logic + "\n    document.getElementById('returnResampleModal').style.display = 'flex';"
        )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

print("Patched index.html")

admin_path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\admin.html'
with open(admin_path, 'r', encoding='utf-8') as f:
    admin_text = f.read()

if "data['OPTIONS_PHRASES'] === undefined" not in admin_text:
    admin_text = admin_text.replace(
        "if (data['OPTIONS_GRADES'] === undefined)",
        "if (data['OPTIONS_PHRASES'] === undefined) data['OPTIONS_PHRASES'] = '合格放行, 水分偏高, 金屬異常, 微粒超標, 外觀異常, 其他';\n        if (data['OPTIONS_GRADES'] === undefined)"
    )

with open(admin_path, 'w', encoding='utf-8') as f:
    f.write(admin_text)

print("Patched admin.html")
