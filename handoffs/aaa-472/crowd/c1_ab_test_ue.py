# i5 #493 C1 A/B in Play: 150 x Zc0 (plain copy) then 150 x Zc1 (copy + BPC_CrowdTier), same spots, 8 s CSV each. Spawned zombies are destroyed after.
import math, random, time, unreal
GS, SL, ELL = unreal.GameplayStatics, unreal.SystemLibrary, unreal.EditorLevelLibrary
F = '/Game/_i5tmpC1z'; C0, C1 = [unreal.load_asset(F + n).generated_class() for n in ('/Zc0', '/Zc1')]
def W(): return ELL.get_game_world()
random.seed(7); SPOTS = [(math.cos(a) * r, math.sin(a) * r) for a, r in ((random.uniform(0, 6.283), random.uniform(1000, 7000)) for _ in range(150))]
live = []
def spawn(cls):
    p = GS.get_player_pawn(W(), 0).get_actor_location()
    for dx, dy in SPOTS:
        a = GS.begin_deferred_actor_spawn_from_class(W(), cls, unreal.Transform(p + unreal.Vector(dx, dy, 150), unreal.Rotator(0, 0, 0)), unreal.SpawnActorCollisionHandlingMethod.ADJUST_IF_POSSIBLE_BUT_ALWAYS_SPAWN)
        a = GS.finish_spawning_actor(a, unreal.Transform(p + unreal.Vector(dx, dy, 150), unreal.Rotator(0, 0, 0)))
        if a:
            live.append(a)
            if not a.get_controller(): a.spawn_default_controller()
def clear():
    for a in live:
        try: a.destroy_actor()
        except Exception: pass
    live.clear()
def off():
    return sum(1 for a in live if a.get_component_by_class(unreal.SkeletalMeshComponent) and a.get_component_by_class(unreal.SkeletalMeshComponent).get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION)
def con(c): SL.execute_console_command(W(), c)
PH = [('A plain', C0), ('B CrowdTier', C1), ('A plain again', C0)]
S = {'last': time.perf_counter(), 'p': 'start', 't': 0.0, 'i': 0, 'buf': []}
def tick(dt):
    if not W(): unreal.unregister_slate_post_tick_callback(H); print('ab: Play ended'); return
    try:
        if GS.is_game_paused(W()): GS.set_game_paused(W(), False)
        now = time.perf_counter(); dt = now - S['last']; S['last'] = now; S['t'] += dt
        if S['p'] == 'start': spawn(PH[S['i']][1]); print('ab: spawned', len(live), PH[S['i']][0]); S.update(p='settle', t=0.0); return
        if S['p'] == 'settle' and S['t'] > 4.0: con('csvprofile start'); S.update(p='run', t=0.0, buf=[]); return
        if S['p'] == 'run':
            S['buf'].append(dt)
            if S['t'] >= 8.0:
                con('csvprofile stop'); b = S['buf']
                print('ab RESULT %-14s %6.1f ms, %d frames, %d spawned, %d body collision off' % (PH[S['i']][0], 1000 * sum(b) / len(b), len(b), len(live), off()))
                clear(); S['i'] += 1
                if S['i'] >= len(PH): unreal.unregister_slate_post_tick_callback(H); print('ab DONE'); return
                S.update(p='gap', t=0.0)
        if S['p'] == 'gap' and S['t'] > 1.5: S['p'] = 'start'
    except Exception as e:
        unreal.unregister_slate_post_tick_callback(H); print('ab: ERROR, stopped:', e); clear()
H = unreal.register_slate_post_tick_callback(tick)
print('ab: started')
