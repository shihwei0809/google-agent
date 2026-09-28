import os

for folder in ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Fix cData filtering so failed items appear in the completed list
    text = text.replace(
        "let cData = filtered.filter(s => s.status === 'completed');",
        "let cData = filtered.filter(s => s.status === 'completed' || s.status === 'failed');"
    )

    # 2. Fix buildT100Option status mapping (replace getOrderSubmissionInfo display logic)
    text = text.replace(
        "const mark = sub ? (sub.status === 'completed' ? '✅[已驗合格] ' : '✅[已送樣待驗] ') : '⏳[待送樣] ';\n",
        "let mark = '⏳[待送樣] ';\n          if (sub) {\n            if (sub.status === 'completed') mark = '✅[已驗合格] ';\n            else if (sub.status === 'failed') mark = '⛔[被退件需重送] ';\n            else mark = '✅[已送樣待驗] ';\n          }\n"
    )
    
    # 3. Make sure global history render handles failed correctly
    text = text.replace(
        "else if (s.status === 'completed' && s.qcResult === 'PASS') statusBadge = `<span style=\"background:#d1fae5; color:#065f46; padding:2px 6px; border-radius:4px; font-size:0.8rem;\">合格(PASS)</span>`;",
        "else if ((s.status === 'completed' || s.status === 'failed') && (s.qcResult === 'PASS' || s.qcResult === 'FAIL')) statusBadge = `<span style=\"background:${s.qcResult==='PASS'?'#d1fae5':'#fee2e2'}; color:${s.qcResult==='PASS'?'#065f46':'#b91c1c'}; padding:2px 6px; border-radius:4px; font-size:0.8rem;\">${s.qcResult==='PASS'?'合格(PASS)':'退回(FAIL)'}</span>`;"
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

print("Patched cData and T100 mark")
