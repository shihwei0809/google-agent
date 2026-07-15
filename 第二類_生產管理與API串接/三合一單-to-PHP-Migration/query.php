<?php
// query.php - V37: 槽號樣式優化 (粗體+紅色)

$host = 'localhost';
$db   = 'ipacoacheck'; 
$user = 'root';      
$pass = '';      
$charset = 'utf8mb4';

$results = [];
$error = "";
$total_pages = 1;
$page = isset($_GET['page']) && is_numeric($_GET['page']) ? (int)$_GET['page'] : 1;
$records_per_page = 15; 

try {
    $dsn = "mysql:host=$host;dbname=$db;charset=$charset";
    $pdo = new PDO($dsn, $user, $pass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
    ]);

    $search     = $_GET['q'] ?? '';
    $start_date = $_GET['start_date'] ?? ''; 
    $end_date   = $_GET['end_date'] ?? '';   
    $offset     = ($page - 1) * $records_per_page;
    
    $conditions = [];
    $params = [];

    if (!empty($search)) {
        $conditions[] = "(batch_no LIKE ? OR material_no LIKE ? OR source_doc_no LIKE ? OR weighbridge_no LIKE ? OR supplier LIKE ?)";
        $params[] = "%$search%";
        $params[] = "%$search%";
        $params[] = "%$search%";
        $params[] = "%$search%";
        $params[] = "%$search%";
    }

    if (!empty($start_date)) {
        $conditions[] = "DATE(created_at) >= ?";
        $params[] = $start_date;
    }
    if (!empty($end_date)) {
        $conditions[] = "DATE(created_at) <= ?";
        $params[] = $end_date;
    }

    $where_sql = "";
    if (count($conditions) > 0) {
        $where_sql = "WHERE " . implode(' AND ', $conditions) . " ";
    }

    $count_sql = "SELECT COUNT(*) FROM coa_verification_logs " . $where_sql;
    $stmt_count = $pdo->prepare($count_sql);
    $stmt_count->execute($params);
    $total_records = $stmt_count->fetchColumn();
    $total_pages = ceil($total_records / $records_per_page);

    $sql = "SELECT * FROM coa_verification_logs " . $where_sql . "ORDER BY id DESC LIMIT $records_per_page OFFSET $offset";
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $results = $stmt->fetchAll();

} catch (PDOException $e) {
    $error = "資料庫連線錯誤: " . $e->getMessage();
}
?>

<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COA 核對紀錄列表</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f8fafc; }
        .table-header { background-color: #f1f5f9; color: #475569; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
        .table-row { transition: background-color 0.15s; border-bottom: 1px solid #e2e8f0; }
        .table-row:hover { background-color: #f8fafc; }
        .cell { padding: 12px 16px; white-space: nowrap; font-size: 0.875rem; color: #334155; vertical-align: middle; }
        .badge { padding: 2px 8px; border-radius: 99px; font-size: 0.7rem; font-weight: bold; display: inline-flex; align-items: center; gap: 4px; }
        .badge-success { background-color: #dcfce7; color: #166534; border: 1px solid #86efac; }
        .badge-fail { background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
        
        .btn-link { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-decoration: none; transition: all 0.2s; margin-right: 4px; }
        .btn-batch { background-color: #eff6ff; color: #2563eb; border: 1px solid #dbeafe; }
        .btn-batch:hover { background-color: #2563eb; color: white; }
        .btn-loc { background-color: #f0fdf4; color: #16a34a; border: 1px solid #dcfce7; }
        .btn-loc:hover { background-color: #16a34a; color: white; }
    </style>
</head>
<body>

    <div class="w-full mx-auto p-4">
        
        <div class="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 mb-4 bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div class="flex items-center gap-3 w-full xl:w-auto justify-between xl:justify-start">
                <div class="flex items-center gap-3">
                    <h1 class="text-lg font-bold text-gray-800 whitespace-nowrap">📋 COA 紀錄</h1>
                    <span class="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded font-mono">Total: <?= $total_records ?></span>
                </div>
                <a href="index.html" class="xl:hidden bg-gray-800 text-white px-3 py-2 rounded text-sm font-bold whitespace-nowrap">回掃描</a>
            </div>
            
            <div class="w-full xl:w-auto">
                <form method="GET" action="query.php" class="flex flex-col md:flex-row gap-2 w-full">
                    <div class="flex gap-2 items-center w-full md:w-auto bg-gray-50 p-1 rounded border border-gray-200">
                        <input type="date" name="start_date" value="<?= htmlspecialchars($start_date) ?>" 
                               class="bg-white p-1.5 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-blue-500 outline-none w-full md:w-36">
                        <span class="text-gray-400 font-bold">~</span>
                        <input type="date" name="end_date" value="<?= htmlspecialchars($end_date) ?>" 
                               class="bg-white p-1.5 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-blue-500 outline-none w-full md:w-36">
                    </div>

                    <div class="flex gap-2 w-full md:w-auto flex-1">
                        <input type="text" name="q" value="<?= htmlspecialchars($search) ?>" 
                               placeholder="搜尋批號/料號/單號/供應商..." 
                               class="flex-1 p-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 outline-none min-w-[150px]">
                        
                        <button type="submit" class="bg-blue-600 text-white px-5 py-2 rounded text-sm font-bold hover:bg-blue-700 whitespace-nowrap">搜尋</button>
                        
                        <?php if($search || $start_date || $end_date): ?>
                            <a href="query.php" class="bg-gray-100 text-gray-600 px-3 py-2 rounded text-sm font-bold hover:bg-gray-200 flex items-center justify-center whitespace-nowrap">清除</a>
                        <?php endif; ?>
                    </div>

                    <a href="index.html" class="hidden xl:flex bg-gray-800 text-white px-3 py-2 rounded text-sm font-bold hover:bg-gray-700 whitespace-nowrap items-center">回掃描</a>
                </form>
            </div>
        </div>

        <?php if ($error): ?>
            <div class="bg-red-50 text-red-600 p-3 rounded mb-4 text-sm border border-red-200 text-center"><?= $error ?></div>
        <?php endif; ?>

        <div class="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="table-header px-4 py-3 text-left">時間 / 狀態</th>
                            <th class="table-header px-4 py-3 text-left text-blue-700">批號 (Batch)</th>
                            <th class="table-header px-4 py-3 text-left text-purple-700">單據號碼</th>
                            <th class="table-header px-4 py-3 text-left">供應商</th>
                            <th class="table-header px-4 py-3 text-left">料號</th>
                            <th class="table-header px-4 py-3 text-left">槽號</th>
                            <th class="table-header px-4 py-3 text-left">地點</th>
                            <th class="table-header px-4 py-3 text-center">照片憑證</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        <?php if (count($results) > 0): ?>
                            <?php foreach ($results as $row): ?>
                                <tr class="table-row hover:bg-blue-50">
                                    <td class="cell">
                                        <div class="text-xs text-gray-400 mb-1"><?= date('m-d H:i', strtotime($row['created_at'])) ?></div>
                                        <span class="badge <?= strpos($row['verification_status'], '成功') !== false ? 'badge-success' : 'badge-fail' ?>">
                                            <?= strpos($row['verification_status'], '成功') !== false ? '✅ 成功' : '❌ 失敗' ?>
                                        </span>
                                    </td>
                                    <td class="cell font-bold text-blue-700 text-base">
                                        <?= htmlspecialchars($row['batch_no']) ?>
                                    </td>
                                    
                                    <td class="cell text-sm">
                                        <?php if (!empty($row['source_doc_no'])): ?>
                                            <div class="text-blue-700 font-bold">源: <?= htmlspecialchars($row['source_doc_no']) ?></div>
                                        <?php endif; ?>
                                        <?php if (!empty($row['weighbridge_no'])): ?>
                                            <div class="text-red-600 font-bold text-xs mt-1">磅: <?= htmlspecialchars($row['weighbridge_no']) ?></div>
                                        <?php endif; ?>
                                        <?php if (empty($row['source_doc_no']) && empty($row['weighbridge_no'])): ?>
                                            <span class="text-gray-300">-</span>
                                        <?php endif; ?>
                                    </td>

                                    <td class="cell text-gray-700 font-medium">
                                        <?= htmlspecialchars($row['supplier']) ?: '<span class="text-gray-300">-</span>' ?>
                                    </td>

                                    <td class="cell font-mono text-gray-500">
                                        <?= htmlspecialchars($row['material_no']) ?>
                                    </td>
                                    
                                    <td class="cell font-bold text-red-600 text-base">
                                        <?= htmlspecialchars($row['tank_no']) ?>
                                    </td>

                                    <td class="cell text-gray-500 text-xs">
                                        <?= htmlspecialchars($row['delivery_place']) ?>
                                    </td>
                                    
                                    <td class="cell text-center">
                                        <div class="flex flex-col gap-1 items-center justify-center">
                                            <?php if (!empty($row['photo_filename'])): ?>
                                                <a href="uploads/<?= htmlspecialchars($row['photo_filename']) ?>" target="_blank" 
                                                   class="btn-link btn-batch">
                                                   📦 批號
                                                </a>
                                            <?php endif; ?>
                                            <?php if (!empty($row['photo_location'])): ?>
                                                <a href="uploads/<?= htmlspecialchars($row['photo_location']) ?>" target="_blank" 
                                                   class="btn-link btn-loc">
                                                   🏭 地磅
                                                </a>
                                            <?php endif; ?>
                                        </div>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                        <?php else: ?>
                            <tr>
                                <td colspan="8" class="px-6 py-10 text-center text-gray-400">
                                    📭 查無資料
                                </td>
                            </tr>
                        <?php endif; ?>
                    </tbody>
                </table>
            </div>
        </div>

        <?php if ($total_pages > 1): ?>
        <div class="mt-4 flex justify-between items-center bg-white p-3 rounded-lg border border-gray-200 shadow-sm">
            <?php 
                $queryStr = "&q=" . urlencode($search) . "&start_date=" . urlencode($start_date) . "&end_date=" . urlencode($end_date);
            ?>
            
            <?php if ($page > 1): ?>
                <a href="?page=<?= $page - 1 ?><?= $queryStr ?>" class="text-sm px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 text-gray-700 font-bold">« 上一頁</a>
            <?php else: ?>
                <span class="text-sm px-3 py-1 bg-gray-50 rounded text-gray-300 cursor-not-allowed">« 上一頁</span>
            <?php endif; ?>

            <span class="text-sm text-gray-600 font-bold">頁次 <?= $page ?> / <?= $total_pages ?></span>

            <?php if ($page < $total_pages): ?>
                <a href="?page=<?= $page + 1 ?><?= $queryStr ?>" class="text-sm px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 text-gray-700 font-bold">下一頁 »</a>
            <?php else: ?>
                <span class="text-sm px-3 py-1 bg-gray-50 rounded text-gray-300 cursor-not-allowed">下一頁 »</span>
            <?php endif; ?>
        </div>
        <?php endif; ?>

    </div>
</body>
</html>
