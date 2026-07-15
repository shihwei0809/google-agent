<?php
// schedule_mgr.php
// 🟢 排程管理介面 (支援從 Excel 直接複製貼上)

require_once 'db.php';
$message = '';
$messageType = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $rawText = $_POST['schedule_data'] ?? '';
    // 將貼上的文字以換行符號切割成陣列
    $batches = explode("\n", str_replace("\r", "", $rawText));
    $validBatches = [];
    
    foreach($batches as $b) {
        $cleanBatch = trim($b);
        if ($cleanBatch !== '') {
            $validBatches[] = $cleanBatch;
        }
    }

    if (count($validBatches) > 0) {
        try {
            // 清空舊的排程資料
            $pdo->exec("TRUNCATE TABLE daily_schedules");
            
            // 寫入新排程
            $stmt = $pdo->prepare("INSERT INTO daily_schedules (batch_no) VALUES (?)");
            $pdo->beginTransaction();
            foreach ($validBatches as $batch) {
                $stmt->execute([$batch]);
            }
            $pdo->commit();
            
            $message = "✅ 成功更新！已匯入 " . count($validBatches) . " 筆有效批號。";
            $messageType = "success";
        } catch (Exception $e) {
            $pdo->rollBack();
            $message = "❌ 匯入失敗：" . $e->getMessage();
            $messageType = "error";
        }
    } else {
        // 如果傳入空值，代表要清空排程 (暫停核對功能)
        $pdo->exec("TRUNCATE TABLE daily_schedules");
        $message = "⚠️ 已清空所有排程！目前系統將【暫停】排程核對功能。";
        $messageType = "warning";
    }
}

// 取得目前資料庫中的排程數量
$currentCount = $pdo->query("SELECT COUNT(*) FROM daily_schedules")->fetchColumn();
?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>排程資料匯入</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Noto Sans TC', sans-serif; background: #f0f2f5; padding: 20px; color: #333; max-width: 600px; margin: 0 auto; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-top: 20px; }
        textarea { width: 100%; height: 250px; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-family: monospace; font-size: 14px; margin-bottom: 15px; }
        .btn-submit { background: #1a73e8; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; font-size: 16px; }
        .btn-submit:hover { background: #1557b0; }
        .alert { padding: 12px; border-radius: 6px; margin-bottom: 15px; font-weight: bold; }
        .alert.success { background: #e6f4ea; color: #137333; }
        .alert.error { background: #fce8e6; color: #c5221f; }
        .alert.warning { background: #fef7e0; color: #b06000; }
        .status-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .nav-links { margin-bottom: 20px; }
        .nav-links a { margin-right: 15px; color: #1a73e8; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="nav-links">
        <a href="index.php">⬅ 返回掃描頁</a>
        <a href="?page=query">📊 返回查詢頁</a>
    </div>

    <h2>📅 Excel 區間排程匯入</h2>
    
    <?php if($message): ?>
        <div class="alert <?php echo $messageType; ?>"><?php echo $message; ?></div>
    <?php endif; ?>

    <div class="card">
        <div class="status-bar">
            <span>請將 Excel 的「批號」整欄複製，並貼在下方：</span>
            <span style="background:#e8f0fe; color:#1a73e8; padding:4px 8px; border-radius:12px; font-size:12px; font-weight:bold;">
                目前系統內有 <?php echo $currentCount; ?> 筆排程
            </span>
        </div>
        
        <form method="POST">
            <textarea name="schedule_data" placeholder="範例：
225B29M8201 00021
225B29M8201 00022
1L140025...
(每行一個批號)"></textarea>
            <button type="submit" class="btn-submit">💾 更新並覆蓋排程</button>
            <p style="font-size: 12px; color: #888; text-align: center; margin-top: 10px;">提示：若要清空排程 (暫停核對功能)，請留白並直接點擊更新。</p>
        </form>
    </div>
</body>
</html>
