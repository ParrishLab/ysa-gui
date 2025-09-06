; ====== Preprocessor configuration ======
; Allow GitHub Actions to pass these via /DSourceDir /DOutputDir /DAppVersion
#define SourceDir GetEnv("SourceDir")
#define OutputDir GetEnv("OutputDir")
#define AppVersionFromEnv GetEnv("AppVersion")
#define FileVersionFromEnv GetEnv("FileVersion")

; Fallbacks if not provided or for local/manual builds
#if SourceDir == ""
  #define SourceDir "dist\YsaGUI"
#endif
#if OutputDir == ""
  #define OutputDir "src\helpers\update\Output"
#endif

; Display version (can be semver with suffixes)
#if AppVersionFromEnv == ""
  #define MyAppVersion "0.0.0-dev"
#else
  #define MyAppVersion AppVersionFromEnv
#endif

; Strict 4-part numeric version for Windows file version resource
#if FileVersionFromEnv == ""
  #define MyFileVersion "0.0.0.0"
#else
  #define MyFileVersion FileVersionFromEnv
#endif

; ====== Product identity (fixed across releases) ======
#define MyAppName "YSA GUI"
#define MyAppPublisher "Parrish Lab"
#define MyAppExeName "YsaGUI.exe"
#define MyAppIconName "icon.ico"

[Setup]
AppId={{96289611-0927-480E-9561-C6976C2BB9F6}}  ; Keep this GUID forever for this product/edition (now, Windows will treat future installers as upgrades instead of separate apps)
AppName={#MyAppName}
AppVersion={#MyAppVersion}
; ↓↓↓ these MUST be numeric x.x.x.x
VersionInfoProductVersion={#MyFileVersion}
VersionInfoFileVersion={#MyFileVersion}
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
VersionInfoProductVersion={#MyAppVersion}
VersionInfoFileVersion={#MyAppVersion}

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
