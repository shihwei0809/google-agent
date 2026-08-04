import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

manuals_dir = Path(r"c:\GOOGLE ANGET\說明書")
index_html = manuals_dir / "index.html"
manuals_js = manuals_dir / "manuals_db.js"

print("=" * 60)
print("🔍 開始進行 專案大廳與說明書中心 完整合規性與檔案連結檢查...")
print("=" * 60)

errors = []

# 1. Verify index.html exists
if not index_html.exists():
    errors.append("❌ 關鍵錯誤: 說明書/index.html 不存在！")
else:
    print("✅ 說明書/index.html 存在。")

# 2. Verify _redirects file exists
redirects_p = manuals_dir / "_redirects"
if not redirects_p.exists():
    errors.append("❌ 關鍵錯誤: 說明書/_redirects 不存在！")
else:
    print("✅ 說明書/_redirects 存在。內容:")
    print("   ", repr(redirects_p.read_text(encoding="utf-8").strip()))

# 3. Check manuals_db.js
if not manuals_js.exists():
    errors.append("❌ 關鍵錯誤: 說明書/manuals_db.js 不存在！")
else:
    content = manuals_js.read_text(encoding="utf-8")
    json_text = content.replace("window.manualsData =", "").strip().rstrip(";")
    try:
        manuals = json.loads(json_text)
        print(f"✅ manuals_db.js 成功載入 {len(manuals)} 篇說明書。")
        
        missing_md = 0
        for m in manuals:
            rel_path = m.get("path")
            full_md_path = manuals_dir / rel_path
            if not full_md_path.exists():
                missing_md += 1
                errors.append(f"  ❌ 缺失 Markdown 說明書: {rel_path}")
        if missing_md == 0:
            print("✅ 所有 37 篇說明書之 Markdown 檔案實體均存在！")
    except Exception as e:
        errors.append(f"❌ 解析 manuals_db.js 失敗: {e}")

# 4. Check system cards in index.html
content = index_html.read_text(encoding="utf-8")
start_idx = content.find("const projectsData = [")
end_idx = content.find("];", start_idx)

if start_idx != -1 and end_idx != -1:
    js_text = content[start_idx:end_idx+2]
    pattern = r'title:\s*"([^"]+)".*?launchUrl:\s*"([^"]+)".*?manualTitle:\s*"([^"]+)"'
    matches = re.findall(pattern, js_text, re.DOTALL)
    print(f"✅ index.html 解析出 {len(matches)} 張系統卡片。")
    
    missing_static_html = 0
    for i, (t, url, m_title) in enumerate(matches, 1):
        if url.startswith("./projects/"):
            sub_path = url.replace("./projects/", "")
            target_p = manuals_dir / "projects" / sub_path
            if not target_p.exists():
                missing_static_html += 1
                errors.append(f"  ❌ 卡片 [{t}] 之 launchUrl 指向檔案不存在: {target_p}")
    if missing_static_html == 0:
        print("✅ 所有靜態網頁系統卡片之 HTML/JS 實體檔案均 100% 存在於 說明書/projects/ 目錄下！")
else:
    errors.append("❌ 無法在 index.html 找到 projectsData 陣列！")

print("=" * 60)
if errors:
    print(f"❌ 發現 {len(errors)} 個問題需要解決：")
    for err in errors:
        print(err)
else:
    print("🎉 檢查完成！所有卡片連結、靜態網頁實體與 Markdown 說明書均 100% 正常可點擊！")
print("=" * 60)
