<?php
// 權限檢查：僅允許來自本機網域的請求
$referer = $_SERVER['HTTP_REFERER'] ?? '';
if (empty($referer) || strpos($referer, 'ngrok-free.dev') === false) {
    header("HTTP/1.1 403 Forbidden");
    exit("禁止存取");
}

$path = $_GET['path'] ?? '';
if (empty($path)) exit;

// 過濾路徑
$path = str_replace(['..', '\\'], '', $path);
$fullPath = "E:/tanker_photos/" . $path;

// 關鍵：將 UTF-8 路徑轉為 BIG5 才能在 Windows 系統開啟中文資料夾
$encodedPath = mb_convert_encoding($fullPath, "BIG5", "UTF-8");

if (file_exists($encodedPath)) {
    header('Content-Type: image/jpeg');
    readfile($encodedPath);
} else {
    header("HTTP/1.0 404 Not Found");
    echo "找不到檔案";
}
