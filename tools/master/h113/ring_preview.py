import unreal, traceback, os
OUT = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
FLAG = r'C:\Unreal Backups\Castle Defender\Tools\master\h113\preview_mode.txt'
mode = open(FLAG, encoding='utf-8-sig').read().strip() if os.path.exists(FLAG) else 'spawn'
L = []
try:
    EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if mode == 'spawn':
        cls = unreal.load_class(None, '/Game/Codex/AssignmentMarkers102_v1/BP_AssignmentMarker102.BP_AssignmentMarker102_C')
        base = unreal.Vector(1000, 1130, 2)
        D = '/Game/Codex/AssignmentMarkers102_v1'
        spawned = []
        for i in range(4):
            a = EAS.spawn_actor_from_class(cls, base + unreal.Vector(0, i * 160, 0), unreal.Rotator(0, 0, 0))
            a.set_actor_label('TMP_Marker102_preview_%d' % i)
            a.set_actor_hidden_in_game(False)
            # preview MIs for styles 1..4 so the four styles can be compared
            for c in a.get_components_by_class(unreal.DecalComponent):
                c.set_editor_property('decal_material', unreal.load_asset('%s/MI_Assignment102_Ground_%d' % (D, i + 1)))
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                c.set_material(0, unreal.load_asset('%s/MI_Assignment102_Air_%d' % (D, i + 1)))
            spawned.append(a.get_name())
        ues.set_level_viewport_camera_info(base + unreal.Vector(-420, 240, 300), unreal.Rotator(0, -35, 0))
        L.append('spawned %s' % spawned)
    else:
        n = 0
        for a in EAS.get_all_level_actors():
            if a.get_actor_label().startswith('TMP_Marker102_preview'):
                EAS.destroy_actor(a); n += 1
        L.append('destroyed %d' % n)
except Exception:
    L.append(traceback.format_exc())
open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
