# Shop v2 step 1: add the Emberoath as weapon row 26 in BPC_WeaponKit (i5 core, 2026-11-01). UE 5.8 Python.
#   py ".../emberoath_row_ue.py"          read-only: mesh bounds of SM_Emberoath vs the CK swords
#   py ".../emberoath_row_ue.py" --apply  backup BPC_WeaponKit -> BPC_WeaponKit_BACKUP418, append the row, compile, save
#   py ".../emberoath_row_ue.py" --revert remove the Emberoath row again (compile, save)
# Stats: the Starmetal class (mine-201 RECIPES: damage +60 % over a longsword's 58 -> 90 is too much for a one-hander,
# Decision: 85 dmg, speed 0.95, 2,500 gold: the top of the list, above the Zweihander's 80 / 1,200).
import sys, unreal
A = sys.argv[1:]
EAL = unreal.EditorAssetLibrary
P = '/Game/CastleDefender/Gameplay/Castle/BPC_WeaponKit'
MESH = '/Game/CastleDefender/Weapons/Emberoath/SM_Emberoath'
log = []
for p in (MESH, '/Game/CastleDefender/Weapons/CK/ArmingSword/SM_CK_ArmingSword', '/Game/CastleDefender/Weapons/CK/Longsword/SM_CK_Longsword'):
    b = unreal.load_asset(p).get_bounding_box()
    log.append('%-60s min (%.1f, %.1f, %.1f) max (%.1f, %.1f, %.1f)' % (p.split('/')[-1], b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z))
if '--apply' in A or '--revert' in A:
    bp = unreal.load_asset(P)
    cdo = unreal.get_default_object(unreal.BlueprintEditorLibrary.generated_class(bp))
    names = list(cdo.get_editor_property('Names'))
    cols = {k: list(cdo.get_editor_property(k)) for k in ('Names', 'Prices', 'Damage', 'Speed', 'Meshes')}
    if '--apply' in A:
        if 'Emberoath' in names: log.append('already has Emberoath')
        else:
            if not EAL.does_asset_exist(P + '_BACKUP418'): EAL.duplicate_asset(P, P + '_BACKUP418')
            # The CK kit meshes are stored at 1/100 (metres as cm) and the hand chain scales them up; SM_Emberoath is
            # real cm. So the shop uses a new copy built at 0.0135, ~90 cm overall (the original mesh is not touched).
            KIT = MESH + '_Kit'
            if not EAL.does_asset_exist(KIT): EAL.duplicate_asset(MESH, KIT)
            km = unreal.load_asset(KIT); sme = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
            bs = sme.get_lod_build_settings(km, 0); bs.set_editor_property('build_scale3d', unreal.Vector(0.0135, 0.0135, 0.0135))
            sme.set_lod_build_settings(km, 0, bs); EAL.save_asset(KIT, only_if_is_dirty=False)
            b = km.get_bounding_box(); log.append('SM_Emberoath_Kit max z %.2f (CK longsword 1.0)' % b.max.z)
            row = {'Names': 'Emberoath', 'Prices': 2500, 'Damage': 85, 'Speed': 0.95, 'Meshes': km}
            for k in cols: cols[k].append(row[k])
    else:
        if 'Emberoath' in names:
            i = names.index('Emberoath')
            for k in cols: cols[k].pop(i)
    if cols['Names'] != names:
        for k, v in cols.items(): cdo.set_editor_property(k, v)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        EAL.save_asset(P, only_if_is_dirty=False)
        log.append('BPC_WeaponKit now %d rows: last = %s' % (len(cols['Names']), cols['Names'][-1]))
out = '\n'.join(log); unreal.log('i5 emberoath: ' + out); print(out)
