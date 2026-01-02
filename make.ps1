# PowerShell Wrapper for DocNexus Build System
param(
    [Parameter(Position = 0)]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
$BuildScript = "$ScriptDir\scripts\build.py"

# If no 'python' in path, we might be in trouble for initial setup,
# but usually devs have global python.
$Python = "python" 

if ($Command -eq "help") {
    Write-Host "Wrapper for scripts/build.py" -ForegroundColor Cyan
    Write-Host "Usage: .\make.ps1 [setup|build|clean|run]"
    exit
}

& $Python $BuildScript $Command
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build script failed with exit code $LASTEXITCODE"
}
