Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\..\tools\confluence_sync"
try {
  confluence-sync-mcp
}
finally {
  Pop-Location
}

