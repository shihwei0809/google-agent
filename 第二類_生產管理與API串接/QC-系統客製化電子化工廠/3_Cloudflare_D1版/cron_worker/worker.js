// QC 系統超時檢驗 24/7 背景排程 Worker (Cloudflare Worker)
// 觸發頻率: 每 5 分鐘一次 (Cron: */5 * * * *)
// 功能: 定時向 https://qc-samples.pages.dev/api?action=checkOverdue 發送請求，
//       無需任何人開啟網頁，即時偵測樣品是否超過 2 小時 / 4 小時未判定並推送 Teams 警報。

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

addEventListener('scheduled', event => {
  event.waitUntil(handleScheduled(event));
});

async function runCheck() {
  const url = 'https://qc-samples.pages.dev/api?action=checkOverdue';
  const res = await fetch(url, {
    method: 'GET',
    headers: {
      'User-Agent': 'QC-Cron-Scheduler/1.0',
      'Cache-Control': 'no-cache'
    }
  });
  return await res.text();
}

async function handleRequest(request) {
  try {
    const data = await runCheck();
    return new Response(data, {
      status: 200,
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*'
      }
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

async function handleScheduled(event) {
  try {
    const data = await runCheck();
    console.log('[QC Cron Trigger] Completed successfully:', data);
  } catch (err) {
    console.error('[QC Cron Trigger] Failed:', err);
  }
}
