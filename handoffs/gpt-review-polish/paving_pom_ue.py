# #451 courtyard cobbles POM smear (i5, 2026-11-03). MI_Castle_Paving_POM uses parallax occlusion with Depth 0.025; at
# grazing angles the cobbles smear into "hairy" streaks (shots/pair_courtyard_cobbles.png). Real setts are 4-8 cm proud
# of their joints but we look at them from 1.7 m over 10-30 m: AAA practice is a shallower POM depth (or more steps) so
# silhouettes don't shear. NEW child instance MI_Castle_Paving_POM_451 (Depth = DEPTH) on Castle_CourtyardFloor_Single only.
# MI_Castle_Paving_POM / M_Castle_Paving_POM are NOT edited. Does not save the map (saves the new MI).
#   py paving_pom_ue.py [--depth 0.012] --dry-run | --apply | --revert        (backup paving_pom_backup.json)
import json, os, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/'
A = sys.argv[1:]
DEPTH = float(A[A.index('--depth') + 1]) if '--depth' in A else 0.012
BK = H + 'paving_pom_backup.json'
SRC = '/Game/CastleDefender/Shared/Materials/Castle/MI_Castle_Paving_POM'
NEW = '/Game/CastleDefender/Shared/Materials/Castle/POM451/MI_Castle_Paving_POM_451'
EAS, EAL, MEL = unreal.get_editor_subsystem(unreal.EditorActorSubsystem), unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
floor = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == 'Castle_CourtyardFloor_Single']
if '--revert' in A:
    bk = json.load(open(BK))
    for a in floor:
        if a.get_path_name() in bk: a.modify(); a.static_mesh_component.set_material(0, unreal.load_asset(bk[a.get_path_name()])); print('reverted', a.get_actor_label())
    raise SystemExit
print('%s: %d floor actor(s), POM Depth %.3f -> %.3f' % ('APPLY' if '--apply' in A else 'DRY RUN', len(floor), MEL.get_material_instance_scalar_parameter_value(unreal.load_asset(SRC), 'Depth'), DEPTH))
if '--apply' in A:
    if EAL.does_asset_exist(NEW): mi = unreal.load_asset(NEW)
    else:
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NEW.split('/')[-1], NEW.rsplit('/', 1)[0], unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, unreal.load_asset(SRC))
    MEL.set_material_instance_scalar_parameter_value(mi, 'Depth', DEPTH); MEL.update_material_instance(mi); EAL.save_asset(NEW)
    bk = json.load(open(BK)) if os.path.exists(BK) else {}
    for a in floor:
        c = a.static_mesh_component; bk.setdefault(a.get_path_name(), c.get_materials()[0].get_path_name())
        a.modify(); c.set_material(0, mi)
    json.dump(bk, open(BK, 'w'), indent=0)
