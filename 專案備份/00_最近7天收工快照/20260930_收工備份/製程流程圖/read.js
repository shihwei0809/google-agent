const fs = require('fs');
let html = fs.readFileSync('public/index.html', 'utf8');
let idx = html.indexOf('data-type="custom_block"');
console.log(html.substring(idx - 100, idx + 300));
