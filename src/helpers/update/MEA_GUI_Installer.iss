; ====== Preprocessor configuration ======
#ifndef AppVersionFromCI
  #define AppVersionFromCI "0.0.0-dev"
#endif

#ifndef FileVerFromCI
  #define FileVerFromCI "0.0.0.0"
#endif

#ifndef SourceDir
  #define SourceDir "..\..\..\dist\YsaGUI"
#endif

#ifndef OutputDir
  #define OutputDir "."
#endif

; ====== Product identity (fixed across releases) ======
#define MyAppName "YSA GUI"
#define MyAppPublisher "Parrish Lab"
#define MyAppExeName "YsaGUI.exe"
#define MyAppIconName "icon.ico"

; Debug prints in the ISCC log so you can see what arrived
#pragma message "MyAppVersion = {#AppVersionFromCI}"
#pragma message "MyFileVer    = {#FileVerFromCI}"
#pragma message "SourceDir    = {#SourceDir}"
#pragma message "OutputDir    = {#OutputDir}"

; ====== Setup ======
[Setup]
AppId={{96289611-0927-480E-9561-C6976C2BB9F6}}  ; Keep this GUID forever for this product/edition (now, Windows will treat future installers as upgrades instead of separate apps)
AppName={#MyAppName}
AppVersion={#AppVersionFromCI}              ; shown to users
VersionInfoVersion={#FileVerFromCI}         ;  must be numeric x.x.x.x
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=YSA_GUI_Windows
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
SetupIconFile="..\..\..\resources\{#MyAppIconName}"
OutputDir={#OutputDir}  ; write to the folder we pass from CI

; Sets EXE file properties on installer
VersionInfoProductName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\YsaGUI.exe"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "YsaGUI.exe"
Source: "..\..\..\resources\{#MyAppIconName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
