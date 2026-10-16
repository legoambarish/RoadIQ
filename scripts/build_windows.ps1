param(
    [string]$PythonPath = '',
    [switch]$IncludeModels
)

$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    throw 'RoadIQ.exe must be built on Windows.'
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = if ($PythonPath) { (Resolve-Path -LiteralPath $PythonPath).Path } else { Join-Path $repoRoot '.venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Python 3.12 build environment not found. Follow the Windows build setup in README.md first.'
}
$pythonVersion = & $python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($pythonVersion.Trim() -ne '3.12') {
    throw "RoadIQ.exe requires the documented Python 3.12 build environment; found $pythonVersion."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'Node.js and npm are required to build the bundled dashboard.'
}

$frontend = Join-Path $repoRoot 'frontend'
$frontendBuild = Join-Path $repoRoot 'build\windows-frontend'
$previousViteApiBase = $env:VITE_API_BASE_URL
$env:VITE_API_BASE_URL = '/api/v1'
Push-Location $frontend
try {
    npm ci
    if ($LASTEXITCODE -ne 0) { throw 'npm ci failed.' }
    npm run build -- --outDir ../build/windows-frontend --emptyOutDir
    if ($LASTEXITCODE -ne 0) { throw 'The frontend TypeScript/Vite build failed.' }
}
finally {
    Pop-Location
    if ($null -eq $previousViteApiBase) {
        Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
    } else {
        $env:VITE_API_BASE_URL = $previousViteApiBase
    }
}

$previousBundleModels = $env:ROADIQ_BUNDLE_MODELS
$env:ROADIQ_BUNDLE_MODELS = if ($IncludeModels) { '1' } else { '0' }
try {
    & $python -m PyInstaller --noconfirm --distpath (Join-Path $repoRoot 'dist') --workpath (Join-Path $repoRoot 'build\pyinstaller') (Join-Path $repoRoot 'packaging\RoadIQ.spec')
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed to build RoadIQ.exe.' }
}
finally {
    if ($null -eq $previousBundleModels) { Remove-Item Env:ROADIQ_BUNDLE_MODELS -ErrorAction SilentlyContinue }
    else { $env:ROADIQ_BUNDLE_MODELS = $previousBundleModels }
}
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed to build RoadIQ.exe.' }
$executable = Join-Path $repoRoot 'dist\RoadIQ.exe'
if (-not (Test-Path -LiteralPath $executable)) { throw 'PyInstaller reported success but dist\RoadIQ.exe was not created.' }
Write-Output "Built $executable (trained models included: $IncludeModels)"
