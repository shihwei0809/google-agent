#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精算與條碼驗證工具：處理物流時程計算與 TSMC 條碼 Regex 比對。
"""

import os
import re
import sys
import argparse
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

# TSMC N-series 經典條碼規則範例：N + 6位日期碼 + 1位廠區/等級代碼(大寫字母) + - + 3位流水號 (例如 N260530A-001)
TSMC_BARCODE_REGEX = r'^N\d{6}[A-Z]-\d{3}$'

def load_materials():
    filepath = "input/materials.txt"
    if not os.path.exists(filepath):
        # 預設參數
        return {"WEIGHT": 18.0, "FLOW_RATE": 1.2, "BARCODE": "N260530A-001"}
        
    data = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            data[k.strip().upper()] = v.strip()
            
    # 轉換資料型態
    try:
        data["WEIGHT"] = float(data.get("WEIGHT", 18.0))
    except ValueError:
        data["WEIGHT"] = 18.0
        
    try:
        data["FLOW_RATE"] = float(data.get("FLOW_RATE", 1.2))
    except ValueError:
        data["FLOW_RATE"] = 1.2
        
    data["BARCODE"] = data.get("BARCODE", "N260530A-001")
    return data

def run_calc(data):
    weight = data["WEIGHT"]
    flow_rate = data["FLOW_RATE"]
    
    if flow_rate <= 0:
        print("錯誤：流速不可為 0 或負數")
        return
        
    hours = round(weight / flow_rate, 2)
    
    # 預估完成時間（以現在時間起算）
    now = datetime.now()
    finish_time = now + timedelta(hours=hours)
    
    report = f"""# 🚢 ISOTANK 卸料時間精算報告

*   **評估時間**：{now.strftime('%Y-%m-%d %H:%M:%S')}
*   **輸入參數**：
    *   載重量 (Weight)：`{weight} T`
    *   標準流速 (Flow Rate)：`{flow_rate} T/hr`

---

## 📊 計算結果

*   **所需卸料總時數**：`{hours} 小時` (約 {int(hours)} 小時 {int((hours % 1) * 60)} 分鐘)
*   **預計卸料完成時間**：`{finish_time.strftime('%Y-%m-%d %H:%M:%S')}`

> [!NOTE]
> 本計算報告由 Python 內核精算，流速無條件保持穩定。現場實際卸料若受管線壓力影響，請依壓力錶為準微調。
"""
    os.makedirs("output", exist_ok=True)
    with open("output/schedule_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("✓ 已生成卸料時程精算報告：output/schedule_report.md")
    print(f"  -> 所需總時數：{hours} 小時")

def run_verify(data):
    barcode = data["BARCODE"]
    is_valid = bool(re.match(TSMC_BARCODE_REGEX, barcode))
    
    now = datetime.now()
    
    status_emoji = "✅ 符合規範" if is_valid else "❌ 格式錯誤"
    
    report = f"""# 🔍 原物料/產品條碼安全驗證報告

*   **檢驗時間**：{now.strftime('%Y-%m-%d %H:%M:%S')}
*   **待檢條碼**：`{barcode}`
*   **判定結果**：`{status_emoji}`

---

## 📋 驗證細節

1.  **Regex 規則基準**：`{TSMC_BARCODE_REGEX}` (TSMC N-series 標準產品標籤)
2.  **判定分析**：
"""
    if is_valid:
        report += f"    *   條碼 `{barcode}` 完全符合 TSMC 進貨標籤規格，允許放行並寫入系統資料庫。\n"
    else:
        report += f"    *   警報：條碼 `{barcode}` 未能通過標準 Regex 比對！\n"
        report += "    *   原因：長度不符、未包含大寫廠區代碼或流水號格式錯誤。**現場禁止放行**，請聯絡品管主管。\n"
        
    report += "\n---\n*品質控制系統自動備檔紀錄。*"
    
    os.makedirs("output", exist_ok=True)
    with open("output/barcode_verify_log.md", "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"✓ 已完成條碼驗證判定：{status_emoji}")
    print("  -> 驗證紀錄已寫入：output/barcode_verify_log.md")

def main():
    parser = argparse.ArgumentParser(description="槽車與條碼精算驗證內核")
    parser.add_argument("--mode", required=True, choices=["calc", "verify"], help="執行模式")
    args = parser.parse_args()
    
    data = load_materials()
    
    if args.mode == "calc":
        run_calc(data)
    elif args.mode == "verify":
        run_verify(data)

if __name__ == "__main__":
    main()
