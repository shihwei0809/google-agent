; Inno Setup Script for 勝一三合一單產生系統
#define MyAppName "勝一三合一單產生系統"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Shiny Chemical"
#define MyAppExeName "勝一三合一單產生系統.exe"

[Setup]
AppId={{8A65C71B-4E73-4D88-82B2-61D1E532B6CF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=勝一三合一單產生系統_Setup_v{#MyAppVersion}
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
Source: "dist\勝一三合一單產生系統-免安裝版.exe"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion
Source: "台積電槽車barcode三合一單-範本.xlsx"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "地點代號對照表.xlsx"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "L269100_SEP73E4_COA.csv"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "L2C9100_SEP73E5_COA.csv"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "L2C9173_CPNE4R_COA.csv"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "L2C9501_PMAHQ_COA.csv"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "L2R9501_PMAHQR_COA.csv"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "Chemical_Lorry_L269100_SEP73E4.xlsx"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "Chemical_Lorry_L2C9100_SEP73E5.xlsx"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "Chemical_Lorry_L2C9173_CPNE4R.xlsx"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "Chemical_Lorry_L2C9501_PMAHQ.xlsx"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "Chemical_Lorry_L2R9501_PMAHQR.xlsx"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "splash.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "一鍵更新系統程式.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\一鍵手動更新"; Filename: "{app}\一鍵更新系統程式.bat"
Name: "{group}\解除安裝 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "立即啟動 {#MyAppName}"; Flags: nowait postinstall skipifsilent
