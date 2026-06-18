<?php
header('Content-Type: application/json');

// 1. 資料庫連線設定
$host = 'localhost';
$db   = 'your_database_name';
$user = 'your_username';
$pass = 'your_password';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$db;charset=utf8mb4", $user, $pass);
    
    // 2. 接收 JSON 資料
    $json = file_get_contents('php://input');
    $data = json_decode($json, true);

    if (!$data) {
        throw new Exception("無效的資料輸入");
    }

    // 3. 處理圖片儲存 (Base64 轉檔案)
    $photoData = $data['photoData'];
    $fileName = "";
    
    if (!empty($photoData)) {
        $folderPath = "uploads/";
        if (!is_dir($folderPath)) mkdir($folderPath, 0755, true);
        
        $parts = explode(',', $photoData);
        $imageType = str_replace(['data:image/', ';base64'], '', explode(':', $parts[0])[1]);
        $imageData = base64_decode($parts[1]);
        
        $fileName = "Check_" . $data['check1'] . "_" . time() . "." . $imageType;
        file_put_contents($folderPath . $fileName, $imageData);
    }

    // 4. 寫入資料庫
    $stmt = $pdo->prepare("INSERT INTO validation_data (main_qr, check1, check2, photo_path) VALUES (?, ?, ?, ?)");
    $stmt->execute([
        $data['mainQr'],
        $data['check1'],
        $data['check2'],
        "uploads/" . $fileName
    ]);

    echo json_encode(['success' => true, 'message' => "✅ 資料上傳成功！"]);

} catch (Exception $e) {
    echo json_encode(['success' => false, 'message' => "錯誤: " . $e->getMessage()]);
}
?>
