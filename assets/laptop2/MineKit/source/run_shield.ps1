# Builds and bakes a shield. powershell -ExecutionPolicy Bypass -File run_shield.ps1 [-Shield Heater|Round] [-Size 4096] [-Samples 24] [-SkipBuild]
# Each step runs in its own Blender process; log in heater_bake.log ("ALL DONE" / "FAILED <step>"). Needs ~2 GB free.
param([string]$Shield = 'Heater', [int]$Size = 4096, [int]$Samples = 24, [switch]$SkipBuild)
$b = 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe'
Set-Location $PSScriptRoot
$env:WORK = $PSScriptRoot; $env:SHIELD = $Shield; if ($Shield -like "Potion*") { $env:VARIANT = $Shield.Substring(6) }; if ($Shield -like "Flora*") { $env:VARIANT = $Shield.Substring(5) }; if ($Shield -like "Props*") { $env:VARIANT = $Shield.Substring(5) }; if ($Shield -like "Camp*") { $env:VARIANT = $Shield.Substring(4) }; if ($Shield -like "Ground*") { $env:VARIANT = $Shield.Substring(6) }; $env:BAKE_SIZE = "$Size"; $env:BAKE_SAMPLES = "$Samples"
$log = "$($Shield.ToLower())_bake.log"; "start $(Get-Date)" | Set-Content $log
function Step($name, [string[]]$argv, $okText) {
    $t = Get-Date
    $out = & $b @argv 2>&1 | Out-String
    $ok = $out -match [regex]::Escape($okText)
    "$name ok=$ok minutes=$([math]::Round(((Get-Date) - $t).TotalMinutes, 1))" | Add-Content $log
    ($out -split "`n" | Select-String '^TRIS') -join "`n" | Add-Content $log
    if (-not $ok) { ($out -split "`n" | Select-String 'Error|Traceback|Malloc|line ' | Select-Object -Last 8) -join "`n" | Add-Content $log; "FAILED $name" | Add-Content $log; exit 1 }
}
if (-not $SkipBuild) { foreach ($r in 'low', 'high') { $env:RES = $r; $bs = if ($Shield -like 'Potion*') { 'build_potion.py' } elseif ($Shield -like 'Flora*') { 'build_flora.py' } elseif ($Shield -like 'Props*') { 'build_props.py' } elseif ($Shield -like 'Camp*') { 'build_camp.py' } elseif ($Shield -like 'Ground*') { 'build_ground.py' } else { "build_$($Shield.ToLower()).py" }; if ($Shield -like 'Potion*') { $env:VARIANT = $Shield.Substring(6) }; if ($Shield -like 'Flora*') { $env:VARIANT = $Shield.Substring(5) }; if ($Shield -like 'Props*') { $env:VARIANT = $Shield.Substring(5) }; if ($Shield -like 'Camp*') { $env:VARIANT = $Shield.Substring(4) }; if ($Shield -like 'Ground*') { $env:VARIANT = $Shield.Substring(6) }; Step "build $r" @('-b', '--factory-startup', '-P', $bs) 'BUILD OK' } }
$env:STAGE = 'prep'; Step 'prep' @('-b', "$($Shield)_low.blend", '-P', 'bake_shield.py') 'STAGE prep OK'
$chans = @('BC', 'RG', 'MT', 'AO', 'Normal'); if ($Shield -in @('Sword', 'Ballista') -or ($Shield -like 'Flora*' -and $Shield -notin @('FloraDaisy','FloraPoppy','FloraFoxglove')) -or $Shield -in @('CampTorchPost', 'CampCampfire', 'CampForge', 'CampLantern', 'CampOreStar') -or $Shield -like 'Ground*') { $chans += 'EM' }; if ($Shield -eq 'GroundCorrupt') { $chans += 'HT' }
foreach ($s in $chans) {
    $env:STAGE = $s
    foreach ($q in 0..3) { $env:QUAD = "$q"; Step "$s q$q" @('-b', "$($Shield)_bake.blend", '-P', 'bake_shield.py') "STAGE $s OK" }
    Remove-Item Env:QUAD
}
$env:STAGE = 'finish'; Step 'finish' @('-b', "$($Shield)_bake.blend", '-P', 'bake_shield.py') 'STAGE finish OK'
Remove-Item 'tex\*_raw_*.exr' -ErrorAction SilentlyContinue
Remove-Item "$($Shield)_bake.blend", "$($Shield)_high.blend" -ErrorAction SilentlyContinue
$tn = if ($Shield -eq 'Sword') { 'T_Emberoath' } elseif ($Shield -like 'Potion*') { 'T_Potion_' + $Shield.Substring(6) } elseif ($Shield -eq 'Gate') { 'T_SiegeGate' } elseif ($Shield -eq 'Ballista') { 'T_FireBallista' } elseif ($Shield -like 'Flora*') { 'T_Flora_' + $Shield.Substring(5) } elseif ($Shield -like 'Props*') { 'T_Barracks_' + $Shield.Substring(5) } elseif ($Shield -like 'Camp*') { 'T_Camp_' + $Shield.Substring(4) } elseif ($Shield -like 'Ground*') { 'T_Ground_' + $Shield.Substring(6) } else { "T_$($Shield)Shield" }
$chk = & $b @('-b', '--factory-startup', '-P', 'pbr_check.py', '--', "$PSScriptRoot/tex/$($tn)_BaseColor.png", "$PSScriptRoot/tex/$($tn)_ORM.png") 2>&1 | Out-String
($chk -split "`n" | Select-String '^PBR') -join "`n" | Add-Content $log
"ALL DONE $(Get-Date)" | Add-Content $log
