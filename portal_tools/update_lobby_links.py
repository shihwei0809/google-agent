import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

index_path = Path(r"D:\GOOGLE ANGET\說明書\index.html")
content = index_path.read_text(encoding="utf-8")

# 1. Update hr-quiz-v2 URL
content = content.replace("https://hr-quiz-v2.pages.dev/index_with_mp3.html", "https://hr-quiz-v2.pages.dev/index_with_mp3")

# 2. Update t100_simulator URL
content = content.replace("https://google-agent.pages.dev/projects/t100_simulator.html", "https://google-agent.pages.dev/projects/t100_simulator")

# 3. Update recycle URL to unblocked portal
content = content.replace("https://recycle-feed-records.pages.dev/", "https://recycle-portal.pages.dev/")

# 4. Insert ACT / EGUPS planner card if not present
act_card = """        {title: "ACT / EGUPS 動態生產排程與進耗存整合系統 (Cloudflare PWA)",
                category: "cat2",
                launchUrl: "https://prod-planner-pwa.pages.dev/",
                manualTitle: "ACT / EGUPS 動態生產排程與進耗存整合系統 - 操作說明書",
                desc: "ACT 與 EGUPS 產品全自動動態生產排程、安全水位警報與進耗存推演。支援 Google 試算表即時雙向同步、歷史存檔快照、多人編輯無縫衝突防護，並具備 PWA 離線安裝功能。",
                tags: ["PWA", "Cloudflare Pages", "Google Sheets", "動態排程", "EGUPS", "ACT"],
                githubUrl: "https://github.com/shihwei0809/google-agent/tree/main/ACT動態生產排程與進耗存整合系統",},
"""

anchor = '{title: "IPA 專用動態生產排程與進耗存整合系統 (Cloudflare D1 PWA)",'
if "prod-planner-pwa" not in content:
    if anchor in content:
        content = content.replace(anchor, act_card + "        " + anchor)
        print("Success: Added ACT/EGUPS dynamic planner card to projectsData")
    else:
        print("Warning: Anchor not found in index.html")
else:
    print("Info: ACT/EGUPS planner card already exists")

index_path.write_text(content, encoding="utf-8")
print("Success: D:\\GOOGLE ANGET\\說明書\\index.html successfully updated!")
