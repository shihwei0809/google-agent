<?php
// query_view.php
// 🟢 MySQL 資料庫讀取專用版 (V4.1: 修正欄位對接與排程核對 UI)

require_once 'db_config.php'; // 確保連線檔案名稱正確

// 設定預設日期範圍：當月 1 日至今日
$defaultStart = date('Y-m-01');
$defaultEnd = date('Y-m-d');
$dateStart = $_GET['dateStart'] ?? $defaultStart;
$dateEnd = $_GET['dateEnd'] ?? $defaultEnd;
$keyword = $_GET['keyword'] ?? '';

// 基本 SQL 查詢：根據日期篩選
$sql = "SELECT * FROM shipping_records WHERE DATE(created_at) BETWEEN ? AND ?";
$params = [$dateStart, $dateEnd];

// 關鍵字搜尋邏輯：涵蓋外箱、批號、場所
if ($keyword) {
    $sql .= " AND (
        wh_mat LIKE ? OR 
        tank1_batch LIKE ? OR tank2_batch LIKE ? OR tank3_batch LIKE ? OR tank4_batch LIKE ? OR
        master_batch1 LIKE ? OR work_location LIKE ?
    )";
    $likeKey = "%$keyword%";
    // 注入參數
    array_push($params, $likeKey, $likeKey, $likeKey, $likeKey, $likeKey, $likeKey, $likeKey);
}

$sql .= " ORDER BY id DESC LIMIT 100";

try {
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $rows = $stmt->fetchAll();
    $rowCount = count($rows);
} catch (PDOException $e) {
    die("資料庫讀取失敗: " . $e->getMessage());
}
?>
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>出貨紀錄查詢 (MySQL)</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <style>
        /* 延用您提供的高質感樣式 */
        body { font-family: 'Noto Sans TC', sans-serif; background: #f0f2f5; padding: 20px; color: #333; margin: 0; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
        .btn-back { background: #5f6368; color: white; padding: 8px 16px; border-radius: 20px; text-decoration: none; font-size: 14px; font-weight: bold; }
        
        .search-card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; display: flex; gap: 15px; flex-wrap: wrap; align-items: center; }
        .search-card input[type="date"], .search-card input[type="text"] { padding: 8px; border: 1px solid #ddd; border-radius: 5px; }
        .btn-search { background: #1a73e8; color: white; border: none; padding: 8px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }

        .table-container { overflow-x: auto; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; min-width: 900px; }
        th { background: #f8f9fa; color: #444; padding: 12px; text-align: left; font-weight: bold; border-bottom: 2px solid #eee; }
        td { padding: 12px; border-bottom: 1px solid #eee; font-size: 14px; vertical-align: top; }
        
        .badge { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; margin-bottom: 4px; }
        .mode-badge { background: #e8f0fe; color: #1967d2; }
        .status-badge { background: #e6f4ea; color: #137333; }
        .batch-list { font-family: monospace; line-height: 1.4; color: #555; }
        .db-status { font-size: 13px; color: #137333; background: #e6f4ea; padding: 6px 12px; border-radius: 20px; border: 1px solid #ceead6; font-weight: bold; }

        /* 🟢 iOS 風格的 Toggle Switch */
        .switch-container { display: flex; align-items: center; gap: 8px; background: #f8f9fa; padding: 8px 12px; border-radius: 8px; border: 1px solid #ddd; }
        .switch { position: relative; display: inline-block; width: 40px; height: 20px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 34px; }
        .slider:before { position: absolute; content: ""; height: 14px; width: 14px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }
        input:checked + .slider { background-color: #1a73e8; }
        input:checked + .slider:before { transform: translateX(20px); }
    </style>
</head>
<body>

    <div class="header">
        <a href="index.php" class="btn-back">⬅ 返回掃描頁</a>
        <div style="text-align:right;">
            <h2 style="margin:0; color:#1a73e8;">📊 出貨紀錄查詢</h2>
            <div style="margin-top: 5px;"><span class="db-status">🟢 MySQL 連線正常 (共 <?php echo $rowCount; ?> 筆)</span></div>
        </div>
    </div>

    <form class="search-card" method="GET">
        <div style="display: flex; align-items: center; gap: 5px;">
            <label style="font-weight:bold; color:#555;">日期範圍：</label>
            <input type="date" name="dateStart" value="<?php echo $dateStart; ?>">
            <span>~</span>
            <input type="date" name="dateEnd" value="<?php echo $dateEnd; ?>">
        </div>
        
        <input type="text" name="keyword" placeholder="輸入批號或料號..." value="<?php echo htmlspecialchars($keyword); ?>" style="flex-grow:1; min-width: 150px;">
        <button type="submit" class="btn-search">🔍 查詢</button>

        <div class="switch-container">
            <label class="switch">
                <input type="checkbox" id="toggleSchedule" checked>
                <span class="slider"></span>
            </label>
            <label for="toggleSchedule" style="font-size: 14px; font-weight: bold; color: #444; cursor: pointer;">🛡️ 顯示排程核對</label>
        </div>
    </form>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th width="5%">ID</th>
                    <th width="15%">時間 / 場所</th>
                    <th width="8%">模式</th>
                    <th width="20%">繳庫料號 / 批號</th>
                    <th>桶槽作業紀錄 (1~4)</th>
                    <th>4合1 紀錄</th>
                    <th>判定結果</th>
                </tr>
            </thead>
            <tbody>
                <?php if ($rowCount === 0): ?>
                    <tr><td colspan="7" style="text-align:center; padding: 40px; color: #888;">∅ 查無資料</td></tr>
                <?php else: ?>
                    <?php foreach ($rows as $row): ?>
                    <tr>
                        <td>#<?php echo $row['id']; ?></td>
                        <td>
                            <div style="font-weight:bold; font-size:15px; color:#1a73e8;"><?php echo htmlspecialchars($row['work_location']); ?></div>
                            <div style="color:#666; font-size:13px; margin-top:4px;">
                                <?php echo date('Y/m/d H:i', strtotime($row['created_at'])); ?>
                            </div>
                        </td>
                        <td><span class="badge mode-badge"><?php echo htmlspecialchars($row['mode']); ?></span></td>
                        <td>
                            <div style="word-break: break-all; font-weight:bold; color:#333;">
                                料號: <?php echo htmlspecialchars($row['wh_mat']); ?>
                            </div>
                            <div style="color:#666; font-size:12px; margin-top:4px; font-family: monospace;">
                                P1: <?php echo htmlspecialchars($row['wh_batch1']); ?><br>
                                P2: <?php echo htmlspecialchars($row['wh_batch2']); ?>
                            </div>
                        </td>
                        <td class="batch-list">
                            <?php 
                                for($i=1; $i<=4; $i++) {
                                    if(!empty($row["tank{$i}_batch"])) {
                                        echo "<div><span style='color:#999'>T$i:</span> " . htmlspecialchars($row["tank{$i}_batch"]) . "</div>";
                                    }
                                }
                            ?>
                        </td>
                        <td class="batch-list">
                            <?php if(!empty($row['master_mat'])): ?>
                                <div style="color:#1a73e8; font-weight:bold; margin-bottom: 4px;">Mat: <?php echo htmlspecialchars($row['master_mat']); ?></div>
                            <?php endif; ?>
                            <?php 
                                for($i=1; $i<=4; $i++) {
                                    if(!empty($row["master_batch{$i}"])) {
                                        echo "<div><span style='color:#999'>B$i:</span> " . htmlspecialchars($row["master_batch{$i}"]) . "</div>";
                                    }
                                }
                            ?>
                        </td>
                        <td>
                            <div style="display: flex; flex-direction: column; align-items: flex-start;">
                                <span class="badge status-badge"><?php echo htmlspecialchars($row['result_status']); ?></span>
                                <span class="badge schedule-ui" style="background: #eee; color: #666; border: 1px solid #ddd; font-size: 11px;">
                                    ⏳ 預留比對位
                                </span>
                            </div>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                <?php endif; ?>
            </tbody>
        </table>
    </div>

    <script>
        $(document).ready(function() {
            // 監聽「顯示排程核對」開關狀態
            $('#toggleSchedule').change(function() {
                if($(this).is(':checked')) {
                    $('.schedule-ui').fadeIn(200);
                } else {
                    $('.schedule-ui').fadeOut(200);
                }
            });

            // 初始化狀態
            if(!$('#toggleSchedule').is(':checked')) {
                $('.schedule-ui').hide();
            }
        });
    </script>
</body>
</html>
