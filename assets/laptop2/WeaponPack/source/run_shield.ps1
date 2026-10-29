# Builds and bakes a shield. powershell -ExecutionPolicy Bypass -File run_shield.ps1 [-Shield Heater|Round] [-Size 4096] [-Samples 24] [-SkipBuild]
# Each step runs in its own Blender process; log in heater_bake.log ("ALL DONE" / "FAILED <step>"). Needs ~2 GB free.
param([string]$Shield = 'Heater', [int]$Size = 4096, [int]$Samples = 24, [switch]$SkipBuild)
$b = 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe'
Set-Location $PSScriptRoot
$env:WORK = $PSScriptRoot; $env:SHIELD = $Shield; $env:BAKE_SIZE = "$Size"; $env:BAKE_SAMPLES = "$Samples"
$log = "$($Shield.ToLower())_bake.log"; "start $(Get-Date)" | Set-Content $log
function Step($name, [string[]]$argv, $okText) {
    $t = Get-Date
    $out = & $b @argv 2>&1 | Out-String
    $ok = $out -match [regex]::Escape($okText)
    "$name ok=$ok minutes=$([math]::Round(((Get-Date) - $t).TotalMinutes, 1))" | Add-Content $log
    ($out -split "`n" | Select-String '^TRIS') -join "`n" | Add-Content $log
    if (-not $ok) { ($out -split "`n" | Select-String 'Error|Traceback|Malloc|line ' | Select-Object -Last 8) -join "`n" | Add-Content $log; "FAILED $name" | Add-Content $log; exit 1 }
}
if (-not $SkipBuild) { foreach ($r in 'low', 'high') { $env:RES = $r; Step "build $r" @('-b', '--factory-startup', '-P', "build_$($Shield.ToLower()).py") 'BUILD OK' } }
$env:STAGE = 'prep'; Step 'prep' @('-b', "$($Shield)_low.blend", '-P', 'bake_shield.py') 'STAGE prep OK'
$chans = @('BC', 'RG', 'MT', 'AO', 'Normal'); if ($Shield -eq 'Sword') { $chans += 'EM' }
foreach ($s in $chans) {
    $env:STAGE = $s
    foreach ($q in 0..3) { $env:QUAD = "$q"; Step "$s q$q" @('-b', "$($Shield)_bake.blend", '-P', 'bake_shield.py') "STAGE $s OK" }
    Remove-Item Env:QUAD
}
$env:STAGE = 'finish'; Step 'finish' @('-b', "$($Shield)_bake.blend", '-P', 'bake_shield.py') 'STAGE finish OK'
Remove-Item 'tex\raw_*.exr' -ErrorAction SilentlyContinue
"ALL DONE $(Get-Date)" | Add-Content $log
