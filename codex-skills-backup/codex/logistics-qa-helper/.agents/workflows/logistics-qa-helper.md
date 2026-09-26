---
name: logistics-qa-helper
description: 一鍵計算卸料時程或驗證條碼規則並輸出成果
---

# /isotank-calc
請載入 `logistics-qa-helper` Skill，執行物流計算流程：
1. 確保 `input/materials.txt` 內含有 `WEIGHT` 和 `FLOW_RATE`。
2. 執行命令 `python scripts/calc_and_verify.py --mode calc`。
3. 將預估時程與計算報告寫入 `output/schedule_report.md`。

# /barcode-verify
請載入 `logistics-qa-helper` Skill，執行條碼驗證流程：
1. 確保 `input/materials.txt` 內含有 `BARCODE` 欄位。
2. 執行命令 `python scripts/calc_and_verify.py --mode verify`。
3. 將判定結果（合格/警報）寫入 `output/barcode_verify_log.md`。
