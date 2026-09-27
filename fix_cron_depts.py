path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
old_depts = """      const deptsWebhooks = {
        '資材課': configMap['TEAMS_WEBHOOK_資材課'],
        '現場一課': configMap['TEAMS_WEBHOOK_現場一課'],
        '現場二課': configMap['TEAMS_WEBHOOK_現場二課'],
        '二部一課': configMap['TEAMS_WEBHOOK_二部一課'],
        '二部二課': configMap['TEAMS_WEBHOOK_二部二課'],
        '回收處理課': configMap['TEAMS_WEBHOOK_回收處理課']
      };"""

text = text.replace(old_depts, "      // deptsWebhooks dynamically resolved via TEAMS_WEBHOOK_ + dept")
text = text.replace("if (s.dept && deptsWebhooks[s.dept]) urls.push(deptsWebhooks[s.dept]);", "if (s.dept && configMap['TEAMS_WEBHOOK_' + s.dept]) urls.push(configMap['TEAMS_WEBHOOK_' + s.dept]);")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
