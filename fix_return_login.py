path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Adaptive
old_ret = "${s.qcResult === 'FAIL' ? `<button onclick=\"openReturnResample('${s.id}')\""
new_ret = "${s.qcResult === 'FAIL' && loggedInUser ? `<button onclick=\"openReturnResample('${s.id}')\""
text = text.replace(old_ret, new_ret)

# Traditional
old_ret2 = "${s.qcResult === 'FAIL' ? `<br><button onclick=\"openReturnResample('${s.id}')\""
new_ret2 = "${s.qcResult === 'FAIL' && loggedInUser ? `<br><button onclick=\"openReturnResample('${s.id}')\""
text = text.replace(old_ret2, new_ret2)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
