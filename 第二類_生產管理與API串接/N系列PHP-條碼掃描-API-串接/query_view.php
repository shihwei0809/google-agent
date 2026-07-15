<?php
// query_view.php
// 🟢 MySQL 資料庫讀取專用版 (V3.0: 修正欄位寬度)

require_once 'db.php'; 

$defaultStart = date('Y-m-01');
$defaultEnd = date('Y-m-d');
$dateStart = $_GET['dateStart'] ?? $defaultStart;
$dateEnd = $_GET['dateEnd'] ?? $defaultEnd;
$keyword = $_GET['keyword'] ?? '';

$sql = "SELECT * FROM shipment_records WHERE DATE(created_at) BETWEEN ? AND ?";
$params = [$dateStart, $dateEnd];

if ($keyword) {
    $sql .= " AND (
        box_barcode LIKE ? OR 
        tank1_batch LIKE ? OR tank2_batch LIKE ? OR tank3_batch LIKE ? OR tank4_batch LIKE ? OR
        master_batch1 LIKE ?
    )";
    $likeKey = "%$keyword%";
    array_push($params, $likeKey, $likeKey, $likeKey, $likeKey, $likeKey, $likeKey);
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
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>出貨紀錄查詢 (MySQL)</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Noto Sans TC', sans-serif; background: #f0f2f5; padding: 20px; color: #333; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .btn-back { background: #5f6368; color: white; padding: 8px 16px; border-radius: 20px; text-decoration: none; font-size: 14px; }
        
        .search-card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
        .search-card input { padding: 8px; border: 1px solid #ddd; border-radius: 5px; }
        .btn-search { background: #1a73e8; color: white; border: none; padding: 8px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .btn-search:hover { background: #1557b0; }

        .table-container { overflow-x: auto; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; min-width: 900px; }
        
        /* 👇 關鍵修改：移除 th 的固定 width，讓它們更寬敞 */
        th { background: #f8f9fa; color: #444; padding: 12px; text-align: left; font-weight: bold; border-bottom: 2px solid #eee; white-space: nowrap; }
        
        td { padding: 12px; border-bottom: 1px solid #eee; font-size: 14px; vertical-align: top; }
        tr:hover { background-color: #f1f3f4; }
        
        .badge { display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .mode-badge { background: #e8f0fe; color: #1967d2; }
        .status-badge { background: #e6f4ea; color: #137333; }
        .batch-list { font-family: monospace; line-height: 1.4; color: #555; }
        .db-status { font-size: 12px; color: #137333; background: #e6f4ea; padding: 5px 10px; border-radius: 4px; border: 1px solid #ceead6; }
    </style>
</head>
<body>

    <div class="header">
        <a href="index.php" class="btn-back">⬅ 返回掃描頁</a>
        <div style="text-align:right;">
            <h2 style="margin:0; color:#1a73e8;">📊 出貨紀錄查詢</h2>
            <span class="db-status">🟢 MySQL 連線正常 (共 <?php echo $rowCount; ?> 筆)</span>
        </div>
    </div>

    <form class="search-card">
        <input type="hidden" name="page" value="query"> 
        <label>日期範圍：</label>
        <input type="date" name="dateStart" value="<?php echo $dateStart; ?>">
        <span>~</span>
        <input type="date" name="dateEnd" value="<?php echo $dateEnd; ?>">
        <input type="text" name="keyword" placeholder="輸入外箱或批號..." value="<?php echo htmlspecialchars($keyword); ?>" style="flex-grow:1;">
        <button type="submit" class="btn-search">🔍 查詢</button>
    </form>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th width="5%">ID</th>
                    <th width="20%">時間 / 場所</th>
                    <th width="8%">模式</th>
                    <th width="20%">外箱條碼 / 料號</th>
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
                            <div style="font-weight:bold; font-size:16px;"><?php echo $row['location']; ?></div>
                            <div style="color:#666; font-size:13px; margin-top:4px;">
                                <?php echo date('Y/m/d H:i', strtotime($row['created_at'])); ?>
                            </div>
                        </td>
                        <td><span class="badge mode-badge"><?php echo $row['mode']; ?></span></td>
                        <td>
                            <div style="word-break: break-all; font-weight:bold; color:#333;">
                                <?php echo htmlspecialchars($row['box_barcode']); ?>
                            </div>
                            <?php if($row['box_mat']): ?>
                            <div style="color:#666; font-size:12px; margin-top:4px;">
                                料號: <?php echo $row['box_mat']; ?> / 效期: <?php echo $row['box_expiry']; ?>
                            </div>
                            <?php endif; ?>
                        </td>
                        <td class="batch-list">
                            <?php 
                                for($i=1; $i<=4; $i++) {
                                    if(!empty($row["tank{$i}_batch"])) {
                                        echo "<div><span style='color:#999'>T$i:</span> " . $row["tank{$i}_batch"] . "</div>";
                                    }
                                }
                            ?>
                        </td>
                        <td class="batch-list">
                            <?php if(!empty($row['master_mat'])): ?>
                                <div style="color:#1a73e8; font-weight:bold;">Mat: <?php echo $row['master_mat']; ?></div>
                            <?php endif; ?>
                            <?php 
                                for($i=1; $i<=4; $i++) {
                                    if(!empty($row["master_batch{$i}"])) {
                                        echo "<div><span style='color:#999'>B$i:</span> " . $row["master_batch{$i}"] . "</div>";
                                    }
                                }
                            ?>
                        </td>
                        <td><span class="badge status-badge"><?php echo $row['result_text']; ?></span></td>
                    </tr>
                    <?php endforeach; ?>
                <?php endif; ?>
            </tbody>
        </table>
    </div>

</body>
</html>
