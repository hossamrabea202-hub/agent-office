# checkking bake chain, runs on its own (started outside any Claude session) on the PC that has C:\Users\hossam.rabea\checkking-work.
# 1) waits for the shoulders + gauntlets v2 re-bake (bake_v2_all.ps1) and redoes it if it was cut off,
# 2) builds + bakes boots, then shins,
# 3) after each piece copies its results into the office repo clone and commits + pushes ("checkking (auto-bake): ...").
# Log: C:\Users\hossam.rabea\checkking-work\bake_chain.log
$ErrorActionPreference = 'Continue'
$W = 'C:\Users\hossam.rabea\checkking-work'; $R = "$W\repo"; $B = 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe'
$GH = 'C:\Program Files\GitHub CLI\gh.exe'; $log = "$W\bake_chain.log"
$OS = "$R\assets\checkking\Obsidian-Sovereign"
function L($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Add-Content $log }
function FreeMB { [math]::Round((Get-PSDrive C).Free / 1MB) }
function Done($dir, $since) { $p = "$W\$dir\bake4k.log"; if (-not (Test-Path $p)) { return $false }
    $t = Get-Content $p; ($t -match '^ALL DONE').Count -gt 0 -and (Get-Item $p).LastWriteTime -gt $since }
function Push($msg, $paths) {
    for ($i = 0; $i -lt 4; $i++) {
        git -C $R pull -q --rebase 2>&1 | Out-Null
        foreach ($p in $paths) { git -C $R add -- $p 2>&1 | Out-Null }
        git -C $R commit -q -m "$msg`n`nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" 2>&1 | Out-Null
        git -C $R push -q 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { L "pushed: $msg"; return $true }
        Start-Sleep 20
    }
    L "PUSH FAILED: $msg"; return $false
}
function Say($text) { & $GH issue comment 25 --repo hossamrabea202-hub/agent-office --body "From: checkking (Claude)`n`n$text" 2>&1 | Out-Null }
function CopyTex($dir, $tn, $dest) { New-Item -ItemType Directory -Force "$dest\textures" | Out-Null
    foreach ($n in 'BaseColor', 'ORM', 'Normal_DirectX') { Copy-Item "$W\$dir\tex\$($tn)_$n.png" "$dest\textures\" -Force } }

L "chain start, $(FreeMB) MB free"
$start = (Get-Date).AddHours(-1)

# ---- 1) shoulders + gauntlets v2 re-bake ----
while (Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -match 'bake_v2_all\.ps1' }) { Start-Sleep 60 }
foreach ($p in @(@('shoulders', '', 'Shoulders'), @('gauntlets', '0.5', 'Gauntlets'))) {
    $d = "$W\$($p[0])"
    if (-not (Done $p[0] $start)) {
        L "$($p[0]) re-bake not finished, redoing ($(FreeMB) MB free)"
        Remove-Item "$d\tex\raw_*.exr" -Confirm:$false -ErrorAction SilentlyContinue
        $a = @('-b', "$d\bake_ready.blend", '-P', "$W\remat_v2.py"); if ($p[1]) { $a += @('--', $p[1]) }
        & $B @a 2>&1 | Out-Null
        & "$d\run_bake.ps1" -Only BC,RG,MT,AO,Normal,finish
        Remove-Item "$d\tex\raw_*.exr" -Confirm:$false -ErrorAction SilentlyContinue
    }
    if (Done $p[0] $start) {
        CopyTex $p[0] "T_ObsidianSovereign_$($p[2])" "$OS\$($p[2])"
        if (Push "checkking (auto-bake): $($p[2]) v2 textures (same material as the chest v2; meshes and UVs unchanged)" @("assets/checkking/Obsidian-Sovereign/$($p[2])/textures")) {
            Say "auto-bake: Obsidian $($p[2]) v2 textures pushed (matches the chest v2 look; FBX/UVs unchanged, so a texture re-import is enough)." }
    } else { L "$($p[0]) FAILED, see $d\bake4k.log" }
}

# ---- 2) + 3) boots, then shins ----
foreach ($p in @(@('boots', 'Boots', 'boot_final.blend', 'render_boot.py'), @('shins', 'Shins', 'shin_final.blend', 'render_shin.py'))) {
    $d = "$W\$($p[0])"
    L "$($p[0]) bake start ($(FreeMB) MB free)"
    & "$d\run_bake.ps1"
    Remove-Item "$d\tex\raw_*.exr" -Confirm:$false -ErrorAction SilentlyContinue
    if (-not (Done $p[0] $start)) { L "$($p[0]) FAILED, see $d\bake4k.log"; Say "auto-bake: Obsidian $($p[1]) bake FAILED on the old PC (log in checkking-work\$($p[0])\bake4k.log). Rebuild from assets/checkking/Obsidian-Sovereign/$($p[1])/source."; continue }
    $dest = "$OS\$($p[1])"
    CopyTex $p[0] "T_ObsidianSovereign_$($p[1])" $dest
    foreach ($s in 'L', 'R') { Copy-Item "$d\SM_ObsidianSovereign_$($p[1])_$s.fbx" "$dest\" -Force }
    New-Item -ItemType Directory -Force "$dest\renders" | Out-Null
    & $B -b "$d\$($p[2])" -P "$d\$($p[3])" -- "$dest\renders\$($p[0])4k" 64 1400 keep 2>&1 | Out-Null
    if (Push "checkking (auto-bake): Obsidian $($p[1]) L/R baked (4K BaseColor/ORM/Normal DX, FBX, renders)" @("assets/checkking/Obsidian-Sovereign/$($p[1])")) {
        Say "auto-bake: Obsidian $($p[1]) L/R baked and pushed (assets/checkking/Obsidian-Sovereign/$($p[1])): 4K textures, FBX, renders. README + UE import script still to write." }
}
L "chain end, $(FreeMB) MB free"
