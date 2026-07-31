const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const rendersDir = path.join(__dirname, 'renders');
  if (!fs.existsSync(rendersDir)) {
    fs.mkdirSync(rendersDir, { recursive: true });
  }

  const browser = await chromium.launch({
    args: ['--autoplay-policy=no-user-gesture-required', '--mute-audio'],
  });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
    recordVideo: { 
      dir: rendersDir, 
      size: { width: 1920, height: 1080 } 
    },
  });
  const page = await context.newPage();
  
  const fileUrl = 'file:///' + path.join(__dirname, 'index.html').replace(/\\/g, '/') + '?render=true';
  console.log('Loading page:', fileUrl);
  
  await page.goto(fileUrl);
  await page.waitForTimeout(800); // 讓字型與圖片完成載入
  
  console.log('Recording 109 seconds...');
  await page.waitForTimeout(109000); // 107.7s 總片長 + 1.3s 結尾緩衝
  
  await context.close();
  await browser.close();
  console.log('Recording finished.');
})();
