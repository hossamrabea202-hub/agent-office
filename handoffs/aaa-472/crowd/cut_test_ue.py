# i5 #493: which per-frame costs can be cut. Play only, each step put back, nothing saved. CSV capture per step, 6 s each.
import time, unreal
GS, SL, ELL = unreal.GameplayStatics, unreal.SystemLibrary, unreal.EditorLevelLibrary
L = lambda p: unreal.load_asset(p).generated_class()
ZC = [L('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'), L('/Game/CastleDefender/Characters/Enemies/FleshBrute/BP_FleshBrute')]
SC = L('/Game/CastleDefender/Characters/Knight/BP_SoldierSword')
def W(): return ELL.get_game_world()
def zs():
    o = []
    for c in ZC: o += list(GS.get_all_actors_of_class(W(), c))
    return o
keep = {}
def navwalk(on):
    for z in zs():
        cm = z.get_component_by_class(unreal.CharacterMovementComponent)
        if not cm: continue
        if on:
            keep[z.get_name()] = cm.movement_mode
            if cm.movement_mode == unreal.MovementMode.MOVE_WALKING: cm.set_movement_mode(unreal.MovementMode.MOVE_NAV_WALKING)
        elif keep.get(z.get_name()) == unreal.MovementMode.MOVE_WALKING and cm.movement_mode == unreal.MovementMode.MOVE_NAV_WALKING:
            cm.set_movement_mode(unreal.MovementMode.MOVE_WALKING)
def meshcol(on):
    for z in zs():
        me = z.get_component_by_class(unreal.SkeletalMeshComponent)
        if not me: continue
        if on: keep['m' + z.get_name()] = me.get_collision_enabled(); me.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        elif 'm' + z.get_name() in keep: me.set_collision_enabled(keep['m' + z.get_name()])
def soldiers(on):
    for s in GS.get_all_actors_of_class(W(), SC): s.set_actor_tick_enabled(not on)
def con(c): SL.execute_console_command(W(), c)
STEPS = [('BASE', None), ('A zombies NavWalking', navwalk), ('BASE', None), ('B zombie mesh collision off', meshcol), ('BASE', None),
         ('C soldier tick off', soldiers), ('BASE', None), ('D HUD off', lambda on: con('showhud')), ('BASE', None)]
S = {'last': time.perf_counter(), 'p': 'wait', 't': 0.0, 'i': 0, 'buf': []}
def tick(dt):
    if not W(): unreal.unregister_slate_post_tick_callback(H); print('cut: Play ended'); return
    if GS.is_game_paused(W()): GS.set_game_paused(W(), False)
    now = time.perf_counter(); dt = now - S['last']; S['last'] = now; S['t'] += dt
    if S['p'] == 'wait':
        if len(zs()) < 100 and S['t'] < 150: return
        S['p'] = 'start'
    if S['p'] == 'start':
        f = STEPS[S['i']][1]
        if f: f(True)
        S.update(p='settle', t=0.0); return
    if S['p'] == 'settle' and S['t'] > 1.0: con('csvprofile start'); S.update(p='run', t=0.0, buf=[]); return
    if S['p'] == 'run':
        S['buf'].append(dt)
        if S['t'] >= 6.0:
            con('csvprofile stop'); b = S['buf']; nm, f = STEPS[S['i']]
            print('cut RESULT %-30s %6.1f ms, %d frames, %d zombies, %d soldiers' % (nm, 1000 * sum(b) / len(b), len(b), len(zs()), len(GS.get_all_actors_of_class(W(), SC))))
            if f: f(False)
            S['i'] += 1
            if S['i'] >= len(STEPS): unreal.unregister_slate_post_tick_callback(H); print('cut DONE'); return
            S.update(p='gap', t=0.0)
    if S['p'] == 'gap' and S['t'] > 0.8: S['p'] = 'start'
H = unreal.register_slate_post_tick_callback(tick)
print('cut: started, zombies', len(zs()))
