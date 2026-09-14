import os
file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\影片生成\pdf-to-video\app.py'
with open(file_path, 'r', encoding='utf-8') as f:
    app_py = f.read()

target = '''        all_models = [
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash",
            "gemini-3.5-flash",
            "gemini-3.5-pro",
            "gemini-2.5-flash",
            "gemini-1.5-pro-latest"
        ]'''

replacement = '''        all_models = [
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-pro",
            "gemini-2.5-flash",
            "gemini-1.5-flash-latest"
        ]'''

if target in app_py:
    app_py = app_py.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(app_py)
    print("Success")
else:
    print("Target not found")
