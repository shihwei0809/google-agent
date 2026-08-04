// 用 Playwright Headless 錄製 index.html，輸出無音訊的 webm
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
  
  // 使用 ?render=true 啟用自動無遮罩渲染
  const fileUrl = 'file:///' + path.join(__dirname, 'index.html').replace(/\\/g, '/') + '?render=true&nosub=true';
  console.log('Loading page:', fileUrl);
  
  await page.goto(fileUrl);
  await page.waitForTimeout(500); // 讓字型與資源完成初始載入
  
  console.log('Recording 120 seconds...');
  await page.waitForTimeout(120000); // 118.8s 總片長 + 1.2s 結尾緩衝
  
  await context.close();
  await browser.close();
  console.log('Recording finished.');
})();
