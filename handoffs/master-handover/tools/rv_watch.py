import unreal, os, json
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
LOG = os.path.join(D, 'rv_watch_log.txt')
GS = unreal.GameplayStatics
try:
    for h in _RVH: unreal.unregister_slate_post_tick_callback(h)
except NameError: pass
_RVH = []
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
acts = GS.get_all_actors_of_class(gw, unreal.Actor)
vit = [a for a in acts if a.get_class().get_name() == 'BP_TentacleVitals_C']
cannons = [a for a in acts if a.get_class().get_name() == 'BP_Cannon_C']
def comp(v): return [c for c in v.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name() == 'BPC_TentacleStrike_C'][0]
def brk(c):
    k = [x for x in c.get_components_by_class(unreal.ActorComponent) if x.get_class().get_name() == 'BPC_CannonBreak_C']
    return k[0].get_editor_property('HP') if k else None
open(LOG, 'w').write('')
S = {'next': 0.0, 'end': GS.get_time_seconds(gw) + 16.0}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None:
        for h in _RVH: unreal.unregister_slate_post_tick_callback(h)
        return
    t = GS.get_time_seconds(w)
    if t < S['next']: return
    S['next'] = t + 0.5
    row = ['t=%.1f' % t]
    for v in vit:
        c = comp(v); st = c.get_editor_property('State')
        if st or c.get_editor_property('RevengePending') or not c.get_editor_property('ShieldArmed') or not c.get_editor_property('HPArmed'):
            tc = c.get_editor_property('TargetCannon'); la = c.get_editor_property('LastAttacker')
            row.append('%s st=%d pend=%s hpA=%s shA=%s tgt=%s la=%s' % (v.get_actor_label(), st, c.get_editor_property('RevengePending'), c.get_editor_property('HPArmed'), c.get_editor_property('ShieldArmed'), tc.get_actor_label() if tc else None, la.get_actor_label() if la else None))
    hp = ['%s=%s' % (c.get_actor_label(), brk(c)) for c in cannons if brk(c) is not None]
    row.append('cannonHP ' + ' '.join(hp))
    open(LOG, 'a').write(' | '.join(row) + '\n')
    if t > S['end']:
        for h in _RVH: unreal.unregister_slate_post_tick_callback(h)
_RVH.append(unreal.register_slate_post_tick_callback(tick))
