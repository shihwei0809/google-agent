import re

file_path = 'C:/GOOGLE ANGET/IPAHQ排程/public/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the specific table header for the dashboard
old_th = '<th>司機代碼</th>\n                <th>操作</th>'
new_th = '<th>司機代碼</th>\n                <th>三合一單</th>\n                <th>操作</th>'

if old_th in html:
    html = html.replace(old_th, new_th)
    print("Dashboard table header updated.")
else:
    print("Could not find the exact string. Using regex fallback.")
    html = re.sub(r'(<th>司機代碼</th>\s*<th>操作</th>)', r'<th>司機代碼</th>\n                <th>三合一單</th>\n                <th>操作</th>', html)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
