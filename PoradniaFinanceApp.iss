; Inno Setup Script for Poradnia Finance App
; This script creates a professional Windows installer for PoradniaFinanceApp

[Setup]
AppName=Poradnia Manager
AppVersion=1.0
AppPublisher=Poradnia Finance
AppPublisherURL=https://example.com
AppSupportURL=https://example.com/support
AppUpdatesURL=https://example.com/updates
DefaultDirName={autopf}\PoradniaManager
DefaultGroupName=Poradnia Manager
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=PoradniaFinanceApp_Setup
SetupIconFile=assets\app_icon.ico
UninstallDisplayIcon={app}\PoradniaFinanceApp.exe
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64 arm64

[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1,10.0

[Files]
; Main executable
Source: "dist\PoradniaFinanceApp.exe"; DestDir: "{app}"; Flags: ignoreversion
; Database (will be created on first run, but include empty if it exists)
Source: "poradnie.db"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
; Assets
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
; License/Readme
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\Poradnia Manager"; Filename: "{app}\PoradniaFinanceApp.exe"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,Poradnia Manager}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Poradnia Manager"; Filename: "{app}\PoradniaFinanceApp.exe"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Poradnia Manager"; Filename: "{app}\PoradniaFinanceApp.exe"; WorkingDir: "{app}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\PoradniaFinanceApp.exe"; Description: "{cm:LaunchProgram,Poradnia Manager}"; Flags: nowait postinstall skipifsilent

[InstallDelete]
; Clean up old installation files if needed
Type: files; Name: "{app}\*.pyc"
Type: files; Name: "{app}\*.pyo"
