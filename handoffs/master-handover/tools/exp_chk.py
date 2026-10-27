import unreal, os
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
names = ['BP_ArmyHUD', 'BP_BarracksHUD', 'BP_CommanderHUD', 'BP_SoldierCommander', 'BP_ThirdPersonCharacter', 'BP_JellyBlob',
         'BP_SoldierLevelUpFX', 'BP_SoldierLevelWatch', 'BP_ZombieCharge', 'BP_HeroAuras', 'BP_BurnAura', 'BP_DefenseAura',
         'BP_HealAura', 'BP_SkillTreeHUD', 'BP_Zombie', 'BP_Cannonball']
ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets(unreal.ARFilter(package_paths=['/Game/CastleDefender'], recursive_paths=True, class_names=['Blueprint']))
by = {str(a.asset_name): str(a.package_name) for a in assets}
L = []
for n in names:
    p = by.get(n)
    if not p: L.append('%s NOT FOUND' % n); continue
    t = unreal.AssetExportTask(); t.set_editor_property('object', unreal.load_asset(p)); t.set_editor_property('filename', os.path.join(D, 't3d', 'chk_%s.t3d' % n))
    t.set_editor_property('exporter', unreal.ObjectExporterT3D()); t.set_editor_property('automated', True); t.set_editor_property('prompt', False); t.set_editor_property('replace_identical', True)
    L.append('%s %s %s' % (n, p, unreal.Exporter.run_asset_export_task(t)))
open(os.path.join(D, 'exp_chk_log.txt'), 'w').write('\n'.join(L))
