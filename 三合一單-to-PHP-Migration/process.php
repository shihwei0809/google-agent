<?php
// process.php - V45: 客製化地點比對 (三合一去頭尾 vs T100廠別+廠區)

error_reporting(0);
ini_set('display_errors', 0);
header('Content-Type: application/json; charset=utf-8');
ini_set('memory_limit', '256M');

$host = 'localhost';
$db   = 'ipacoacheck'; 
$user = 'root';      
$pass = '';      
$charset = 'utf8mb4';

// ★★★ 雙 API Key 分流 ★★★
$apiKeys = [
    'AIzaSyCxpDwmsFfKtYkz-_rnqPJW_iVh5j-wQd4',
    'AIzaSyCdI7WZKnyUtYL0mubKslz7Cvq2wqStS_8'
];
$keyIndex = intval(date('s')) % 2;
$currentKey = $apiKeys[$keyIndex];

function callGoogleVision($base64Image, $apiKey) {
    if (strpos($base64Image, ',') !== false) {
        $parts = explode(',', $base64Image);
        $base64Image = end($parts);
    }
    $apiUrl = 'https://vision.googleapis.com/v1/images:annotate?key=' . $apiKey;
    $requestData = [
        'requests' => [ [
            'image' => [ 'content' => $base64Image ],
            'features' => [ [ 'type' => 'TEXT_DETECTION', 'maxResults' => 10 ] ]
        ] ]
    ];
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $apiUrl);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($requestData));
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false); 
    $result = curl_exec($ch);
    curl_close($ch);
    return json_decode($result, true);
}

try {
    $dsn = "mysql:host=$host;dbname=$db;charset=$charset";
    $pdo = new PDO($dsn, $user, $pass, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

    $inputJSON = file_get_contents('php://input');
    $input = json_decode($inputJSON, true);
    if (!$input) throw new Exception('未收到資料');

    $rawQrBatch = trim($input['batchNo'] ?? '');
    $rawLoc     = trim($input['deliveryPlace'] ?? ''); 
    $rawTank    = trim($input['tankNo'] ?? ''); 
    $inputSupplier = trim($input['supplier'] ?? ''); 
    
    $photoBatch = $input['photoBatch'] ?? ''; 
    $photoLoc   = $input['photoLoc'] ?? '';   

    if (empty($photoBatch) || empty($photoLoc)) throw new Exception('請拍攝兩張照片');

    // 📸 解析照片
    $ocrResultBatch = callGoogleVision($photoBatch, $currentKey);
    $textCOA = $ocrResultBatch['responses'][0]['fullTextAnnotation']['text'] ?? '';
    $cleanCOA = preg_replace('/\s+/', '', strtoupper($textCOA));

    $ocrResultLoc = callGoogleVision($photoLoc, $currentKey);
    $textWeigh = $ocrResultLoc['responses'][0]['fullTextAnnotation']['text'] ?? '';
    $cleanWeigh = preg_replace('/\s+/', '', strtoupper($textWeigh));

    // 1. 雙單號抓取 (11碼截斷)
    $sourceDocNo = "";   
    $weighbridgeNo = ""; 
    if (preg_match('/(ESXM101-[0-9A-Z]{11})/', $cleanWeigh, $matches)) $sourceDocNo = $matches[1];
    if (preg_match('/(ESXM201-[0-9A-Z]{11})/', $cleanWeigh, $matches)) $weighbridgeNo = $matches[1];

    // 2. 供應商自動補償
    $finalSupplier = $inputSupplier;
    if (empty($finalSupplier)) {
        if (preg_match('/供應商[\s:.]*([0-9]{5,})/u', $textWeigh, $m)) $finalSupplier = $m[1];
        elseif (preg_match('/(3759[0-9]+|1000[0-9]{3,})/', $cleanWeigh, $m)) $finalSupplier = $m[1];
    }

    // ⚙️ 比對參數
    $replacements = ['O'=>'0', 'D'=>'0', 'Q'=>'0', 'I'=>'1', 'L'=>'1', '|'=>'1', 'Z'=>'2', 'S'=>'5', 'B'=>'8', 'G'=>'6'];
    $fuzzyWeigh = strtr($cleanWeigh, $replacements);

    // A. 批號
    $cleanRawBatch = preg_replace('/\s+/', '', strtoupper($rawQrBatch));
    $batchTargets = [];
    if (!empty($cleanRawBatch)) { 
        $batchTargets[] = $cleanRawBatch;
        if (substr($cleanRawBatch, 0, 1) === '6' || strlen($cleanRawBatch) >= 11) $batchTargets[] = substr($cleanRawBatch, 1);
    }
    
    // B. 槽號
    $cleanRawTank = preg_replace('/\s+/', '', strtoupper($rawTank));
    $tankTargets = [];
    if (!empty($cleanRawTank)) { 
        $tankTargets[] = $cleanRawTank;
        if (substr($cleanRawTank, 0, 1) === '5') $tankTargets[] = substr($cleanRawTank, 1);
        if (strlen($cleanRawTank) > 3) $tankTargets[] = substr($cleanRawTank, 1);
        $tankTargets = array_unique($tankTargets);
    }

    // C. 地點變體 (標準版)
    $locTarget = preg_replace('/\s+/', '', strtoupper($rawLoc));
    $locTargets = [];
    if (!empty($locTarget)) { 
        $locTargets[] = $locTarget;
        if (strlen($locTarget) > 3) {
            if (substr($locTarget, 0, 1) === 'E') $locTargets[] = substr($locTarget, 1);
            if (substr($locTarget, -1) === 'A') $locTargets[] = substr($locTarget, 0, -1);
            if (substr($locTarget, 0, 1) === 'E' && substr($locTarget, -1) === 'A') $locTargets[] = substr($locTarget, 1, -1);
        }
    }

    // 🛑 關卡 1: COA 批號
    $check1_Batch = false;
    if (!empty($batchTargets)) {
        $fuzzyCOA = strtr($cleanCOA, $replacements);
        foreach ($batchTargets as $t) {
            $fuzzyT = strtr($t, $replacements);
            if (strpos($cleanCOA, $t) !== false || strpos($fuzzyCOA, $fuzzyT) !== false) {
                $check1_Batch = true; break;
            }
        }
    }

    // ==========================================
    // 🛑 關卡 2: 地磅 地點 (V45 重點修正)
    // ==========================================
    $check2_Loc = false;
    $locDebugMsg = ""; // 用來顯示系統拼湊了什麼，方便除錯

    // 1. 標準比對 (既有邏輯：直接找字串)
    if (!empty($locTargets)) {
        foreach ($locTargets as $lt) {
            $fuzzyLT = strtr($lt, $replacements);
            if (strpos($cleanWeigh, $lt) !== false || strpos($fuzzyWeigh, $fuzzyLT) !== false) {
                $check2_Loc = true; break;
            }
        }
    }

    // 2. ★★★ V45 新增：T100 拆解組合比對 ★★★
    // 只有當上面標準比對失敗，且目標長度夠長時才執行
    if (!$check2_Loc && strlen($locTarget) > 5) {
        
        // 步驟 A: 三合一單「去頭去尾」 (例如 E1550156A -> 1550156)
        $sheetCore = substr($locTarget, 1, -1);
        $fuzzySheetCore = strtr($sheetCore, $replacements);

        // 步驟 B: 從照片中「挖」出廠別與廠區
        $t100_Factory = "";
        $t100_Area = "";

        // 抓取 "廠別" 後面的 4 碼 (例如 F180 或 1550)
        // \D* 代表忽略中間的非數字字元 (如空格、冒號)
        if (preg_match('/廠別\D*([A-Z0-9]{4})/u', $cleanWeigh, $m)) {
            $t100_Factory = $m[1];
        }

        // 抓取 "廠區" 後面的 3 碼 (例如 182B 取 182)
        if (preg_match('/廠區\D*([A-Z0-9]{3})/u', $cleanWeigh, $m)) {
            $t100_Area = $m[1];
        }

        // 步驟 C: 組合 (廠別 + 廠區)
        if (!empty($t100_Factory) && !empty($t100_Area)) {
            $t100_Combined = $t100_Factory . $t100_Area;
            $fuzzy_T100_Combined = strtr($t100_Combined, $replacements);

            // 步驟 D: 比對 (支援模糊比對)
            if ($sheetCore === $t100_Combined || 
                $fuzzySheetCore === $fuzzy_T100_Combined ||
                strpos($t100_Combined, $sheetCore) !== false) { // 寬容模式：包含也算過
                $check2_Loc = true;
            } else {
                // 如果抓到了但比對失敗，記錄下來方便除錯
                $locDebugMsg = "(系統拼湊: $t100_Combined vs 單據: $sheetCore)";
            }
        }
    }

    // 🛑 關卡 3: 地磅 槽號
    $check3_Tank = false; $tankErrorMsg = "";
    if (empty($tankTargets)) {
        $check3_Tank = false; $tankErrorMsg = "(QR Code 缺少槽號)";
    } else {
        $textForTankCheck = $cleanWeigh;
        $fuzzyTextForTankCheck = $fuzzyWeigh; 
        foreach ($batchTargets as $bt) {
            $textForTankCheck = str_replace($bt, '------', $textForTankCheck);
            $fuzzyBT = strtr($bt, $replacements);
            $fuzzyTextForTankCheck = str_replace($fuzzyBT, '------', $fuzzyTextForTankCheck);
        }
        foreach ($tankTargets as $tankT) {
            if (empty($tankT)) continue;
            $fuzzyTankT = strtr($tankT, $replacements);
            if (strpos($textForTankCheck, $tankT) !== false || strpos($fuzzyTextForTankCheck, $fuzzyTankT) !== false) {
                $check3_Tank = true; break;
            }
        }
        if (!$check3_Tank) $tankErrorMsg = "(未發現獨立槽號)";
    }

    // 🛑 關卡 4: 地磅 批號
    $check4_SystemBatch = false;
    $batchDebugMsg = "";
    if (!empty($batchTargets)) {
        foreach ($batchTargets as $t) {
            $fuzzyT = strtr($t, $replacements);
            if (strpos($cleanWeigh, $t) !== false || strpos($fuzzyWeigh, $fuzzyT) !== false) {
                $check4_SystemBatch = true; break;
            }
        }
    }
    if (!$check4_SystemBatch) {
        preg_match_all('/(26[0-9A-Z]{7,}|626[0-9A-Z]{7,})/', $cleanWeigh, $candidates);
        if (!empty($candidates[0])) {
            $batchDebugMsg = "\n🔍 系統發現疑似: " . implode(", ", array_slice($candidates[0], 0, 2));
        } else {
            $batchDebugMsg = "\n🔍 AI 讀到開頭: " . mb_substr($cleanWeigh, 0, 15) . "...";
        }
    }

    $isSuccess = $check1_Batch && $check2_Loc && $check3_Tank && $check4_SystemBatch;
    $responseMsg = $isSuccess ? "✅ 四重核對成功！" : "❌ 核對失敗";
    $responseMsg .= "\n----------------";
    if ($check1_Batch) $responseMsg .= "\n✅ COA批號: OK"; else $responseMsg .= "\n❌ COA批號不符";
    
    // 顯示地點結果 + 除錯資訊
    if ($check2_Loc) $responseMsg .= "\n✅ 地點: OK"; 
    else $responseMsg .= "\n❌ 地點不符 " . $locDebugMsg;

    if ($check3_Tank) $responseMsg .= "\n✅ 槽號: OK"; else $responseMsg .= "\n❌ 槽號不符 " . $tankErrorMsg;
    
    if ($check4_SystemBatch) $responseMsg .= "\n✅ 系統批號: OK"; 
    else $responseMsg .= "\n❌ 系統批號不符" . $batchDebugMsg;

    if (!empty($sourceDocNo)) $responseMsg .= "\n📄 來源: " . $sourceDocNo;
    if (!empty($weighbridgeNo)) $responseMsg .= "\n⚖️ 磅單: " . $weighbridgeNo;
    if (!empty($finalSupplier)) $responseMsg .= "\n🏭 供應商: " . $finalSupplier;

    // 存檔
    if ($isSuccess) {
        $monthFolder = date("Ym");
        $targetDir = 'uploads/' . $monthFolder . '/';
        if (!file_exists($targetDir)) mkdir($targetDir, 0777, true);

        $file1Name = "Batch_" . preg_replace('/[^A-Za-z0-9]/', '', $rawQrBatch) . "_" . date("Ymd_His") . ".jpg";
        $file2Name = "Loc_" . preg_replace('/[^A-Za-z0-9]/', '', $rawLoc) . "_" . date("Ymd_His") . ".jpg";
        
        file_put_contents($targetDir . $file1Name, base64_decode(explode(',', $photoBatch)[1]));
        file_put_contents($targetDir . $file2Name, base64_decode(explode(',', $photoLoc)[1]));

        $sql = "INSERT INTO coa_verification_logs 
                (material_no, tank_no, batch_no, supplier, delivery_place, raw_qr, source_doc_no, weighbridge_no, verification_status, photo_filename, photo_location, ocr_snippet) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
        
        $pdo->prepare($sql)->execute([
            $input['materialNo'], $input['tankNo'], $input['batchNo'],
            $finalSupplier, 
            $input['deliveryPlace'], $input['rawQr'],
            $sourceDocNo, $weighbridgeNo, 
            "四重核對成功", $monthFolder.'/'.$file1Name, $monthFolder.'/'.$file2Name, ""
        ]);
    }

    echo json_encode(['success' => $isSuccess, 'message' => $responseMsg]);

} catch (Exception $e) {
    echo json_encode(['success' => false, 'message' => '系統錯誤: ' . $e->getMessage()]);
}
?>
