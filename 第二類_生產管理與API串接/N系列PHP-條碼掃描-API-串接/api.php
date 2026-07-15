        // ==========================================
        // 🛑 2.5 區間排程核對 (修正版：自動忽略桶號)
        // ==========================================
        
        // 先檢查系統目前是否有匯入排程
        $scheduleCount = $pdo->query("SELECT COUNT(*) FROM daily_schedules")->fetchColumn();
        
        if ($scheduleCount > 0) {
            
            // 💡 建立一個輔助功能：專門切掉空白與後面的桶號，只留主批號
            function getBaseBatch($fullString) {
                // 將字串用空白切開，例如 "225B29M8201 00021" 會變成陣列 ["225B29M8201", "00021"]
                $parts = explode(' ', trim($fullString));
                // 只回傳第一段 (主批號)
                return $parts[0]; 
            }

            // 收集本次掃描的所有批號，並在收集時直接「去尾」
            $scannedBatches = [];
            if (!empty($f[1])) $scannedBatches[] = getBaseBatch($f[1]);
            if (!empty($f[3])) $scannedBatches[] = getBaseBatch($f[3]);
            if (!empty($f[5])) $scannedBatches[] = getBaseBatch($f[5]);
            if (!empty($f[7])) $scannedBatches[] = getBaseBatch($f[7]);

            // 去除重複 (如果四桶都是同一個主批號，只要查一次資料庫就好)
            $uniqueBatches = array_unique($scannedBatches);

            // 逐一比對主批號是否存在於排程中
            $stmtCheck = $pdo->prepare("SELECT COUNT(*) FROM daily_schedules WHERE batch_no = ?");
            foreach ($uniqueBatches as $baseBatch) {
                $stmtCheck->execute([$baseBatch]);
                if ($stmtCheck->fetchColumn() == 0) {
                    // 只要有一桶的主批號不在排程內，立刻報錯阻擋！
                    $errorList[] = "❌ 排程異常：\n主批號 [$baseBatch]\n不在匯入的排程清單中！";
                }
            }
        }
