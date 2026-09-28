import os
for folder in ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Adaptive mode Judge button
    text = text.replace(
        "${loggedInUser ? `<button class=\"btn-action btn-judge\" onclick=\"openJudge('${s.id}')\" style=\"width:100%; padding:4px 0; font-size:0.75rem; margin:0;\">判定</button>` : `<div style=\"text-align:center; color:#94a3b8; font-size:0.75rem; margin-top:8px; border: 1px dashed #cbd5e1; border-radius: 4px; padding: 2px;\">登入後判定</div>`}",
        "<button class=\"btn-action btn-judge\" onclick=\"openJudge('${s.id}')\" style=\"width:100%; padding:4px 0; font-size:0.75rem; margin:0;\">判定</button>"
    )
    # Adaptive mode Resample button
    text = text.replace(
        "${s.qcResult === 'FAIL' && loggedInUser ? `<button onclick=\"openReturnResample('${s.id}')\" style=\"font-size:0.7rem; background:#f97316; color:white; border:none; border-radius:6px; padding:3px 8px; cursor:pointer; width:100%;\">↩️ 退回重新送樣</button>` : ''}",
        "${s.qcResult === 'FAIL' ? `<button onclick=\"openReturnResample('${s.id}')\" style=\"font-size:0.7rem; background:#f97316; color:white; border:none; border-radius:6px; padding:3px 8px; cursor:pointer; width:100%;\">↩️ 退回重新送樣</button>` : ''}"
    )

    # Full mode Judge button
    text = text.replace(
        "${loggedInUser ? `<button class=\"btn-action btn-judge\" onclick=\"openJudge('${s.id}')\">判定</button>` : `<div style=\"text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:5px; border: 1px dashed #cbd5e1; border-radius: 4px; padding: 2px;\">登入後判定</div>`}",
        "<button class=\"btn-action btn-judge\" onclick=\"openJudge('${s.id}')\">判定</button>"
    )
    # Full mode Resample button
    text = text.replace(
        "${s.qcResult === 'FAIL' && loggedInUser ? `<br><button onclick=\"openReturnResample('${s.id}')\" style=\"font-size:0.7rem; background:#f97316; color:white; border:none; border-radius:6px; padding:2px 8px; cursor:pointer; margin-top:3px;\">↩️ 退回重新送樣</button>` : ''}",
        "${s.qcResult === 'FAIL' ? `<br><button onclick=\"openReturnResample('${s.id}')\" style=\"font-size:0.7rem; background:#f97316; color:white; border:none; border-radius:6px; padding:2px 8px; cursor:pointer; margin-top:3px;\">↩️ 退回重新送樣</button>` : ''}"
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
print("Patched button visibility")
