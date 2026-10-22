Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\GOOGLE ANGET\HTTPS遠端網頁穿透中心"
WshShell.Run "cmd /c python main.py", 0, False