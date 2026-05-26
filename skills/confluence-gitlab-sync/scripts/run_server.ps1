Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Prefer monorepo-local bootstrap when available; otherwise use installed command.
$repoServerScript = Join-Path $PSScriptRoot "..\..\..\packages\confluence-sync-mcp\scripts\run_server_venv.ps1"
if (Test-Path $repoServerScript) {
  Push-Location "$PSScriptRoot\..\..\..\packages\confluence-sync-mcp"
  try {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $repoServerScript
    if ($LASTEXITCODE -ne 0) {
      throw "MCP server failed with exit code $LASTEXITCODE"
    }
  }
  finally {
    Pop-Location
  }
}
else {
  & confluence-sync-mcp
  if ($LASTEXITCODE -ne 0) {
    throw "MCP server failed with exit code $LASTEXITCODE"
  }
}

