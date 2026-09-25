export async function onRequestPost(context) {
  const { request, env } = context;
  try {
    const body = await request.json();
    const GAS_API_URL = "https://script.google.com/macros/s/AKfycbyJNqo25ny2IiwajeltMlSi1M8PnVonczlLA2UoEoxZYGSE72tiWTEJ61Y_wQhPU0H5/exec";

    // 1. 呼叫 GOOGLE APPS SCRIPT 進行 AI 辨識與邏輯核對
    const gasResponse = await fetch(GAS_API_URL, {
      method: 'POST',
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify(body)
    });
    
    const gasResult = await gasResponse.json();

    // 2. 如果動作是核對表單，且 GAS 判定核對成功，再寫入 D1 (雙寫入)
    if (body.action === "processFormAndVerify" && gasResult.success) {
      const stmt = env.DB.prepare(`
        INSERT INTO verifications (
          material_no, tank_no, batch_no, supplier, original_location, 
          raw_qr, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
      `).bind(
        body.formObject.materialNo || "", body.formObject.tankNo || "", body.formObject.batchNo || "", 
        body.formObject.supplier || "", body.formObject.deliveryPlace || "", 
        body.formObject.rawQr || "", "核對成功"
      );
      // 背景寫入 D1，不阻擋前台速度
      context.waitUntil(stmt.run().catch(e => console.error("D1 Write Error:", e)));
    }

    // 3. 將 Google 的核對結果原封不動回傳給前台
    return new Response(JSON.stringify(gasResult), { headers: { "Content-Type": "application/json" } });

  } catch (e) {
    return new Response(JSON.stringify({ success: false, message: e.toString() }), { 
      status: 500, 
      headers: { "Content-Type": "application/json" } 
    });
  }
}
