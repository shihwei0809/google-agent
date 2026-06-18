<?php
$pdo = new PDO("mysql:host=127.0.0.1;dbname=ipahqtankcheck;charset=utf8mb4", 'root', '', [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

if (isset($_GET['export'])) {
    header("Content-Type: application/vnd.ms-excel; charset=utf-8");
    header("Content-Disposition: attachment; filename=槽車紀錄_" . date('Ymd') . ".xls");
    echo "\xEF\xBB\xBF<table border='1'><tr><th>時間</th><th>主單 QR</th><th>槽號 A</th><th>槽號 B</th></tr>";
    $stmt = $pdo->query("SELECT * FROM tanker_logs ORDER BY created_at DESC");
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        echo "<tr><td>{$row['created_at']}</td><td>'{$row['main_qr']}</td><td>'{$row['check_a']}</td><td>'{$row['check_b']}</td></tr>";
    }
    echo "</table>"; exit;
}

$rows = $pdo->query("SELECT * FROM tanker_logs ORDER BY created_at DESC LIMIT 100")->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>歷史紀錄</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light p-4">
    <div class="container bg-white p-4 shadow rounded">
        <div class="d-flex justify-content-between mb-4">
            <h2 class="fw-bold text-success">🚚 槽車核對紀錄</h2>
            <div>
                <a href="?export=1" class="btn btn-primary">📊 匯出 Excel</a>
                <a href="index.php" class="btn btn-outline-secondary">返回掃描</a>
            </div>
        </div>
        <table class="table table-striped align-middle">
            <thead class="table-dark">
                <tr><th>時間</th><th>槽號</th><th>主單</th><th>照片</th></tr>
            </thead>
            <tbody>
                <?php foreach($rows as $r): ?>
                <tr>
                    <td><?= $r['created_at'] ?></td>
                    <td><span class="badge bg-primary"><?= $r['check_a'] ?></span></td>
                    <td style="max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;"><?= $r['main_qr'] ?></td>
                    <td>
                        <?php if($r['photo_url']): ?>
                            <a href="<?= $r['photo_url'] ?>" target="_blank"><img src="<?= $r['photo_url'] ?>" width="60" class="rounded shadow-sm"></a>
                        <?php else: ?>
                            <span class="text-muted small">無照片</span>
                        <?php endif; ?>
                    </td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    </div>
</body>
</html>
