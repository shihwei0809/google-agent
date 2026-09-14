import os
import re
file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_interactive_builder\app.py'
with open(file_path, 'r', encoding='utf-8') as f:
    app_py = f.read()

target = '''    FALLBACK_MODELS = [
        "gemini-3.5-flash", "gemini-2.5-flash",
        "gemini-2.0-flash", "gemini-2.0-flash-lite",
    ]'''
replacement = '''    FALLBACK_MODELS = [
        "gemini-3.8-flash", "gemini-3.5-flash",
        "gemini-2.5-flash", "gemini-2.0-flash",
    ]'''
app_py = app_py.replace(target, replacement)

target2 = '''        FALLBACK_MODELS = [
            "gemini-3.5-flash",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
        ]'''
replacement2 = '''        FALLBACK_MODELS = [
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
        ]'''
app_py = app_py.replace(target2, replacement2)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(app_py)
print("Updated app.py")
