# Source Code Backup - N系列BARCODE出貨核對 - Index.html

> [!NOTE]
> *   **原始本機路徑**: [Index.html](file:///D:/GOOGLE%20ANGET/N系列BARCODE出貨核對/Index.html)
> *   **自動備份時間**: `2026-07-15 13:39:13`
> *   **語言類型**: `html`

``` html
<!DOCTYPE html>
<html>
  <head>
    <base target="_top">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
    <style>
      body { font-family: 'Noto Sans TC', sans-serif; background-color: #f0f2f5; padding: 10px; margin: 0; color: #444; }
      .container { max-width: 600px; margin: 0 auto; padding-bottom: 120px; }
      
      h3 { 
        text-align: center; color: #1a73e8; margin-bottom: 15px; font-weight: 700; font-size: 20px; 
        display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 10px; position: relative; 
      }
      
      .query-link { 
        font-size: 14px; text-decoration: none; color: #555; font-weight: bold; 
        background: #fff; border: 1px solid #ddd; padding: 6px 15px; border-radius: 15px; white-space: nowrap; box-shadow: 0 1px 2px rgba(0,0,0,0.1);
      }
      .query-link:hover { background: #f8f9fa; }

      @media (min-width: 600px) {
        h3 { flex-direction: row; gap: 0; }
        .query-link { position: absolute; right: 0; top: 50%; transform: translateY(-50%); }
      }
      
      .top-control-bar { margin-bottom: 10px; display: flex; flex-direction: column; gap: 10px; }
      .mode-switch { display: flex; gap: 5px; width: 100%; justify-content: space-between; }
      .sub-control-bar { display: flex; gap: 5px; width: 100%; align-items: center; }

      .mode-option {
        background: white; padding: 10px 2px; border: 1px solid #dadce0; border-radius: 8px; cursor: pointer;
        font-size: 13px; font-weight: bold; color: #5f6368; transition: all 0.2s ease;
        display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; text-align: center; height: 50px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
      }
      .mode-option:hover { border-color: #1a73e8; color: #1a73e8; }
      .mode-option.active { border: 2px solid #1a73e8; background: #e8f0fe; color: #1a73e8; box-shadow: 0 2px 5px rgba(26, 115, 232, 0.2); }
      
      input[type="radio"] { display: none; }
      
      .select-wrapper { flex: 1; display: flex; align-items: center; padding: 8px 12px; background: white; border: 1px solid #dadce0; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); height: 40px; box-sizing: border-box; }
      .select-wrapper label { font-size: 14px; font-weight: bold; color: #333; margin-right: 8px; white-space: nowrap; }
      .custom-select { border: none; background: transparent; font-size: 15px; font-weight: bold; color: #1a73e8; outline: none; width: 100%; cursor: pointer; }
      .qty-wrapper { display: none; background: #fff8e1; border-color: #fbbc04; } 

      .card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); border-left: 5px solid #ccc; }
      .card-title { font-size: 16px; font-weight: 700; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; color: #202124; }
      .c-blue { border-left-color: #4285f4; } .c-green { border-left-color: #34a853; } .c-orange { border-left-color: #fbbc04; }
      
      .input-group { display: flex; flex-direction: column; width: 100%; margin-bottom: 12px; }
      .input-group label { font-size: 13px; color: #5f6368; margin-bottom: 5px; font-weight: 600; margin-left: 2px; }
      .input-wrapper { position: relative; display: flex; align-items: center; width: 100%; }
      .input-wrapper input { width: 100%; padding: 12px 75px 12px 12px; border: 1px solid #dadce0; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #fff; transition: border 0.2s; height: 48px; }
      .input-wrapper input:focus { border-color: #4285f4; border-width: 2px; outline: none; padding-left: 11px; }
      .action-icons { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); display: flex; gap: 6px; }
      .icon-btn { cursor: pointer; border-radius: 6px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
      .scan-btn { background-color: #e8f0fe; color: #1a73e8; }
      .clear-btn { background-color: #fce8e6; color: #d93025; }
      
      .hidden-force { display: none !important; }
      .toggle-btn { font-size: 13px; color: #1a73e8; cursor: pointer; background: #e8f0fe; padding: 4px 10px; border-radius: 12px; text-decoration: none; display: inline-block; }
      
      #reader-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 9999; display: none; flex-direction: column; align-items: center; justify-content: center; }
      #reader { width: 90%; max-width: 500px; background: #000; border-radius: 12px; overflow: hidden; }
      #close-reader { margin-top: 20px; padding: 12px 30px; background: white; color: black; border: none; border-radius: 30px; font-weight: bold; font-size: 16px; cursor: pointer; }
      
      .btn-check { width: 100%; padding: 15px; background: #1a73e8; color: white; font-size: 18px; font-weight: bold; border: none; border-radius: 8px; margin-top: 10px; cursor: pointer; box-shadow: 0 4px 6px rgba(26, 115, 232, 0.3); }
      .btn-check:active { transform: scale(0.98); background: #185abc; }
      .btn-clear { background: none; color: #5f6368; margin-top: 20px; width: 100%; border: none; text-decoration: underline; cursor: pointer; font-size: 14px; padding: 10px; }
      
      #result { position: fixed; bottom: 20px; left: 5%; right: 5%; width: 90%; padding: 15px; text-align: left; font-weight: bold; border-radius: 12px; display: none; z-index: 999; box-shadow: 0 4px 15px rgba(0,0,0,0.3); box-sizing: border-box; cursor: pointer; }
      .success { background-color: #e6f4ea; color: #137333; border: 1px solid #ceead6; text-align: center !important; } 
      .error { background-color: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }
    </style>
  </head>
  <body onload="initPage()">
    <div id="reader-modal"><div id="reader"></div><button id="close-reader" onclick="stopScanner()">關閉鏡頭</button></div>

    <div class="container">
      <h3>
          <span>🔍 N系列BARCODE現場作業檢點</span>
          <a href="<?= ScriptApp.getService().getUrl() ?>?page=query" target="_blank" class="query-link">📊 查詢出貨紀錄</a>
      </h3>
      
      <div class="top-control-bar">
        <div class="mode-switch">
          <label class="mode-option active" id="opt-full"><input type="radio" name="checkMode" value="ship_full" checked><span>整板出貨</span></label>
          <label class="mode-option" id="opt-mixed"><input type="radio" name="checkMode" value="ship_mixed"><span>混板出貨</span></label>
          <label class="mode-option" id="opt-loose"><input type="radio" name="checkMode" value="ship_loose"><span>散桶</span></label>
          <label class="mode-option" id="opt-az"><input type="radio" name="checkMode" value="ship_az"><span>AZ檢查</span></label>
        </div>

        <div class="sub-control-bar">
            <div class="select-wrapper">
                <label>場所:</label>
                <select id="workLocation" class="custom-select">
                    <option value="崙尾一廠" selected>崙尾一廠</option>
                    <option value="本廠">本廠</option>
                </select>
            </div>
            <div class="select-wrapper qty-wrapper" id="qty-wrapper">
                <label>數量:</label>
                <select id="barrelCount" class="custom-select" onchange="updateLayout()">
                    <option value="1">1 桶</option>
                    <option value="2">2 桶</option>
                    <option value="3">3 桶</option>
                </select>
            </div>
        </div>
      </div>

      <script>
        function createInput(label, id, placeholder, wrapperId) {
          var wrapAttr = wrapperId ? `id="${wrapperId}"` : '';
          return `<div class="input-group" ${wrapAttr}><label>${label}</label><div class="input-wrapper"><input type="text" id="${id}" placeholder="${placeholder}"><div class="action-icons"><div class="icon-btn scan-btn" onclick="startScanner('${id}')">📷</div><div class="icon-btn clear-btn" onclick="clearOne('${id}')">✕</div></div></div></div>`;
        }
      </script>

      <div class="card c-blue">
        <div class="card-title">📦 1. 現場作業桶槽</div>
        <script>document.write(createInput('桶1 批號','f0','掃描批號QR'));</script>
        <script>document.write(createInput('桶1 料號','f1','掃描料號貼紙'));</script>
        <div id="row-tank-2">
          <script>document.write(createInput('桶2 批號','f2','掃描批號QR'));</script>
          <script>document.write(createInput('桶2 料號','f3','掃描料號貼紙'));</script>
        </div>
        <div id="row-tank-3">
          <script>document.write(createInput('桶3 批號','f4','掃描批號QR'));</script>
          <script>document.write(createInput('桶3 料號','f5','掃描料號貼紙'));</script>
        </div>
        <div id="row-tank-4">
          <script>document.write(createInput('桶4 批號','f6','掃描批號QR'));</script>
          <script>document.write(createInput('桶4 料號','f7','掃描料號貼紙'));</script>
        </div>
      </div>

      <div class="card c-green" id="card-master">
        <div class="card-title">🧩 2. 四合一標籤</div>
        <script>document.write(createInput('四合一 料號 (必填)','f8','掃描'));</script>
        <script>document.write(createInput('4in1 批號1 (對應桶1)','f9','掃描'));</script>
        <div id="wrap-batch-2"><script>document.write(createInput('4in1 批號2 (對應桶2)','f10','掃描'));</script></div>
        <div id="wrap-batch-3"><script>document.write(createInput('4in1 批號3 (對應桶3)','f11','掃描'));</script></div>
        <div id="wrap-batch-4"><script>document.write(createInput('4in1 批號4 (對應桶4)','f12','掃描'));</script></div>
      </div>
      
      <div class="card c-orange" id="card-wh">
        <div class="card-title">
            📄 3. 繳庫單
            <span class="toggle-btn" onclick="toggleThirdBatch()" id="btn-toggle-3">+ 新增第3批</span>
        </div>
        <script>document.write(createInput('繳庫 料號','f13','掃描'));</script>
        <script>document.write(createInput('繳庫 批號1','f14','掃描'));</script>
        <script>document.write(createInput('繳庫 批號2','f15','掃描'));</script>
        <div class="hidden-force" id="row-wh-3">
            <script>document.write(createInput('繳庫 批號3 (選填)','f16','極少數混3批時使用'));</script>
        </div>
      </div>

      <button class="btn-check" onclick="handleSubmit()">🚀 巡檢核對並存檔</button>
      <button class="btn-clear" onclick="manualClear()">清空重掃</button>
    </div>
    
    <div id="result"></div>

    <script>
      var currentMode = 'ship_full';
      var html5QrCode;
      var currentInputId = '';
      var inputTimer = null;

      function initPage() { 
        setupAutoHide();
        $('input[name="checkMode"]').change(function() { setMode(this.value); });
        setMode('ship_full'); 

        var savedLoc = localStorage.getItem('s_workLocation');
        if(savedLoc) $('#workLocation').val(savedLoc);
        $('#workLocation').change(function() { localStorage.setItem('s_workLocation', $(this).val()); });

        setupSmartJump(); 
        setTimeout(function() { var f = document.getElementById('f0'); if(f) f.focus(); }, 300);
      }

      function toggleThirdBatch() {
          var row = document.getElementById('row-wh-3');
          var btn = document.getElementById('btn-toggle-3');
          if (row.classList.contains('hidden-force')) {
              row.classList.remove('hidden-force');
              btn.innerText = "- 隱藏第3批";
              document.getElementById('f16').focus();
          } else {
              row.classList.add('hidden-force');
              btn.innerText = "+ 新增第3批";
              document.getElementById('f16').value = ""; 
          }
      }

      function setupAutoHide() {
         $(document).ready(function() {
             $(document).on('click touchstart', function(e) {
                 if (!$(e.target).closest('#result, .btn-check').length) {
                     if ($('#result').is(':visible') && $('#result').hasClass('error')) {
                         $('#result').fadeOut(300);
                     }
                 }
             });
             $('input, select').on('focus click', function() { $('#result').fadeOut(300); });
         });
      }

      function highlightField(id) {
          var el = document.getElementById(id);
          if(el) {
            el.style.backgroundColor = "#e8f0fe";
            setTimeout(function(){ el.style.backgroundColor = "#fff"; }, 500);
          }
      }

      function setupSmartJump() {
        document.addEventListener('input', function(e) {
          if (e.target.tagName === 'INPUT' && e.target.type === 'text') {
            if (inputTimer) clearTimeout(inputTimer);
            inputTimer = setTimeout(function() {
              if (e.target.value.trim() !== "") handleInputComplete(e.target.id, e.target.value.trim());
            }, 250);
          }
        });
        document.addEventListener('keydown', function(e) {
          if (e.target.tagName === 'INPUT' && e.target.type === 'text') {
            if (e.keyCode === 13 || e.key === 'Enter' || e.keyCode === 9) {
              e.preventDefault();
              if (inputTimer) clearTimeout(inputTimer);
              handleInputComplete(e.target.id, e.target.value.trim());
            }
          }
        });
      }

      function handleInputComplete(inputId, value) {
         document.getElementById(inputId).value = value;
         jumpToNext(inputId); 
      }

      function setMode(mode) {
        currentMode = mode;
        $('.mode-option').removeClass('active');
        if (mode === 'ship_full') $('#opt-full').addClass('active');
        else if (mode === 'ship_mixed') $('#opt-mixed').addClass('active');
        else if (mode === 'ship_az') $('#opt-az').addClass('active');
        else $('#opt-loose').addClass('active');
        
        var radios = document.getElementsByName('checkMode');
        for(var i=0; i<radios.length; i++) { if(radios[i].value === mode) radios[i].checked = true; }
        updateLayout();
      }

      function updateLayout() {
        var qtyWrapper = document.getElementById('qty-wrapper');
        var qtySelect = document.getElementById('barrelCount');
        var masterCard = document.getElementById('card-master');
        var whCard = document.getElementById('card-wh');
        var barrelCount = 4;

        qtyWrapper.style.display = 'none'; 
        masterCard.style.display = 'block'; 
        whCard.style.display = 'block';

        if (currentMode === 'ship_full' || currentMode === 'ship_mixed') {
          barrelCount = 4;
        } else if (currentMode === 'ship_az') {
          masterCard.style.display = 'none'; 
          whCard.style.display = 'none';
          barrelCount = 4;
        } else {
          qtyWrapper.style.display = 'flex';
          barrelCount = parseInt(qtySelect.value);
        }

        toggleVisibility('row-tank-2', barrelCount >= 2);
        toggleVisibility('wrap-batch-2', barrelCount >= 2);
        toggleVisibility('row-tank-3', barrelCount >= 3);
        toggleVisibility('wrap-batch-3', barrelCount >= 3);
        toggleVisibility('row-tank-4', barrelCount >= 4);
        toggleVisibility('wrap-batch-4', barrelCount >= 4);
      }

      function toggleVisibility(elementId, isVisible) {
        var el = document.getElementById(elementId);
        if (el) {
          if (isVisible) el.classList.remove('hidden-force');
          else el.classList.add('hidden-force');
        }
      }

      function startScanner(inputId) {
        currentInputId = inputId;
        document.getElementById('reader-modal').style.display = 'flex';
        html5QrCode = new Html5Qrcode("reader");
        html5QrCode.start(
          { facingMode: "environment" }, { fps: 10, qrbox: { width: 250, height: 250 } },
          (decodedText) => {
            document.getElementById(currentInputId).value = decodedText;
            stopScanner();
            handleInputComplete(currentInputId, decodedText);
          }, () => {}
        ).catch(err => { alert("無法啟動相機。"); document.getElementById('reader-modal').style.display = 'none'; });
      }

      function stopScanner() {
        if(html5QrCode) {
          html5QrCode.stop().then(() => { html5QrCode.clear(); document.getElementById('reader-modal').style.display = 'none'; });
        } else { document.getElementById('reader-modal').style.display = 'none'; }
      }

      function jumpToNext(currentId) {
        var inputs = Array.from(document.querySelectorAll('input[type=text]'));
        var visibleInputs = inputs.filter(input => input.offsetParent !== null);
        var currentIndex = visibleInputs.findIndex(input => input.id === currentId);
        if (currentIndex !== -1 && currentIndex < visibleInputs.length - 1) {
          var nextInput = visibleInputs[currentIndex + 1];
          nextInput.focus();
        }
      }

      function clearOne(id) { var el = document.getElementById(id); if (el) { el.value = ""; el.focus(); } }

      function handleSubmit() {
        var inputs = document.querySelectorAll('input[type=text]');
        inputs.forEach(function(input) { if (input.offsetParent === null) input.value = ""; });
        var fields = []; for(var i=0; i<17; i++) fields.push(document.getElementById('f'+i).value);
        var loc = $('#workLocation').val();

        if (currentMode !== 'ship_az' && fields[8].trim() === "") { alert("四合一料號必填!"); return; }
        if(!fields[1] && !fields[3] && !fields[5] && !fields[7]){ alert("請至少掃描一桶!"); return; }
        
        $('#result').hide();
        google.script.run.withSuccessHandler(onSuccess).withFailureHandler(onFailure).processAndSave({ 
            fields: fields, 
            mode: currentMode,
            location: loc
        });
      }

      function onSuccess(response) {
        var resDiv = document.getElementById('result');
        $(resDiv).removeClass('success error').show();
        if (response.status === 'success') {
          resDiv.className = 'success'; resDiv.innerHTML = response.message + '<br>(欄位已自動清空)';
          clearInputsOnly(); 
          setTimeout(function(){ document.getElementById('f0').focus(); }, 100);
          setTimeout(function(){ $(resDiv).fadeOut(500); }, 3000); 
        } else {
          resDiv.className = 'error'; resDiv.innerHTML = response.message.replace(/\n/g, '<br>');
        }
      }
      function onFailure(error) { alert("程式錯誤: "+error); }
      function clearInputsOnly() { for(var i=0; i<17; i++) document.getElementById('f'+i).value = ""; }
      function manualClear() { clearInputsOnly(); $('#result').hide(); document.getElementById('f0').focus(); }
    </script>
  </body>
</html>

```
