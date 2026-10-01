import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add solid option
old_select = '<option value="custom">自訂流體管線 (Custom)</option>'
new_select = '<option value="custom">自訂流體管線 (Custom)</option>\n            <option value="solid">純線條無方向 (Solid Line)</option>'
if old_select in content:
    content = content.replace(old_select, new_select)
else:
    print("Could not find old_select")

# Update renderWires logic
old_js = '''} else if (wire.type === 'custom') {
          strokeColor = wire.color || '#334155';
          labelColor = wire.labelColor || strokeColor;
          marker = 'url(#arrow-custom)';
          if (state.globalAnim && wire.animated !== false) {
            flowClass = 'flow-liquid-pulse';
          }
        }'''
new_js = '''} else if (wire.type === 'custom') {
          strokeColor = wire.color || '#334155';
          labelColor = wire.labelColor || strokeColor;
          marker = 'url(#arrow-custom)';
          if (state.globalAnim && wire.animated !== false) {
            flowClass = 'flow-liquid-pulse';
          }
        } else if (wire.type === 'solid') {
          strokeColor = wire.color || '#64748b';
          labelColor = wire.labelColor || strokeColor;
          marker = '';
          flowClass = '';
        }'''
if old_js in content:
    content = content.replace(old_js, new_js)
else:
    print("Could not find old_js")

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated public/index.html")
