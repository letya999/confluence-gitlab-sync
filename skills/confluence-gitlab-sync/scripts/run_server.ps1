Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\..\..\..\packages\confluence-sync-mcp"
try {
  confluence-sync-mcp
}
finally {
  Pop-Location
}

