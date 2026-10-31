# Builds low + high fauld (TGA, from checkking's greave runner), then runs every bake stage in its own Blender process; logs to bake4k.log ("ALL DONE" / "FAILED <stage>").
param([int]$Size = 2048, [int]$Samples = 24, [string[]]$Only = @())
$b = 'U:\blender.exe'
Set-Location 'T:\obs\waist'
$log = 'bake4k.log'
"start $(Get-Date)" | Set-Content $log
$env:BAKE_SIZE = "$Size"; $env:BAKE_SAMPLES = "$Samples"
if (-not $Only.Count -or $Only -contains 'build') {
    foreach ($r in '1', '3') {
        $env:CHEST_RES = $r
        $out = & $b -b --factory-startup -P build_waist.py 2>&1 | Out-String
        "build r$r ok=$($out -match 'BUILD OK')" | Add-Content $log
        if ($out -notmatch 'BUILD OK') { "FAILED build" | Add-Content $log; exit 1 }
    }
}
$stages = @(@('prep', 'waist_build_r1.blend'), @('BC', 'bake_ready.blend'), @('RG', 'bake_ready.blend'), @('MT', 'bake_ready.blend'),
            @('AO', 'bake_ready.blend'), @('Normal', 'bake_ready.blend'), @('finish', 'bake_ready.blend'))
foreach ($s in $stages) {
    if ($Only.Count -and $Only -notcontains $s[0]) { continue }
    $env:STAGE = $s[0]
    if ($s[0] -in 'BC','RG','MT','AO','Normal') {
        foreach ($q in 0..3) {
            $env:QUAD = "$q"; $t = Get-Date
            $out = & $b -b $s[1] -P bake_staged.py 2>&1 | Out-String
            $ok = $out -match "STAGE $($s[0]) OK"
            "$($s[0]) q$q ok=$ok minutes=$([math]::Round(((Get-Date) - $t).TotalMinutes, 1))" | Add-Content $log
            if (-not $ok) { ($out -split "`n" | Select-String 'Error|Traceback|Malloc|line ' | Select-Object -Last 8) -join "`n" | Add-Content $log; "FAILED $($s[0]) q$q" | Add-Content $log; exit 1 }
        }
        Remove-Item Env:QUAD; continue
    }
    $t = Get-Date
    $out = & $b -b $s[1] -P bake_staged.py 2>&1 | Out-String
    $ok = $out -match "STAGE $($s[0]) OK"
    "$($s[0]) ok=$ok minutes=$([math]::Round(((Get-Date) - $t).TotalMinutes, 1))" | Add-Content $log
    ($out -split "`n" | Select-String '^TRIS') -join "`n" | Add-Content $log
    if (-not $ok) { ($out -split "`n" | Select-String 'Error|Traceback|Malloc|line ' | Select-Object -Last 8) -join "`n" | Add-Content $log; "FAILED $($s[0])" | Add-Content $log; exit 1 }
}
"ALL DONE $(Get-Date)" | Add-Content $log
