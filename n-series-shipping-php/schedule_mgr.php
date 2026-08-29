<?php
// schedule_mgr.php
require_once 'db_config.php';
require_once 'Logic.php'; // 需使用 ShippingHelper::normalizeBatch

$message = "";

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $rawText = $_POST['schedule_text'] ?? '';
    
    if (!empty($rawText)) {
        try {
            // 1. 先清空舊排程 (或是您可以根據需求改為增加)
            $pdo->exec("TRUNCATE TABLE daily_schedules");
            
            // 2. 解析文字，依換行或逗號拆分
            $rows = preg_split('/[\n\r,]+/', $rawText);
            $count = 0;
            
            $stmt = $pdo->prepare("INSERT INTO daily_schedules (batch_no) VALUES (?)");
            
            foreach ($rows as $row) {
                $cleanBatch = ShippingHelper::normalizeBatch(trim($row));
                if ($cleanBatch !== "") {
                    $stmt->execute([$cleanBatch]);
                    $count++;
                }
            }
            $message = "<div class='success'>✅ 排程更新成功！共匯入 $count 筆批號。</div>";
        } catch (Exception $e) {
            $message = "<div class='error'>❌ 匯入失敗: " . $e->getMessage() . "</div>";
        }
    }
}
?>
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>T100 排程管理</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Noto Sans TC', sans-serif; background: #f0f2f5; padding: 20px; display: flex; justify-content: center; }
        .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 100%; max-width: 500px; }
        h2 { color: #1a73e8; margin-top: 0; }
        textarea { width: 100%; height: 300px; padding: 12px; border: 1px solid #ccc; border-radius: 8px; box-sizing: border-box; font-family: monospace; resize: vertical; }
        .btn-save { width: 100%; background: #1a73e8; color: white; border: none; padding: 15px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 15px; }
        .success { background: #e6f4ea; color: #137333; padding: 10px; border-radius: 5px; margin-bottom: 15px; }
        .error { background: #fce8e6; color: #c5221f; padding: 10px; border-radius: 5px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🛡️ T100 排程匯入</h2>
        <p style="font-size: 14px; color: #666;">請從 T100 複製批號欄位，直接貼在下方：</p>
        <?php echo $message; ?>
        <form method="POST">
            <textarea name="schedule_text" placeholder="例如：
            7240301001
            7240301002
            1240305001TS..."></textarea>
            <button type="submit" class="btn-save">💾 覆蓋並更新排程</button>
        </form>
        <div style="margin-top: 20px; text-align: center;">
            <a href="index.php" style="color: #5f6368; text-decoration: none; font-size: 14px;">← 返回現場掃描</a>
        </div>
    </div>
</body>
</html>
