# Source Code Backup - N系列BARCODE出貨核對 - Query.html

> [!NOTE]
> *   **原始本機路徑**: [Query.html](file:///D:/GOOGLE%20ANGET/N系列BARCODE出貨核對/Query.html)
> *   **自動備份時間**: `2026-07-15 13:39:13`
> *   **語言類型**: `html`

``` html
<!DOCTYPE html>
<html>
  <head>
    <base target="_top">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
      body { font-family: 'Noto Sans TC', sans-serif; background-color: #f8f9fa; margin: 0; padding: 15px; color: #333; }
      .container { width: fit-content; min-width: 100%; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 5px rgba(0,0,0,0.05); }
      
      .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee; position: relative; }
      h3 { color: #1a73e8; margin: 0; font-size: 20px; font-weight: 700; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 10px; width: 100%; text-align: center; }
      
      .top-links { display: flex; gap: 10px; }
      .action-link { font-size: 13px; text-decoration: none; color: #555; font-weight: bold; background: #fff; padding: 8px 15px; border-radius: 20px; white-space: nowrap; border: 1px solid #ddd; cursor: pointer; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
      .action-link:hover { background: #f8f9fa; }
      .link-blue { color: #1a73e8; border-color: #d2e3fc; background: #e8f0fe; }

      @media (min-width: 600px) {
        h3 { flex-direction: row; justify-content: flex-start; text-align: left; width: auto; gap: 10px; }
        .top-links { margin-left: auto; }
      }

      .search-bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; background: #fff; padding: 0 0 15px 0; }
      .search-label { font-weight: bold; color: #444; font-size: 13px; margin-right: 2px; }
      .date-input { padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; color: #333; }
      .text-input { flex: 1; padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; min-width: 200px; }
      .btn-search { background-color: #1a73e8; color: white; border: none; padding: 6px 20px; border-radius: 4px; font-size: 13px; font-weight: bold; cursor: pointer; margin-left: auto; }
      .btn-search:hover { background-color: #1557b0; }

      .toggle-switch { display: flex; align-items: center; background: #e8f0fe; padding: 5px 10px; border-radius: 6px; border: 1px solid #d2e3fc; margin-left: 10px; cursor: pointer; }
      .toggle-switch input { margin: 0 5px 0 0; cursor: pointer; width: 14px; height: 14px; }
      .toggle-switch span { font-size: 13px; font-weight: bold; color: #1a73e8; }

      .table-responsive { border: 1px solid #eee; border-radius: 6px; overflow-x: auto; }
      .data-table { width: auto; border-collapse: collapse; font-size: 12px; }
      .data-table th { background-color: #f1f3f4; color: #5f6368; font-weight: bold; text-align: left; padding: 10px 12px; border-bottom: 2px solid #ddd; white-space: nowrap; }
      .data-table td { padding: 8px 12px; border-bottom: 1px solid #f1f3f4; vertical-align: top; color: #3c4043; line-height: 1.4; white-space: nowrap; }
      .data-table tr:hover { background-color: #f8fbff; }

      .col-id    { width: 40px; color: #999; font-weight: bold; text-align: center; }
      .col-info  { width: 100px; } 
      .col-mode  { width: 60px; text-align: center; }
      .col-tanks { width: auto; min-width: 250px; } 
      .col-4in1  { width: auto; min-width: 150px; }   
      .col-wh    { width: auto; min-width: 150px; }   
      .col-res   { width: 140px; text-align: center; } 

      .data-table th.col-id, .data-table th.col-mode, .data-table th.col-res { text-align: center; }

      .loc-text { font-weight: bold; font-size: 13px; color: #202124; display: block; margin-bottom: 2px; }
      .date-text { font-size: 11px; color: #888; }
      .mode-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #1a73e8; background: #e8f0fe; }
      .mode-badge.az { color: #c5221f; background: #fce8e6; }
      
      .data-list { display: flex; flex-direction: column; gap: 4px; }
      .data-item { font-family: 'Roboto Mono', monospace; font-size: 11.5px; border-bottom: 1px dashed #eee; padding-bottom: 2px; white-space: nowrap; }
      .data-item:last-child { border-bottom: none; }
      
      .lbl { color: #5f6368; font-weight: bold; margin-right: 5px; font-size: 11px; }
      .txt-blue { color: #1a73e8; font-weight: bold; }
      .txt-green { color: #137333; font-weight: bold; }
      .txt-orange { color: #e37400; font-weight: bold; }

      .res-tag { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; white-space: normal; line-height: 1.2; }
      .res-ok { background-color: #e6f4ea; color: #137333; border: 1px solid #ceead6; }
      .res-err { background-color: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }
      
      .sch-ok { margin-top:6px; font-size:11px; color:#137333; background:#e6f4ea; padding:3px 6px; border-radius:4px; display:inline-block; border:1px solid #ceead6; width: max-content; }
      .sch-err { margin-top:6px; font-size:11px; color:#c5221f; background:#fce8e6; padding:3px 6px; border-radius:4px; display:inline-block; border:1px solid #fad2cf; width: max-content; }

      #loading { text-align: center; padding: 30px; color: #5f6368; font-size: 14px; display: none; }
      .pagination { display: flex; justify-content: flex-end; align-items: center; gap: 10px; margin-top: 15px; }
      .page-btn { padding: 5px 12px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; color: #555; font-size: 12px; }
      .page-btn:disabled { background: #f5f5f5; color: #ccc; cursor: not-allowed; }

      /* --- 更新排程 Modal --- */
      #schedule-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 8888; display: none; justify-content: center; align-items: center; }
      .schedule-box { background: white; padding: 20px; border-radius: 12px; width: 95%; max-width: 700px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); white-space: normal; }
      .schedule-box h4 { margin: 0 0 10px 0; color: #1a73e8; }
      .schedule-box p { font-size: 13px; color: #555; margin-bottom: 10px; line-height: 1.5; }
      
      /* 設定讓 Excel 貼上後依然保留排版 */
      .schedule-box textarea { 
        width: 100%; height: 350px; border: 2px dashed #ccc; border-radius: 8px; 
        padding: 10px; font-size: 12px; box-sizing: border-box; resize: none; 
        white-space: pre; overflow-wrap: normal; overflow-x: auto; font-family: monospace;
      }
      .schedule-box textarea:focus { border-color: #1a73e8; outline: none; }
      
      .modal-btns { display: flex; justify-content: space-between; align-items: center; margin-top: 15px; }
      .btn-cancel { padding: 8px 15px; border: none; background: #eee; color: #333; border-radius: 6px; cursor: pointer; font-weight: bold; }
      .btn-save { padding: 8px 20px; border: none; background: #1a73e8; color: white; border-radius: 6px; cursor: pointer; font-weight: bold; }
      .btn-save:hover { background: #1557b0; }
      .btn-clear-data { padding: 8px 15px; border: none; background: #fce8e6; color: #c5221f; border-radius: 6px; cursor: pointer; font-weight: bold; }
      .btn-clear-data:hover { background: #fad2cf; }
    </style>
  </head>
  <body>
    <div id="schedule-modal">
        <div class="schedule-box">
            <h4>📅 出貨排程管理</h4>
            <p>目前系統內的排程資料如下。您可以核對是否正確，或直接「全選並貼上」新的 Excel 資料來覆蓋它。</p>
            <textarea id="schedule-data" placeholder="載入中...或請在此貼上 Excel 資料..."></textarea>
            
            <div class="modal-btns">
                <button class="btn-clear-data" onclick="clearSchedule()" id="btn-clear-schedule">🗑️ 清空目前排程</button>
                
                <div style="display: flex; gap: 10px;">
                    <button class="btn-cancel" onclick="closeScheduleModal()">取消</button>
                    <button class="btn-save" onclick="submitSchedule()" id="btn-submit-schedule">💾 覆蓋儲存</button>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
      <div class="header">
        <h3>
          <span>📊 出貨紀錄查詢</span>
          <div class="top-links">
             <button class="action-link link-blue" onclick="openScheduleModal()">📅 更新排程</button>
             <button class="action-link" onclick="goHome()">← 返回掃描頁</button>
          </div>
        </h3>
      </div>

      <div class="search-bar">
        <span class="search-label">日期範圍 :</span>
        <input type="date" id="dateStart" class="date-input">
        <span style="color:#999">~</span>
        <input type="date" id="dateEnd" class="date-input">
        <span class="search-label" style="margin-left: 15px;">搜尋 :</span>
        <input type="text" id="batchInput" class="text-input" placeholder="輸入外箱條碼或批號...">
        
        <label class="toggle-switch">
          <input type="checkbox" id="checkScheduleToggle" checked onchange="doSearch()">
          <span>🛡️ 啟用排程核對</span>
        </label>

        <button class="btn-search" onclick="doSearch()">查詢</button>
      </div>

      <div id="loading">⏳ 資料搜尋中...</div>
      
      <div class="table-responsive">
        <table class="data-table">
          <thead>
            <tr>
              <th class="col-id">ID</th>
              <th class="col-info">時間 / 場所</th>
              <th class="col-mode">模式</th>
              <th class="col-tanks">桶槽作業紀錄 (1~4)</th>
              <th class="col-4in1">4合1 紀錄</th>
              <th class="col-wh">外箱條碼 / 料號</th> 
              <th class="col-res">判定結果</th>
            </tr>
          </thead>
          <tbody id="tableBody"></tbody>
        </table>
      </div>

      <div class="pagination" id="paginationControl" style="visibility:hidden;">
        <button class="page-btn" id="btnPrev" onclick="changePage(-1)">上一頁</button>
        <span id="pageInfo" style="font-size:13px; font-weight:bold; color:#5f6368;">第 1 頁</span>
        <button class="page-btn" id="btnNext" onclick="changePage(1)">下一頁</button>
      </div>
    </div>

    <script>
      var allData = [];
      var currentPage = 1;
      var pageSize = 20;

      window.onload = function() {
        var today = new Date().toISOString().split('T')[0];
        var lastWeek = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        document.getElementById('dateStart').value = lastWeek;
        document.getElementById('dateEnd').value = today;
      };

      function goHome() {
         google.script.run.withSuccessHandler(function(url){
             window.top.location.href = url.split('?')[0]; 
         }).getScriptUrl();
      }

      // 打開視窗時：讀取目前排程顯示出來
      function openScheduleModal() {
          document.getElementById('schedule-modal').style.display = 'flex';
          var ta = document.getElementById('schedule-data');
          ta.value = "⏳ 正在讀取目前的排程資料，請稍候...";
          ta.disabled = true;

          google.script.run
            .withSuccessHandler(function(text) {
                ta.disabled = false;
                ta.value = text;
                ta.focus();
            })
            .withFailureHandler(function(err) {
                ta.disabled = false;
                ta.value = "";
                alert("讀取排程失敗：" + err);
            })
            .getScheduleRawText();
      }

      function closeScheduleModal() {
          document.getElementById('schedule-modal').style.display = 'none';
      }

      function submitSchedule() {
          var tsvData = document.getElementById('schedule-data').value.trim();
          if(tsvData === "") {
              alert("請先貼上資料！如果想清空排程，請使用左下角的「清空目前排程」按鈕。"); 
              return;
          }
          
          var btn = document.getElementById('btn-submit-schedule');
          btn.innerText = "⏳ 儲存中...";
          btn.disabled = true;

          google.script.run
            .withSuccessHandler(function(res) {
                alert(res.msg);
                if(res.success) {
                   closeScheduleModal();
                   doSearch(); 
                }
                btn.innerText = "💾 覆蓋儲存";
                btn.disabled = false;
            })
            .withFailureHandler(function(err) {
                alert("伺服器錯誤：" + err);
                btn.innerText = "💾 覆蓋儲存";
                btn.disabled = false;
            })
            .updateScheduleData(tsvData);
      }

      // 新增：清空排程邏輯
      function clearSchedule() {
          if(!confirm("確定要清空目前的排程資料嗎？\n(清空後，所有啟用了核對的歷史紀錄都會顯示「不在排程」)")) return;
          
          var btn = document.getElementById('btn-clear-schedule');
          btn.innerText = "⏳ 清空中...";
          btn.disabled = true;

          google.script.run
            .withSuccessHandler(function(res) {
                alert(res.msg);
                if(res.success) {
                   document.getElementById('schedule-data').value = "";
                   closeScheduleModal();
                   doSearch(); 
                }
                btn.innerText = "🗑️ 清空目前排程";
                btn.disabled = false;
            })
            .withFailureHandler(function(err) {
                alert("伺服器錯誤：" + err);
                btn.innerText = "🗑️ 清空目前排程";
                btn.disabled = false;
            })
            .clearScheduleData();
      }

      function doSearch() {
        var ds = document.getElementById('dateStart').value;
        var de = document.getElementById('dateEnd').value;
        var kw = document.getElementById('batchInput').value.trim();
        var useSchedule = document.getElementById('checkScheduleToggle').checked; 
        
        document.getElementById('loading').style.display = 'block';
        document.getElementById('tableBody').innerHTML = '';
        document.getElementById('paginationControl').style.visibility = 'hidden';

        google.script.run
          .withSuccessHandler(function(data) {
             allData = data;
             currentPage = 1;
             renderTable();
             document.getElementById('loading').style.display = 'none';
             document.getElementById('paginationControl').style.visibility = (allData.length > 0) ? 'visible' : 'hidden';
          })
          .withFailureHandler(function(e){ 
             alert("查詢錯誤: " + e); 
             document.getElementById('loading').style.display = 'none'; 
          })
          .searchRecords(ds, de, kw, useSchedule); 
      }

      function renderTable() {
        var tbody = document.getElementById('tableBody');
        tbody.innerHTML = "";
        
        if (!allData || allData.length === 0) {
          tbody.innerHTML = "<tr><td colspan='7' style='text-align:center; padding:30px; color:#888;'>查無資料</td></tr>";
          return;
        }

        var startIdx = (currentPage - 1) * pageSize;
        var endIdx = Math.min(startIdx + pageSize, allData.length);
        var pageData = allData.slice(startIdx, endIdx);

        document.getElementById('pageInfo').innerText = "第 " + currentPage + " 頁 / 共 " + Math.ceil(allData.length / pageSize) + " 頁";
        document.getElementById('btnPrev').disabled = (currentPage === 1);
        document.getElementById('btnNext').disabled = (endIdx >= allData.length);

        var useSchedule = document.getElementById('checkScheduleToggle').checked;

        var html = "";
        pageData.forEach(function(row, index) {
           var globalIdx = allData.length - (startIdx + index); 
           var badgeClass = (row.mode.indexOf("AZ") !== -1) ? "az" : "";

           var whHtml = "<div class='data-list'>";
           if(row.wh.mat) whHtml += `<div class='data-item txt-orange'>Mat: ${row.wh.mat}</div>`;
           if(row.wh.batches) {
               row.wh.batches.forEach((b, k) => {
                   if(b) whHtml += `<div class='data-item'><span class='lbl'>W${k+1}:</span>${b}</div>`;
               });
           }
           whHtml += "</div>";

           var tankHtml = "<div class='data-list'>";
           for(var i=0; i<4; i++) {
               if(row.tanks[i].batch || row.tanks[i].mat) {
                   tankHtml += `<div class='data-item'><span class='lbl'>T${i+1}:</span>${row.tanks[i].batch} <span class='lbl' style='margin-left:5px;color:#1a73e8'>${row.tanks[i].mat}</span></div>`;
               }
           }
           tankHtml += "</div>";

           var masterHtml = "<div class='data-list'>";
           if(row.master.mat) masterHtml += `<div class='data-item txt-green'>Mat: ${row.master.mat}</div>`;
           if(row.master.batches) {
               row.master.batches.forEach((b, k) => {
                   if(b) masterHtml += `<div class='data-item'><span class='lbl'>B${k+1}:</span>${b}</div>`;
               });
           }
           masterHtml += "</div>";

           var resText = row.result || ""; 
           var resClass = (resText.indexOf("合格") !== -1) ? "res-ok" : "res-err";
           
           var schTag = "";
           if (useSchedule) {
               if (row.inSchedule === true) {
                   schTag = `<div class="sch-ok">📅 排程相符</div>`;
               } else if (row.inSchedule === false) {
                   schTag = `<div class="sch-err">⚠️ 不在排程</div>`;
               }
           }

           html += `<tr>
             <td class="col-id">#${globalIdx}</td>
             <td class="col-info">
                <span class="loc-text">${row.location}</span>
                <span class="date-text">${row.date}<br>${row.time}</span>
             </td>
             <td class="col-mode"><span class="mode-badge ${badgeClass}">${row.mode}</span></td>
             
             <td class="col-tanks">${tankHtml}</td>
             <td class="col-4in1">${masterHtml}</td>
             <td class="col-wh">${whHtml}</td>
             
             <td class="col-res">
                <span class="res-tag ${resClass}">${resText}</span><br>
                ${schTag}
             </td>
           </tr>`;
        });
        tbody.innerHTML = html;
      }

      function changePage(delta) { currentPage += delta; renderTable(); }
    </script>
  </body>
</html>

```
