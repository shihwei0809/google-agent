<?php
header('Content-Type: application/json');
require_once 'db_config.php';
require_once 'Logic.php'; // 包含 ShippingHelper 類別

// 接收 JSON 資料
$rawData = file_get_contents("php://input");
$data = json_decode($rawData, true);

if (!$data) {
    echo json_encode(['status' => 'error', 'message' => '無效的資料請求']);
    exit;
}

$f = $data['fields'];
$mode = $data['mode'];
$location = $data['location'];
$allErrors = [];

// ==========================================
// 1. T100 排程防呆攔截邏輯
// ==========================================
if ($mode !== 'ship_az') {
    $scannedBatches = [];
    // 收集桶槽掃描的批號 (f0, f2, f4, f6)
    foreach([0, 2, 4, 6] as $idx) {
        if (!empty($f[$idx])) {
            $scannedBatches[] = ShippingHelper::normalizeBatch($f[$idx]);
        }
    }

    if (!empty($scannedBatches)) {
        // 檢查批號是否在 daily_schedules 白名單中
        $placeholders = implode(',', array_fill(0, count($scannedBatches), '?'));
        $stmt = $pdo->prepare("SELECT batch_no FROM daily_schedules WHERE batch_no IN ($placeholders)");
        $stmt->execute($scannedBatches);
        $foundBatches = $stmt->fetchAll(PDO::FETCH_COLUMN);

        foreach ($scannedBatches as $sb) {
            if (!in_array($sb, $foundBatches)) {
                $allErrors[] = "⚠️ 攔截：批號 [$sb] 不在今日匯入的排程清單中！";
            }
        }
    }
}

// ==========================================
// 2. 基本邏輯檢查 (例如料號一致性)
// ==========================================
if ($mode !== 'ship_az') {
    $masterMat = ShippingHelper::cleanMatMaster($f[8]);
    if (empty($masterMat)) {
        $allErrors[] = "❌ 四合一料號為必填項。";
    }
}

// ==========================================
// 3. 執行寫入或回傳錯誤
// ==========================================
if (!empty($allErrors)) {
    echo json_encode(['status' => 'error', 'message' => implode("<br>", $allErrors)]);
    exit;
}

try {
    $sql = "INSERT INTO shipping_records (
        work_location, mode, 
        tank1_batch, tank1_mat, tank2_batch, tank2_mat, 
        tank3_batch, tank3_mat, tank4_batch, tank4_mat,
        master_mat, master_batch1, master_batch2, master_batch3, master_batch4,
        wh_mat, wh_batch1, wh_batch2, wh_batch3, result_status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

    $stmt = $pdo->prepare($sql);
    $params = [
        $location, $mode,
        $f[0], $f[1], $f[2], $f[3], $f[4], $f[5], $f[6], $f[7],
        $f[8], $f[9], $f[10], $f[11], $f[12],
        $f[13], $f[14], $f[15], $f[16], "批號一致 合格"
    ];
    $stmt->execute($params);

    echo json_encode(['status' => 'success', 'message' => '✅ 紀錄成功！']);
} catch (Exception $e) {
    echo json_encode(['status' => 'error', 'message' => '資料庫存檔失敗: ' . $e->getMessage()]);
}
