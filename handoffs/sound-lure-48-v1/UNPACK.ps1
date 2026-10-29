$ErrorActionPreference = 'Stop'
$encoded = Join-Path $PSScriptRoot 'package.zip.b64'
$archive = Join-Path $PSScriptRoot 'Sound_Lure_48_Source_Handoff.zip'
$destination = Join-Path $PSScriptRoot 'extracted'
if ((Test-Path -LiteralPath $archive) -or (Test-Path -LiteralPath $destination)) { throw 'Refusing existing archive or extraction folder.' }
$bytes = [Convert]::FromBase64String([IO.File]::ReadAllText($encoded))
$sha = [Security.Cryptography.SHA256]::Create()
try { $actual = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
if ($actual -ne 'd7c17b7d52415581c0154d41673b8729bea1148d637f2af31a4921e3be744f74') { throw 'Package SHA256 mismatch; nothing extracted.' }
[IO.File]::WriteAllBytes($archive,$bytes)
Expand-Archive -LiteralPath $archive -DestinationPath $destination
Write-Output "Verified and extracted: $destination. Read README before installation."
