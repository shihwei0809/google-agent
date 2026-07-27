const path = require("node:path");
const fs = require("node:fs");
const { chromium } = require("playwright");

const root = __dirname;
const url = `file://${path.join(root, "index.html").replace(/\\/g, "/")}?render=true`;
const out = path.join(root, "renders", "video.webm");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
    recordVideo: {
      dir: path.join(root, "renders"),
      size: { width: 1920, height: 1080 },
    },
  });
  const page = await context.newPage();
  await page.goto(url);
  await page.waitForFunction(() => window.__VIDEO_DONE__ === true, null, { timeout: 90000 });
  const video = page.video();
  await page.close();
  await context.close();
  await browser.close();
  const tempPath = await video.path();
  if (fs.existsSync(out)) fs.unlinkSync(out);
  fs.renameSync(tempPath, out);
  console.log(out);
})();
