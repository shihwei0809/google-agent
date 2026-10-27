; Inno Setup Script for 三合一單自動產生器
#define MyAppName "三合一單自動產生器"
#define MyAppVersion "2.2.2"
#define MyAppPublisher "Shiny Chemical"
#define MyAppExeName "三合一單自動產生器.exe"

[Setup]
AppId={{9B78D82A-3D62-4C67-93A1-70C0D421A5BE}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=三合一單自動產生器_Setup_v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "建立桌面捷徑 (Create desktop shortcut)"; GroupDescription: "捷徑設定"

[Files]
Source: "dist\三合一單自動產生器-免安裝版.exe"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion
Source: "台積電槽車barcode三合一單-範本.xlsx"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "地點代號對照表.xlsx"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "splash.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "一鍵更新系統程式.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\一鍵手動更新"; Filename: "{app}\一鍵更新系統程式.bat"
Name: "{group}\解除安裝 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "立即啟動 {#MyAppName}"; Flags: nowait postinstall skipifsilent
