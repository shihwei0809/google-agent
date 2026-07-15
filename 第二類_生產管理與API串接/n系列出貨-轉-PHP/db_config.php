<?php
// db_config.php - 資料庫連線配置
$host = 'localhost';
$db   = 'n_barcode_out';
$user = 'root';
$pass = ''; // XAMPP 預設通常為空
$charset = 'utf8mb4';

$dsn = "mysql:host=$host;dbname=$db;charset=$charset";
$options = [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES   => false,
];

try {
    $pdo = new PDO($dsn, $user, $pass, $options);
} catch (\PDOException $e) {
    die("資料庫連線失敗: " . $e->getMessage());
}
