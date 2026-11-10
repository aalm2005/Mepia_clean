param([string]$PythonPath, [string]$NodePath)
$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
$runtimePath = Join-Path $repoPath '.test_tmp\demo_runtime.json'
if (Test-Path -LiteralPath $runtimePath) {
    $demoRuntime = Get-Content -LiteralPath $runtimePath -Raw | ConvertFrom-Json
    if (-not $PythonPath) { $PythonPath = $demoRuntime.python }
    if (-not $NodePath) { $NodePath = $demoRuntime.node }
}
if (-not $PythonPath) {
    $candidate = Join-Path $repoPath '.venv\Scripts\python.exe'
    $PythonPath = if (Test-Path -LiteralPath $candidate) { $candidate } else { 'python' }
}
if (-not $NodePath) { $NodePath = 'node' }
Push-Location -LiteralPath $repoPath
try { & $PythonPath -B scripts/start_mepia_demo.py --node $NodePath }
finally { Pop-Location }
