# #470 (i5, 2026-11-03). Owner: "remove all the funny snake looking like black so called cracks from the stones".
# They are a WORLD-SPACE crack overlay (T_CrackMask, CrackAmount / CrackSize_cm) that the stone materials paint across the
# masonry with no regard for joints or stone edges, so they read as black snakes. Real stone cracks follow joints and edges;
# the baked masonry already carries its joints, chips and wear. Fix: CrackAmount = 0 on every stone material instance.
# Not touched: wood cracks (CrackStrength on the drawbridge) and carved geometry cracks (fountain CrackDepthWindow).
#   py crack470_ue.py --dry-run | --apply | --revert      backup crack470_backup.json (each MI's old CrackAmount). Aborts in PIE.
# Base MATERIALS used directly on meshes (no MI) can't be changed from here: they are listed for a 1-minute manual edit.
import json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
H = next((h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/castle-harmony-461/', 'C:/Users/hossa/Documents/agent-office/handoffs/castle-harmony-461/')
          if os.path.isdir(h)), None)
BK = H + 'crack470_backup.json'
MEL, EAL = unreal.MaterialEditingLibrary, unreal.EditorAssetLibrary
ar = unreal.AssetRegistryHelpers.get_asset_registry()
f = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant')], package_paths=['/Game/CastleDefender'], recursive_paths=True)
if '--revert' in A:
    bk = json.load(open(BK)); n = 0
    for p, v in bk.items():
        mi = unreal.load_asset(p)
        if mi: MEL.set_material_instance_scalar_parameter_value(mi, 'CrackAmount', v); MEL.update_material_instance(mi); EAL.save_loaded_asset(mi); n += 1
    print('REVERTED', n, 'MIs'); raise SystemExit
bk = json.load(open(BK)) if os.path.exists(BK) else {}
todo, bases = [], set()
for ad in ar.get_assets(f):
    p = str(ad.package_name)
    if '/AssetPacks/' in p or 'Drawbridge' in p or 'Fountain' in p: continue
    mi = unreal.load_asset(p)
    if not mi or 'CrackAmount' not in [str(x) for x in MEL.get_scalar_parameter_names(mi)]: continue
    v = MEL.get_material_instance_scalar_parameter_value(mi, 'CrackAmount')
    q = mi
    while isinstance(q, unreal.MaterialInstance): q = q.get_editor_property('parent')
    if q: bases.add(q.get_path_name().split('.')[0])
    if v > 0: todo.append((p, v))
for p, v in sorted(todo): print('MI %-80s CrackAmount %.2f -> 0' % (p, v))
print('stone MIs with cracks on:', len(todo), '| base materials behind them:', sorted(b.split('/')[-1] for b in bases))
# base materials used DIRECTLY by placed meshes (an MI can't override those)
direct = set()
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            if isinstance(m, unreal.Material) and m.get_path_name().split('.')[0] in bases: direct.add((m.get_name(), a.get_actor_label()))
for m, a in sorted(direct): print('BASE MATERIAL used directly (set its CrackAmount default to 0 by hand):', m, 'on', a)
if '--apply' not in A: print('DRY RUN: nothing changed'); raise SystemExit
for p, v in todo:
    mi = unreal.load_asset(p); bk.setdefault(p, v)
    MEL.set_material_instance_scalar_parameter_value(mi, 'CrackAmount', 0.0); MEL.update_material_instance(mi); EAL.save_loaded_asset(mi)
json.dump(bk, open(BK, 'w'), indent=1)
print('APPLIED: CrackAmount 0 on', len(todo), 'MIs (saved). Revert: --revert')
