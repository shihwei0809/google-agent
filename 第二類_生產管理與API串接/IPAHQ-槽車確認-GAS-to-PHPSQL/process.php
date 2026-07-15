<?php
header('Content-Type: application/json; charset=utf-8');

// --- 1. 資料庫連線 ---
$host = '127.0.0.1';
$db   = 'ipahqtankcheck';
$user = 'root';
$pass = '';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$db;charset=utf8mb4", $user, $pass, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
} catch (PDOException $e) {
    echo json_encode(['success' => false, 'message' => "資料庫連線失敗"]); exit;
}

// --- 2. 接收資料 ---
$data = json_decode(file_get_contents('php://input'), true);
if (!$data) { echo json_encode(['success' => false, 'message' => "無效請求"]); exit; }

$mainQr = strtoupper(trim($data['mainQr']));
$check1 = strtoupper(trim($data['check1']));
$check2 = strtoupper(trim($data['check2']));
$photoData = $data['photoData'] ?? '';

// --- 3. 邏輯核對 ---
if (empty($mainQr) || empty($check1) || empty($check2)) {
    echo json_encode(['success' => false, 'message' => "欄位不完整"]); exit;
}
if (strpos($mainQr, $check1) === false) {
    echo json_encode(['success' => false, 'message' => "❌ 核對失敗：槽號不在主單內"]); exit;
}
if ($check1 !== $check2) {
    echo json_encode(['success' => false, 'message' => "❌ 核對失敗：A/B 槽號不符"]); exit;
}

// --- 4. 處理圖片 (E 槽存儲，選填) ---
$dbPath = ""; 
if (!empty($photoData) && strpos($photoData, 'base64') !== false) {
    $month = (int)date('m');
    $year = date('Y');
    $group = (ceil($month / 2) * 2 - 1) . "-" . (ceil($month / 2) * 2) . "月";
    $folderName = $year . "_" . $group;

    $baseDir = "E:/tanker_photos/";
    $targetDir = $baseDir . $folderName . "/";

    // 自動建立資料夾
    if (!is_dir($targetDir)) {
        mkdir($targetDir, 0777, true);
    }

    $imgParts = explode(',', $photoData);
    $imgData = base64_decode($imgParts[1]);
    $fileName = "Check_" . $check1 . "_" . time() . ".jpg";
    $fullSavePath = $targetDir . $fileName;

    if (file_put_contents($fullSavePath, $imgData)) {
        $dbPath = "show_image.php?path=" . urlencode($folderName . "/" . $fileName);
    }
}

// --- 5. 寫入資料庫 ---
$stmt = $pdo->prepare("INSERT INTO tanker_logs (main_qr, check_a, check_b, photo_url, client_ip) VALUES (?, ?, ?, ?, ?)");
$stmt->execute([$mainQr, $check1, $check2, $dbPath, $_SERVER['REMOTE_ADDR']]);

echo json_encode(['success' => true, 'message' => "✅ 資料核對成功並已存檔！"]);
