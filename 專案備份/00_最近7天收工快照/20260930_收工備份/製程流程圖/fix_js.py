import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

broken_block = """        render: (n) => {
          const bg = n.bgColor || '#ffffff';
          const img = n.imageUrl ? <image href=" + n.imageUrl + " x="5" y="5" width="90" height="90" preserveAspectRatio="xMidYMid meet" /> : '';
          const textY = n.imageUrl ? 115 : 55;
          return <g>
            <rect x="0" y="0" width="100" height="100" rx="8" fill=" + bg + " stroke="#1e293b" stroke-width="2.5" />
             + img + 
            <text x="50" y=" + textY + " font-size="12" font-weight="bold" fill="#1e293b" text-anchor="middle"> + n.title + </text>
            <text x="50" y=" + (textY + 16) + " font-size="10" fill="#64748b" text-anchor="middle"> + (n.tag || '') + </text>
          </g>;
        }"""

fixed_block = """        render: (n) => {
          const bg = n.bgColor || '#ffffff';
          const img = n.imageUrl ? `<image href="${n.imageUrl}" x="5" y="5" width="90" height="90" preserveAspectRatio="xMidYMid meet" />` : '';
          const textY = n.imageUrl ? 115 : 55;
          return `<g>
            <rect x="0" y="0" width="100" height="100" rx="8" fill="${bg}" stroke="#1e293b" stroke-width="2.5" />
            ${img}
            <text x="50" y="${textY}" font-size="12" font-weight="bold" fill="#1e293b" text-anchor="middle">${n.title}</text>
            <text x="50" y="${textY + 16}" font-size="10" fill="#64748b" text-anchor="middle">${n.tag || ''}</text>
          </g>`;
        }"""

if broken_block in content:
    content = content.replace(broken_block, fixed_block)
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Broken block not found. Trying regex.")
    
