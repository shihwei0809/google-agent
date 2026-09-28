path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

skip_fn = """
  function skipSample() {
    let barcode = document.getElementById('barcode').value.trim();
    const productName = document.getElementById('productName').value.trim();
    const tankNo = document.getElementById('tankNo').value.trim();
    const customer = document.getElementById('customer').value.trim();
    const requester = document.getElementById('requester').value.trim();
    const dept = document.getElementById('dept').value;
    const remark = document.getElementById('remark')?.value?.trim() || '';

    if (!productName || !tankNo || !customer || !requester) {
      alert("⚠️ 請先將上方的基本資料填妥！");
      return; 
    }

    if (!barcode) {
      const todayStr = new Date().toISOString().split('T')[0].replace(/-/g, '');
      barcode = `${todayStr}-庫存`;
    }

    if(!confirm("確定要將此筆排程標記為「免送樣」直接結案嗎？\\n(結案後將不會出現在待檢驗清單)")) return;

    const btn = document.getElementById('skipBtn'); 
    btn.disabled = true; 
    btn.innerText = "寫入結案紀錄中...";
    
    const payload = { 
      id: 'ID-' + Date.now(),
      barcode: barcode, 
      flowType: document.getElementById('flowType').value, 
      grade: document.getElementById('grade').value,
      productName: productName, 
      tankNo: tankNo, 
      customer: customer, 
      quantity: document.getElementById('quantity').value, 
      dept: dept, 
      requester: requester,
      remark: remark,
      status: 'completed',
      qcResult: '免送樣',
      qcNote: '預先充填出貨，免送樣結案',
      qcApprover: '系統自動',
      createdAt: new Date().toISOString(),
      completedAt: new Date(new Date().getTime() + 8*60*60*1000).toISOString().replace('T', ' ').substring(0, 19)
    };

    fetch(GAS_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify({ action: 'createSample', payload: payload })
    })
    .then(res => res.json())
    .then(res => {
      resetForm();
      btn.disabled = false;
      btn.innerText = "直接結案 (免送樣)";
      if(res.success) {
        showToast("✅ 免送樣結案成功！已從排程中移除。");
        load();
      } else {
        alert("失敗：" + res.error);
      }
    })
    .catch(err => {
      btn.disabled = false;
      btn.innerText = "直接結案 (免送樣)";
      alert("雲端連線失敗：" + err.message);
    });
  }
"""

text = text.replace('  function getWaitTimeBadge(createdAt) {', skip_fn + '\n  function getWaitTimeBadge(createdAt) {')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
