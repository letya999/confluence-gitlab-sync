Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venvDir = Join-Path $root ".venv"
$pythonExe = Join-Path $venvDir "Scripts\\python.exe"

if (-not (Test-Path $pythonExe)) {
  py -3 -m venv $venvDir
}

& $pythonExe -m pip install -e $root | Out-Host
& $pythonExe -m confluence_sync.server

