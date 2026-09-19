import sys
import codecs
import re

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

with open('static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Make statusBox clear after 3s when generating ZIP
content = re.sub(
    r'statusBox\.innerText = `✅ 產生成功！.*?`;',
    'statusBox.innerText = `✅ 產生成功！請檢查伺服器所在的資料夾。`;\\n                setTimeout(() => { statusBox.innerText = "等待操作..."; }, 3000);',
    content
)

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
