param([Parameter(Mandatory=$true)][string]$Destination)
$ErrorActionPreference = 'Stop'
$resolvedDestination = [IO.Path]::GetFullPath($Destination)
$archivePath = $resolvedDestination + '.zip'
if ((Test-Path -LiteralPath $resolvedDestination) -or (Test-Path -LiteralPath $archivePath)) {
    throw 'Choose a new destination. Existing folders and zip files are never overwritten.'
}
$bytes = [Convert]::FromBase64String((Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'package.zip.b64')))
$hasher = [Security.Cryptography.SHA256]::Create()
try { $actualHash = ([BitConverter]::ToString($hasher.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() }
finally { $hasher.Dispose() }
$expectedHash = (Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'PACKAGE_SHA256.txt')).Trim()
if ($actualHash -ne $expectedHash) { throw 'Package SHA256 mismatch; download the complete current handoff again.' }
$parentDirectory = [IO.Path]::GetDirectoryName($resolvedDestination)
if (-not (Test-Path -LiteralPath $parentDirectory -PathType Container)) { throw 'Destination parent must already exist.' }
[IO.File]::WriteAllBytes($archivePath, $bytes)
Expand-Archive -LiteralPath $archivePath -DestinationPath $resolvedDestination
$manifest = Get-Content -Raw -LiteralPath (Join-Path $resolvedDestination 'SHA256SUMS.json') | ConvertFrom-Json
$prefix = $resolvedDestination.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
foreach ($item in $manifest.PSObject.Properties) {
    $filePath = [IO.Path]::GetFullPath((Join-Path $resolvedDestination $item.Name))
    if (-not $filePath.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe manifest path.' }
    if ((Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.Value.sha256) {
        throw ('Extracted file hash mismatch: ' + $item.Name)
    }
}
Write-Output ('Verified and extracted to ' + $resolvedDestination + '. Read BLUEPRINT_SETUP.md. No Unreal operations were performed.')
