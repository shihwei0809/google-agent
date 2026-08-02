<?php
/**
 * ==============================================================================
 * 鴻勝化學 - T100 ERP QC 檢驗結果對接中間件 (備案獨立版本 v1.0)
 * 
 * 📌 設計目的：
 *    本介面獨立放置於專用資料夾，專門用於處理「鼎新 T100 ERP」資料庫連線、
 *    QC 品管檢驗單 (如 QC301 / ESQC301 / asqi600) 狀態判定，以及彈性規則設定。
 * 
 * 📌 特點說明：
 *    1. 完全與主系統隔離，不影響目前正式環境運作。
 *    2. 針對未來 T100 QC 檢驗單據格式/欄位隨時異動，提供高度彈性的動態配置。
 *    3. 所有 SQL 與業務判斷邏輯皆撰寫巨細靡遺的中文註解與註記，方便日後維護調校。
 * ==============================================================================
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// ------------------------------------------------------------------------------
// 【高度彈性配置區】未來若 T100 單別、狀態碼或欄位名稱改變，在此區快速修改即可
// ------------------------------------------------------------------------------
$T100_CONFIG = [
    // 💡 預設可通過的 QC 單別（支援複選，未來若新增 QC302、QC401 可在陣列加入）
    'ALLOWED_DOC_TYPES' => ['QC301', 'QC302', 'ESQC301'],

    // 💡 可視為「真正的合格放行」之狀態代碼（如: 'PASS' 代表合格、'Y' 代表審核通過）
    'PASS_STATUS_CODES' => ['PASS', 'Y', '1', 'APPROVED'],

    // 💡 開關：是否啟用「模擬測試模式」（當無實體 Oracle/T100 資料庫連線時可設為 true 進行測試）
    'SIMULATION_MODE' => true,

    // 💡 T100 資料庫連線設定 (依據鼎新 T100 預設通常為 Oracle 或 SQL Server)
    'DB' => [
        'TYPE'     => 'OCI', // OCI (Oracle) 或 DSN / MYSQL
        'HOST'     => '192.168.1.100',
        'PORT'     => '1521',
        'SERVICE'  => 'topprd', // T100 正式庫名稱 (如 topprd)
        'USER'     => 'ds_t100',
        'PASSWORD' => 'secret_password',
        'CHARSET'  => 'AL32UTF8'
    ]
];

// ------------------------------------------------------------------------------
// 【主要請求處理入口】
// ------------------------------------------------------------------------------
$action = $_GET['action'] ?? $_POST['action'] ?? 'check_t100_qc';

switch ($action) {
    case 'check_t100_qc':
        handleQcVerification($T100_CONFIG);
        break;
        
    case 'get_config':
        // 供前端或測試端查詢目前彈性規則
        echo json_encode([
            'status' => 'success',
            'config' => $T100_CONFIG
        ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
        break;

    default:
        echo json_encode([
            'status'  => 'error',
            'message' => '未知的請求動作 Action: ' . htmlspecialchars($action)
        ], JSON_UNESCAPED_UNICODE);
        break;
}

/**
 * ------------------------------------------------------------------------------
 * 【核心判定邏輯函數】檢查指定櫃號/批號的 T100 QC 檢驗結果
 * ------------------------------------------------------------------------------
 */
function handleQcVerification($config) {
    // 取得前端傳入的查詢條件（可依櫃號 containerNo、來源單號 sourceNo 或品名 itemNo 查詢）
    $rawInput = file_get_contents('php_input');
    $postData = json_decode($rawInput, true) ?? $_POST;

    $containerNo = trim($postData['containerNo'] ?? $_GET['containerNo'] ?? '');
    $docType     = trim($postData['docType'] ?? $_GET['docType'] ?? 'QC301');
    $itemNo      = trim($postData['itemNo'] ?? $_GET['itemNo'] ?? '');

    if (empty($containerNo)) {
        echo json_encode([
            'status'  => 'error',
            'message' => '缺少必要參數：請提供槽車櫃號 (containerNo)'
        ], JSON_UNESCAPED_UNICODE);
        return;
    }

    // 💡 情況 A：模擬測試模式 (Simulation Mode)
    if ($config['SIMULATION_MODE']) {
        $result = simulateT100QcCheck($containerNo, $docType, $config);
        echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
        return;
    }

    // 💡 情況 B：正式連線 T100 資料庫查詢
    try {
        $dbResult = queryT100Database($containerNo, $docType, $itemNo, $config);
        echo json_encode($dbResult, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    } catch (Exception $e) {
        echo json_encode([
            'status'  => 'error',
            'message' => 'T100 資料庫查詢失敗：' . $e->getMessage()
        ], JSON_UNESCAPED_UNICODE);
    }
}

/**
 * ------------------------------------------------------------------------------
 * 【SQL 查詢核心】針對 T100 品管檢驗單結構 (如 esqc301 / asqi600) 進行撈取
 * 註：若未來 T100 資料表名稱或欄位有更動，只需調整下列 SQL 敘述即可。
 * ------------------------------------------------------------------------------
 */
function queryT100Database($containerNo, $docType, $itemNo, $config) {
    $dbCfg = $config['DB'];
    
    // 建立 Oracle OCI PDO 連線範例
    $dsn = "oci:dbname=//" . $dbCfg['HOST'] . ":" . $dbCfg['PORT'] . "/" . $dbCfg['SERVICE'] . ";charset=" . $dbCfg['CHARSET'];
    $pdo = new PDO($dsn, $dbCfg['USER'], $dbCfg['PASSWORD'], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
    ]);

    /**
     * 📌 T100 標準單據結構範例解說：
     * - 表單別 (esqcdoc) : 單據類型 (如 QC301 / ESQC301)
     * - 單據號碼 (esqcno)  : 品管檢驗單號
     * - 來源單號 (esqcsno) : 採購進貨/生產入庫單號
     * - 櫃號/備註 (esqcrem) : 槽車櫃號或提單備註
     * - 檢驗狀態 (esqcstat): 審核與判定狀態 ('Y':已放行/合格)
     */
    $sql = "SELECT 
                esqcno AS qc_doc_no,
                esqcdoc AS qc_type,
                esqcsno AS source_doc_no,
                esqcitem AS item_code,
                esqcitemname AS item_name,
                esqcrem AS container_remark,
                esqcstat AS qc_status_code,
                esqcdate AS inspect_date
            FROM topprd.esqc_t
            WHERE (esqcrem LIKE :containerNo OR esqcsno LIKE :containerNo)
              AND rownum <= 1
            ORDER BY esqcdate DESC";

    $stmt = $pdo->prepare($sql);
    $stmt->execute([':containerNo' => '%' . $containerNo . '%']);
    $row = $stmt->fetch();

    if (!$row) {
        return [
            'is_qualified' => false,
            'status'       => 'not_found',
            'message'      => "❌ T100 查無櫃號 [{$containerNo}] 之 QC 檢驗紀錄，禁止卸料！",
            'containerNo'  => $containerNo
        ];
    }

    // 檢查檢驗狀態碼是否符合彈性合格條件
    $statusCode = strtoupper(trim($row['qc_status_code']));
    $isQualified = in_array($statusCode, $config['PASS_STATUS_CODES']);

    return [
        'is_qualified'  => $isQualified,
        'status'        => $isQualified ? 'qualified' : 'unqualified',
        'message'       => $isQualified ? "✅ T100 判定合格！允許卸料與對刷" : "⚠️ T100 檢驗狀態為 [{$statusCode}]（未合格/未審核），禁止卸料！",
        't100_detail'   => [
            'qc_doc_no'   => $row['qc_doc_no'],
            'qc_type'     => $row['qc_type'],
            'item_name'   => $row['item_name'],
            'qc_status'   => $statusCode,
            'inspect_date'=> $row['inspect_date']
        ]
    ];
}

/**
 * ------------------------------------------------------------------------------
 * 【模擬測試函數】模擬不同櫃號的 T100 回傳結果 (無資料庫時測試用)
 * ------------------------------------------------------------------------------
 */
function simulateT100QcCheck($containerNo, $docType, $config) {
    // 預設特例測試邏輯：如果櫃號包含 "FAIL" 或 "999" 則模擬不合格
    if (strpos($containerNo, 'FAIL') !== false || strpos($containerNo, '999') !== false) {
        return [
            'is_qualified' => false,
            'status'       => 'unqualified',
            'simulation'   => true,
            'message'      => "⚠️ [模擬測試] T100 品管檢驗單未通過 (狀態碼: REJECT/未放行)，系統自動阻斷卸料！",
            'containerNo'  => $containerNo,
            't100_detail'  => [
                'qc_doc_no'    => 'ESQC301-20260729099',
                'qc_type'      => $docType,
                'item_name'    => 'IPA 高純度化學品',
                'qc_status'    => 'REJECT (退貨/不合格)',
                'inspect_date' => date('Y-m-d H:i:s')
            ]
        ];
    }

    // 一般情況模擬合格
    return [
        'is_qualified' => true,
        'status'       => 'qualified',
        'simulation'   => true,
        'message'      => "✅ [模擬測試] T100 品管檢驗單合格判定通過 (單別: {$docType}, 狀態: PASS)，准予卸料對刷",
        'containerNo'  => $containerNo,
        't100_detail'  => [
            'qc_doc_no'    => 'ESQC301-20260729032',
            'qc_type'      => $docType,
            'item_name'    => 'TMAH-LT 電子級原料',
            'qc_status'    => 'PASS (已審核放行)',
            'inspect_date' => date('Y-m-d H:i:s')
        ]
    ];
}
