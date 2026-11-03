# #440 phase B ground colour (i5, 2026-11-03). M_MountainBackdrop line 113: grass = lerp(gl*GrassTint*2.2, ForestTint*(0.35+gl*2.6), noise), so
# GrassTint and ForestTint DO drive the meadow (the old "untinted soil" guess was wrong). The grass scan is very dark (luminance 0.038),
# so today's tints give open ground ~40 sRGB (measured on the Master ~35). The old test changed nothing because per-proxy sets don't
# stick. So this edits the Landscape's own MI, MI_MountainBackdrop_Near: asset only, no map save. Live MI edit, hence backup + revert.
# Target open meadow ~0.10 linear (~89 sRGB), G above R (living grass), forest floor ~0.085 linear. KB: soil 0.13, grass 0.21.
#   py land440b_ue.py --dry-run                  which landscapes use the MI, old -> new (nothing changed)
#   py land440b_ue.py --apply                    set + save the MI; backup land440b_backup.json
#   py land440b_ue.py --apply --grass 1.0,1.2,0.6 --forest 0.15,0.18,0.1     softer values
#   py land440b_ue.py --revert                   old tints back
# Aborts in PIE.
import json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
MEL, EAL = unreal.MaterialEditingLibrary, unreal.EditorAssetLibrary
HERE = next(h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/grass-440/', 'C:/Users/hossa/Documents/agent-office/handoffs/grass-440/') if os.path.isdir(h))
BK = HERE + 'land440b_backup.json'
MI = '/Game/CastleDefender/Environment/Mountains/Materials/MI_MountainBackdrop_Near'
arg = lambda k, d: [float(x) for x in A[A.index(k) + 1].split(',')] if k in A else d
GRASS, FOREST = arg('--grass', [1.25, 1.5, 0.72]), arg('--forest', [0.2, 0.24, 0.13])
mi = unreal.load_asset(MI)
get = lambda n: list(MEL.get_material_instance_vector_parameter_value(mi, n).to_tuple())
def put(n, v): MEL.set_material_instance_vector_parameter_value(mi, n, unreal.LinearColor(v[0], v[1], v[2], 1.0))
if '--revert' in A:
    d = json.load(open(BK)); put('GrassTint', d['GrassTint']); put('ForestTint', d['ForestTint']); MEL.update_material_instance(mi); EAL.save_loaded_asset(mi); os.remove(BK)
    print('REVERTED', d); raise SystemExit
users = {}
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if isinstance(a, unreal.LandscapeProxy):
        m = a.get_editor_property('landscape_material'); k = m.get_name() if m else 'None'
        users.setdefault(k, []).append(a.get_class().get_name())
print('landscape materials:', {k: len(v) for k, v in users.items()})
print('GrassTint', [round(x, 3) for x in get('GrassTint')[:3]], '->', GRASS, '| ForestTint', [round(x, 3) for x in get('ForestTint')[:3]], '->', FOREST)
if '--apply' not in A: print('dry run: nothing changed'); raise SystemExit
if not os.path.exists(BK): json.dump({'GrassTint': get('GrassTint'), 'ForestTint': get('ForestTint')}, open(BK, 'w'), indent=1)
put('GrassTint', GRASS); put('ForestTint', FOREST); MEL.update_material_instance(mi); EAL.save_loaded_asset(mi)
print('APPLIED + saved', MI.split('/')[-1], '| no map save. Look at the meadow lit, then base colour: open ground should read about 80-100 sRGB')
