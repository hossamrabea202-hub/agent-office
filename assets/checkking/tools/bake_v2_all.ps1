# v2 re-bake of shoulders then gauntlets from their existing bake_ready.blend; deletes each bake's raw EXRs when it's done.
$b = 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe'
foreach ($p in @(@('shoulders', ''), @('gauntlets', '0.5'))) {
    $d = "C:\Users\hossam.rabea\checkking-work\$($p[0])"
    Copy-Item "$d\bake_ready.blend" "$d\bake_ready_v1.blend" -Force
    $a = @('-b', "$d\bake_ready.blend", '-P', 'C:\Users\hossam.rabea\checkking-work\remat_v2.py'); if ($p[1]) { $a += @('--', $p[1]) }
    $out = & $b @a 2>&1 | Out-String
    if ($out -notmatch 'REMAT OK') { "REMAT FAILED $($p[0])"; ($out -split "`n" | Select-Object -Last 15) -join "`n"; exit 1 }
    & "$d\run_bake.ps1" -Only BC,RG,MT,AO,Normal,finish
    Get-Content "$d\bake4k.log" -Tail 2
    Remove-Item "$d\tex\raw_*.exr" -Confirm:$false -ErrorAction SilentlyContinue
    "{0}: done, {1:N0} MB free" -f $p[0], ((Get-PSDrive C).Free/1MB)
}
