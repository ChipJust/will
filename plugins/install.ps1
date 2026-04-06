#!/usr/bin/env pwsh
# Install will repo plugins into Claude Code's plugin directory.
# Run from the will repo root: .\plugins\install.ps1

$WillDir = Split-Path -Parent $PSScriptRoot
$ClaudePlugins = "$env:USERPROFILE\.claude\plugins\marketplaces\will-plugins\plugins"
$KnownMarketplaces = "$env:USERPROFILE\.claude\plugins\known_marketplaces.json"

Write-Host "==> Installing will plugins to $ClaudePlugins"
New-Item -ItemType Directory -Force -Path $ClaudePlugins | Out-Null

Get-ChildItem -Directory "$WillDir\plugins" | Where-Object { $_.Name -notmatch "^install" } | ForEach-Object {
    $name = $_.Name
    Write-Host "    Installing plugin: $name"
    $dest = Join-Path $ClaudePlugins $name
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
    Copy-Item $_.FullName $dest -Recurse
}

if (Test-Path $KnownMarketplaces) {
    $data = Get-Content $KnownMarketplaces | ConvertFrom-Json
    $data | Add-Member -Force -NotePropertyName "will-plugins" -NotePropertyValue @{
        source = @{ source = "local"; path = "$WillDir\plugins" }
        installLocation = $ClaudePlugins
        lastUpdated = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    }
    $data | ConvertTo-Json -Depth 5 | Set-Content $KnownMarketplaces
    Write-Host "    Registered will-plugins marketplace"
}

Write-Host "==> Plugins installed. Restart Claude Code to pick them up."
