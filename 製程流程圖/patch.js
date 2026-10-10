const fs = require('fs');
let html = fs.readFileSync('public/index.html', 'utf8');

const targetText = '<text x="10" y="28" font-size="${fsize}" font-weight="600" fill="${txt}">${n.title}</text>';
const newText = '<text font-size="${fsize}" font-weight="600" fill="${txt}">\n                  ${(n.title||"").split("\\n").map((line, i) => `<tspan x="10" dy="${i===0 ? 20 : 16}">${line}</tspan>`).join("")}\n                </text>';

html = html.replace(targetText, newText);

const targetRect = '<rect x="0" y="0" width="130" height="50" rx="6" fill="${bg}" stroke="${bdr}" stroke-width="1.8" filter="drop-shadow(0 1px 2px rgba(0,0,0,0.06))" />';
const newRect = '<rect x="0" y="0" width="${Math.max(130, Math.max(...(n.title||\\"\\").split(\\"\\\\n\\").map(l=>l.length*(parseInt(fsize)||12))) + 20)}" height="${Math.max(50, (n.title||\\"\\").split(\\"\\\\n\\").length * ((parseInt(fsize)||12)+4) + 12)}" rx="6" fill="${bg}" stroke="${bdr}" stroke-width="1.8" filter="drop-shadow(0 1px 2px rgba(0,0,0,0.06))" />';

// Because of string escaping, let's just do it directly.
