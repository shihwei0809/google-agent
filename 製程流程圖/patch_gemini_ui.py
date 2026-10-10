import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace OpenAI references with Gemini
content = content.replace('OpenAI API Key (必填，您的金鑰僅儲存於本機)', 'Gemini API Key (必填，您的金鑰僅儲存於本機)')
content = content.replace('placeholder="sk-proj-..."', 'placeholder="AIzaSy..."')
content = content.replace('localStorage.getItem(\'chemflow_openai_key\')', 'localStorage.getItem(\'chemflow_gemini_key\')')
content = content.replace('localStorage.setItem(\'chemflow_openai_key\'', 'localStorage.setItem(\'chemflow_gemini_key\'')

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated index.html to Gemini")
