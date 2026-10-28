import unreal, traceback
OUT = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
STEP = r'C:\Unreal Backups\Castle Defender\Tools\master\ts_test_step.txt'
step = open(STEP, encoding='utf-8-sig').read().strip()
L = []
try:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if step == 'sim':
        les.editor_play_simulate(); L.append('simulate started')
    elif step == 'end':
        les.editor_request_end_play(); L.append('simulate ended')
    else:
        w = ues.get_game_world()
        L.append('t=%.1f' % unreal.GameplayStatics.get_time_seconds(w))
        acts = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
        sold = [a for a in acts if 'Soldier' in a.get_class().get_name()]
        marks = [a for a in acts if 'AssignmentMarker102' in a.get_class().get_name()]
        L.append('soldiers %d markers %d' % (len(sold), len(marks)))
        for s in sold[:8]:
            comps = [c for c in s.get_components_by_class(unreal.ActorComponent) if 'AssignmentRing' in c.get_name()]
            ordc = [c for c in s.get_components_by_class(unreal.SceneComponent) if c.get_name() == 'Order']
            ox = ordc[0].get_editor_property('relative_location').x if ordc else None
            c = comps[0] if comps else None
            L.append('%s cls=%s loc=%s Order.X=%s LastStyle=%s Marker=%s' % (s.get_name()[-14:], s.get_class().get_name(), s.get_actor_location(), ox, c.get_editor_property('LastStyle') if c else None, c.get_editor_property('Marker').get_name() if c and c.get_editor_property('Marker') else None))
        for m in marks[:8]:
            L.append('%s owner=%s loc=%s hidden=%s alive=%s' % (m.get_name(), m.get_owner().get_name()[-14:] if m.get_owner() else None, m.get_actor_location(), m.get_editor_property('hidden'), m.get_editor_property('MarkerAlive')))
        if step == 'style':
            # push style 1..7 across markers for a visual check
            for i, m in enumerate(marks[:8]):
                m.call_method('SetAssignment102', args=(i % 8,))
            L.append('styles pushed 0..7')
except Exception:
    L.append(traceback.format_exc())
open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
try:
    if step == 'shot':
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1920x1080')
        open(OUT, 'a', encoding='utf-8').write('\nshot requested')
except Exception:
    open(OUT, 'a', encoding='utf-8').write('\n' + traceback.format_exc())
try:
    if step == 'cam':
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        ues.set_level_viewport_camera_info(unreal.Vector(1000 - 450, 1190 - 350, 92 + 320), unreal.Rotator(0, -35, 38))
        open(OUT, 'a', encoding='utf-8').write('\ncamera set')
except Exception:
    open(OUT, 'a', encoding='utf-8').write('\n' + traceback.format_exc())
try:
    if step == 'show':
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        acts = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
        marks = [a for a in acts if 'AssignmentMarker102' in a.get_class().get_name()]
        for i, m in enumerate(marks):
            o = m.get_owner()
            if o:
                m.set_actor_location(o.get_actor_location() - unreal.Vector(0, 0, 90), False, True)
            m.set_actor_hidden_in_game(False)
            m.call_method('SetAssignment102', args=((i + 1) % 8,))
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        ues.set_level_viewport_camera_info(unreal.Vector(1000 - 520, 1190 - 420, 92 + 330), unreal.Rotator(0, -32, 40))
        open(OUT, 'a', encoding='utf-8').write('\nforced visible %d markers' % len(marks))
except Exception:
    open(OUT, 'a', encoding='utf-8').write('\n' + traceback.format_exc())
