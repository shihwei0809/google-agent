path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Add the remark field after requester
new_field = '''        </div>
        <div>
          <label>備註 (選填)</label>
          <input type="text" id="remark" placeholder="如果有特殊狀況請填寫...">
        </div>
      </div>'''
text = re.sub(r'</div>\s*</div>\s*<button type="button" id="submitBtn"', new_field + '\n      <button type="button" id="submitBtn"', text)

# Add remark to submitForm
text = re.sub(
    r'const dept = document.getElementById\(\'dept\'\).value;',
    r"const dept = document.getElementById('dept').value;\n    const remark = document.getElementById('remark')?.value?.trim() || '';",
    text
)

text = re.sub(
    r'requester: requester,',
    r'requester: requester,\n      remark: remark,',
    text
)

# Add remark to Teams Webhook cardPayload (if I can find it)
# wait, cardPayload has text block. Let's just append it to the text.
text = re.sub(
    r'送樣人員：\$\{requester\}',
    r'送樣人員：${requester}\n備註：${remark||"無"}',
    text
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
