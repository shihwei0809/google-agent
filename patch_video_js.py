import os
file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\影片生成\pdf-to-video\templates\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

target = '''        if (selectedMethod === 'gemini') {
          const opt35f = document.createElement('option');
          opt35f.value = 'gemini-3.5-flash';
          opt35f.textContent = 'Gemini 3.5 Flash (預設推薦)';'''

replacement = '''        if (selectedMethod === 'gemini') {
          const opt38f = document.createElement('option');
          opt38f.value = 'gemini-3.8-flash';
          opt38f.textContent = 'Gemini 3.8 Flash (最新極速)';
          modelSelect.appendChild(opt38f);

          const opt37f = document.createElement('option');
          opt37f.value = 'gemini-3.7-flash';
          opt37f.textContent = 'Gemini 3.7 Flash';
          modelSelect.appendChild(opt37f);

          const opt36f = document.createElement('option');
          opt36f.value = 'gemini-3.6-flash';
          opt36f.textContent = 'Gemini 3.6 Flash';
          modelSelect.appendChild(opt36f);

          const opt35f = document.createElement('option');
          opt35f.value = 'gemini-3.5-flash';
          opt35f.textContent = 'Gemini 3.5 Flash';'''

if target in html:
    html = html.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Success replacing JS")
else:
    print("JS target not found")
