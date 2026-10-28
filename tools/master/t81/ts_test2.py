import unreal, os, time
OUT = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
STEP = r'C:\Unreal Backups\Castle Defender\Tools\master\ts_test_step.txt'
step = open(STEP, encoding='utf-8-sig').read().strip()
lines = []
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if step == 'sim':
    les.editor_play_simulate()
    lines.append('simulate started')
elif step == 'end':
    les.editor_request_end_play()
    lines.append('simulate ended')
else:
    w = ues.get_game_world()
    lines.append('world %s t=%.1f' % (w.get_name() if w else None, unreal.GameplayStatics.get_time_seconds(w) if w else -1))
    if w:
        acts = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
        tent = [a for a in acts if 'TentacleVitals' in a.get_name()]
        blobs = [a for a in acts if 'JellyBlob' in a.get_name()]
        zomb = [a for a in acts if 'Zombie' in a.get_name()]
        lines.append('tentacles %d blobs %d zombies %d' % (len(tent), len(blobs), len(zomb)))
        if step == 'hit' and tent:
            t = tent[0]
            comps = [c for c in t.get_components_by_class(unreal.ActorComponent) if 'TentacleSpit' in c.get_name()]
            lines.append('tent %s loc=%s comps=%s' % (t.get_name(), t.get_actor_location(), [c.get_name() for c in comps]))
            if comps:
                c = comps[0]
                for i in range(3):
                    c.call_method('OnTentacleHit', args=(t, 10.0, None, None, None))
                lines.append('hit x3 HitCount=%s NextSpitT=%s' % (c.get_editor_property('HitCount'), c.get_editor_property('NextSpitT')))
                acts = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
                blobs = [a for a in acts if 'JellyBlob' in a.get_name()]
        for b in blobs:
            try:
                am = b.get_editor_property('ArmedMax')
            except Exception as e:
                am = 'err'
            lines.append('%s loc=%s vel=%s ArmedMax=%s' % (b.get_name(), b.get_actor_location(), b.get_velocity(), am))
        for z in zomb[:12]:
            try:
                m = z.get_editor_property('Mesh'); r = m.get_editor_property('GlobalAnimRateScale')
            except Exception as e:
                r = 'err'
            lines.append('%s loc=%s rate=%s' % (z.get_name(), z.get_actor_location(), r))
open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
