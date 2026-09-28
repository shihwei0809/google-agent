const {execSync} = require('child_process');
const fs = require('fs');
const cwd = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠';
const hashes = ['ba12d9a', 'c3ef37c', '9de9434'];

for (const h of hashes) {
  try {
    // use escaped octal path
    const cmd = `git show ${h}:"第二類_生產管理與API串接/QC-系統客製化電子化工廠/1_Web_網頁版/Index.html"`;
    const out = execSync(cmd, {cwd, encoding:'buffer'});
    const str = out.toString('utf8');
    const bad = str.match(/[\ue000-\uf8ff]/g);
    console.log(h, 'PUA:', bad ? bad.length : 0, 'size:', out.length);
    if (!bad) {
      // Write this clean version to disk
      fs.writeFileSync(cwd + '/1_Web_網頁版/index.html', out);
      console.log('  -> Written to 1_Web_網頁版/index.html');
      break;
    }
  } catch(e) { console.log(h, 'ERROR:', e.message.substring(0, 80)); }
}
