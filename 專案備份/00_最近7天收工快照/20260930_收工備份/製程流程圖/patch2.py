import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'(<option value="custom">.*?</option>)', r'\1\n            <option value="solid">純線條無方向 (Solid Line)</option>', content)

pattern = r"(} else if \(wire\.type === 'custom'\) \{.*?\n\s*\})"
replacement = r"\1 else if (wire.type === 'solid') {\n          strokeColor = wire.color || '#64748b';\n          labelColor = wire.labelColor || strokeColor;\n          marker = '';\n          flowClass = '';\n          strokeWidth = '2';\n        }"
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Regex patch applied")
