const fs = require('fs');
const {execSync} = require('child_process');

// git show ba12d9a for 1_Web_網頁版 - write to temp file first
execSync('git show ba12d9a:"第二類_生產管理與API串接/QC-系統客製化電子化工廠/1_Web_網頁版/index.html" > clean_1web.html', {
  cwd:'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠',
  shell: 'cmd.exe'
});

const content = fs.readFileSync('C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/clean_1web.html');
const bad = content.toString('utf8').match(/[\ue000-\uf8ff]/g);
console.log('PUA in clean_1web.html:', bad ? bad.length : 0);
console.log('File size:', content.length);
