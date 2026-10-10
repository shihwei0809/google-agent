import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_js = '''} else {
          // 自訂流體'''
new_js = '''} else if (wire.type === 'solid') {
          // 純線條無方向
          strokeColor = wire.color || '#64748b';
          labelColor = wire.labelColor || strokeColor;
          marker = '';
          flowClass = '';
          strokeWidth = '2';
        } else {
          // 自訂流體'''

if old_js in content:
    content = content.replace(old_js, new_js)
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced solid in JS")
else:
    print("Not found js target")
