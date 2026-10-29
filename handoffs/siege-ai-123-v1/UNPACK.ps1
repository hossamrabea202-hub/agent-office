$ErrorActionPreference = 'Stop'
$encoded = Join-Path $PSScriptRoot 'package.zip.b64'
$archive = Join-Path $PSScriptRoot 'Siege_AI_123_Source_Milestone.zip'
$destination = Join-Path $PSScriptRoot 'extracted'
if ((Test-Path -LiteralPath $archive) -or (Test-Path -LiteralPath $destination)) { throw 'Refusing existing archive or extraction folder.' }
$bytes = [Convert]::FromBase64String([IO.File]::ReadAllText($encoded))
$sha = [Security.Cryptography.SHA256]::Create()
try { $actual = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
if ($actual -ne '2d6d78b9c959a23cf81c6a691b5c9e377d4d555301458bebdd2b8258b837a422') { throw 'Package hash mismatch; nothing extracted.' }
[IO.File]::WriteAllBytes($archive,$bytes)
Expand-Archive -LiteralPath $archive -DestinationPath $destination
Write-Output "Verified and extracted: $destination. Read README before installation."
