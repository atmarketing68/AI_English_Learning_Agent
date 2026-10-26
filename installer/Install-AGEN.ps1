$ErrorActionPreference = 'Stop'
$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $env:LOCALAPPDATA 'AGEN'
$desktop = [Environment]::GetFolderPath('Desktop')

if ((Resolve-Path $source).Path.TrimEnd('\') -ne $target.TrimEnd('\')) {
    New-Item $target -ItemType Directory -Force | Out-Null
    robocopy $source $target /E /NFL /NDL /NJH /NJS | Out-Null
    if ($LASTEXITCODE -ge 8) { throw 'Copying AGEN files failed' }
}

$shortcutPath = Join-Path $desktop 'AGEN English Learning Agent.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $target 'Start-AGEN.cmd'
$shortcut.WorkingDirectory = $target
$shortcut.IconLocation = "$(Join-Path $target 'AGEN.ico'),0"
$shortcut.Description = 'Launch AGEN English Learning Agent'
$shortcut.Save()

Write-Host "AGEN installed to $target"
Write-Host "Desktop shortcut created: $shortcutPath"
Start-Process (Join-Path $target 'Start-AGEN.cmd')
