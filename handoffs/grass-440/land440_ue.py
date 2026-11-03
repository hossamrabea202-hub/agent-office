# #440 ground colour (i5, 2026-11-03): the meadow ground measured ~35 sRGB in base colour (KB targets: bare soil ~0.13 linear
# ~100 sRGB, green grass ~0.21 linear ~127 sRGB, Epic measured values). Cause: MI_MountainBackdrop_Near GrassTint (0.27,0.30,0.17)
# and ForestTint (0.085,0.09,0.06). NEW child MI only; the live MI is never edited. Aborts in PIE.
#   py land440_ue.py mi <gr,gg,gb> <fr,fg,fb>                  create / update MI_MountainBackdrop_Near_440 (saved)
#   py land440_ue.py assign [--only 3_3_0,3_4_0,...] [--dry-run] put it on the landscape proxies (all, or the listed tiles)
#   py land440_ue.py revert                                     back to MI_MountainBackdrop_Near on every proxy that has _440
import sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]; mode = A[0]
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
D = '/Game/CastleDefender/Environment/Mountains/Materials/'
OLD, NEW = D + 'MI_MountainBackdrop_Near', D + 'MI_MountainBackdrop_Near_440'
if mode == 'mi':
    g, f = [float(v) for v in A[1].split(',')], [float(v) for v in A[2].split(',')]
    mi = unreal.load_asset(NEW) if EAL.does_asset_exist(NEW) else unreal.AssetToolsHelpers.get_asset_tools().create_asset('MI_MountainBackdrop_Near_440', D[:-1], unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset(OLD))
    MEL.set_material_instance_vector_parameter_value(mi, 'GrassTint', unreal.LinearColor(g[0], g[1], g[2], 1))
    MEL.set_material_instance_vector_parameter_value(mi, 'ForestTint', unreal.LinearColor(f[0], f[1], f[2], 1))
    MEL.update_material_instance(mi); EAL.save_loaded_asset(mi); print('MI', NEW, 'GrassTint', g, 'ForestTint', f); raise SystemExit
only = A[A.index('--only') + 1].split(',') if '--only' in A else None
n = 0
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if 'LandscapeStreamingProxy' not in a.get_class().get_name(): continue
    tile = a.get_actor_label().replace('LandscapeStreamingProxy_', '')
    cur = a.get_editor_property('landscape_material'); cn = cur.get_path_name().split('.')[0] if cur else ''
    if mode == 'assign':
        if only and tile not in only: continue
        if cn != OLD: print('SKIP', tile, cn); continue
        n += 1
        if '--dry-run' in A: continue
        a.modify(); a.editor_set_landscape_material(unreal.load_asset(NEW))       # rebuilds the component MICs (a raw set_editor_property does not)
    elif mode == 'revert':
        if cn != NEW: continue
        n += 1; a.modify(); a.editor_set_landscape_material(unreal.load_asset(OLD))
print(mode, ('(dry run) ' if '--dry-run' in A else '') + 'proxies:', n)
