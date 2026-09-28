const fs = require('fs');
const html = fs.readFileSync('C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/3_Cloudflare_D1版/index.html', 'utf8');

const idx = html.indexOf("FilterMode === 'resample'");
if (idx >= 0) {
  console.log('resample filter found:');
  console.log(html.substring(idx-10, idx+400));
} else {
  console.log('NOT FOUND');
}
