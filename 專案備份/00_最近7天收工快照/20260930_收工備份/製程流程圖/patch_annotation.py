import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace annotation_card render text
pattern = r'<text x="10" y="28" font-size="\$\{fsize\}" font-weight="600" fill="\$\{txt\}">\$\{n\.title\}</text>'
replacement = """<text font-size="${fsize}" font-weight="600" fill="${txt}">
                  ${(n.title||'').split('\\n').map((line, i) => `<tspan x="10" dy="${i===0 ? 20 : 16}">${line}</tspan>`).join('')}
                </text>"""

content = content.replace(pattern, replacement)

# We should also adjust the height of the annotation card based on the number of lines.
# But for now, we'll just allow it to overflow or be resized. Wait, the rect is fixed width="130" height="50"
# Let's make the rect height dynamic!
rect_pattern = r'<rect x="0" y="0" width="130" height="50" rx="6" fill="\$\{bg\}" stroke="\$\{bdr\}" stroke-width="1.8" filter="drop-shadow\(0 1px 2px rgba\(0,0,0,0\.06\)\)" />'
rect_replacement = """<rect x="0" y="0" width="${Math.max(130, Math.max(...(n.title||'').split('\\n').map(l=>l.length*12)) + 20)}" height="${Math.max(50, (n.title||'').split('\\n').length * 16 + 12)}" rx="6" fill="${bg}" stroke="${bdr}" stroke-width="1.8" filter="drop-shadow(0 1px 2px rgba(0,0,0,0.06))" />"""

content = content.replace(rect_pattern, rect_replacement)


with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Annotation fixed!")
