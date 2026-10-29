$ErrorActionPreference = 'Stop'
$encoded = Join-Path $PSScriptRoot 'package.zip.b64'
$archive = Join-Path $PSScriptRoot 'Weapon_Upgrades_95_Source_Checkpoint.zip'
$destination = Join-Path $PSScriptRoot 'extracted'
if ((Test-Path -LiteralPath $archive) -or (Test-Path -LiteralPath $destination)) { throw 'Refusing existing archive or extraction folder.' }
$bytes = [Convert]::FromBase64String([IO.File]::ReadAllText($encoded))
$sha = [Security.Cryptography.SHA256]::Create()
try { $actual = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
if ($actual -ne '4e68d42f3c44ed0e3e555f685bcef7f9a818051928ad77fc944fadb55baddf74') { throw 'Package SHA256 mismatch; nothing extracted.' }
[IO.File]::WriteAllBytes($archive,$bytes)
Expand-Archive -LiteralPath $archive -DestinationPath $destination
Write-Output "Verified and extracted: $destination. Read README before installation."
