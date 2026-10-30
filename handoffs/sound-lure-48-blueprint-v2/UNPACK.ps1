$ErrorActionPreference = 'Stop'
$packageRoot = $PSScriptRoot
$manifest = Get-Content -LiteralPath (Join-Path $packageRoot 'manifest.json') -Raw | ConvertFrom-Json
$zipPath = Join-Path $packageRoot 'sound-lure-48-blueprint.zip'
$destination = Join-Path $packageRoot 'unpacked'
if (Test-Path -LiteralPath $destination) { throw 'unpacked already exists; choose a fresh directory instead of overwriting it.' }
$bytes = [Convert]::FromBase64String((Get-Content -LiteralPath (Join-Path $packageRoot 'package.zip.b64') -Raw))
$hasher = [Security.Cryptography.SHA256]::Create()
try { $hash = ([BitConverter]::ToString($hasher.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant() } finally { $hasher.Dispose() }
if ($hash -ne $manifest.sha256) { throw 'Package SHA256 mismatch; no extraction performed.' }
if ($bytes.Length -ne $manifest.bytes) { throw 'Package size mismatch; no extraction performed.' }
if (Test-Path -LiteralPath $zipPath) {
    if ((Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hash) { throw 'A different ZIP already exists; refusing to overwrite.' }
} else { [IO.File]::WriteAllBytes($zipPath, $bytes) }
Expand-Archive -LiteralPath $zipPath -DestinationPath $destination
Write-Output "Verified and extracted to $destination. Read README.md. Only the Master runs Unreal."
