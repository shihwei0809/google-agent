<?php
// index.php
// 🟢 前端最終版 V9：
// 1. 【架構升級】徹底捨棄 radio input，改用純 div 與 data-mode 屬性控制分頁，100% 根除手機點擊失效與卡死問題。
// 2. 採用「訊號冷卻偵測」自動跳格 (防中文輸入法干擾)
// 3. 修正四合一垂直排列
// 4. 包含 AZ 出貨地
// 5. 鎖定螢幕鍵盤 (inputmode="none")

if (isset($_GET['page']) && $_GET['page'] === 'query') {
    include 'query_view.php'; 
    exit;
}
?>
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>N系列BARCODE現場作業檢點</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
    <style>
      body { font-family: 'Noto Sans TC', sans-serif; background-color: #f0f2f5; padding: 10px; margin: 0; color: #444; }
      .container { max-width: 600px; margin: 0 auto; padding-bottom: 120px; }
      h3 { text-align: center; color: #1a73e8; margin-bottom: 15px; font-weight: 700; font-size: 20px; }
      
      .top-control-bar { margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
      .mode-switch { display: flex; gap: 5px; width: 100%; justify-content: space-between; }
      
      /* 按鈕樣式 (已改為純 div) */
      .mode-option { background: white; padding: 10px 2px; border: 1px solid #dadce0; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: bold; color: #5f6368; flex: 1; text-align: center; height: 50px; display: flex; align-items: center; justify-content: center; flex-direction: column; user-select: none; }
      .mode-option.active { border: 2px solid #1a73e8; background: #e8f0fe; color: #1a73e8; }
      
      .select-wrapper, .qty-wrapper { display: flex; align-items: center; gap: 5px; font-size: 14px; font-weight: bold; }
      select { padding: 8px; border-radius: 6px; border: 1px solid #ccc; font-size: 14px; }

      .card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 15px; border-left: 5px solid #ccc; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
      .c-blue { border-left-color: #1a73e8; }
      .c-green { border-left-color: #1e8e3e; }
      .card-title { font-weight: bold; margin-bottom: 10px; display: flex; align-items: center; gap: 5px; font-size: 15px; }
      
      .input-group { display: flex; flex-direction: column; width: 100%; margin-bottom:10px;}
      .input-group label { font-size: 12px; color: #5f6368; margin-bottom: 4px; }
      .input-wrapper { position: relative; display: flex; align-items: center; width: 100%; }
      
      .input-wrapper input { 
          width: 100%; padding: 12px 75px 12px 12px; 
          border: 1px solid #dadce0; border-radius: 8px; 
          height: 48px; box-sizing: border-box; font-size: 16px; 
          caret-color: transparent; 
      }
      .input-wrapper input:focus { border-color: #1a73e8; outline: none; background: #fff; }
      
      .action-icons { position: absolute; right: 6px; display: flex; gap: 6px; }
      .icon-btn { cursor: pointer; border-radius: 6px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: #f1f3f4; color: #5f6368; }
      
      .az-zone {
          border: 2px dashed #fbbc04;
          background-color: #fffcf5;
          padding: 10px;
          margin: 10px 0;
          border-radius: 8px;
          display: none; 
      }
      .az-zone label { color: #c5221f !important; font-weight: bold; }
      .az-zone input { border-color: #fbbc04; }

      .btn-check { width: 100%; padding: 15px; background: #1a73e8; color: white; border: none; border-radius: 8px; margin-top: 10px; font-size: 18px; font-weight: bold; cursor: pointer; }
      .btn-check:active { background: #1557b0; }
      
      #reader-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 9999; display: none; align-items: center; justify-content: center; flex-direction: column; }
      #reader { width: 90%; max-width: 500px; }
      
      #result { position: fixed; bottom: 20px; left: 5%; right: 5%; padding: 15px; background: #fff; border: 1px solid #ccc; display: none; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 1000; cursor: pointer; }
      .success { background: #e6f4ea; color: #137333; border-color: #ceead6; }
      .error { background: #fce8e6; color: #c5221f; border-color: #fad2cf; font-weight: bold; }
      
      .link-bar { text-align: right; margin-bottom: 10px; }
      .link-btn { text-decoration: none; background: #e8f0fe; color: #1a73e8; padding: 6px 12px; border-radius: 20px; font-weight: bold; font-size: 13px; }
    </style>
  </head>
  <body onload="initPage()">
    <div id="reader-modal"><div id="reader"></div><button onclick="stopScanner()" style="margin-top:20px;padding:10px 30px;font-size:16px;">關閉掃描</button></div>

    <div class="container">
      <h3>🔍 N系列BARCODE現場作業檢點</h3>
      
      <div class="link-bar">
        <a href="?page=query" class="link-btn">📊 查詢出貨紀錄</a>
      </div>

      <div class="top-control-bar">
         <div class="mode-switch">
           <div class="mode-option active" id="opt-full" data-mode="field_full"><span>整板</span></div>
           <div class="mode-option" id="opt-az" data-mode="field_az"><span>AZ</span></div>
           <div class="mode-option" id="opt-loose" data-mode="field_loose"><span>散桶</span></div>
         </div>
         
         <div class="select-wrapper">
           <span>場所:</span>
           <select id="workLocation" onchange="saveLocation()"><option value="本廠">本廠</option><option value="崙尾一廠">崙尾一廠</option><option value="彰濱一廠">彰濱一廠</option></select>
         </div>

         <div class="qty-wrapper" id="qty-wrapper" style="display:none">
           <span>數量:</span>
           <select id="barrelCount" onchange="updateLayout()"><option value="1">1</option><option value="2">2</option><option value="3">3</option></select>
         </div>
      </div>

      <script>
        function createInput(label, id, placeholder, wrapperId) {
          var wrapAttr = wrapperId ? `id="${wrapperId}"` : '';
          return `<div class="input-group" ${wrapAttr}>
                    <label>${label}</label>
                    <div class="input-wrapper">
                      <input type="text" id="${id}" placeholder="${placeholder}" 
                             inputmode="none" autocomplete="off"
                             onfocus="$('#result').fadeOut(200)" 
                             onclick="$('#result').fadeOut(200)">
                      <div class="action-icons">
                        <div class="icon-btn" onclick="startScanner('${id}')">📷</div>
                        <div class="icon-btn" onclick="clearOne('${id}')">✕</div>
                      </div>
                    </div>
                  </div>`;
        }
      </script>

      <div class="card" style="border-left: 5px solid #fbbc04;">
        <div class="card-title">📦 1. 料號+效期條碼</div>
        <script>document.write(createInput('料號+效期條碼','f_box','掃描長條碼'));</script>
      </div>

      <div class="card c-blue">
        <div class="card-title">🛢️ 2. 現場作業桶槽</div>
        
        <script>document.write(createInput('桶1 批號','f0','掃描QR'));</script>
        
        <div id="zone-az-dest" class="az-zone">
             <script>document.write(createInput('📍 出貨地 (限AZ)','f_az_dest','掃描出貨地 310651601', 'wrap-az-dest'));</script>
        </div>

        <script>document.write(createInput('桶1 料號','f1','掃描貼紙'));</script>

        <div id="row-tank-2">
            <script>document.write(createInput('桶2 批號','f2','掃描QR'));</script>
            <script>document.write(createInput('桶2 料號','f3','掃描貼紙'));</script>
        </div>
        <div id="row-tank-3">
            <script>document.write(createInput('桶3 批號','f4','掃描QR'));</script>
            <script>document.write(createInput('桶3 料號','f5','掃描貼紙'));</script>
        </div>
        <div id="row-tank-4">
            <script>document.write(createInput('桶4 批號','f6','掃描QR'));</script>
            <script>document.write(createInput('桶4 料號','f7','掃描貼紙'));</script>
        </div>
      </div>

      <div class="card c-green" id="card-master">
        <div class="card-title">🧩 3. 四合一標籤</div>
        <script>document.write(createInput('四合一 料號','f8','掃描'));</script>
        <script>document.write(createInput('4in1 批號1','f9','掃描'));</script>
        <script>document.write(createInput('4in1 批號2','f10','掃描', 'wrap-batch-2'));</script>
        <script>document.write(createInput('4in1 批號3','f11','掃描', 'wrap-batch-3'));</script>
        <script>document.write(createInput('4in1 批號4','f12','掃描', 'wrap-batch-4'));</script>
      </div>

      <button class="btn-check" onclick="handleSubmit()">🚀 巡檢核對並存檔</button>
      <button class="btn-clear" onclick="manualClear()" style="width:100%;margin-top:10px;background:none;border:none;color:#666;">清空重掃</button>
    </div>
    
    <div id="result" onclick="$(this).fadeOut(200)"></div>

    <script>
      var currentMode = 'field_full';
      var html5QrCode;
      var currentInputId = '';
      var scanTimer; 
      
      function initPage() { 
          // 🟢 監聽純 DIV 按鈕點擊事件，抓取自訂的 data-mode 屬性
          $('.mode-option').on('click', function() { 
              var selectedMode = $(this).attr('data-mode');
              if (selectedMode) {
                  setMode(selectedMode); 
              }
          });

          var savedLoc = localStorage.getItem('savedLocation');
          if(savedLoc) document.getElementById('workLocation').value = savedLoc;
          setMode('field_full'); // 初始化預設為整板
          
          // 訊號冷卻偵測 (自動跳格防呆)
          $(document).on('input', 'input[type="text"]', function(e) {
              var $this = $(this);
              clearTimeout(scanTimer);
              scanTimer = setTimeout(function() {
                  if($this.val().length > 0) {
                      var $inputs = $('input[type="text"]:visible'); 
                      var idx = $inputs.index($this); 
                      
                      if (idx < $inputs.length - 1) {
                          var $next = $inputs.eq(idx + 1);
                          $next.focus();
                          $next.select(); 
                      } else {
                          $this.blur(); 
                      }
                  }
              }, 200); 
          });
      }
      
      function setMode(mode) {
         currentMode = mode;
         // UI 切換
         $('.mode-option').removeClass('active');
         if(mode === 'field_full') $('#opt-full').addClass('active');
         else if(mode === 'field_az') $('#opt-az').addClass('active');
         else $('#opt-loose').addClass('active');
         
         updateLayout();
      }

      function updateLayout() {
         var qtySelect = document.getElementById('barrelCount');
         var masterCard = document.getElementById('card-master');
         var azZone = document.getElementById('zone-az-dest');
         var barrelCount = 4;

         if (currentMode === 'field_az') {
             azZone.style.display = 'block'; 
         } else {
             azZone.style.display = 'none';
             document.getElementById('f_az_dest').value = "";
         }

         if (currentMode === 'field_full') {
             document.getElementById('qty-wrapper').style.display = 'none'; 
             masterCard.style.display = 'block'; 
             barrelCount = 4;
         } else if (currentMode === 'field_az') {
             document.getElementById('qty-wrapper').style.display = 'none'; 
             masterCard.style.display = 'none'; 
             barrelCount = 4;
         } else {
             document.getElementById('qty-wrapper').style.display = 'flex'; 
             masterCard.style.display = 'none'; 
             barrelCount = parseInt(qtySelect.value);
         }
         
         function toggle(id, show) { 
             var el = document.getElementById(id); 
             if(el) el.style.display = show ? 'block' : 'none'; 
         }
         
         toggle('row-tank-2', barrelCount >= 2); 
         toggle('wrap-batch-2', barrelCount >= 2);
         toggle('row-tank-3', barrelCount >= 3); 
         toggle('wrap-batch-3', barrelCount >= 3);
         toggle('row-tank-4', barrelCount >= 4); 
         toggle('wrap-batch-4', barrelCount >= 4);
      }

      function handleSubmit() {
        var locVal = document.getElementById('workLocation').value;
        var boxVal = document.getElementById('f_box').value;
        var azDestVal = document.getElementById('f_az_dest').value;

        var fields = [boxVal];
        for(var i=0; i<14; i++) {
             var el = document.getElementById('f'+i);
             fields.push(el ? el.value : "");
        }

        if(!fields[2] && !fields[4] && !fields[6] && !fields[8]){ alert("請至少掃描一桶!"); return; }
        
        $('#result').hide();

        var payload = {
            fields: fields,
            mode: currentMode,
            location: locVal,
            az_dest: azDestVal
        };

        fetch('api.php?action=save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => onSuccess(data))
        .catch(error => onFailure(error));
      }

      function onSuccess(response) {
        var resDiv = document.getElementById('result');
        $(resDiv).removeClass('success error').show();
        if (response.status === 'success') {
          resDiv.className = 'success'; 
          resDiv.innerHTML = response.message.replace(/\n/g, '<br>');
          $('input[type="text"]').val('');
          setTimeout(function(){ document.getElementById('f_box').focus(); }, 100);
          setTimeout(function(){ if ($(resDiv).hasClass('success')) $(resDiv).fadeOut(500); }, 4000);
        } else {
          resDiv.className = 'error'; 
          resDiv.innerHTML = response.message.replace(/\n/g, '<br>');
        }
      }
      
      function onFailure(error) { alert("連線錯誤: " + error); }
      function saveLocation() { localStorage.setItem('savedLocation', document.getElementById('workLocation').value); }
      
      function manualClear() { 
          $('input[type="text"]').val('');
          $('#result').hide();
      }

      function startScanner(inputId) {
         currentInputId = inputId;
         $('#reader-modal').css('display','flex');
         html5QrCode = new Html5Qrcode("reader");
         html5QrCode.start({ facingMode: "environment" }, { fps: 10, qrbox: 250 },
           (decodedText) => {
               stopScanner();
               document.getElementById(currentInputId).value = decodedText;
               $('#'+currentInputId).trigger('input');
           })
           .catch(err => { console.log(err); });
      }
      function stopScanner() {
        if(html5QrCode) { html5QrCode.stop().then(() => { $('#reader-modal').hide(); html5QrCode.clear(); }); }
        else { $('#reader-modal').hide(); }
      }
      function clearOne(id) { document.getElementById(id).value = ""; document.getElementById(id).focus(); }
    </script>
  </body>
</html>
