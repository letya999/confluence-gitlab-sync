Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venvDir = Join-Path $root ".venv"
$pythonExe = Join-Path $venvDir "Scripts\\python.exe"

if (-not (Test-Path $pythonExe)) {
  & py -3 -m venv $venvDir *> $null
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to create Python virtual environment at $venvDir"
  }
}

# Install the package only when missing to keep MCP startup fast and quiet.
& $pythonExe -c "import confluence_sync" *> $null
if ($LASTEXITCODE -ne 0) {
  & $pythonExe -m pip install --disable-pip-version-check --quiet -e $root *> $null
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to install package into venv"
  }
}
& $pythonExe -m confluence_sync.server

