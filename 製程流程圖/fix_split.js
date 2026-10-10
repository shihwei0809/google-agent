const fs = require('fs');
let html = fs.readFileSync('public/index.html', 'utf8');

// Replace all .split('\\n') with .split(/\r?\n/)
html = html.replace(/split\('\\\\n'\)/g, "split(/\\r?\\n/)");

// Improve the text width calculation (Chinese char is roughly full width, ascii is half)
// Instead of complex logic, just give a good approximation based on string length and ascii char counts.
const replaceWidth = 'Math.max(...(n.title||\'\').split(/\\r?\\n/).map(l => (l.replace(/[\\x00-\\xff]/g, \"\").length * (parseInt(fsize)||12) + (l.length - l.replace(/[\\x00-\\xff]/g, \"\").length) * (parseInt(fsize)*0.6||7)) + 20))';
html = html.replace(/Math\.max\(\.\.\.\(n\.title\|\|''\)\.split\(\/\\r\?\\n\/\)\.map\(l=>l\.length\*\([^)]+\)\)\) \+ 20/g, replaceWidth);

fs.writeFileSync('public/index.html', html, 'utf8');
console.log("Replaced");
