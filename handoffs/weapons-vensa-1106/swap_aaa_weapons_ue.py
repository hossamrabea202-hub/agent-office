# Weapons at Vesna (audit seat, 2026-11-06): point BPC_WeaponKit's Meshes[] at TGA's AAA meshes for the 5 #397 weapons. Data only, no graph change.
#   py "<repo>/handoffs/weapons-vensa-1106/swap_aaa_weapons_ue.py"            dry run: prints live vs AAA mesh per row, bounds, changes nothing
#   py ".../swap_aaa_weapons_ue.py" --apply                                     writes Meshes[idx] = CK_AAA mesh, compiles, saves (backup json next to this file)
#   py ".../swap_aaa_weapons_ue.py" --revert                                    restores Meshes[] from the backup json
# Run AFTER assets/tga/WeaponsAAA/import_weapons_aaa_ue.py (DRY_RUN = False) and only on the owner's OK of TGA's before/after sheet.
# Syntax-checked only, never run in UE (no editor on this seat). Save after it.
import json, os, sys, unreal

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = '/Game/CastleDefender/Gameplay/Castle/BPC_WeaponKit'
ROWS = {0: 'ArmingSword', 6: 'Longsword', 10: 'WarAxe', 14: 'FlangedMace', 23: 'Halberd'}
AAA = '/Game/CastleDefender/Weapons/CK_AAA/%s/SM_CK_%s'
BACKUP = os.path.join(HERE, 'swap_aaa_backup.json')
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
mode = 'apply' if '--apply' in sys.argv else 'revert' if '--revert' in sys.argv else 'dry'
log = ['swap AAA weapons: ' + mode]

bp = unreal.load_asset(KIT)
BEL.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class())
names = list(cdo.get_editor_property('Names')); meshes = list(cdo.get_editor_property('Meshes'))
log.append('BPC_WeaponKit rows: %d names, %d meshes' % (len(names), len(meshes)))

def bounds(m):
    if not m: return 'none'
    b = m.get_bounding_box(); return 'z %.1f..%.1f cm, %d tris' % (b.min.z, b.max.z, m.get_num_triangles(0))

if mode == 'revert':
    old = json.load(open(BACKUP))
    for k, p in old.items():
        i = int(k); meshes[i] = unreal.load_asset(p) if p else None; log.append('row %2d %-14s <- %s' % (i, names[i], p))
else:
    backup = {}
    for i, folder in ROWS.items():
        if i >= len(names) or names[i].replace(' ', '') != folder:
            log.append('row %2d: expected %s, found %r: STOP, the kit order changed' % (i, folder, names[i] if i < len(names) else None)); continue
        p = AAA % (folder, folder); ok = EAL.does_asset_exist(p)
        live = meshes[i]; new = unreal.load_asset(p) if ok else None
        log.append('row %2d %-14s live %s [%s]  aaa %s [%s]' % (i, names[i], live.get_path_name() if live else 'none', bounds(live), p if ok else 'MISSING (run import_weapons_aaa_ue.py)', bounds(new)))
        if mode == 'apply' and ok:
            backup[str(i)] = live.get_path_name() if live else ''; meshes[i] = new
    if mode == 'apply':
        json.dump(backup, open(BACKUP, 'w'), indent=1); log.append('backup -> ' + BACKUP)
if mode != 'dry':
    cdo.set_editor_property('Meshes', meshes); BEL.compile_blueprint(bp); EAL.save_asset(KIT); log.append('saved ' + KIT + ' (an equipped weapon re-reads Meshes on the next ApplyEquip: put it away and take it again, or restart Play)')
else:
    log.append('dry run: nothing changed. Full bounds (all three axes) live vs AAA must match before --apply: the live kit is 0.01 scale, run reimport_aaa_scale_ue.py --apply first.')
out = '\n'.join(log); open(os.path.join(HERE, 'swap_aaa_weapons.txt'), 'w').write(out); unreal.log(out)
