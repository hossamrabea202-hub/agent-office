# Run in the editor Python console WHILE Play/PIE is running (or after). Reports what the trail ISM really uses in the game world.
import unreal, traceback
L = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
out = []
try:
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    gw = ues.get_game_world(); ew = ues.get_editor_world()
    out.append('PIE world: %s' % (gw.get_name() if gw else None))
    cls = unreal.load_class(None, '/Game/CastleDefender/Gameplay/JellyTrail/BP_JellyTrailManager.BP_JellyTrailManager_C')
    for tag, w in (('GAME', gw), ('EDITOR', ew)):
        if not w: continue
        for a in unreal.GameplayStatics.get_all_actors_of_class(w, cls):
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                m = c.get_material(0)
                out.append('%s %s.%s mat=%s mesh=%s instances=%d customFloats=%d visible=%s' % (tag, a.get_name(), c.get_name(), m.get_path_name() if m else None,
                    c.static_mesh.get_name() if c.static_mesh else None, c.get_instance_count(), c.get_editor_property('num_custom_data_floats'), c.is_visible()))
        # any other ISM in the game world that uses a JellyTrail material (someone else drawing trails?)
        for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
            for c in a.get_components_by_class(unreal.PrimitiveComponent):
                for i in range(c.get_num_materials()):
                    m = c.get_material(i)
                    if m and 'JellyTrail' in m.get_path_name() and not isinstance(a, cls):
                        out.append('%s OTHER %s.%s[%d] = %s' % (tag, a.get_name(), c.get_name(), i, m.get_path_name()))
    v2 = unreal.load_asset('/Game/CastleDefender/VFX/JellyTrail/M_JellyTrail_v2')
    out.append('v2 blend=%s ISMusage=%s' % (v2.get_editor_property('blend_mode'), v2.get_editor_property('used_with_instanced_static_meshes')))
except Exception:
    out.append(traceback.format_exc())
open(L, 'w').write('\n'.join(out))
