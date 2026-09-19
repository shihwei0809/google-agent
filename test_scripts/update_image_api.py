import os
file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

target = '''        } else {
          imgSrc = 'https://loremflickr.com/640/400/' + encodeURIComponent(imageKeyword) + ',safety/all';
        }'''
replacement = '''        } else {
          // 使用 pollinations.ai 免費 AI 生圖 API 取代傳統隨機圖庫
          imgSrc = 'https://image.pollinations.ai/prompt/' + encodeURIComponent(imageKeyword + " detailed, photorealistic, professional training material style") + '?width=640&height=400&nologo=true';
        }'''

if target in html:
    html = html.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Success")
else:
    print("Not found")
