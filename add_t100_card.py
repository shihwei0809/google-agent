import re
from pathlib import Path

index_path = Path(r"c:\GOOGLE ANGET\說明書\index.html")
content = index_path.read_text(encoding="utf-8")

# Check if t100_simulator.html entry is already in projectsData
if "./projects/t100_simulator.html" not in content:
    t100_card_obj = """{title: "鼎新 T100 ERP QC 串接與三重對刷演練控制台",
                category: "cat2",
                launchUrl: "./projects/t100_simulator.html",
                manualTitle: "鼎新 T100 ERP QC 串接中間件備案 — 操作與設定手冊",
                desc: "專門提供給資訊人員與長官簡報展示的視覺化模擬演練控制台。包含【一關: 現場對刷】、【二關: T100 QC合格檢驗】、【三關: QC授權放行】與即時動態流程圖。",
                tags: ["模擬演練", "T100 ERP", "三重防呆", "SVG 畫布"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/第二類_生產管理與API串接/IPAHQ-槽車確認-GAS-to-PHPSQL"},"""
    
    # Insert right before cat2 items
    content = content.replace('{title: "IPAHQ 槽車確認與掃描系統",', t100_card_obj + "\n        {title: \"IPAHQ 槽車確認與掃描系統\",")
    index_path.write_text(content, encoding="utf-8")
    print("Successfully added T100 ERP QC Simulator card to projectsData!")
else:
    print("T100 ERP QC Simulator card already exists in projectsData.")
