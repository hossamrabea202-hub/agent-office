# Builds and bakes the siege barricade kit (#29). powershell -File run_kit.ps1 [-Assets Palisade,Cheval] [-Size 4096]
# Each step runs in its own Blender process; log in kit_bake.log ("ALL DONE" / "FAILED <step>"). Needs ~2 GB free.
param([string[]]$Assets = @('Palisade', 'Cheval'), [int]$Size = 4096, [int]$Samples = 24)
$b = 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe'
Set-Location $PSScriptRoot
$env:WORK = $PSScriptRoot; $env:BAKE_SIZE = "$Size"; $env:BAKE_SAMPLES = "$Samples"
$log = 'kit_bake.log'; "start $(Get-Date)" | Set-Content $log
function Step($name, [string[]]$argv, $okText) {
    $t = Get-Date
    $out = & $b @argv 2>&1 | Out-String
    $ok = $out -match [regex]::Escape($okText)
    "$name ok=$ok minutes=$([math]::Round(((Get-Date) - $t).TotalMinutes, 1))" | Add-Content $log
    ($out -split "`n" | Select-String '^TRIS') -join "`n" | Add-Content $log
    if (-not $ok) { ($out -split "`n" | Select-String 'Error|Traceback|Malloc|line ' | Select-Object -Last 8) -join "`n" | Add-Content $log; "FAILED $name" | Add-Content $log; exit 1 }
}
foreach ($a in $Assets) {
    $env:ASSET = $a
    foreach ($r in 'low', 'high') { $env:RES = $r; Step "$a build $r" @('-b', '--factory-startup', '-P', 'build_kit.py') 'BUILD OK' }
    $env:STAGE = 'prep'; Step "$a prep" @('-b', "$($a)_low.blend", '-P', 'bake_kit.py') 'STAGE prep OK'
    foreach ($s in 'BC', 'RG', 'AO', 'Normal') {
        $env:STAGE = $s
        foreach ($q in 0..3) { $env:QUAD = "$q"; Step "$a $s q$q" @('-b', "$($a)_bake.blend", '-P', 'bake_kit.py') "STAGE $s OK" }
        Remove-Item Env:QUAD
    }
    $env:STAGE = 'finish'; Step "$a finish" @('-b', "$($a)_bake.blend", '-P', 'bake_kit.py') 'STAGE finish OK'
    Remove-Item "tex\$($a)_raw_*.exr" -ErrorAction SilentlyContinue
}
"ALL DONE $(Get-Date)" | Add-Content $log
