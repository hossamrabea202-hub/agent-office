# #440 (i5): read-only: the landscape material instance chain + parameters. Aborts in PIE.
import unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
MEL = unreal.MaterialEditingLibrary
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if 'Landscape' not in a.get_class().get_name(): continue
    try: m = a.get_editor_property('landscape_material')
    except Exception: m = None
    print('LAND', a.get_actor_label(), a.get_class().get_name(), m.get_path_name() if m else None, [round(v) for v in a.get_actor_location().to_tuple()])
mi = unreal.load_asset('/Game/CastleDefender/Environment/Mountains/Materials/MI_MountainBackdrop_Near')
p = mi
while isinstance(p, unreal.MaterialInstance): print('CHAIN', p.get_path_name()); p = p.get_editor_property('parent')
print('BASE', p.get_path_name() if p else None)
for n in MEL.get_scalar_parameter_names(mi): print('  S', n, round(MEL.get_material_instance_scalar_parameter_value(mi, n), 3))
for n in MEL.get_vector_parameter_names(mi): v = MEL.get_material_instance_vector_parameter_value(mi, n); print('  V', n, [round(x, 3) for x in (v.r, v.g, v.b, v.a)])
for n in MEL.get_texture_parameter_names(mi): t = MEL.get_material_instance_texture_parameter_value(mi, n); print('  T', n, t.get_path_name() if t else None)
