Set shell = CreateObject("WScript.Shell")
currentDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptPosition)
shell.CurrentDirectory = currentDir
shell.Run "cmd /c start.bat", 0, False
