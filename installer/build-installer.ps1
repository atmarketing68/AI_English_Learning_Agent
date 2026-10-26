$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'agen-backend'
$web = Join-Path $root 'agen-web'
$dist = Join-Path $PSScriptRoot 'dist\AGEN'
$pyinstaller = Join-Path $backend 'venv\Scripts\pyinstaller.exe'

Write-Host '==> Cleaning package output'
Remove-Item (Join-Path $PSScriptRoot 'dist') -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $backend 'build') -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $backend 'dist') -Recurse -Force -ErrorAction SilentlyContinue
New-Item $dist -ItemType Directory -Force | Out-Null

if (-not (Test-Path $pyinstaller)) {
    throw "PyInstaller not found. Run: $backend\venv\Scripts\python.exe -m pip install pyinstaller"
}

Write-Host '==> Building backend executable (using agen-api.spec)'
Push-Location $backend
& $pyinstaller --noconfirm --clean agen-api.spec
Pop-Location
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller backend build failed' }
New-Item (Join-Path $dist 'backend') -ItemType Directory -Force | Out-Null
robocopy (Join-Path $backend 'dist\agen-api') (Join-Path $dist 'backend') /E /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -ge 8) { throw 'Backend package copy failed' }

Write-Host '==> Building Next.js standalone frontend'
Push-Location $web
$env:DESKTOP_BUILD = '1'
$env:NEXT_PUBLIC_API_URL = 'http://127.0.0.1:8000/api/v1'
npm run build
Pop-Location
New-Item (Join-Path $dist 'frontend') -ItemType Directory -Force | Out-Null
robocopy (Join-Path $web '.next\standalone') (Join-Path $dist 'frontend') /E /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -ge 8) { throw 'Frontend standalone copy failed' }
New-Item (Join-Path $dist 'frontend\.next\static') -ItemType Directory -Force | Out-Null
robocopy (Join-Path $web '.next\static') (Join-Path $dist 'frontend\.next\static') /E /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -ge 8) { throw 'Frontend static copy failed' }
if (Test-Path (Join-Path $web 'public')) {
    robocopy (Join-Path $web 'public') (Join-Path $dist 'frontend\public') /E /NFL /NDL /NJH /NJS | Out-Null
    if ($LASTEXITCODE -ge 8) { throw 'Frontend public copy failed' }
}

Write-Host '==> Bundling Node runtime'
$node = (Get-Command node).Source
Copy-Item $node (Join-Path $dist 'node.exe') -Force

Copy-Item (Join-Path $PSScriptRoot 'Start-AGEN.cmd') $dist -Force
Copy-Item (Join-Path $PSScriptRoot 'Stop-AGEN.cmd') $dist -Force
Copy-Item (Join-Path $PSScriptRoot 'Install-AGEN.cmd') $dist -Force
Copy-Item (Join-Path $PSScriptRoot 'Install-AGEN.ps1') $dist -Force
Copy-Item (Join-Path $PSScriptRoot 'AGEN.env.example') (Join-Path $dist '.env.example') -Force
Copy-Item (Join-Path $web 'src\app\favicon.ico') (Join-Path $dist 'AGEN.ico') -Force -ErrorAction SilentlyContinue

# Locate ISCC.exe: PATH first, then common per-user / Program Files locations.
$isccPath = $null
$cmd = Get-Command iscc -ErrorAction SilentlyContinue
if ($cmd) { $isccPath = $cmd.Source }
if (-not $isccPath) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
        (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe')
    )
    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { $isccPath = $c; break } }
}

if ($isccPath) {
    Write-Host "==> Building Inno Setup installer ($isccPath)"
    & $isccPath (Join-Path $PSScriptRoot 'AGEN.iss')
    if ($LASTEXITCODE -ne 0) { throw 'Inno Setup build failed' }
    $setupExe = Join-Path $PSScriptRoot 'dist\AGEN-Setup.exe'
    if (Test-Path $setupExe) { Write-Host "One-click installer ready: $setupExe" }
} else {
    Write-Warning 'Inno Setup (ISCC.exe) not found; portable package was created only.'
}

Write-Host "Package ready: $dist"