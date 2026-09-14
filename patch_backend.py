import os
file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_interactive_builder\app.py'
with open(file_path, 'r', encoding='utf-8') as f:
    app_py = f.read()

target1 = '''    FALLBACK_MODELS = [
        "gemini-3.8-flash", "gemini-3.5-flash",
        "gemini-2.5-flash", "gemini-2.0-flash",
    ]'''
replacement1 = '''    FALLBACK_MODELS = [
        "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash",
        "gemini-3.5-pro", "gemini-3.5-flash",
        "gemini-2.5-pro", "gemini-2.5-flash"
    ]'''
app_py = app_py.replace(target1, replacement1)

target2 = '''        FALLBACK_MODELS = [
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
        ]'''
replacement2 = '''        FALLBACK_MODELS = [
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-pro",
            "gemini-3.5-flash",
            "gemini-2.5-pro",
            "gemini-2.5-flash"
        ]'''
app_py = app_py.replace(target2, replacement2)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(app_py)
