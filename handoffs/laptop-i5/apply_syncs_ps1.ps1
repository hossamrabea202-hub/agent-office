# i5 (2026-11-03): apply i9's sync zips in order onto the project root, with the editor CLOSED.
# Every file a zip would overwrite is first copied to $Backup (same relative path, first copy wins = the pre-sync original).
# A DELETE_THESE.txt inside a zip (one project-relative path per line) is honoured after that zip: backed up, then deleted.
#   powershell -File apply_syncs_ps1.ps1 -Zips <folder with NN_*.zip> [-DryRun]
param([string]$Zips = 'C:\UnrealProjects\sync_1103_all', [switch]$DryRun)
$ErrorActionPreference = 'Stop'
$Proj = 'C:\UnrealProjects\Castle Defender 5.8'
$Backup = 'C:\UnrealProjects\CD58_backup_before_sync7_1103'
if (Get-Process UnrealEditor -ErrorAction SilentlyContinue) { throw 'Close the Unreal editor first' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
$log = @()
foreach ($zp in (Get-ChildItem $Zips -Filter '*.zip' | Sort-Object Name)) {
    $z = [IO.Compression.ZipFile]::OpenRead($zp.FullName)
    $n = 0; $new = 0; $dels = @()
    foreach ($e in $z.Entries) {
        if ($e.FullName.EndsWith('/') -or $e.FullName.EndsWith('\')) { continue }
        $rel = $e.FullName -replace '/', '\'
        if ($rel -match '(^|\\)DELETE_THESE\.txt$') {
            $r = New-Object IO.StreamReader($e.Open()); $dels += ($r.ReadToEnd() -split "`r?`n" | Where-Object { $_.Trim() }); $r.Close(); continue
        }
        if ($rel -match '\.\.') { throw "bad path in $($zp.Name): $rel" }
        $dst = Join-Path $Proj $rel
        if (Test-Path $dst) {
            $bk = Join-Path $Backup $rel
            if (-not (Test-Path $bk) -and -not $DryRun) { New-Item -ItemType Directory -Force (Split-Path $bk) | Out-Null; Copy-Item $dst $bk }
        } else { $new++ }
        if (-not $DryRun) { New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null; [IO.Compression.ZipFileExtensions]::ExtractToFile($e, $dst, $true) }
        $n++
    }
    $z.Dispose()
    foreach ($d in $dels) {
        $rel = (($d.Trim() -split '\s+')[0] -replace '/', '\').TrimStart('\'); $dst = Join-Path $Proj $rel
        if (Test-Path $dst) {
            $bk = Join-Path $Backup $rel
            if (-not $DryRun) { if (-not (Test-Path $bk)) { New-Item -ItemType Directory -Force (Split-Path $bk) | Out-Null; Copy-Item $dst $bk }; Remove-Item $dst }
            $log += "  deleted $rel"
        } else { $log += "  delete: not found $rel" }
    }
    $log += ('{0}: {1} files ({2} new), {3} deletes{4}' -f $zp.Name, $n, $new, $dels.Count, $(if ($DryRun) { ' [dry run]' } else { '' }))
}
$log | ForEach-Object { $_ }
$log | Out-File -Encoding utf8 (Join-Path $Zips 'apply_log.txt')
