export async function onRequestPost(context) {
  try {
    const data = await context.request.json();
    
    // 從 payload 取出資料，若無則給預設值
    const name = data.name || "未知";
    const timestamp = data.timestamp || new Date().toLocaleString('zh-TW');
    const score = data.score !== undefined ? data.score : 0;
    const correctCount = data.correctCount || 0;
    const total = data.total || 5;
    
    // 對應到可能送出的 5 題答案
    const q1 = data.q1 || "";
    const q2 = data.q2 || "";
    const q3 = data.q3 || "";
    const q4 = data.q4 || "";
    const q5 = data.q5 || "";

    // 寫入 D1 資料庫
    const stmt = context.env.DB.prepare(`
      INSERT INTO exam_records (timestamp, name, score, correctCount, total, q1, q2, q3, q4, q5)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(timestamp, name, score, correctCount, total, q1, q2, q3, q4, q5);

    await stmt.run();

    return new Response(JSON.stringify({ status: "ok", message: "Recorded to Cloudflare D1" }), {
      headers: { "Content-Type": "application/json" }
    });
  } catch (err) {
    return new Response(JSON.stringify({ status: "error", message: err.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
}
