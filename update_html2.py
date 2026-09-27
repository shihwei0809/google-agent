path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
text = re.sub(
    r'\$\{s\.qcNote \? `<div style="font-size:0\.82rem; color:#475569; margin-top:4px; background:#f1f5f9; padding:4px 8px; border-radius:4px;"><b>備註：</b>\$\{s\.qcNote\}</div>` : \'\'\}',
    r'${s.remark ? `<div style="font-size:0.82rem; color:#475569; margin-top:4px;"><b>送樣備註：</b>${s.remark}</div>` : \'\'}\n          ${s.qcNote ? `<div style="font-size:0.82rem; color:#475569; margin-top:4px; background:#f1f5f9; padding:4px 8px; border-radius:4px;"><b>判定備註：</b>${s.qcNote}</div>` : \'\'}',
    text
)

text = re.sub(
    r'\[人員: \$\{s\.requester\}\]',
    r'[人員: ${s.requester}]${s.remark ? ` [備註: ${s.remark}]` : ""}',
    text
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
