<?php
// query.php - 整合排程管理與查詢
require_once 'db_config.php';
require_once 'Logic.php';

// 處理排程匯入
$mgrMsg = "";
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'import_schedule') {
    $rawText = $_POST['schedule_text'] ?? '';
    if (!empty($rawText)) {
        try {
            $pdo->exec("TRUNCATE TABLE daily_schedules");
            $rows = preg_split('/[\n\r,]+/', $rawText);
            $count = 0;
            $stmt = $pdo->prepare("INSERT INTO daily_schedules (batch_no) VALUES (?)");
            foreach ($rows as $row) {
                $clean = ShippingHelper::normalizeBatch(trim($row));
                if ($clean !== "") { $stmt->execute([$clean]); $count++; }
            }
            $mgrMsg = "<div style='color:green; background:#e6f4ea; padding:10px;'>✅ 排程已更新，共 $count 筆。</div>";
        } catch (Exception $e) {
            $mgrMsg = "<div style='color:red;'>❌ 錯誤: " . $e->getMessage() . "</div>";
        }
    }
}

// 處理 AJAX 查詢
if (isset($_GET['action'])) {
    if ($_GET['action'] === 'search') {
        $ds = $_GET['dateStart'] . ' 00:00:00';
        $de = $_GET['dateEnd'] . ' 23:59:59';
        $kw = $_GET['keyword'] ?? '';

        $sql = "SELECT * FROM shipping_records WHERE created_at BETWEEN ? AND ?";
        $params = [$ds, $de];
        if ($kw !== '') {
            $sql .= " AND (tank1_batch LIKE ? OR wh_mat LIKE ? OR work_location LIKE ?)";
            $sk = "%$kw%";
            array_push($params, $sk, $sk, $sk);
        }
        $sql .= " ORDER BY created_at DESC";
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);
        echo json_encode($stmt->fetchAll());
        exit;
    }
}
?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>出貨紀錄與管理中心</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Noto Sans TC', sans-serif; background: #f8f9fa; padding: 20px; }
        .container { max-width: 1200px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .admin-box { background: #fff3e0; padding: 15px; border-radius: 8px; display: none; margin-top: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border-bottom: 1px solid #eee; padding: 12px; text-align: left; }
    </style>
</head>
<body>
    <div class="container">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3>📊 出貨紀錄與排程管理</h3>
            <a href="index.php" style="text-decoration:none; color:#1a73e8; font-weight:bold;">← 返回掃描頁</a>
        </div>

        <button onclick="$('.admin-box').slideToggle()" style="background:#e65100; color:white; border:none; padding:8px 15px; border-radius:5px; cursor:pointer;">🛡️ 管理 T100 排程</button>
        
        <div class="admin-box">
            <form method="POST">
                <input type="hidden" name="action" value="import_schedule">
                <textarea name="schedule_text" style="width:100%; height:100px;" placeholder="貼入批號清單..."></textarea>
                <button type="submit" style="margin-top:10px; padding:10px 20px; background:#e65100; color:white; border:none; border-radius:5px;">💾 更新白名單</button>
                <?php echo $mgrMsg; ?>
            </form>
        </div>

        <hr style="margin:20px 0; border:0; border-top:1px solid #eee;">

        <div class="search-bar">
            日期: <input type="date" id="dateStart"> ~ <input type="date" id="dateEnd">
            關鍵字: <input type="text" id="batchInput">
            <button onclick="doSearch()" style="background:#1a73e8; color:white; border:none; padding:8px 20px; border-radius:5px;">查詢</button>
        </div>

        <table>
            <thead><tr><th>時間 / 場所</th><th>模式</th><th>紀錄批號</th><th>判定</th></tr></thead>
            <tbody id="tableBody"></tbody>
        </table>
    </div>

    <script>
      function doSearch() {
          const ds = $('#dateStart').val(); const de = $('#dateEnd').val(); const kw = $('#batchInput').val();
          if(!ds || !de) { alert("請選擇日期"); return; }
          $('#tableBody').empty();
          $.getJSON(`query.php?action=search&dateStart=${ds}&dateEnd=${de}&keyword=${kw}`, function(data) {
              if(data.length === 0) $('#tableBody').append('<tr><td colspan="4" style="text-align:center;">查無資料</td></tr>');
              data.forEach(row => {
                  $('#tableBody').append(`<tr>
                      <td>${row.created_at}<br><b>${row.work_location}</b></td>
                      <td>${row.mode}</td>
                      <td>${row.tank1_batch}</td>
                      <td>${row.result_status}</td>
                  </tr>`);
              });
          });
      }
    </script>
</body>
</html>
