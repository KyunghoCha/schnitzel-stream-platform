# setup_env.ps1
# Windows PowerShell 개발 환경 설정 스크립트

Write-Host "Setting up environment for schnitzel-stream-platform..." -ForegroundColor Cyan

# 1. PYTHONPATH 설정 (src 디렉토리 포함)
$currentDir = Get-Location
$srcPath = Join-Path $currentDir "src"

if (Test-Path $srcPath) {
    $env:PYTHONPATH = $srcPath
    Write-Host "[SUCCESS] PYTHONPATH set to: $srcPath" -ForegroundColor Green
} else {
    Write-Host "[ERROR] 'src' directory not found. Please run this script in the project root." -ForegroundColor Red
    exit 1
}

# 2. 가상환경 체크 (선택 사항)
if ($null -eq $env:VIRTUAL_ENV) {
    Write-Host "[WARNING] No virtual environment (venv) detected. It's recommended to use one." -ForegroundColor Yellow
} else {
    Write-Host "[INFO] Active virtual environment: $env:VIRTUAL_ENV" -ForegroundColor Cyan
}

Write-Host "`nReady to run! Try: python -m schnitzel_stream validate" -ForegroundColor Magenta
