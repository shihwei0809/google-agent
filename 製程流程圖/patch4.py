import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r"(\} else \{\n\s*// [^\n]*\n\s*strokeColor = wire\.color \|\| '#334155';)"
replacement = r"} else if (wire.type === 'solid') {\n          strokeColor = wire.color || '#64748b';\n          labelColor = wire.labelColor || strokeColor;\n          marker = '';\n          flowClass = '';\n          strokeWidth = '2';\n        \1"

content = re.sub(pattern, replacement, content)

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("regex applied for renderWires solid")
