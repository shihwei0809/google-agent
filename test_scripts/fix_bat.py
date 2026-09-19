content = '''@echo off
cd /d "%~dp0sop_generator"
call "點我啟動產生器(Windows免安裝).bat"
'''
with open(r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\點我啟動教育訓練產生器.bat', 'w', encoding='cp950') as f:
    f.write(content)
