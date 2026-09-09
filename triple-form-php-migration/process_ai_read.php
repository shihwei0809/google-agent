<?php
// process_ai_read.php - V43: 雙 API Key 奇偶秒數強制分流 (AI 讀單專用)

error_reporting(0);
ini_set('display_errors', 0);
header('Content-Type: application/json; charset=utf-8');
mb_internal_encoding("UTF-8");

// ★★★ 設定雙 API Key ★★★
$apiKeys = [
    'AIzaSyCxpDwmsFfKtYkz-_rnqPJW_iVh5j-wQd4',
    'AIzaSyCdI7WZKnyUtYL0mubKslz7Cvq2wqStS_8'
];

// ★★★ V43: 依照「秒數」決定使用哪一組 ★★★
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

function callGeminiApi($base64Image, $apiKey) {
    if (strpos($base64Image, ',') !== false) {
        $parts = explode(',', $base64Image);
        $base64Image = end($parts);
    }
    $apiUrl = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key=' . $apiKey;
    $requestData = [
        "contents" => [ [
            "parts" => [
                ["text" => "請將這張出貨單上的所有文字完整辨識出來，不要遺漏任何數字、料號、槽號、批號或地點。不要做任何解釋，直接輸出原始文字。"],
                ["inline_data" => ["mime_type" => "image/jpeg", "data" => $base64Image]]
            ]
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
    $json = json_decode($result, true);
    if (isset($json['candidates'][0]['content']['parts'][0]['text'])) {
        return $json['candidates'][0]['content']['parts'][0]['text'];
    }
    if (isset($json['error'])) {
        throw new Exception("Gemini API Error: " . $json['error']['message']);
    }
    return "";
}

try {
    $inputJSON = file_get_contents('php://input');
    $input = json_decode($inputJSON, true);
    $photoData = $input['photoData'] ?? '';
    $geminiKey = $input['geminiKey'] ?? '';

    if (empty($photoData)) throw new Exception('未收到照片');

    // 呼叫 AI (有 Gemini Key 則優先用 Gemini，否則退回舊版 GCP Vision)
    $text = '';
    if (!empty($geminiKey)) {
        $text = callGeminiApi($photoData, $geminiKey);
    } else {
        $ocrResult = callGoogleVision($photoData, $currentKey);
        $text = $ocrResult['responses'][0]['fullTextAnnotation']['text'] ?? '';
    }
    
    // 預處理：移除可能干擾的符號，將全形冒號轉半形
    $cleanText = str_replace(['：', '　', '|'], [':', ' ', ' '], $text);

    $data = [
        'batchNo' => '',
        'tankNo' => '',
        'materialNo' => '',
        'deliveryPlace' => '',
        'supplier' => ''
    ];

    // 1. 送達地點
    if (preg_match('/送達地點[\s:.]*([E|F][0-9A-Z]+)/u', $cleanText, $m)) {
        $data['deliveryPlace'] = $m[1];
    } elseif (preg_match('/地點[\s:.]*([E|F][0-9A-Z]+)/u', $cleanText, $m)) {
        $data['deliveryPlace'] = $m[1];
    }

    // 2. 供應商
    if (preg_match('/供應商[\s:.]*([0-9]+)/u', $cleanText, $m)) {
        $data['supplier'] = $m[1];
    }

    // 3. 料號
    if (preg_match('/料號[\s:.]*([A-Z0-9]+)/u', $cleanText, $m)) {
        $data['materialNo'] = $m[1];
    }

    // 4. 槽號
    if (preg_match('/槽號[\s:.]*([0-9A-Z]+)/u', $cleanText, $m)) {
        $data['tankNo'] = $m[1];
    }

    // 5. 批號
    if (preg_match('/批號[\s:.]*([0-9A-Z]+)/u', $cleanText, $m)) {
        $data['batchNo'] = $m[1];
    }

    // --- 保險機制 ---
    if (empty($data['deliveryPlace'])) {
        if (preg_match('/\b([E|F][A-Z0-9]{5,})\b/', $cleanText, $m)) $data['deliveryPlace'] = $m[1];
    }
    if (empty($data['batchNo'])) {
        if (preg_match('/\b(626[0-9A-Z]{5,}|261[0-9A-Z]{5,})\b/', $cleanText, $m)) $data['batchNo'] = $m[1];
    }
    if (empty($data['tankNo'])) {
        if (preg_match('/\b(5?E3[0-9]{2,})\b/', $cleanText, $m)) $data['tankNo'] = $m[1];
    }

    echo json_encode([
        'success' => true, 
        'data' => $data, 
        'debug_text' => mb_substr($cleanText, 0, 100) 
    ]);

} catch (Exception $e) {
    echo json_encode(['success' => false, 'message' => $e->getMessage()]);
}
?>
