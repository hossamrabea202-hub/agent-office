# #259 Play check (i5, by script): farmers' positions vs the main gate (x -151) and the farm plots' stage, in PIE.
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
acts = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
t = unreal.GameplayStatics.get_time_seconds(w)
print('game time %.0f s, paused %s' % (t, unreal.GameplayStatics.is_game_paused(w)))
for a in acts:
    cn = a.get_class().get_name()
    if 'Farmer' in cn:
        l = a.get_actor_location(); print('farmer %-24s (%6.0f, %6.0f, %5.0f) %s' % (a.get_name()[-24:], l.x, l.y, l.z, 'OUTSIDE gate' if l.x < -151 else 'inside'))
    if 'Plot' in cn or 'Farm' in cn and 'Farmer' not in cn:
        l = a.get_actor_location(); st = ''
        for k in ('Stage', 'GrowStage', 'Growth'):
            try: st += '%s=%s ' % (k, a.get_editor_property(k))
            except Exception: pass
        print('plot   %-24s (%6.0f, %6.0f) %s %s' % (a.get_name()[-24:], l.x, l.y, cn, st))
