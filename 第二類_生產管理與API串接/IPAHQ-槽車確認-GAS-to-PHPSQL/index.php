<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>IPAHQ 槽車掃描核對 (混合輸入版)</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
  <style>
    body { font-family: sans-serif; background-color: #f0fdf4; -webkit-tap-highlight-color: transparent; }
    /* 移除 cursor: not-allowed，恢復一般輸入框樣式 */
    .input-box { width: 100%; padding: 12px; border: 2px solid #ccc; border-radius: 12px; font-size: 16px; background: white; transition: all 0.2s; }
    .valid-input { border-color: #22c55e !important; background-color: #f0fdf4 !important; color: #15803d; }
    .invalid-input { border-color: #ef4444 !important; background-color: #fef2f2 !important; color: #b91c1c; }
    .btn-scan-main { background-color: #5850ec; box-shadow: 0 4px #4338ca; color: white; border-radius: 12px; width: 56px; height: 52px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; cursor: pointer; }
    .btn-scan-sub { background-color: #0ea5e9; box-shadow: 0 4px #0284c7; color: white; border-radius: 12px; width: 56px; height: 52px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; cursor: pointer; }
    .btn-clear-single { background-color: #f3f4f6; color: #9ca3af; border-radius: 12px; width: 44px; height: 52px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    #camView { display: none; position: fixed; inset: 0; background: black; z-index: 9999; flex-direction: column; align-items: center; justify-content: center; }
    #reader { width: 100%; max-width: 400px; background: white; border-radius: 20px; overflow: hidden; }
  </style>
</head>
<body class="p-4 sm:p-6">
  <div class="max-w-md mx-auto bg-white p-6 rounded-3xl shadow-xl border border-gray-100">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-black text-green-800">IPAHQ 槽車核對</h2>
      <a href="history.php" class="text-sm text-blue-600 font-bold underline">歷史紀錄</a>
    </div>
    
    <form id="myForm" onsubmit="handleFormSubmit(event)">
      <div class="mb-5">
        <label class="block font-bold text-zinc-700 mb-2 text-sm">1. 三合一單 QR Code</label>
        <div class="flex gap-2">
          <input type="text" id="mainQr" class="input-box" placeholder="掃描或手動輸入..." oninput="validateAll()" onkeydown="handleManualNext(event, 'check1')" autocomplete="off">
          <button type="button" onclick="clearSingle('mainQr')" class="btn-clear-single">✕</button>
          <button type="button" onclick="triggerScan('mainQr', 'check1')" class="btn-scan-main text-xl">📷</button>
        </div>
      </div>

      <div class="mb-5">
        <label class="block font-bold text-zinc-700 mb-2 text-sm">2. 三合一單 槽號 (A)</label>
        <div class="flex gap-2">
          <input type="text" id="check1" class="input-box" placeholder="掃描或手動輸入..." oninput="validateAll()" onkeydown="handleManualNext(event, 'check2')" autocomplete="off">
          <button type="button" onclick="clearSingle('check1')" class="btn-clear-single">✕</button>
          <button type="button" onclick="triggerScan('check1', 'check2')" class="btn-scan-sub text-xl">📷</button>
        </div>
        <p id="msg1" class="text-xs mt-1 h-4 font-bold"></p>
      </div>

      <div class="mb-5">
        <label class="block font-bold text-zinc-700 mb-2 text-sm">3. 槽車實體條碼 (B)</label>
        <div class="flex gap-2">
          <input type="text" id="check2" class="input-box" placeholder="掃描或手動輸入..." oninput="validateAll()" onkeydown="handleManualNext(event, null)" autocomplete="off">
          <button type="button" onclick="clearSingle('check2')" class="btn-clear-single">✕</button>
          <button type="button" onclick="triggerScan('check2', null)" class="btn-scan-sub text-xl">📷</button>
        </div>
        <p id="msg2" class="text-xs mt-1 h-4 font-bold"></p>
      </div>

      <div class="mb-8 border-2 border-dashed border-zinc-300 p-5 rounded-2xl text-center bg-zinc-50 relative">
        <button type="button" onclick="clearPhoto()" id="btnDelPhoto" class="hidden absolute top-2 right-2 bg-white rounded-full w-8 h-8 shadow">✕</button>
        <input type="file" accept="image/*" capture="environment" id="cam" class="hidden" onchange="zipImg(this)">
        <button type="button" onclick="document.getElementById('cam').click()" class="text-green-700 font-bold flex flex-col items-center gap-1 mx-auto text-sm">
          <span>📷 4. 拍照存證 (選填)</span>
        </button>
        <div id="photoStatus" class="text-xs mt-2 text-zinc-400">選填照片</div>
        <img id="prev" class="mt-3 mx-auto hidden max-h-44 rounded-xl border-4 border-white shadow-lg">
        <input type="hidden" id="photoData">
      </div>

      <button type="submit" id="submitBtn" disabled class="w-full py-5 rounded-2xl text-zinc-400 font-bold text-xl bg-zinc-200 transition-all">等待核對中...</button>
    </form>
  </div>

  <div id="camView">
    <div id="reader"></div>
    <button type="button" onclick="forceStopScan()" class="mt-10 px-10 py-3 bg-white text-black rounded-full font-bold">取消</button>
  </div>

  <script>
    let html5QrScanner = null;
    
    function clearSingle(id) { 
        document.getElementById(id).value = ""; 
        document.getElementById(id).className = "input-box";
        validateAll(); 
        document.getElementById(id).focus(); 
    }
    
    function clearPhoto() { 
        document.getElementById('photoData').value = ""; 
        document.getElementById('prev').classList.add('hidden'); 
        document.getElementById('btnDelPhoto').classList.add('hidden'); 
        validateAll(); 
    }

    // --- 核心：手動輸入按 Enter 跳轉 ---
    function handleManualNext(event, nextId) {
        if (event.key === "Enter") {
            event.preventDefault(); // 防止表單直接送出
            if (nextId) {
                document.getElementById(nextId).focus();
            } else {
                document.activeElement.blur();
            }
        }
    }

    // --- 核心：相機掃描自動跳轉 ---
    async function triggerScan(targetId, nextId) {
      document.getElementById('camView').style.display = 'flex';
      html5QrScanner = new Html5Qrcode("reader");
      await html5QrScanner.start({ facingMode: "environment" }, { fps: 15, qrbox: 250 }, (text) => {
        document.getElementById(targetId).value = text.toUpperCase();
        forceStopScan(); 
        validateAll();
        if (nextId) document.getElementById(nextId).focus();
      }).catch(err => { alert("相機啟動失敗"); forceStopScan(); });
    }

    async function forceStopScan() {
      if (html5QrScanner) { try { await html5QrScanner.stop(); } catch(e){} html5QrScanner.clear(); html5QrScanner = null; }
      document.getElementById('camView').style.display = 'none';
    }

    function validateAll() {
      const main = document.getElementById('mainQr').value.trim().toUpperCase();
      const c1 = document.getElementById('check1').value.trim().toUpperCase();
      const c2 = document.getElementById('check2').value.trim().toUpperCase();
      const subBtn = document.getElementById('submitBtn');

      let v1 = (c1 && main.includes(c1));
      setUI('check1', 'msg1', v1 ? "✅ 通過" : "❌ 不在主單內", v1);
      
      let v2 = (c2 && v1 && c2 === c1);
      setUI('check2', 'msg2', v2 ? "✅ 核對一致" : "❌ 核對失敗", v2);

      const ok = main && v1 && v2;
      subBtn.disabled = !ok;
      subBtn.className = ok ? "w-full py-5 rounded-2xl text-white font-bold text-xl bg-green-600 shadow-lg cursor-pointer" : "w-full py-5 rounded-2xl text-zinc-400 font-bold text-xl bg-zinc-200";
      subBtn.innerText = ok ? "確認上傳資料" : "等待核對中...";
    }

    function setUI(id, msgId, txt, isValid) {
      document.getElementById(id).className = isValid ? "input-box valid-input" : "input-box invalid-input";
      document.getElementById(msgId).innerText = txt;
      document.getElementById(msgId).style.color = isValid ? "#15803d" : "#b91c1c";
    }

    function zipImg(el) {
      if (!el.files[0]) return;
      const fr = new FileReader();
      fr.onload = (e) => {
        const i = new Image(); i.src = e.target.result;
        i.onload = () => {
          const cvs = document.createElement('canvas');
          const maxW = 800;
          cvs.width = maxW; cvs.height = i.height * (maxW / i.width);
          cvs.getContext('2d').drawImage(i, 0, 0, cvs.width, cvs.height);
          document.getElementById('photoData').value = cvs.toDataURL('image/jpeg', 0.6);
          document.getElementById('prev').src = document.getElementById('photoData').value;
          document.getElementById('prev').classList.remove('hidden');
          document.getElementById('btnDelPhoto').classList.remove('hidden');
          document.getElementById('photoStatus').innerText = "✅ 照片已就緒";
          validateAll();
        }
      };
      fr.readAsDataURL(el.files[0]);
    }

    function handleFormSubmit(e) {
      e.preventDefault();
      const btn = document.getElementById('submitBtn');
      btn.innerText = "🚀 上傳中..."; btn.disabled = true;
      fetch('process.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mainQr: document.getElementById('mainQr').value,
          check1: document.getElementById('check1').value,
          check2: document.getElementById('check2').value,
          photoData: document.getElementById('photoData').value
        })
      }).then(res => res.json()).then(res => {
        alert(res.message);
        if(res.success) location.reload();
        else { btn.innerText = "重新上傳"; btn.disabled = false; }
      }).catch(err => alert("網路錯誤"));
    }
  </script>
</body>
</html>
