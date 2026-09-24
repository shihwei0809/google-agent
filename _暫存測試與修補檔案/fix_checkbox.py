path = r'D:\GOOGLE ANGET\三合一單自動產生器\main.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

content = content.replace('text="☑ 全選所有列"', 'text="全選所有列"')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
