<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>N系列BARCODE出貨核對 (V5.0 旗艦版)</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Noto Sans TC', sans-serif; background-color: #f0f2f5; padding: 10px; margin: 0; color: #444; }
        .container { max-width: 600px; margin: 0 auto; padding-bottom: 120px; }
        h3 { text-align: center; color: #1a73e8; margin-bottom: 15px; font-weight: 700; display: flex; flex-direction: column; align-items: center; gap: 10px; position: relative; }
        .query-link { font-size: 13px; text-decoration: none; color: #555; background: #eee; padding: 6px 15px; border-radius: 15px; white-space: nowrap; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
        @media (min-width: 600px) { h3 { flex-direction: row; justify-content: space-between; } }
        
        .mode-switch { display: flex; gap: 5px; width: 100%; margin-bottom: 10px; }
        .mode-option { background: white; padding: 10px 2px; border: 1px solid #dadce0; border-radius: 8px; cursor: pointer; flex: 1; text-align: center; font-size: 13px; font-weight: bold; height: 50px; display: flex; align-items: center; justify-content: center; }
        .mode-option.active { border: 2px solid #1a73e8; background: #e8f0fe; color: #1a73e8; }
        input[type="radio"] { display: none; }

        .select-wrapper { flex: 1; display: flex; align-items: center; padding: 8px 12px; background: white; border: 1px solid #dadce0; border-radius: 8px; height: 40px; box-sizing: border-box; }
        .custom-select { border: none; background: transparent; font-size: 15px; font-weight: bold; color: #1a73e8; outline: none; width: 100%; cursor: pointer; }

        .card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); border-left: 5px solid #ccc; }
        .c-blue { border-left-color: #4285f4; } .c-green { border-left-color: #34a853; } .c-orange { border-left-color: #fbbc04; }
        
        .input-group { display: flex; flex-direction: column; margin-bottom: 12px; }
        .input-wrapper { position: relative; display: flex; align-items: center; }
        .input-wrapper input { width: 100%; padding: 12px 75px 12px 12px; border: 1px solid #dadce0; border-radius: 8px; font-size: 16px; height: 48px; transition: background-color 0.3s; }
        .input-wrapper input:focus { border-color: #1a73e8; outline: none; background-color: #fffde7; }
        
        .action-icons { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); display: flex; gap: 6px; }
        .icon-btn { cursor: pointer; border-radius: 6px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
        .scan-btn { background-color: #e8f0fe; color: #1a73e8; }
        .clear-btn { background-color: #fce8e6; color: #d93025; }
        
        #reader-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 9999; display: none; flex-direction: column; align-items: center; justify-content: center; }
        #result { position: fixed; bottom: 20px; left: 5%; right: 5%; padding: 15px; border-radius: 12px; display: none; z-index: 999; font-weight: bold; }
        .success { background-color: #e6f4ea; color: #137333; border: 1px solid #ceead6; text-align: center; }
        .error { background-color: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }
        .hidden-force { display: none !important; }
    </style>
</head>
<body onload="initPage()">
    <div id="reader-modal"><div id="reader"></div><button onclick="stopScanner()" style="margin-top:20px; padding:12px 30px; border-radius:30px; font-weight:bold;">關閉鏡頭</button></div>

    <div class="container">
        <h3>
            <span>🔍 N系列BARCODE出貨核對</span>
            <div style="display: flex; gap: 8px;">
                <a href="schedule_mgr.php" class="query-link" style="background: #fff3e0; color: #e65100;">🛡️ 排程管理</a>
                <a href="query.php" class="query-link">📊 查詢紀錄</a>
            </div>
        </h3>

        <div class="top-control-bar">
            <div class="mode-switch">
                <label class="mode-option active" id="opt-full"><input type="radio" name="checkMode" value="ship_full" checked><span>整板出貨</span></label>
                <label class="mode-option" id="opt-mixed"><input type="radio" name="checkMode" value="ship_mixed"><span>混板出貨</span></label>
                <label class="mode-option" id="opt-loose"><input type="radio" name="checkMode" value="ship_loose"><span>散桶</span></label>
                <label class="mode-option" id="opt-az"><input type="radio" name="checkMode" value="ship_az"><span>AZ檢查</span></label>
            </div>
            <div class="sub-control-bar" style="display:flex; gap:10px;">
                <div class="select-wrapper">
                    <label style="font-size:14px; font-weight:bold; margin-right:5px;">場所:</label>
                    <select id="workLocation" class="custom-select">
                        <option value="彰濱一廠">彰濱一廠</option>
                        <option value="彰濱二廠" selected>彰濱二廠</option>
                    </select>
                </div>
                <div class="select-wrapper qty-wrapper" id="qty-wrapper" style="display:none; background:#fff8e1;">
                    <label style="font-size:14px; font-weight:bold; margin-right:5px;">數量:</label>
                    <select id="barrelCount" class="custom-select" onchange="updateLayout()">
                        <option value="1">1 桶</option><option value="2">2 桶</option><option value="3">3 桶</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="card c-blue">
            <div class="card-title" style="font-weight:bold; margin-bottom:10px;">📦 1. 現場作業桶槽</div>
            <div id="tank-fields-container"></div>
        </div>

        <div class="card c-green" id="card-master">
            <div class="card-title" style="font-weight:bold; margin-bottom:10px;">🧩 2. 四合一標籤</div>
            <div id="master-fields-container"></div>
        </div>

        <div class="card c-orange" id="card-wh">
            <div class="card-title" style="font-weight:bold; margin-bottom:10px;">📄 3. 繳庫單 <span onclick="$('#row-wh-3').toggleClass('hidden-force')" style="font-size:12px; color:#1a73e8; cursor:pointer; float:right;">+ 更多批號</span></div>
            <div id="wh-fields-container"></div>
        </div>

        <button class="btn-check" style="width:100%; padding:15px; background:#1a73e8; color:white; border:none; border-radius:8px; font-size:18px; font-weight:bold; cursor:pointer;" onclick="handleSubmit()">🚀 巡檢核對並存檔</button>
        <button onclick="manualClear()" style="width:100%; background:none; border:none; color:#888; text-decoration:underline; margin-top:15px; cursor:pointer;">清空重掃</button>
    </div>

    <div id="result"></div>

    <script>
        var scanTimer = null;
        var COOL_DOWN_TIME = 100; // 訊號冷卻偵測
        var html5QrCode;

        function createInputHtml(label, id, placeholder, wrapperId) {
            let wid = wrapperId ? `id="${wrapperId}"` : '';
            return `<div class="input-group" ${wid}><label style="font-size:13px; font-weight:600; margin-bottom:5px;">${label}</label><div class="input-wrapper"><input type="text" id="${id}" placeholder="${placeholder}" inputmode="none"><div class="action-icons"><div class="icon-btn scan-btn" onclick="startScanner('${id}')">📷</div><div class="icon-btn clear-btn" onclick="clearOne('${id}')">✕</div></div></div></div>`;
        }

        function initPage() {
            renderFields();
            setupSmartJump();
            $('input[name="checkMode"]').change(function() { updateLayout(); });
            let savedLoc = localStorage.getItem('s_workLocation');
            if(savedLoc) $('#workLocation').val(savedLoc);
            $('#workLocation').change(function() { localStorage.setItem('s_workLocation', $(this).val()); });
            updateLayout();
            $('#f0').focus();
        }

        function renderFields() {
            let tankHtml = ""; for(let i=0; i<4; i++) { tankHtml += createInputHtml(`桶${i+1} 批號`, `f${i*2}`, "掃描批號", `row-tank-${i+1}`) + createInputHtml(`桶${i+1} 料號`, `f${i*2+1}`, "掃描料號", `row-tank-${i+1}-m`); }
            $('#tank-fields-container').html(tankHtml);
            let masterHtml = createInputHtml("四合一 料號", "f8", "掃描"); for(let i=0; i<4; i++) { masterHtml += createInputHtml(`4in1 批號${i+1}`, `f${9+i}`, "掃描", `wrap-batch-${i+1}`); }
            $('#master-fields-container').html(masterHtml);
            $('#wh-fields-container').html(createInputHtml("繳庫 料號", "f13", "掃描") + createInputHtml("繳庫 批號1", "f14", "掃描") + createInputHtml("繳庫 批號2", "f15", "掃描") + `<div class="hidden-force" id="row-wh-3">${createInputHtml("繳庫 批號3", "f16", "選填")}</div>`);
        }

        function updateLayout() {
            let mode = $('input[name="checkMode"]:checked').val();
            $('.mode-option').removeClass('active'); $(`input[value="${mode}"]`).parent().addClass('active');
            let bc = 4; $('#qty-wrapper').hide(); $('#card-master, #card-wh').show();
            if (mode === 'ship_loose') { $('#qty-wrapper').css('display', 'flex'); bc = parseInt($('#barrelCount').val()); } 
            else if (mode === 'ship_az') { $('#card-master, #card-wh').hide(); }
            for (let i = 1; i <= 4; i++) { let show = (i <= bc); $(`#row-tank-${i}, #row-tank-${i}-m, #wrap-batch-${i}`).toggleClass('hidden-force', !show); }
        }

        function setupSmartJump() {
            $(document).on('input', 'input[type="text"]', function() {
                let id = this.id; let val = this.value;
                if (scanTimer) clearTimeout(scanTimer);
                if (val.trim() !== "") { scanTimer = setTimeout(() => { handleScan(id, val.trim()); }, COOL_DOWN_TIME); }
            });
        }

        function handleScan(id, val) {
            $(`#${id}`).css('background-color', '#e8f0fe'); setTimeout(() => $(`#${id}`).css('background-color', '#fff'), 500);
            let visible = $('input[type="text"]:visible');
            let idx = visible.index($(`#${id}`));
            if (idx !== -1 && idx < visible.length - 1) { visible.eq(idx + 1).focus(); }
        }

        function startScanner(id) {
            $('#reader-modal').css('display', 'flex');
            html5QrCode = new Html5Qrcode("reader");
            html5QrCode.start({ facingMode: "environment" }, { fps: 10, qrbox: 250 }, (txt) => { $(`#${id}`).val(txt).trigger('input'); stopScanner(); }).catch(() => stopScanner());
        }

        function stopScanner() { if(html5QrCode) html5QrCode.stop().then(() => $('#reader-modal').hide()); else $('#reader-modal').hide(); }
        function clearOne(id) { $(`#${id}`).val('').focus(); }
        function manualClear() { $('input[type="text"]').val(''); $('#f0').focus(); $('#result').hide(); }

        function handleSubmit() {
            let fields = []; for(let i=0; i<17; i++) fields.push($(`#f${i}`).val() || "");
            $.ajax({
                url: 'save_action.php',
                type: 'POST',
                data: JSON.stringify({ fields: fields, mode: $('input[name="checkMode"]:checked').val(), location: $('#workLocation').val() }),
                contentType: 'application/json',
                success: function(res) {
                    $('#result').removeClass('success error').addClass(res.status).html(res.message).fadeIn();
                    if(res.status === 'success') { manualClear(); setTimeout(() => $('#result').fadeOut(), 5000); }
                }
            });
        }
    </script>
</body>
</html>
