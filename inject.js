const fs = require('fs');
const path = 'C:\\GOOGLE ANGET\\第二類_生產管理與API串接\\QC-系統客製化電子化工廠\\3_Cloudflare_D1版\\index.html';
let html = fs.readFileSync(path, 'utf8');

const marqueeCode = \
  // 動態提示字跑馬燈
  function startPlaceholderMarquee(elementId, originalText) {
    const el = document.getElementById(elementId);
    if (!el) return;
    let text = originalText + '   '; 
    setInterval(() => {
      text = text.substring(1) + text[0];
      el.setAttribute('placeholder', text);
    }, 400); 
  }
  document.addEventListener('DOMContentLoaded', () => {
    startPlaceholderMarquee('empIdInput', '掃描或輸入工號... ');
    startPlaceholderMarquee('requester', '姓名（工號查到後會自動填入）... ');
  });
\;

html = html.replace('</script>', marqueeCode + '\n</script>');
fs.writeFileSync(path, html, 'utf8');
console.log('Success');
