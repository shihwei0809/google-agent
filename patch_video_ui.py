import os
import re

file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\影片生成\pdf-to-video\templates\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Replace HTML select options
target_html = '''                    <option value="gemini-3.5-flash">Gemini 3.5 Flash (最新推薦)</option>
                    <option value="gemini-3.5-pro">Gemini 3.5 Pro</option>
                    <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>'''
replacement_html = '''                    <option value="gemini-3.8-flash">Gemini 3.8 Flash (最新極速)</option>
                    <option value="gemini-3.7-flash">Gemini 3.7 Flash</option>
                    <option value="gemini-3.6-flash">Gemini 3.6 Flash</option>
                    <option value="gemini-3.5-pro">Gemini 3.5 Pro</option>
                    <option value="gemini-3.5-flash">Gemini 3.5 Flash</option>
                    <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>'''

if target_html in html:
    html = html.replace(target_html, replacement_html)
else:
    print("HTML options target not found")

# Replace JS dynamic options (they might be in a function updateModelOptions or something)
# Actually let's just do a regex replace if they exist like opt35f.value = 'gemini-3.5-flash';
# It seems the UI is constructing options dynamically. We can just add the new models there.

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated pdf-to-video/templates/index.html")
