# setup_env.ps1
# Docs: docs/ops/command_reference.md, docs/guides/local_console_quickstart.md
# Windows PowerShell bootstrap helper (dependency-first)

param(
    [ValidateSet("base", "console", "yolo")]
    [string]$Profile = "base",
    [ValidateSet("auto", "conda", "pip")]
    [string]$Manager = "auto",
    [switch]$DryRun,
    [switch]$SkipDoctor
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "== schnitzel-stream setup ==" -ForegroundColor Cyan
Write-Host "profile=$Profile"
Write-Host "manager=$Manager"
Write-Host "dry_run=$($DryRun.IsPresent.ToString().ToLowerInvariant())"
Write-Host "skip_doctor=$($SkipDoctor.IsPresent.ToString().ToLowerInvariant())"

$srcPath = Join-Path $scriptDir "src"
if (-Not (Test-Path $srcPath)) {
    Write-Host "[ERROR] src directory not found. Run this script from project root." -ForegroundColor Red
    exit 1
}
$env:PYTHONPATH = $srcPath
Write-Host "[OK] PYTHONPATH=$srcPath" -ForegroundColor Green

$cmd = @("python", "scripts/bootstrap_env.py", "--profile", $Profile, "--manager", $Manager)
if ($DryRun) {
    $cmd += "--dry-run"
}
if ($SkipDoctor) {
    $cmd += "--skip-doctor"
}

Write-Host ("[RUN] " + ($cmd -join " ")) -ForegroundColor Yellow
& $cmd[0] $cmd[1..($cmd.Length - 1)]
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] bootstrap_env failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "[OK] Environment bootstrap complete." -ForegroundColor Green
if ($SkipDoctor) {
    Write-Host "next=python scripts/env_doctor.py --profile $Profile --strict --json" -ForegroundColor Magenta
} else {
    Write-Host "next=python scripts/stream_console.py up --allow-local-mutations" -ForegroundColor Magenta
}
