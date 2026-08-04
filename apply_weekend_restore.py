import re
from pathlib import Path

# 1. Read weekend backup index.html
backup_path = Path(r"c:\GOOGLE ANGET\說明書\index_weekend_backup.html")
target_index_path = Path(r"c:\GOOGLE ANGET\說明書\index.html")

content = backup_path.read_text(encoding="utf-8")

# 2. Inject getCorrectLaunchUrl helper function into index.html JS
helper_js = """
        // 雙模網址動態解析器 (線上使用根目錄絕對路徑防層疊，本機使用相對路徑)
        function getCorrectLaunchUrl(url) {
            if (!url) return "#";
            if (url.startsWith("command:") || url.startsWith("http://") || url.startsWith("https://")) {
                return url;
            }
            if (window.location.protocol === "http:" || window.location.protocol === "https:") {
                // 清理多餘相對路徑前綴
                const clean = url.replace(/^(\.\/|\.\.\/)+/, '');
                return '/' + clean;
            }
            return url;
        }
"""

# Replace card rendering logic in index.html to use getCorrectLaunchUrl and target="_blank"
old_card_action = """                    launchActionHtml = `<a href="${p.launchUrl}" class="card-btn btn-launch" target="_self">"""
new_card_action = """                    const safeUrl = getCorrectLaunchUrl(p.launchUrl);
                    launchActionHtml = `<a href="${safeUrl}" class="card-btn btn-launch" target="_blank">"""

if old_card_action in content:
    content = content.replace(old_card_action, new_card_action)
    print("Replaced launchActionHtml with getCorrectLaunchUrl and target=_blank!")

# Inject helper_js right before renderPortal()
if "function renderPortal()" in content:
    content = content.replace("function renderPortal()", helper_js + "\n        function renderPortal()")
    print("Injected getCorrectLaunchUrl helper JS!")

# Write to 說明書/index.html
target_index_path.write_text(content, encoding="utf-8")
print("Successfully restored 說明書/index.html from weekend backup with getCorrectLaunchUrl injection!")

# 3. Create 說明書/_redirects file
redirects_path = Path(r"c:\GOOGLE ANGET\說明書\_redirects")
redirects_content = """# Force Cloudflare Pages and Netlify to serve static files in /projects/ without SPA fallback
/projects/*  /projects/:splat  200!
"""
redirects_path.write_text(redirects_content, encoding="utf-8")
print("Successfully created 說明書/_redirects!")
