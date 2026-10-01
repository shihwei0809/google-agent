import re
import codecs

file_path = r'd:\GOOGLE ANGET\製程流程圖\public\index.html'

with codecs.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Rename buttons
content = content.replace('匯出專案 JSON', '匯出存圖 (JSON)')
content = content.replace('開啟 JSON', '讀取 JSON')

# Remove the AI Image button
content = re.sub(r'<button[^>]*id="btn-ai-image"[^>]*>.*?</button>', '', content, flags=re.DOTALL)
# Remove the AI Image modal
content = re.sub(r'<div[^>]*id="ai-image-modal"[^>]*>.*?</div>\s*</div>\s*</div>', '', content, flags=re.DOTALL)
# Remove the AI Image click event listeners
content = re.sub(r"document\.getElementById\('btn-ai-image'\)\.addEventListener\('click'.*?\}\);", "", content, flags=re.DOTALL)
content = re.sub(r"document\.getElementById\('close-image-modal'\)\.addEventListener\('click'.*?\}\);", "", content, flags=re.DOTALL)
content = re.sub(r"document\.getElementById\('btn-generate-image'\)\.addEventListener\('click'.*?\}\);", "", content, flags=re.DOTALL)

with codecs.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Safely replaced text and removed AI Image")
