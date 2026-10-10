const fs = require('fs');
let html = fs.readFileSync('public/index.html', 'utf8');

const regex = /<text x="10" y="28" font-size="\$\{fsize\}" font-weight="600" fill="\$\{txt\}">\$\{n\.title\}<\/text>/g;
const replace = `<text x="10" font-size="${fsize}" font-weight="600" fill="${txt}">
                  ${(n.title||'').split('\\n').map((line, i) => \`<tspan x="10" dy="\${i===0 ? 20 : 18}">\${line}</tspan>\`).join('')}
                </text>`;

// Wait, doing this via regex might have string interpolation escaping issues. 
// Let's do it cleanly by searching the exact block.
