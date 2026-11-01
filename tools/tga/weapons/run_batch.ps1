# #397: build the AAA weapons + BEFORE / AFTER lookdev in the same locked rig + pbr_check, for a list of weapons.
#   powershell -File run_batch.ps1 -Out T:\waaa -Weapons arming_sword,longsword,war_axe,halberd,flanged_mace
param([string]$Out = 'T:\waaa', [string[]]$Weapons = @('arming_sword', 'longsword', 'war_axe', 'halberd', 'flanged_mace'))
$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$ck = Join-Path $here '..\..\..\assets\checkking\Weapons'
$names = @{ arming_sword = 'ArmingSword'; longsword = 'Longsword'; war_axe = 'WarAxe'; halberd = 'Halberd'; flanged_mace = 'FlangedMace'; falchion = 'Falchion';
            viking_sword = 'VikingSword'; estoc = 'Estoc'; zweihander = 'Zweihander'; katzbalger = 'Katzbalger'; rondel_dagger = 'RondelDagger'; messer = 'Messer';
            bearded_axe = 'BeardedAxe'; dane_axe = 'DaneAxe'; bardiche = 'Bardiche'; war_hammer = 'WarHammer'; winged_spear = 'WingedSpear'; boar_spear = 'BoarSpear';
            partisan = 'Partisan'; ranseur = 'Ranseur'; pollaxe = 'Pollaxe'; lochaber_axe = 'LochaberAxe'; guisarme = 'Guisarme'; morning_star = 'MorningStar'; glaive = 'Glaive' }
$heads = @('war_axe', 'halberd', 'flanged_mace', 'bearded_axe', 'dane_axe', 'bardiche', 'war_hammer', 'pollaxe', 'lochaber_axe', 'morning_star', 'winged_spear', 'boar_spear', 'partisan', 'ranseur', 'guisarme', 'glaive')
foreach ($w in $Weapons) {
  $n = $names[$w]; $env:DFRAC = $(if ($heads -contains $w) { '0.93' } else { '0.62' })
  & U:\blender.exe -b --factory-startup -P (Join-Path $here 'build_weapon_aaa.py') -- $w $Out 2048 32 2>&1 | Select-String 'WEAPON DONE|ALBEDO|LIFTED|Traceback|Error:'
  $old = Join-Path $ck $n
  & U:\blender.exe -b --factory-startup -P (Join-Path $here 'lookdev_weapon.py') -- "$old\SM_CK_$n.fbx" "$old\textures" "T_CK_$n" "$Out\before_$n.png" 2>&1 | Select-String 'LOOKDEV|Traceback'
  & U:\blender.exe -b --factory-startup -P (Join-Path $here 'lookdev_weapon.py') -- "$Out\$n\SM_CK_$n.fbx" "$Out\$n\textures" "T_CK_$n" "$Out\after_$n.png" 2>&1 | Select-String 'LOOKDEV|Traceback'
  & U:\blender.exe -b --factory-startup -P (Join-Path $here '..\..\laptop2\pbr_check.py') -- "$Out\$n\textures\T_CK_${n}_BaseColor.png" "$Out\$n\textures\T_CK_${n}_ORM.png" "$old\textures\T_CK_${n}_BaseColor.png" "$old\textures\T_CK_${n}_ORM.png" 2>&1 | Select-String 'PBR' | ForEach-Object { "PBRLINE $n " + $_ }
}
'BATCH DONE'
