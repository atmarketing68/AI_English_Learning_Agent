; AGEN — Inno Setup script (one-click installer, no admin required)
; Builds installer\dist\AGEN-Setup.exe from the portable package in installer\dist\AGEN.

[Setup]
AppId={{B5C9E2BB-A5C4-4D53-9A9D-AGEN2026}}
AppName=AGEN English Learning Agent
AppVersion=1.0.0
AppPublisher=AGEN
DefaultDirName={localappdata}\AGEN
DisableProgramGroupPage=yes
DisableDirPage=yes
OutputDir=dist
OutputBaseFilename=AGEN-Setup
Compression=lzma2
SolidCompression=yes
; Per-user install → no UAC/admin prompt, truly one-click.
PrivilegesRequired=lowest
WizardStyle=modern
SetupIconFile=dist\AGEN\AGEN.ico
UninstallDisplayIcon={app}\AGEN.ico
UninstallDisplayName=AGEN English Learning Agent

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng trên màn hình Desktop"; GroupDescription: "Biểu tượng:"; Flags: checkedonce

[Files]
Source: "dist\AGEN\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Desktop shortcut (created when the task is selected — checked by default).
Name: "{autodesktop}\AGEN English Learning Agent"; Filename: "{app}\Start-AGEN.cmd"; IconFilename: "{app}\AGEN.ico"; WorkingDir: "{app}"; Tasks: desktopicon
; Start Menu shortcuts.
Name: "{autoprograms}\AGEN English Learning Agent"; Filename: "{app}\Start-AGEN.cmd"; IconFilename: "{app}\AGEN.ico"; WorkingDir: "{app}"
Name: "{autoprograms}\Dừng AGEN"; Filename: "{app}\Stop-AGEN.cmd"; WorkingDir: "{app}"

[Run]
; Launch AGEN right after install finishes.
Filename: "{app}\Start-AGEN.cmd"; Description: "Khởi chạy AGEN ngay bây giờ"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Stop services before removing files.
Filename: "{app}\Stop-AGEN.cmd"; Flags: runhidden; RunOnceId: "StopAgen"
